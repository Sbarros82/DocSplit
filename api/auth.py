"""Autenticação via JWT do Supabase."""

from __future__ import annotations

from dataclasses import dataclass

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

    Raises HTTPException 401 se o token for inválido ou expirado.
    """
    try:
        from src.pdf_splitter.supabase_client import get_supabase

        response = get_supabase().auth.get_user(token)
        user = getattr(response, "user", None)
        if user is None:
            raise HTTPException(401, "Sessão inválida. Faça login novamente.")
        return CurrentUser(user_id=str(user.id), email=getattr(user, "email", None))
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(503, "Autenticação indisponível no momento.") from exc
    except Exception as exc:
        raise HTTPException(401, "Token inválido ou expirado. Faça login novamente.") from exc


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
