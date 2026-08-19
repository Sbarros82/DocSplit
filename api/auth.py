"""Autenticação via JWT do Supabase."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from fastapi import Depends, Header, HTTPException

try:
    import jwt
    from jwt import PyJWKClient
except Exception:  # pragma: no cover
    jwt = None  # type: ignore
    PyJWKClient = None  # type: ignore


@dataclass
class CurrentUser:
    """Usuário autenticado extraído do JWT do Supabase."""

    user_id: str
    email: str | None = None


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def _user_from_gotrue(token: str) -> CurrentUser | None:
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not supabase_url or not anon_key:
        return None
    try:
        response = httpx.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": anon_key,
            },
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        print(f"[auth] gotrue request failed: {exc}")
        return None
    if response.status_code != 200:
        print(f"[auth] gotrue status={response.status_code} body={response.text[:180]}")
        return None
    data = response.json()
    user = data.get("user") if isinstance(data.get("user"), dict) else data
    user_id = user.get("id")
    if not user_id:
        return None
    return CurrentUser(user_id=str(user_id), email=user.get("email"))


def _user_from_jwt(token: str) -> CurrentUser | None:
    if jwt is None:
        return None
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        print(f"[auth] jwt header error: {exc}")
        return None

    alg = str(header.get("alg") or "HS256")
    payload = None
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")

    try:
        if alg in {"ES256", "RS256"} and PyJWKClient and supabase_url:
            jwks_client = PyJWKClient(f"{supabase_url}/auth/v1/.well-known/jwks.json")
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience="authenticated",
                options={"verify_aud": False},
            )
        else:
            secret = os.environ.get("SUPABASE_JWT_SECRET", "")
            if not secret:
                return None
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": False},
            )
    except Exception as exc:
        print(f"[auth] jwt verify failed alg={alg}: {exc}")
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None
    return CurrentUser(user_id=str(user_id), email=payload.get("email"))


def _user_from_token(token: str) -> CurrentUser:
    user = _user_from_gotrue(token) or _user_from_jwt(token)
    if user is None:
        raise HTTPException(401, "Sessão inválida ou expirada. Faça login novamente.")
    return user


def get_optional_user(
    authorization: str | None = Header(default=None),
) -> CurrentUser | None:
    """Retorna o usuário autenticado, ou None se não houver token válido."""
    token = _bearer_token(authorization)
    if not token:
        return None
    try:
        return _user_from_token(token)
    except HTTPException:
        return None


def get_current_user(
    user: CurrentUser | None = Depends(get_optional_user),
) -> CurrentUser:
    """Exige autenticação. Retorna 401 se o usuário não estiver logado."""
    if user is None:
        raise HTTPException(401, "Faça login para continuar.")
    return user
