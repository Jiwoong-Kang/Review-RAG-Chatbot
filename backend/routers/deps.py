from fastapi import Header, HTTPException


def bearer_token(authorization: str | None = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")
    return token


def optional_bearer(authorization: str | None = Header(None)) -> str | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return token or None


def require_product_read(authorization: str | None = Header(None)) -> str:
    """Login-required product read. Ready for later; GET list/detail stay public for now."""
    return bearer_token(authorization)


def raise_service_error(result: dict) -> None:
    """Map service-layer error dicts to HTTP status (401 auth vs 500 otherwise)."""
    msg = result.get("message") or "Unknown error"
    if msg == "Unauthorized":
        raise HTTPException(status_code=401, detail=msg)
    raise HTTPException(status_code=500, detail=msg)
