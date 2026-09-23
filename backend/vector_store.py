import os

from openai import OpenAI

from database.supabase_client import supabase

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


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


def create_embeddings(product_id: str, description: str, reviews: list[dict]):
    """Upsert embeddings for a product description and its reviews into Supabase pgvector."""
    # Replace any previous vectors for this product (re-upload / add-review safe)
    supabase.table("document_embeddings").delete().eq("product_id", product_id).execute()

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
        }
    ]

    for idx, review in enumerate(reviews):
        content = review.get("content", "")
        documents.append(content)
        rows_meta.append(
            {
                "id": f"{product_id}_review_{idx}",
                "product_id": product_id,
                "content_type": "review",
                "content": content,
                "review_id": review.get("review_id", f"review_{idx}"),
                "rating": str(review.get("rating", "N/A")),
                "review_date": str(review.get("date") or ""),
                "review_index": idx,
            }
        )

    embeddings = _embed_texts(documents)
    rows = []
    for meta, embedding in zip(rows_meta, embeddings):
        row = {**meta, "embedding": embedding}
        rows.append(row)

    # Supabase accepts batches; keep size modest for large review sets
    batch_size = 50
    for start in range(0, len(rows), batch_size):
        supabase.table("document_embeddings").insert(rows[start : start + batch_size]).execute()

    print(f"✓ Created embeddings for product {product_id}: {len(rows)} documents")
    print("  - Description: 1")
    print(f"  - Reviews: {len(reviews)}")

    try:
        probe = search_similar_content(product_id, description[:80] or "product", top_k=1)
        if probe["documents"]:
            print("  - Verification: Embeddings successfully saved ✓")
        else:
            print("  - WARNING: Verification failed - no embeddings found!")
    except Exception as e:
        print(f"  - WARNING: Could not verify embeddings: {e}")


def search_similar_content(product_id: str, query: str, top_k: int = 5):
    """Search for reviews/descriptions similar to the query via pgvector."""
    try:
        query_embedding = _embed_texts([query])[0]
        result = supabase.rpc(
            "match_document_embeddings",
            {
                "query_embedding": query_embedding,
                "match_product_id": product_id,
                "match_count": top_k,
            },
        ).execute()

        rows = result.data or []
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
    except Exception as e:
        print(f"Error searching: {e}")
        return {"ids": [], "documents": [], "metadatas": [], "distances": []}


def delete_embeddings(product_id: str):
    """Delete embeddings for a product (also cascaded when the product row is deleted)."""
    try:
        supabase.table("document_embeddings").delete().eq("product_id", product_id).execute()
        print(f"✓ Deleted embeddings for product {product_id}")
    except Exception as e:
        print(f"Error deleting embeddings: {e}")


def get_all_reviews_summary(product_id: str):
    """Get summary of all reviews for a product from stored embedding rows."""
    try:
        result = (
            supabase.table("document_embeddings")
            .select("content_type, content, rating")
            .eq("product_id", product_id)
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
    except Exception as e:
        print(f"Error getting summary: {e}")
        return {"description": "", "reviews": [], "total_reviews": 0}
