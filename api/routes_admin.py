"""Rotas administrativas: créditos manuais, busca de usuários e senhas."""

from __future__ import annotations

import os
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from api.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])

ADMIN_EMAILS = {
    e.strip().lower()
    for e in os.environ.get("ADMIN_EMAILS", "sbarros1982@gmail.com").split(",")
    if e.strip()
}


def _normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def is_admin_email(email: str | None) -> bool:
    return _normalize_email(email) in ADMIN_EMAILS


def is_admin_user(user: CurrentUser) -> bool:
    if is_admin_email(user.email):
        return True
    try:
        from src.pdf_splitter.supabase_client import get_supabase

        row = (
            get_supabase()
            .table("users")
            .select("role,email")
            .eq("id", user.user_id)
            .single()
            .execute()
            .data
        )
        if not row:
            return False
        if str(row.get("role") or "").lower() == "admin":
            return True
        return is_admin_email(row.get("email"))
    except Exception:
        return False


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Exige usuário autenticado com papel de admin."""
    if not is_admin_user(user):
        raise HTTPException(403, "Acesso restrito a administradores.")
    return user


def generate_password(length: int = 12) -> str:
    """Gera senha aleatória legível (sem caracteres ambíguos)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(max(8, length)))


class GrantCreditsBody(BaseModel):
    email: EmailStr
    credits_mb: int = Field(..., gt=0, le=100_000)
    amount_brl: float = Field(0, ge=0)
    note: str | None = Field(None, max_length=500)
    days_valid: int = Field(90, ge=1, le=3650)


class SetPasswordBody(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=6, max_length=72)
    generate: bool = False


class SearchQuery(BaseModel):
    q: str = Field(..., min_length=2, max_length=120)


@router.get("/me")
def admin_me(user: CurrentUser = Depends(require_admin)) -> dict[str, Any]:
    """Confirma se o usuário logado é admin."""
    from api.version import get_app_version

    return {
        "ok": True,
        "user_id": user.user_id,
        "email": user.email,
        "admin": True,
        "version": get_app_version(),
    }


@router.get("/users")
def list_users(
    q: str | None = None,
    limit: int = 30,
    user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Lista ou busca usuários por e-mail."""
    from src.pdf_splitter.supabase_client import get_supabase

    limit = max(1, min(limit, 100))
    sb = get_supabase()
    query = sb.table("users").select(
        "id,email,role,total_credits_mb,used_credits_mb,free_uses_today,pdf_tools_uses_today,created_at,display_name"
    )
    if q and q.strip():
        query = query.ilike("email", f"%{q.strip()}%")
    response = query.order("created_at", desc=True).limit(limit).execute()
    rows = response.data or []
    for row in rows:
        total = int(row.get("total_credits_mb") or 0)
        used = int(row.get("used_credits_mb") or 0)
        row["available_mb"] = max(0, total - used)
    return {"users": rows}


@router.post("/grant-credits")
def grant_credits(
    body: GrantCreditsBody,
    admin: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Concede créditos manuais (venda faturada / cortesia)."""
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    email = _normalize_email(str(body.email))
    found = sb.table("users").select("*").eq("email", email).limit(1).execute().data
    if not found:
        # tenta case-insensitive
        all_match = (
            sb.table("users")
            .select("*")
            .ilike("email", email)
            .limit(1)
            .execute()
            .data
        )
        if not all_match:
            raise HTTPException(
                404,
                "Usuário não encontrado. Peça para a pessoa criar conta / fazer login antes.",
            )
        found = all_match

    target = found[0]
    user_id = target["id"]
    payment_id = f"invoice_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=body.days_valid)

    tx = {
        "user_id": user_id,
        "amount_brl": round(float(body.amount_brl), 2),
        "credits_mb": int(body.credits_mb),
        "payment_method": "invoice",
        "payment_id": payment_id,
        "payment_status": "approved",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "approved_at": now.isoformat(),
        "payment_metadata": {
            "source": "admin_manual",
            "note": body.note,
            "granted_by": admin.user_id,
            "granted_by_email": admin.email,
        },
    }
    tx_res = sb.table("transactions").insert(tx).execute()
    tx_row = (tx_res.data or [None])[0]
    if not tx_row:
        raise HTTPException(500, "Falha ao registrar a transação de créditos.")

    new_total = int(target.get("total_credits_mb") or 0) + int(body.credits_mb)
    sb.table("users").update({"total_credits_mb": new_total}).eq("id", user_id).execute()

    grant = {
        "user_id": user_id,
        "granted_by": admin.user_id,
        "credits_mb": int(body.credits_mb),
        "amount_brl": round(float(body.amount_brl), 2),
        "note": body.note,
        "transaction_id": tx_row.get("id"),
    }
    grant_res = sb.table("credit_grants").insert(grant).execute()

    return {
        "success": True,
        "user": {
            "id": user_id,
            "email": target.get("email"),
            "total_credits_mb": new_total,
            "available_mb": max(0, new_total - int(target.get("used_credits_mb") or 0)),
        },
        "transaction_id": tx_row.get("id"),
        "grant_id": (grant_res.data or [{}])[0].get("id"),
        "payment_id": payment_id,
        "expires_at": expires_at.isoformat(),
    }


@router.get("/grants")
def list_grants(
    limit: int = 40,
    user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Histórico recente de créditos manuais."""
    from src.pdf_splitter.supabase_client import get_supabase

    limit = max(1, min(limit, 100))
    sb = get_supabase()
    grants = (
        sb.table("credit_grants")
        .select("id,user_id,granted_by,credits_mb,amount_brl,note,created_at,transaction_id")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    user_ids = {g["user_id"] for g in grants if g.get("user_id")}
    user_ids |= {g["granted_by"] for g in grants if g.get("granted_by")}
    emails: dict[str, str] = {}
    if user_ids:
        rows = (
            sb.table("users")
            .select("id,email")
            .in_("id", list(user_ids))
            .execute()
            .data
            or []
        )
        emails = {r["id"]: r.get("email") or "" for r in rows}
    for g in grants:
        g["user_email"] = emails.get(g.get("user_id") or "", "")
        g["granted_by_email"] = emails.get(g.get("granted_by") or "", "")
    return {"grants": grants}


@router.post("/set-password")
def set_password(
    body: SetPasswordBody,
    admin: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Define ou gera senha de login (e-mail/senha) para um usuário."""
    from src.pdf_splitter.supabase_client import get_supabase

    target_email = _normalize_email(str(body.email) if body.email else admin.email)
    if not target_email:
        raise HTTPException(400, "Informe o e-mail do usuário.")

    if body.generate or not body.password:
        password = generate_password(12)
    else:
        password = body.password

    sb = get_supabase()
    # Localiza id em public.users
    users = sb.table("users").select("id,email").ilike("email", target_email).limit(1).execute().data
    if not users:
        raise HTTPException(404, "Usuário não encontrado em public.users.")
    user_id = users[0]["id"]

    try:
        sb.auth.admin.update_user_by_id(user_id, {"password": password})
    except Exception as exc:
        # Fallback: tenta pelo Auth Admin listando por e-mail
        try:
            listed = sb.auth.admin.list_users()
            auth_user = None
            for u in getattr(listed, "users", listed) or []:
                email = getattr(u, "email", None) or (u.get("email") if isinstance(u, dict) else None)
                uid = getattr(u, "id", None) or (u.get("id") if isinstance(u, dict) else None)
                if _normalize_email(email) == target_email and uid:
                    auth_user = str(uid)
                    break
            if not auth_user:
                raise HTTPException(
                    404,
                    "Conta de autenticação não encontrada. Peça para a pessoa fazer login com Google uma vez.",
                ) from exc
            sb.auth.admin.update_user_by_id(auth_user, {"password": password})
            user_id = auth_user
        except HTTPException:
            raise
        except Exception as exc2:
            raise HTTPException(500, f"Não foi possível definir a senha: {exc2}") from exc2

    return {
        "success": True,
        "email": target_email,
        "user_id": user_id,
        "password": password,
        "message": "Senha definida. Guarde-a agora; ela não será exibida de novo.",
    }


@router.get("/ip-usage")
def list_ip_usage(
    limit: int = 40,
    user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Uso gratuito/ferramentas por IP no dia (anti abuso)."""
    from datetime import date

    from src.pdf_splitter.supabase_client import get_supabase

    limit = max(1, min(limit, 100))
    sb = get_supabase()
    rows = (
        sb.table("ip_daily_usage")
        .select("ip,usage_date,free_process_count,tool_use_count,last_email,updated_at")
        .eq("usage_date", date.today().isoformat())
        .order("updated_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    return {"items": rows, "free_limit": 3, "tool_limit": 5}


@router.get("/logs")
def admin_logs(
    limit: int = 50,
    user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Central de logs: jobs recentes + liberações + uso por IP."""
    from datetime import date

    from api.version import get_app_version
    from src.pdf_splitter.supabase_client import get_supabase

    limit = max(1, min(limit, 100))
    sb = get_supabase()

    jobs = (
        sb.table("jobs")
        .select(
            "id,user_id,filename,file_size_mb,pages_count,documents_count,status,"
            "error_message,created_at,completed_at,ip_address,processing_time_seconds"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )

    user_ids = {j["user_id"] for j in jobs if j.get("user_id")}
    emails: dict[str, str] = {}
    if user_ids:
        rows = (
            sb.table("users")
            .select("id,email")
            .in_("id", list(user_ids))
            .execute()
            .data
            or []
        )
        emails = {r["id"]: r.get("email") or "" for r in rows}
    for job in jobs:
        job["user_email"] = emails.get(job.get("user_id") or "", "")

    grants = (
        sb.table("credit_grants")
        .select("id,user_id,granted_by,credits_mb,amount_brl,note,created_at")
        .order("created_at", desc=True)
        .limit(min(limit, 30))
        .execute()
        .data
        or []
    )
    grant_ids = {g["user_id"] for g in grants if g.get("user_id")}
    grant_ids |= {g["granted_by"] for g in grants if g.get("granted_by")}
    if grant_ids:
        rows = (
            sb.table("users")
            .select("id,email")
            .in_("id", list(grant_ids))
            .execute()
            .data
            or []
        )
        for r in rows:
            emails[r["id"]] = r.get("email") or ""
    for g in grants:
        g["user_email"] = emails.get(g.get("user_id") or "", "")
        g["granted_by_email"] = emails.get(g.get("granted_by") or "", "")

    ip_rows = (
        sb.table("ip_daily_usage")
        .select("ip,usage_date,free_process_count,tool_use_count,last_email,updated_at")
        .eq("usage_date", date.today().isoformat())
        .order("updated_at", desc=True)
        .limit(40)
        .execute()
        .data
        or []
    )

    failed = [j for j in jobs if j.get("status") == "failed"][:20]

    return {
        "version": get_app_version(),
        "jobs": jobs,
        "failed_jobs": failed,
        "grants": grants,
        "ip_usage": ip_rows,
    }
