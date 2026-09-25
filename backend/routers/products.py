from fastapi import APIRouter, HTTPException

from database import ProductDatabase
from routers.schemas import ProductUpload, Review

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("/upload")
async def upload_product(product: ProductUpload):
    """Upload product information and reviews."""
    result = await ProductDatabase.create_product(
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        image=product.image,
        reviews=[r.dict() for r in product.reviews],
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    from vector_store import create_embeddings
    reviews_dict = [r.dict() for r in product.reviews]
    create_embeddings(product.product_id, product.description, reviews_dict)

    return {
        "status": "success",
        "product_id": product.product_id,
        "reviews_count": len(product.reviews),
    }


@router.get("")
async def list_products():
    """Get all products list."""
    products = await ProductDatabase.get_all_products()
    return {
        "products": [
            {
                "product_id": p["id"],
                "name": p["name"],
                "image": p.get("image"),
                "created_at": p.get("created_at"),
                "reviews_count": len(p.get("reviews", [])),
            }
            for p in products
        ]
    }


@router.get("/{product_id}")
async def get_product(product_id: str):
    """Get product information."""
    product = await ProductDatabase.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: str):
    """Delete a product."""
    product = await ProductDatabase.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from vector_store import delete_embeddings
    delete_embeddings(product_id)

    result = await ProductDatabase.delete_product(product_id)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return {"status": "success", "message": "Product deleted"}


@router.post("/{product_id}/reviews")
async def add_review(product_id: str, review: Review):
    """Add a review to a product."""
    result = await ProductDatabase.add_review(product_id, review.dict())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    from vector_store import create_embeddings
    product = await ProductDatabase.get_product(product_id)
    create_embeddings(product_id, product["description"], product.get("reviews", []))

    return {"status": "success", "message": "Review added"}
