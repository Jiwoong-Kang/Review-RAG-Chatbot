from fastapi import APIRouter, Depends, HTTPException

from database import ChatHistoryDatabase, ProductDatabase
from routers.deps import bearer_token, raise_service_error
from routers.schemas import ChatMessage
from chat_engine import generate_response

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/history/{product_id}")
def get_chat_history(product_id: str, token: str = Depends(bearer_token)):
    result = ChatHistoryDatabase.list_messages(token, product_id)
    if result["status"] == "error":
        raise_service_error(result)
    return result


@router.delete("/history/{product_id}")
def clear_chat_history(product_id: str, token: str = Depends(bearer_token)):
    result = ChatHistoryDatabase.clear_messages(token, product_id)
    if result["status"] == "error":
        raise_service_error(result)
    return result


@router.post("")
def chat(
    message: ChatMessage,
    token: str = Depends(bearer_token),
):
    """Answer questions about the product (login required)."""
    product = ProductDatabase.get_product(message.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = generate_response(
        message.product_id,
        message.message,
        message.conversation_history,
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["answer"])

    ChatHistoryDatabase.add_message(
        token, message.product_id, "user", message.message
    )
    ChatHistoryDatabase.add_message(
        token,
        message.product_id,
        "assistant",
        result["answer"],
        sources=result.get("sources") or [],
        insufficient_evidence=bool(result.get("insufficient_evidence")),
    )

    return {
        "status": "success",
        "response": result["answer"],
        "sources": result["sources"],
        "insufficient_evidence": result["insufficient_evidence"],
        "product_id": message.product_id,
    }
