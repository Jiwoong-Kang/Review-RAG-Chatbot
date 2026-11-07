import re
import uuid

from fastapi import APIRouter, Depends, HTTPException

from database import AuthService, ProductDatabase, ReviewDatabase
from routers.deps import bearer_token
from routers.schemas import ProductUpload, Review
from vector_store import add_review_embedding, create_embeddings, delete_embeddings

router = APIRouter(prefix="/api/products", tags=["products"])


def _new_product_id(name: str | None = None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")
    slug = slug[:40] if slug else "product"
    return f"{slug}_{uuid.uuid4().hex[:10]}"


@router.post("/upload")
def upload_product(product: ProductUpload, token: str = Depends(bearer_token)):
    """Upload product (any logged-in user becomes owner). Reviews optional; usually added later."""
    user = AuthService.get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    product_id = (product.product_id or "").strip() or _new_product_id(product.name)

    result = ProductDatabase.create_product(
        product_id=product_id,
        name=product.name,
        description=product.description,
        image=product.image,
        owner_id=user["id"],
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    reviews_dict = [r.dict() for r in product.reviews]
    reviews_result = ReviewDatabase.create_reviews(product_id, reviews_dict)
    if reviews_result["status"] == "error":
        ProductDatabase.delete_product(product_id)
        raise HTTPException(status_code=500, detail=reviews_result["message"])

    try:
        create_embeddings(product_id, product.description, reviews_dict)
    except Exception as e:
        ProductDatabase.delete_product(product_id)
        raise HTTPException(
            status_code=500,
            detail=f"Embedding failed; product was rolled back: {e}",
        ) from e

    return {
        "status": "success",
        "product_id": product_id,
        "reviews_count": len(product.reviews),
    }



@router.get("")
def list_products():
    """Get all products list (public read for now)."""
    products = ProductDatabase.get_all_products()
    counts = ReviewDatabase.count_reviews_by_product()
    return {
        "products": [
            {
                "product_id": p["id"],
                "name": p["name"],
                "image": p.get("image"),
                "created_at": p.get("created_at"),
                "reviews_count": counts.get(p["id"], 0),
                "owner_id": p.get("owner_id"),
            }
            for p in products
        ]
    }


@router.get("/{product_id}")
def get_product(product_id: str):
    """Get product information with reviews (public read for now)."""
    product = ProductDatabase.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    reviews = ReviewDatabase.list_reviews(product_id)
    return {**product, "reviews": reviews}


@router.delete("/{product_id}")
def delete_product(product_id: str, token: str = Depends(bearer_token)):
    """Delete a product (owner or admin only)."""
    user = AuthService.get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    product = ProductDatabase.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not AuthService.can_manage_product(user, product):
        raise HTTPException(
            status_code=403,
            detail="Only the product owner or an admin can delete this product",
        )

    delete_embeddings(product_id)

    result = ProductDatabase.delete_product(product_id)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return {"status": "success", "message": "Product deleted"}


@router.post("/{product_id}/reviews")
def add_review(
    product_id: str,
    review: Review,
    token: str = Depends(bearer_token),
):
    """Add a review to a product (attributed to the signed-in user)."""
    user = AuthService.get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    review_dict = review.dict()
    result = ReviewDatabase.add_review(
        product_id,
        review_dict,
        author_user_id=user["id"],
        author_username=user.get("username") or user.get("name"),
    )
    if result["status"] == "error":
        status = 404 if result["message"] == "Product not found" else 500
        raise HTTPException(status_code=status, detail=result["message"])

    row = (result.get("data") or [None])[0]
    if row:
        review_for_embed = {
            "review_id": row["review_id"],
            "content": row["content"],
            "rating": row.get("rating"),
            "date": row.get("review_date"),
            "author_username": row.get("author_username"),
        }
        review_index = row["review_index"]
        saved_review_id = row["review_id"]
    else:
        review_for_embed = {
            **review_dict,
            "author_username": user.get("username") or user.get("name"),
        }
        review_index = 0
        saved_review_id = review_dict.get("review_id")

    try:
        add_review_embedding(product_id, review_for_embed, review_index)
    except Exception as e:
        if saved_review_id:
            ReviewDatabase.delete_review(product_id, saved_review_id)
        raise HTTPException(
            status_code=500,
            detail=f"Embedding failed; review was rolled back: {e}",
        ) from e

    return {"status": "success", "message": "Review added"}
