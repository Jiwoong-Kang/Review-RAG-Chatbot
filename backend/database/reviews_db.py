import httpx
from postgrest.exceptions import APIError

from .supabase_client import supabase

_DB_ERRORS = (APIError, httpx.HTTPError)


def _row_to_api(row: dict) -> dict:
    return {
        "review_id": row["review_id"],
        "content": row["content"],
        "rating": row.get("rating"),
        "date": row.get("review_date"),
        "author_username": row.get("author_username"),
    }


class ReviewDatabase:
    """Reviews stored as rows keyed by product_id (not JSONB on products)."""

    @staticmethod
    def list_reviews(product_id: str) -> list[dict]:
        try:
            result = (
                supabase.table("reviews")
                .select(
                    "review_id, content, rating, review_date, review_index, author_username"
                )
                .eq("product_id", product_id)
                .order("review_index")
                .execute()
            )
            return [_row_to_api(row) for row in (result.data or [])]
        except _DB_ERRORS as e:
            print(f"Error listing reviews: {e}")
            return []

    @staticmethod
    def count_reviews_by_product() -> dict[str, int]:
        try:
            result = supabase.table("reviews").select("product_id").execute()
            counts: dict[str, int] = {}
            for row in result.data or []:
                pid = row["product_id"]
                counts[pid] = counts.get(pid, 0) + 1
            return counts
        except _DB_ERRORS as e:
            print(f"Error counting reviews: {e}")
            return {}

    @staticmethod
    def create_reviews(product_id: str, reviews: list[dict]) -> dict:
        if not reviews:
            return {"status": "success", "data": []}
        try:
            rows = [
                {
                    "product_id": product_id,
                    "review_id": review.get("review_id") or f"review_{idx}",
                    "content": review.get("content") or "",
                    "rating": review.get("rating"),
                    "review_date": review.get("date") or None,
                    "review_index": idx,
                    "author_user_id": review.get("author_user_id"),
                    "author_username": review.get("author_username"),
                }
                for idx, review in enumerate(reviews)
            ]
            result = supabase.table("reviews").insert(rows).execute()
            return {"status": "success", "data": result.data}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def add_review(
        product_id: str,
        review: dict,
        *,
        author_user_id: str | None = None,
        author_username: str | None = None,
    ) -> dict:
        try:
            product = (
                supabase.table("products")
                .select("id")
                .eq("id", product_id)
                .limit(1)
                .execute()
            )
            if not product.data:
                return {"status": "error", "message": "Product not found"}

            last = (
                supabase.table("reviews")
                .select("review_index")
                .eq("product_id", product_id)
                .order("review_index", desc=True)
                .limit(1)
                .execute()
            )
            next_index = (last.data[0]["review_index"] + 1) if last.data else 0

            payload = {
                "product_id": product_id,
                "review_id": review.get("review_id") or f"review_{next_index}",
                "content": review.get("content") or "",
                "rating": review.get("rating"),
                "review_date": review.get("date") or None,
                "review_index": next_index,
                "author_user_id": author_user_id,
                "author_username": author_username,
            }
            result = supabase.table("reviews").insert(payload).execute()
            return {"status": "success", "data": result.data}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def delete_review(product_id: str, review_id: str) -> dict:
        try:
            (
                supabase.table("reviews")
                .delete()
                .eq("product_id", product_id)
                .eq("review_id", review_id)
                .execute()
            )
            return {"status": "success"}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}
