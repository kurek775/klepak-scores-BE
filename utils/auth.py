from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from core.config import settings
from core.oauth import oauth
from core.security import create_app_jwt
from jose import jwt

COOKIE_NAME = "app_session"

async def start_google_login(request: Request):
    redirect_uri = f"{settings.BACKEND_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri, code_challenge_method="S256")

async def handle_google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = await oauth.google.parse_id_token(request, token)
        sub = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name")
        picture = userinfo.get("picture")
        print(token,userinfo)
        if not sub or not email:
            raise HTTPException(status_code=400, detail="Invalid Google userinfo")

        # TODO: tady případně ulož/aktualizuj uživatele v DB
        app_jwt = create_app_jwt(sub, email, name, picture)

        resp = RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/callback")
        resp.set_cookie(
            key=COOKIE_NAME,
            value=app_jwt,
            httponly=True,
            secure=False,  # v prod nasadit True (HTTPS)
            samesite="lax",
            max_age=60 * 60 * 12,
            path="/",
        )
        return resp
    except Exception as e:
        print(e)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/error?m=oauth_failed")

def logout_response():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp

def get_user_from_cookie(request: Request) -> dict:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        # aud verifikaci můžeš vypnout/zapnout dle potřeby
        return jwt.decode(token, options={"verify_aud": False}, key=None)  # dekóduje header, claims
    except Exception:
        # pokud chceš ověřit signaturu, použij settings.JWT_SECRET a algoritmus:
        from ..core.config import settings
        from jose import jwt as jose_jwt
        try:
            return jose_jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG], options={"verify_aud": False})
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid session")
