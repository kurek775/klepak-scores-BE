# services/auth_service.py
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse

from core.config import settings
from core.oauth import oauth
from core.security import create_app_jwt

from jose import jwt as app_jwt  # your app cookie JWT
import httpx
from authlib.jose import jwt as jose_jwt  # for verifying Google's ID token
from authlib.jose import JsonWebKey

import secrets
import logging
import traceback
from urllib.parse import urlencode

log = logging.getLogger("auth")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

COOKIE_NAME = "app_session"
SENSITIVE_QS = {"code", "state"}
SENSITIVE_HDRS = {"authorization", "cookie", "set-cookie"}


def _safe_headers(headers):
    return {
        k: ("<redacted>" if k.lower() in SENSITIVE_HDRS else v)
        for k, v in headers.items()
    }


def _safe_query(params):
    d = dict(params)
    for k in list(d.keys()):
        if k in SENSITIVE_QS:
            v = str(d[k])
            d[k] = f"<redacted:{len(v)}chars>"
    return d


def _redirect_err(code: str, extra: dict | None = None):
    q = {"m": code}
    if extra:
        q.update(extra)
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/error?{urlencode(q)}")


async def start_google_login(request: Request):
    """Start OAuth (Auth Code + PKCE) and store OIDC nonce."""
    redirect_uri = f"{settings.BACKEND_URL}/auth/google/callback"
    nonce = secrets.token_urlsafe(16)
    request.session["oidc_nonce"] = nonce

    log.info(
        "OAuth start; redirect_uri=%s origin=%s client_id_set=%s secret_set=%s",
        redirect_uri,
        request.headers.get("origin"),
        bool(settings.GOOGLE_CLIENT_ID),
        bool(settings.GOOGLE_CLIENT_SECRET),
    )

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        code_challenge_method="S256",
        nonce=nonce,
    )


async def handle_google_callback(request: Request):
    """Exchange code->token, verify ID token (JOSE + Google JWKs), set cookie."""
    # Log sanitized callback
    log.info(
        "OAuth callback: method=%s path=%s query=%s headers=%s session_keys=%s",
        request.method,
        request.url.path,
        _safe_query(request.query_params),
        _safe_headers(request.headers),
        list(request.session.keys()),
    )

    # 1) Exchange authorization code -> tokens
    try:
        token = await oauth.google.authorize_access_token(request)
        log.info(
            "Token exchange OK; token_keys=%s id_token_present=%s",
            list(token.keys()),
            bool(token.get("id_token")),
        )
    except Exception as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        body = getattr(getattr(e, "response", None), "text", "")
        log.error("Token exchange FAILED: %s | status=%s body=%s", str(e), status, body)
        log.debug("Trace:\n%s", traceback.format_exc())
        return _redirect_err(
            "token_exchange_failed", {"status": status or "", "etype": type(e).__name__}
        )

    # 2) Grab raw id_token and verify it with Google JWKs (no parse_id_token edge-cases)
    idt = token.get("id_token")
    if not idt:
        log.error("Token does not contain id_token (keys=%s)", list(token.keys()))
        return _redirect_err("id_token_missing")

    try:
        # Fetch Google JWK set (cache this in real apps)
        jwks_uri = "https://www.googleapis.com/oauth2/v3/certs"
        async with httpx.AsyncClient(timeout=10.0) as client:
            jwks = (await client.get(jwks_uri)).json()

        claims = jose_jwt.decode(idt, JsonWebKey.import_key_set(jwks))
        # Validate standard temporal claims
        claims.validate()

        # Validate issuer & audience
        iss = claims.get("iss")
        if iss not in {"https://accounts.google.com", "accounts.google.com"}:
            log.error("Invalid iss: %s", iss)
            return _redirect_err("id_token_invalid_iss")

        aud = claims.get("aud")
        if aud != settings.GOOGLE_CLIENT_ID:
            log.error("Invalid aud: %s", aud)
            return _redirect_err("id_token_invalid_aud")

        # Validate nonce if we set it
        nonce = request.session.get("oidc_nonce")
        if nonce and claims.get("nonce") != nonce:
            log.error("Invalid nonce. expected=%s got=%s", nonce, claims.get("nonce"))
            return _redirect_err("id_token_invalid_nonce")

        # Map claims to userinfo-ish structure
        sub = claims.get("sub")
        email = claims.get("email")
        name = claims.get("name")
        picture = claims.get("picture")

    except Exception as e:
        log.error("ID token verification FAILED: %s", str(e))
        log.debug("Trace:\n%s", traceback.format_exc())
        return _redirect_err("id_token_invalid", {"etype": type(e).__name__})

    # 3) Final checks + set httpOnly app session cookie
    if not sub or not email:
        log.error(
            "Invalid claims: missing sub/email. claim_keys=%s", list(claims.keys())
        )
        raise HTTPException(status_code=400, detail="Invalid Google userinfo")

    app_token = create_app_jwt(sub, email, name, picture)
    resp = RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/callback")
    resp.set_cookie(
        key=COOKIE_NAME,
        value=app_token,
        httponly=True,
        secure=False,  # True in prod (HTTPS)
        samesite="lax",
        max_age=60 * 60 * 12,
        path="/",
    )
    return resp


def logout_response():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


def get_user_from_cookie(request: Request) -> dict:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        # Verify signature with your app secret
        return app_jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
            options={"verify_aud": False},
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
