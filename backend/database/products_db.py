from datetime import datetime, timezone

import httpx
from postgrest.exceptions import APIError

from .supabase_client import supabase

_DB_ERRORS = (APIError, httpx.HTTPError)


class ProductDatabase:
    """Product database management using Supabase"""

    @staticmethod
    def create_product(
        product_id: str,
        name: str,
        description: str,
        image: str | None = None,
        owner_id: str | None = None,
    ) -> dict:
        """Create a new product (reviews live in the reviews table)."""
        try:
            data = {
                "id": product_id,
                "name": name,
                "description": description,
                "image": image,
                "owner_id": owner_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            result = supabase.table("products").insert(data).execute()
            return {"status": "success", "data": result.data}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_product(product_id: str) -> dict | None:
        """Get a product by ID (without reviews)."""
        try:
            result = (
                supabase.table("products")
                .select("*")
                .eq("id", product_id)
                .execute()
            )
            if result.data:
                return result.data[0]
            return None
        except _DB_ERRORS as e:
            print(f"Error getting product: {e}")
            return None

    @staticmethod
    def get_all_products() -> list[dict]:
        """Get all products (without reviews)."""
        try:
            result = supabase.table("products").select("*").execute()
            return result.data or []
        except _DB_ERRORS as e:
            print(f"Error getting products: {e}")
            return []

    @staticmethod
    def update_product(
        product_id: str,
        name: str | None = None,
        description: str | None = None,
        image: str | None = None,
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

            result = (
                supabase.table("products")
                .update(update_data)
                .eq("id", product_id)
                .execute()
            )
            return {"status": "success", "data": result.data}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def delete_product(product_id: str) -> dict:
        """Delete a product (reviews cascade via FK)."""
        try:
            supabase.table("products").delete().eq("id", product_id).execute()
            return {"status": "success"}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}
