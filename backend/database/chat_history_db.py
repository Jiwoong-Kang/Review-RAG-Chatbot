from typing import Any

import httpx
from postgrest.exceptions import APIError

from .auth_service import AuthService
from .supabase_client import user_client

_DB_ERRORS = (APIError, httpx.HTTPError)


class ChatHistoryDatabase:
    """Per-user, per-product chat messages (RLS via user JWT)."""

    @staticmethod
    def list_messages(access_token: str, product_id: str) -> dict:
        try:
            user = AuthService.get_user(access_token)
            if not user:
                return {"status": "error", "message": "Unauthorized"}
            client = user_client(access_token)
            result = (
                client.table("chat_messages")
                .select("id, role, content, sources, insufficient_evidence, created_at")
                .eq("product_id", product_id)
                .order("created_at", desc=False)
                .execute()
            )
            return {"status": "success", "messages": result.data or []}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def add_message(
        access_token: str,
        product_id: str,
        role: str,
        content: str,
        sources: list[Any] | None = None,
        insufficient_evidence: bool = False,
    ) -> dict:
        try:
            user = AuthService.get_user(access_token)
            if not user:
                return {"status": "error", "message": "Unauthorized"}
            if role not in ("user", "assistant"):
                return {"status": "error", "message": "Invalid role"}
            client = user_client(access_token)
            payload = {
                "user_id": user["id"],
                "product_id": product_id,
                "role": role,
                "content": content,
                "sources": sources or [],
                "insufficient_evidence": bool(insufficient_evidence),
            }
            result = client.table("chat_messages").insert(payload).execute()
            return {"status": "success", "message": result.data[0] if result.data else payload}
        except _DB_ERRORS as e:
            return {"status": "error", "message": str(e)}
