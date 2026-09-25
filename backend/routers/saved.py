from fastapi import APIRouter, Depends, HTTPException

from database import SavedProductDatabase
from routers.deps import bearer_token
from routers.schemas import SavedProductPayload

router = APIRouter(prefix="/api/saved-products", tags=["saved-products"])


@router.get("")
async def list_saved_products(token: str = Depends(bearer_token)):
    result = SavedProductDatabase.list_saved(token)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/{product_id}")
async def get_saved_product(product_id: str, token: str = Depends(bearer_token)):
    result = SavedProductDatabase.get_saved_for_product(token, product_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("")
async def save_product(payload: SavedProductPayload, token: str = Depends(bearer_token)):
    result = SavedProductDatabase.upsert_saved(
        token,
        payload.product_id,
        payload.interest_level,
        payload.personal_note or "",
    )
    if result["status"] == "error":
        status = 404 if result["message"] == "Product not found" else 400
        if result["message"] == "Unauthorized":
            status = 401
        raise HTTPException(status_code=status, detail=result["message"])
    return result


@router.delete("/{product_id}")
async def unsave_product(product_id: str, token: str = Depends(bearer_token)):
    result = SavedProductDatabase.delete_saved(token, product_id)
    if result["status"] == "error":
        status = 401 if result["message"] == "Unauthorized" else 400
        raise HTTPException(status_code=status, detail=result["message"])
    return result
