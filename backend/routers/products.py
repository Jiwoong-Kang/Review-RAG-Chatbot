from fastapi import APIRouter, Depends, HTTPException

from database import AuthService, ProductDatabase, ReviewDatabase
from routers.deps import bearer_token
from routers.schemas import ProductUpload, Review
from vector_store import add_review_embedding, create_embeddings, delete_embeddings

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("/upload")
def upload_product(product: ProductUpload):
    """Upload product information and reviews."""
    result = ProductDatabase.create_product(
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        image=product.image,
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    reviews_dict = [r.dict() for r in product.reviews]
    reviews_result = ReviewDatabase.create_reviews(product.product_id, reviews_dict)
    if reviews_result["status"] == "error":
        ProductDatabase.delete_product(product.product_id)
        raise HTTPException(status_code=500, detail=reviews_result["message"])

    create_embeddings(product.product_id, product.description, reviews_dict)

    return {
        "status": "success",
        "product_id": product.product_id,
        "reviews_count": len(product.reviews),
    }


@router.get("")
def list_products():
    """Get all products list."""
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
            }
            for p in products
        ]
    }


@router.get("/{product_id}")
def get_product(product_id: str):
    """Get product information with reviews."""
    product = ProductDatabase.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    reviews = ReviewDatabase.list_reviews(product_id)
    return {**product, "reviews": reviews}


@router.delete("/{product_id}")
def delete_product(product_id: str):
    """Delete a product."""
    product = ProductDatabase.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

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
    else:
        review_for_embed = {
            **review_dict,
            "author_username": user.get("username") or user.get("name"),
        }
        review_index = 0

    add_review_embedding(product_id, review_for_embed, review_index)

    return {"status": "success", "message": "Review added"}
