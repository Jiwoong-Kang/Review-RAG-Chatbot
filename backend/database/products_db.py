from datetime import datetime, timezone

import httpx
from postgrest.exceptions import APIError

from .supabase_client import supabase

_DB_ERRORS = (APIError, httpx.HTTPError)


class ProductDatabase:
    """Product database management using Supabase"""

    @staticmethod
    async def create_product(
        product_id: str,
        name: str,
        description: str,
        image: str | None = None,
        reviews: list[dict] | None = None
    ) -> dict:
        """Create a new product"""
        if reviews is None:
            reviews = []
        try:
            data = {
                "id": product_id,
                "name": name,
                "description": description,
                "image": image,
                "reviews": reviews,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            result = supabase.table("products").insert(data).execute()
            return {"status": "success", "data": result.data}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def get_product(product_id: str) -> dict | None:
        """Get a product by ID"""
        try:
            result = supabase.table("products").select("*").eq("id", product_id).execute()
            if result.data:
                return result.data[0]
            return None
        except _DB_ERRORS as e:
            print(f"Error getting product: {e}")
            return None

    @staticmethod
    async def get_all_products() -> list[dict]:
        """Get all products"""
        try:
            result = supabase.table("products").select(
                "id, name, description, created_at, image, reviews"
            ).execute()
            return result.data
        except _DB_ERRORS as e:
            print(f"Error getting products: {e}")
            return []

    @staticmethod
    async def update_product(
        product_id: str,
        name: str | None = None,
        description: str | None = None,
        image: str | None = None,
        reviews: list[dict] | None = None
    ) -> dict:
        """Update a product"""
        try:
            update_data = {}
            if name:
                update_data["name"] = name
            if description:
                update_data["description"] = description
            if image:
                update_data["image"] = image
            if reviews is not None:
                update_data["reviews"] = reviews

            result = supabase.table("products").update(update_data).eq("id", product_id).execute()
            return {"status": "success", "data": result.data}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def delete_product(product_id: str) -> dict:
        """Delete a product"""
        try:
            supabase.table("products").delete().eq("id", product_id).execute()
            return {"status": "success"}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def add_review(product_id: str, review: dict) -> dict:
        """Add a review to a product"""
        try:
            product = await ProductDatabase.get_product(product_id)
            if not product:
                return {"status": "error", "message": "Product not found"}

            reviews = product.get("reviews", [])
            reviews.append(review)

            result = supabase.table("products").update({"reviews": reviews}).eq("id", product_id).execute()
            return {"status": "success", "data": result.data}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}
