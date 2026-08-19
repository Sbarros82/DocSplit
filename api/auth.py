"""Autenticação via JWT do Supabase."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """Usuário autenticado extraído do JWT do Supabase."""

    user_id: str
    email: str | None = None


def _user_from_token(token: str) -> CurrentUser:
    """Valida o access token do Supabase e retorna o usuário.

    Usa o endpoint /auth/v1/user com a anon key para não misturar
    o JWT do usuário com a SERVICE_ROLE_KEY do cliente admin.
    """
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not supabase_url or not anon_key:
        raise HTTPException(503, "Autenticação indisponível no momento.")

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
        raise HTTPException(503, "Não foi possível validar a sessão.") from exc

    if response.status_code != 200:
        raise HTTPException(401, "Sessão inválida ou expirada. Faça login novamente.")

    data = response.json()
    user_id = data.get("id")
    if not user_id:
        raise HTTPException(401, "Sessão inválida. Faça login novamente.")
    return CurrentUser(user_id=str(user_id), email=data.get("email"))


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser | None:
    """Retorna o usuário autenticado, ou None se não houver token."""
    if creds is None or not creds.credentials:
        return None
    return _user_from_token(creds.credentials)


def get_current_user(
    user: CurrentUser | None = Depends(get_optional_user),
) -> CurrentUser:
    """Exige autenticação. Retorna 401 se o usuário não estiver logado."""
    if user is None:
        raise HTTPException(401, "Faça login para continuar.")
    return user
