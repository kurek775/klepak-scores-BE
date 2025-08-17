from fastapi import APIRouter, Depends
from starlette.requests import Request
from utils.auth import (
    start_google_login,
    handle_google_callback,
    logout_response,
)


api_router = APIRouter()


@api_router.get("/login")
async def google_login(request: Request):
    return await start_google_login(request)


@api_router.get("/callback")
async def google_callback(request: Request):
    print(request)
    return await handle_google_callback(request)


@api_router.post("/logout")
async def logout():
    return logout_response()
