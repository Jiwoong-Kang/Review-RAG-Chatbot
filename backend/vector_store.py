import os

import httpx
from openai import OpenAI, OpenAIError
from postgrest.exceptions import APIError

from database.supabase_client import supabase

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

_STORE_ERRORS = (APIError, httpx.HTTPError, OpenAIError)


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Encode texts via OpenAI into vectors for cosine similarity."""
    if not texts:
        return []

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    # API may not return data in input order; sort by index
    sorted_data = sorted(response.data, key=lambda item: item.index)
    return [item.embedding for item in sorted_data]


def _review_embedding_row(product_id: str, review: dict, review_index: int, embedding: list[float]) -> dict:
    return {
        "id": f"{product_id}_review_{review_index}",
        "product_id": product_id,
        "content_type": "review",
        "content": review.get("content", ""),
        "review_id": review.get("review_id", f"review_{review_index}"),
        "rating": str(review.get("rating", "N/A")),
        "review_date": str(review.get("date") or ""),
        "review_index": review_index,
        "author_username": review.get("author_username") or None,
        "embedding": embedding,
    }


def create_embeddings(product_id: str, description: str, reviews: list[dict]):
    """Replace embeddings for a product without a delete-first gap.

    1. Embed texts (OpenAI failure leaves existing vectors untouched)
    2. Upsert new rows by primary key id
    3. Delete only stale ids for this product that were not in this build
    """
    documents = [description]
    rows_meta = [
        {
            "id": f"{product_id}_description",
            "product_id": product_id,
            "content_type": "description",
            "content": description,
            "review_id": None,
            "rating": None,
            "review_date": None,
            "review_index": None,
            "author_username": None,
        }
    ]

    for idx, review in enumerate(reviews):
        documents.append(review.get("content", ""))
        rows_meta.append(
            {
                "id": f"{product_id}_review_{idx}",
                "product_id": product_id,
                "content_type": "review",
                "content": review.get("content", ""),
                "review_id": review.get("review_id", f"review_{idx}"),
                "rating": str(review.get("rating", "N/A")),
                "review_date": str(review.get("date") or ""),
                "review_index": idx,
                "author_username": review.get("author_username") or None,
            }
        )

    embeddings = _embed_texts(documents)
    rows = [{**meta, "embedding": emb} for meta, emb in zip(rows_meta, embeddings)]
    new_ids = {row["id"] for row in rows}

    batch_size = 50
    for start in range(0, len(rows), batch_size):
        supabase.table("document_embeddings").upsert(
            rows[start : start + batch_size]
        ).execute()

    existing = (
        supabase.table("document_embeddings")
        .select("id")
        .eq("product_id", product_id)
        .execute()
    )
    stale_ids = [row["id"] for row in (existing.data or []) if row["id"] not in new_ids]
    if stale_ids:
        supabase.table("document_embeddings").delete().in_("id", stale_ids).execute()

    print(f"✓ Created embeddings for product {product_id}: {len(rows)} documents")
    print("  - Description: 1")
    print(f"  - Reviews: {len(reviews)}")
    if stale_ids:
        print(f"  - Removed stale vectors: {len(stale_ids)}")

    try:
        probe = search_similar_content(product_id, description[:80] or "product", top_k=1)
        if probe["documents"]:
            print("  - Verification: Embeddings successfully saved ✓")
        else:
            print("  - WARNING: Verification failed - no embeddings found!")
    except _STORE_ERRORS as e:
        print(f"  - WARNING: Could not verify embeddings: {e}")


def add_review_embedding(product_id: str, review: dict, review_index: int):
    """Embed and insert a single new review without touching existing vectors."""
    content = review.get("content", "")
    embedding = _embed_texts([content])[0]
    row = _review_embedding_row(product_id, review, review_index, embedding)
    supabase.table("document_embeddings").insert(row).execute()
    print(f"✓ Added review embedding for product {product_id} (index {review_index})")


def search_similar_content(
    product_id: str,
    query: str,
    top_k: int = 5,
    content_type: str | None = None,
):
    """Search embeddings via pgvector. Optionally keep only one content_type (e.g. 'review')."""
    try:
        query_embedding = _embed_texts([query])[0]
        # Over-fetch when filtering so we still return up to top_k matches of that type
        match_count = top_k * 3 if content_type else top_k
        result = supabase.rpc(
            "match_document_embeddings",
            {
                "query_embedding": query_embedding,
                "match_product_id": product_id,
                "match_count": match_count,
            },
        ).execute()

        rows = result.data or []
        if content_type:
            rows = [row for row in rows if row.get("content_type") == content_type][:top_k]

        ids = []
        documents = []
        metadatas = []
        distances = []

        for row in rows:
            ids.append(row["id"])
            documents.append(row["content"])
            metadatas.append(
                {
                    "type": row["content_type"],
                    "product_id": row["product_id"],
                    "review_id": row.get("review_id") or "",
                    "rating": row.get("rating") or "N/A",
                    "date": row.get("review_date") or "",
                    "index": row.get("review_index"),
                    "author_username": row.get("author_username") or "",
                }
            )
            similarity = row.get("similarity")
            distances.append(1.0 - float(similarity) if similarity is not None else 1.0)

        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances,
        }
    except _STORE_ERRORS as e:
        print(f"Error searching: {e}")
        return {"ids": [], "documents": [], "metadatas": [], "distances": []}


def delete_embeddings(product_id: str):
    """Delete embeddings for a product (also cascaded when the product row is deleted)."""
    try:
        supabase.table("document_embeddings").delete().eq("product_id", product_id).execute()
        print(f"✓ Deleted embeddings for product {product_id}")
    except _STORE_ERRORS as e:
        print(f"Error deleting embeddings: {e}")


def get_all_reviews_summary(product_id: str):
    """Get summary of all reviews for a product from stored embedding rows."""
    try:
        result = (
            supabase.table("document_embeddings")
            .select("content_type, content, rating, review_index")
            .eq("product_id", product_id)
            .order("review_index")
            .execute()
        )

        reviews = []
        description = ""

        for row in result.data or []:
            if row["content_type"] == "description":
                description = row["content"]
            elif row["content_type"] == "review":
                reviews.append(
                    {
                        "content": row["content"],
                        "rating": row.get("rating") or "N/A",
                    }
                )

        return {
            "description": description,
            "reviews": reviews,
            "total_reviews": len(reviews),
        }
    except _STORE_ERRORS as e:
        print(f"Error getting summary: {e}")
        return {"description": "", "reviews": [], "total_reviews": 0}
