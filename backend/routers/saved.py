from fastapi import APIRouter, Depends, HTTPException

from database import SavedProductDatabase
from routers.deps import bearer_token, raise_service_error
from routers.schemas import SavedProductPayload

router = APIRouter(prefix="/api/saved-products", tags=["saved-products"])


@router.get("")
def list_saved_products(token: str = Depends(bearer_token)):
    result = SavedProductDatabase.list_saved(token)
    if result["status"] == "error":
        raise_service_error(result)
    return result


@router.get("/{product_id}")
def get_saved_product(product_id: str, token: str = Depends(bearer_token)):
    result = SavedProductDatabase.get_saved_for_product(token, product_id)
    if result["status"] == "error":
        raise_service_error(result)
    return result


@router.post("")
def save_product(payload: SavedProductPayload, token: str = Depends(bearer_token)):
    result = SavedProductDatabase.upsert_saved(
        token,
        payload.product_id,
        payload.interest_level,
        payload.personal_note or "",
    )
    if result["status"] == "error":
        msg = result["message"]
        if msg == "Product not found":
            raise HTTPException(status_code=404, detail=msg)
        elif msg.startswith("interest_level"):
            raise HTTPException(status_code=400, detail=msg)
        else:
            raise_service_error(result)
    return result


@router.delete("/{product_id}")
def unsave_product(product_id: str, token: str = Depends(bearer_token)):
    result = SavedProductDatabase.delete_saved(token, product_id)
    if result["status"] == "error":
        raise_service_error(result)
    return result
