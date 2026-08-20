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
    return {"items": rows, "free_limit": 1, "tool_limit": 2}


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


class RefundBody(BaseModel):
    note: str | None = Field(None, max_length=500)
    credits_only: bool = False


@router.get("/transactions")
def list_transactions(
    limit: int = 50,
    q: str | None = None,
    user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Lista compras (MP + faturado) com e-mail e campos de reembolso."""
    from src.pdf_splitter.supabase_client import get_supabase

    limit = max(1, min(limit, 100))
    sb = get_supabase()
    rows = (
        sb.table("transactions")
        .select(
            "id,user_id,amount_brl,credits_mb,payment_method,payment_id,payment_status,"
            "created_at,approved_at,expires_at,fee_brl,net_amount_brl,"
            "refunded_amount_brl,refunded_credits_mb,refunded_at,refund_note,payment_metadata"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )

    user_ids = {r["user_id"] for r in rows if r.get("user_id")}
    emails: dict[str, str] = {}
    users_map: dict[str, dict[str, Any]] = {}
    if user_ids:
        urows = (
            sb.table("users")
            .select("id,email,total_credits_mb,used_credits_mb")
            .in_("id", list(user_ids))
            .execute()
            .data
            or []
        )
        for u in urows:
            emails[u["id"]] = u.get("email") or ""
            users_map[u["id"]] = u

    needle = (q or "").strip().lower()
    items: list[dict[str, Any]] = []
    for row in rows:
        email = emails.get(row.get("user_id") or "", "")
        if needle and needle not in email.lower() and needle not in str(row.get("payment_id") or "").lower():
            continue
        meta = row.get("payment_metadata") or {}
        u = users_map.get(row.get("user_id") or "", {})
        available = max(0, int(u.get("total_credits_mb") or 0) - int(u.get("used_credits_mb") or 0))
        items.append(
            {
                **row,
                "user_email": email,
                "package_id": meta.get("package_id"),
                "source": meta.get("source"),
                "user_available_mb": available,
            }
        )

    return {"transactions": items}


@router.get("/transactions/{transaction_id}/refund-preview")
def refund_preview(
    transaction_id: str,
    user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Calcula valor e créditos a reembolsar sem executar."""
    from api.payment import get_payment
    from api.refunds import build_refund_preview
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    found = (
        sb.table("transactions")
        .select("*")
        .eq("id", transaction_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not found:
        raise HTTPException(404, "Transação não encontrada")
    tx = found[0]
    urows = (
        sb.table("users")
        .select("*")
        .eq("id", tx["user_id"])
        .limit(1)
        .execute()
        .data
        or []
    )
    if not urows:
        raise HTTPException(404, "Usuário da transação não encontrado")

    mp_payment = None
    pid = str(tx.get("payment_id") or "")
    if pid.isdigit():
        try:
            mp_payment = get_payment(pid)
        except Exception as exc:
            raise HTTPException(502, f"Falha ao consultar Mercado Pago: {exc}") from exc

    preview = build_refund_preview(tx, urows[0], mp_payment)
    preview["user_email"] = urows[0].get("email")
    return preview


@router.post("/transactions/{transaction_id}/refund")
def refund_transaction(
    transaction_id: str,
    body: RefundBody,
    admin: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Executa reembolso (créditos + dinheiro no MP quando aplicável)."""
    from api.refunds import execute_refund
    from src.pdf_splitter.supabase_client import get_supabase

    sb = get_supabase()
    found = (
        sb.table("transactions")
        .select("*")
        .eq("id", transaction_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not found:
        raise HTTPException(404, "Transação não encontrada")
    tx = found[0]
    urows = (
        sb.table("users")
        .select("*")
        .eq("id", tx["user_id"])
        .limit(1)
        .execute()
        .data
        or []
    )
    if not urows:
        raise HTTPException(404, "Usuário da transação não encontrado")

    try:
        result = execute_refund(
            tx=tx,
            user=urows[0],
            admin_id=admin.user_id,
            note=body.note,
            force_credits_only=body.credits_only,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Falha no reembolso: {exc}") from exc

    return result


def _is_invoice_tx(tx: dict[str, Any]) -> bool:
    method = str(tx.get("payment_method") or "").lower()
    pid = str(tx.get("payment_id") or "")
    return method == "invoice" or pid.startswith("invoice_")


@router.get("/finance")
def finance_dashboard(
    limit: int = 80,
    user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    """Dashboard financeiro: resumo, faturados, pagos ativos e movimentações."""
    from api.version import get_app_version
    from src.pdf_splitter.supabase_client import get_supabase

    limit = max(1, min(limit, 150))
    sb = get_supabase()

    txs = (
        sb.table("transactions")
        .select(
            "id,user_id,amount_brl,credits_mb,payment_method,payment_id,payment_status,"
            "created_at,approved_at,fee_brl,net_amount_brl,refunded_amount_brl,"
            "refunded_credits_mb,refunded_at,refund_note,payment_metadata"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    users = (
        sb.table("users")
        .select("id,email,role,total_credits_mb,used_credits_mb,created_at")
        .execute()
        .data
        or []
    )
    grants = (
        sb.table("credit_grants")
        .select("id,user_id,granted_by,credits_mb,amount_brl,note,created_at,transaction_id")
        .order("created_at", desc=True)
        .limit(40)
        .execute()
        .data
        or []
    )
    try:
        refunds = (
            sb.table("refund_requests")
            .select(
                "id,transaction_id,user_id,requested_by,status,amount_brl,fee_brl,"
                "credits_mb,mp_refund_id,note,created_at"
            )
            .order("created_at", desc=True)
            .limit(30)
            .execute()
            .data
            or []
        )
    except Exception:
        refunds = []
    jobs = (
        sb.table("jobs")
        .select("id,user_id,file_size_mb,status,created_at,filename")
        .order("created_at", desc=True)
        .limit(80)
        .execute()
        .data
        or []
    )

    emails = {u["id"]: (u.get("email") or "") for u in users}
    users_by_id = {u["id"]: u for u in users}

    invoice_by_user: dict[str, dict[str, Any]] = {}
    paid_by_user: dict[str, dict[str, Any]] = {}

    gross_paid = 0.0
    fees_paid = 0.0
    refunded_money = 0.0
    invoice_credits = 0
    paid_credits = 0

    for tx in txs:
        uid = tx.get("user_id") or ""
        amount = float(tx.get("amount_brl") or 0)
        fee = float(tx.get("fee_brl") or 0)
        credits = int(tx.get("credits_mb") or 0)
        status = str(tx.get("payment_status") or "")
        meta = tx.get("payment_metadata") or {}

        if _is_invoice_tx(tx):
            invoice_credits += credits
            bucket = invoice_by_user.setdefault(
                uid,
                {
                    "user_id": uid,
                    "email": emails.get(uid, ""),
                    "credits_granted_mb": 0,
                    "amount_contracted_brl": 0.0,
                    "purchases": 0,
                    "last_at": None,
                    "notes": [],
                },
            )
            bucket["credits_granted_mb"] += credits
            bucket["amount_contracted_brl"] += amount
            bucket["purchases"] += 1
            bucket["last_at"] = tx.get("created_at")
            if meta.get("note"):
                bucket["notes"].append(str(meta["note"]))
            continue

        if status in {"approved", "partially_refunded", "refunded"}:
            gross_paid += amount
            fees_paid += fee
            refunded_money += float(tx.get("refunded_amount_brl") or 0)
            paid_credits += credits
            bucket = paid_by_user.setdefault(
                uid,
                {
                    "user_id": uid,
                    "email": emails.get(uid, ""),
                    "credits_bought_mb": 0,
                    "amount_paid_brl": 0.0,
                    "fee_brl": 0.0,
                    "purchases": 0,
                    "last_at": None,
                    "methods": set(),
                },
            )
            bucket["credits_bought_mb"] += credits
            bucket["amount_paid_brl"] += amount
            bucket["fee_brl"] += fee
            bucket["purchases"] += 1
            bucket["last_at"] = tx.get("created_at")
            bucket["methods"].add(str(tx.get("payment_method") or ""))

    # Enrich balances + usage
    jobs_by_user: dict[str, list[dict[str, Any]]] = {}
    mb_by_user: dict[str, float] = {}
    for job in jobs:
        uid = job.get("user_id") or ""
        if not uid:
            continue
        jobs_by_user.setdefault(uid, []).append(job)
        mb_by_user[uid] = mb_by_user.get(uid, 0.0) + float(job.get("file_size_mb") or 0)

    invoiced_accounts: list[dict[str, Any]] = []
    for uid, bucket in invoice_by_user.items():
        u = users_by_id.get(uid) or {}
        total = int(u.get("total_credits_mb") or 0)
        used = int(u.get("used_credits_mb") or 0)
        available = max(0, total - used)
        low = total > 0 and available / total <= 0.2
        recent = jobs_by_user.get(uid, [])[:3]
        invoiced_accounts.append(
            {
                **bucket,
                "amount_contracted_brl": round(bucket["amount_contracted_brl"], 2),
                "total_credits_mb": total,
                "used_credits_mb": used,
                "available_mb": available,
                "mb_processed_recent": round(mb_by_user.get(uid, 0.0), 2),
                "jobs_recent": len(jobs_by_user.get(uid, [])),
                "low_balance": low,
                "last_jobs": [
                    {
                        "filename": j.get("filename"),
                        "file_size_mb": j.get("file_size_mb"),
                        "created_at": j.get("created_at"),
                        "status": j.get("status"),
                    }
                    for j in recent
                ],
                "notes": bucket["notes"][:3],
            }
        )
    invoiced_accounts.sort(key=lambda x: (-x["available_mb"], x["email"]))

    paid_accounts: list[dict[str, Any]] = []
    for uid, bucket in paid_by_user.items():
        u = users_by_id.get(uid) or {}
        total = int(u.get("total_credits_mb") or 0)
        used = int(u.get("used_credits_mb") or 0)
        available = max(0, total - used)
        methods = sorted(m for m in bucket["methods"] if m)
        paid_accounts.append(
            {
                "user_id": uid,
                "email": bucket["email"],
                "credits_bought_mb": bucket["credits_bought_mb"],
                "amount_paid_brl": round(bucket["amount_paid_brl"], 2),
                "fee_brl": round(bucket["fee_brl"], 2),
                "purchases": bucket["purchases"],
                "last_at": bucket["last_at"],
                "methods": methods,
                "total_credits_mb": total,
                "used_credits_mb": used,
                "available_mb": available,
                "active_paid": available > 0,
                "mb_processed_recent": round(mb_by_user.get(uid, 0.0), 2),
                "jobs_recent": len(jobs_by_user.get(uid, [])),
            }
        )
    paid_accounts.sort(key=lambda x: (-int(x["active_paid"]), -x["available_mb"], x["email"]))

    tx_items = []
    for row in txs:
        meta = row.get("payment_metadata") or {}
        tx_items.append(
            {
                **row,
                "user_email": emails.get(row.get("user_id") or "", ""),
                "package_id": meta.get("package_id"),
                "source": meta.get("source"),
                "is_invoice": _is_invoice_tx(row),
            }
        )

    for g in grants:
        g["user_email"] = emails.get(g.get("user_id") or "", "")
        g["granted_by_email"] = emails.get(g.get("granted_by") or "", "")
    for r in refunds:
        r["user_email"] = emails.get(r.get("user_id") or "", "")
        r["requested_by_email"] = emails.get(r.get("requested_by") or "", "")

    active_paid = [p for p in paid_accounts if p["active_paid"]]
    low_invoice = [a for a in invoiced_accounts if a["low_balance"]]

    return {
        "version": get_app_version(),
        "summary": {
            "gross_paid_brl": round(gross_paid, 2),
            "fees_brl": round(fees_paid, 2),
            "net_paid_brl": round(gross_paid - fees_paid, 2),
            "refunded_brl": round(refunded_money, 2),
            "invoice_credits_mb": invoice_credits,
            "paid_credits_mb": paid_credits,
            "invoiced_accounts": len(invoiced_accounts),
            "paid_accounts": len(paid_accounts),
            "active_paid_accounts": len(active_paid),
            "low_balance_invoiced": len(low_invoice),
            "credits_in_circulation_mb": sum(
                max(0, int(u.get("total_credits_mb") or 0) - int(u.get("used_credits_mb") or 0))
                for u in users
                if str(u.get("role") or "") != "admin"
            ),
        },
        "invoiced_accounts": invoiced_accounts,
        "paid_accounts": paid_accounts,
        "transactions": tx_items,
        "grants": grants,
        "refunds": refunds,
    }
