from fastapi import APIRouter
from starlette.requests import Request
from utils.auth import get_user_from_cookie


api_router = APIRouter()


@api_router.get("/")
def me(request: Request):
    user = get_user_from_cookie(request)
    return {"email": user.get("email"), "name": user.get("name"), "isAdmin": True}
