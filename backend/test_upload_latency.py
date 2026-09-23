#!/usr/bin/env python3
"""Time the real upload embedding path (OpenAI + Supabase). Writes embeddings for one sample product."""

from __future__ import annotations

import json
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def timed(label: str):
    class _Timer:
        def __enter__(self):
            self.t0 = time.perf_counter()
            print(f"→ {label} ...", flush=True)
            return self

        def __exit__(self, exc_type, exc, tb):
            ms = (time.perf_counter() - self.t0) * 1000
            status = "FAIL" if exc else "ok"
            print(f"← {label}: {status} ({ms:.0f} ms)", flush=True)

    return _Timer()


def main() -> None:
    sample_dir = Path(__file__).resolve().parent.parent / "sample_data"
    sample_path = sorted(sample_dir.glob("*.json"))[0]
    product = json.loads(sample_path.read_text(encoding="utf-8"))
    product_id = product["product_id"]
    description = product["description"]
    reviews = product.get("reviews", [])

    print("=== Upload-path latency probe ===")
    print(f"sample: {sample_path.name}")
    print(f"product_id: {product_id}")
    print(f"reviews: {len(reviews)}")
    print()

    with timed("import vector_store"):
        from vector_store import _embed_texts, search_similar_content
        from database.supabase_client import supabase

    with timed("supabase insert product"):
        supabase.table("products").insert(
            {
                "id": product_id,
                "name": product["name"],
                "description": description,
                "image": product.get("image"),
                "reviews": reviews,
            }
        ).execute()

    documents = [description] + [r.get("content", "") for r in reviews]

    with timed(f"openai embed {len(documents)} texts"):
        embeddings = _embed_texts(documents)

    rows = []
    for idx, (content, embedding) in enumerate(zip(documents, embeddings)):
        if idx == 0:
            rows.append(
                {
                    "id": f"{product_id}_description",
                    "product_id": product_id,
                    "content_type": "description",
                    "content": content,
                    "review_id": None,
                    "rating": None,
                    "review_date": None,
                    "review_index": None,
                    "embedding": embedding,
                }
            )
        else:
            review = reviews[idx - 1]
            rows.append(
                {
                    "id": f"{product_id}_review_{idx - 1}",
                    "product_id": product_id,
                    "content_type": "review",
                    "content": content,
                    "review_id": review.get("review_id", f"review_{idx - 1}"),
                    "rating": str(review.get("rating", "N/A")),
                    "review_date": str(review.get("date") or ""),
                    "review_index": idx - 1,
                    "embedding": embedding,
                }
            )

    with timed("supabase insert embeddings"):
        batch_size = 50
        for start in range(0, len(rows), batch_size):
            supabase.table("document_embeddings").insert(rows[start : start + batch_size]).execute()

    with timed("verification search_similar_content"):
        probe = search_similar_content(product_id, description[:80] or "product", top_k=1)
        print(f"   hits={len(probe.get('documents') or [])}")

    print()
    print("If openai embed is ~1-2s but supabase/verify is huge → DB/RPC. "
          "If this script is fast but upload_sample_data.py is slow → FastAPI/upload path.")


if __name__ == "__main__":
    main()
