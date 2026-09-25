from fastapi import APIRouter, Depends, HTTPException

from database import AuthService
from routers.deps import bearer_token
from routers.schemas import AuthSignIn, AuthSignUp

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup")
async def signup(creds: AuthSignUp):
    result = AuthService.sign_up(creds.name, creds.username, creds.password)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/signin")
async def signin(creds: AuthSignIn):
    result = AuthService.sign_in(creds.username, creds.password)
    if result["status"] == "error":
        raise HTTPException(status_code=401, detail=result["message"])
    return result


@router.post("/signout")
async def signout(token: str = Depends(bearer_token)):
    result = AuthService.sign_out(token)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/me")
async def me(token: str = Depends(bearer_token)):
    user = AuthService.get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return {"status": "success", "user": user}
