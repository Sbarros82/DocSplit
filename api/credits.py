"""Checagem e consumo de créditos, free tier e limite das ferramentas PDF."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import HTTPException, Request

from api.auth import CurrentUser

MAX_FREE_USES_DAY = 1
MAX_FREE_FILE_SIZE_MB = 2.0
MAX_FREE_PAGES = 10
LOGGED_TOOL_LIMIT = 2

_TOOL_USAGE: dict[str, tuple[str, int]] = {}
_IP_MEM: dict[str, tuple[str, int]] = {}


def get_client_ip(request: Request) -> str:
    """IP do cliente considerando proxies do Fly.io."""
    forwarded = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _usable_ip(ip: str | None) -> str | None:
    """Ignora IPs inválidos/locais para não bloquear todo mundo junto."""
    if not ip:
        return None
    value = ip.strip().lower()
    if not value or value in {"unknown", "127.0.0.1", "::1", "localhost"}:
        return None
    if value.startswith("10.") or value.startswith("192.168.") or value.startswith("fc") or value.startswith("fd"):
        return None
    return value


def _today() -> str:
    return date.today().isoformat()


def _parse_date(value: Any) -> str | None:
    if not value:
        return None
    text = str(value)
    return text[:10]


def _mem_count(key: str) -> int:
    day, count = _TOOL_USAGE.get(key, (_today(), 0))
    if day != _today():
        return 0
    return count


def _mem_inc(key: str) -> int:
    count = _mem_count(key) + 1
    _TOOL_USAGE[key] = (_today(), count)
    return count


def _ip_mem_count(kind: str, ip: str) -> int:
    key = f"{kind}:{ip}"
    day, count = _IP_MEM.get(key, (_today(), 0))
    if day != _today():
        return 0
    return count


def _ip_mem_inc(kind: str, ip: str) -> int:
    key = f"{kind}:{ip}"
    count = _ip_mem_count(kind, ip) + 1
    _IP_MEM[key] = (_today(), count)
    return count


def _safe_credits(user_id: str) -> dict | None:
    try:
        from src.pdf_splitter.supabase_client import get_user_credits

        return get_user_credits(user_id)
    except Exception:
        return None


def _load_user_row(user_id: str) -> dict | None:
    try:
        from src.pdf_splitter.supabase_client import get_supabase

        response = get_supabase().table("users").select("*").eq("id", user_id).single().execute()
        return response.data
    except Exception:
        return None


def _reset_daily_counters_if_needed(user: dict) -> dict:
    """Zera contadores diários se o último uso não foi hoje."""
    last_free = _parse_date(user.get("last_free_use"))
    last_tools = _parse_date(user.get("pdf_tools_last_use"))
    today = _today()
    updates: dict[str, Any] = {}
    if last_free and last_free != today and int(user.get("free_uses_today") or 0) > 0:
        updates["free_uses_today"] = 0
        user["free_uses_today"] = 0
    if last_tools and last_tools != today and int(user.get("pdf_tools_uses_today") or 0) > 0:
        updates["pdf_tools_uses_today"] = 0
        user["pdf_tools_uses_today"] = 0
    if updates:
        try:
            from src.pdf_splitter.supabase_client import get_supabase

            get_supabase().table("users").update(updates).eq("id", user["id"]).execute()
        except Exception:
            pass
    return user


def _get_ip_usage_row(ip: str) -> dict | None:
    try:
        from src.pdf_splitter.supabase_client import get_supabase

        response = (
            get_supabase()
            .table("ip_daily_usage")
            .select("*")
            .eq("ip", ip)
            .eq("usage_date", _today())
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def _ip_free_count(ip: str) -> int:
    mem = _ip_mem_count("free", ip)
    row = _get_ip_usage_row(ip)
    db = int((row or {}).get("free_process_count") or 0)
    return max(mem, db)


def _ip_tool_count(ip: str) -> int:
    mem = _ip_mem_count("tool", ip)
    row = _get_ip_usage_row(ip)
    db = int((row or {}).get("tool_use_count") or 0)
    return max(mem, db)


def _bump_ip_usage(
    *,
    ip: str,
    user_id: str | None,
    email: str | None,
    free_delta: int = 0,
    tool_delta: int = 0,
) -> None:
    if free_delta:
        _ip_mem_inc("free", ip)
    if tool_delta:
        _ip_mem_inc("tool", ip)
    try:
        from src.pdf_splitter.supabase_client import get_supabase

        sb = get_supabase()
        today = _today()
        existing = _get_ip_usage_row(ip)
        if existing:
            sb.table("ip_daily_usage").update({
                "free_process_count": int(existing.get("free_process_count") or 0) + free_delta,
                "tool_use_count": int(existing.get("tool_use_count") or 0) + tool_delta,
                "last_user_id": user_id,
                "last_email": email,
                "updated_at": datetime.now().isoformat(),
            }).eq("ip", ip).eq("usage_date", today).execute()
        else:
            sb.table("ip_daily_usage").insert({
                "ip": ip,
                "usage_date": today,
                "free_process_count": free_delta,
                "tool_use_count": tool_delta,
                "last_user_id": user_id,
                "last_email": email,
                "updated_at": datetime.now().isoformat(),
            }).execute()
    except Exception:
        pass


def check_can_process(
    user_id: str,
    file_size_mb: float,
    page_count: int,
    client_ip: str | None = None,
) -> str:
    """Verifica se o usuário pode processar. Retorna 'credits', 'free' ou 'admin'.

    Raises HTTPException 403 se não puder processar.
    """
    user_row = _load_user_row(user_id)
    if user_row and str(user_row.get("role") or "").lower() == "admin":
        return "admin"
    email = (user_row or {}).get("email")
    try:
        from api.routes_admin import is_admin_email

        if is_admin_email(email):
            return "admin"
    except Exception:
        pass

    credits = _safe_credits(user_id)
    available = float((credits or {}).get("available_mb") or 0)
    if available >= file_size_mb and available > 0:
        return "credits"

    user = user_row
    if not user:
        raise HTTPException(403, "Usuário não encontrado. Faça login novamente.")
    user = _reset_daily_counters_if_needed(user)

    uses = int(user.get("free_uses_today") or 0)
    if uses >= MAX_FREE_USES_DAY:
        raise HTTPException(
            403,
            f"Limite gratuito diário atingido ({MAX_FREE_USES_DAY} arquivos/dia). Adquira créditos para continuar.",
        )

    ip = _usable_ip(client_ip)
    if ip is not None and _ip_free_count(ip) >= MAX_FREE_USES_DAY:
        raise HTTPException(
            403,
            f"Limite gratuito diário deste IP atingido ({MAX_FREE_USES_DAY} arquivos/dia). "
            "Adquira créditos para continuar.",
        )

    if file_size_mb > MAX_FREE_FILE_SIZE_MB:
        raise HTTPException(
            403,
            f"Arquivo muito grande para o plano gratuito (máx {MAX_FREE_FILE_SIZE_MB:.0f} MB). Adquira créditos para arquivos maiores.",
        )
    if page_count > MAX_FREE_PAGES:
        raise HTTPException(
            403,
            f"Arquivo com muitas páginas para o plano gratuito (máx {MAX_FREE_PAGES} páginas). Adquira créditos para continuar.",
        )
    return "free"


def consume_after_process(
    user_id: str,
    file_size_mb: float,
    mode: str,
    client_ip: str | None = None,
    email: str | None = None,
) -> float:
    """Desconta créditos ou incrementa o uso gratuito. Retorna MB cobrados."""
    if mode == "admin":
        return 0.0

    if mode == "credits":
        try:
            from src.pdf_splitter.supabase_client import consume_credits

            consume_credits(user_id, file_size_mb)
        except Exception:
            try:
                from src.pdf_splitter.supabase_client import get_supabase

                user = _load_user_row(user_id) or {}
                used = float(user.get("used_credits_mb") or 0) + file_size_mb
                get_supabase().table("users").update({"used_credits_mb": used}).eq("id", user_id).execute()
            except Exception:
                pass
        return round(file_size_mb, 2)

    try:
        from src.pdf_splitter.supabase_client import increment_free_use

        increment_free_use(user_id)
    except Exception:
        pass

    ip = _usable_ip(client_ip)
    if ip is not None:
        _bump_ip_usage(ip=ip, user_id=user_id, email=email, free_delta=1)
    return 0.0


def try_create_job(**kwargs: Any) -> str | None:
    try:
        from src.pdf_splitter.supabase_client import create_job

        return create_job(**kwargs)
    except Exception:
        return None


def try_complete_job(job_id: str | None, **kwargs: Any) -> None:
    if not job_id:
        return
    try:
        from src.pdf_splitter.supabase_client import complete_job

        complete_job(job_id, **kwargs)
    except Exception:
        pass


def try_fail_job(job_id: str | None, error_message: str) -> None:
    if not job_id:
        return
    try:
        from src.pdf_splitter.supabase_client import fail_job

        fail_job(job_id, error_message)
    except Exception:
        pass


def _has_paid_credits(user_id: str) -> bool:
    credits = _safe_credits(user_id)
    return float((credits or {}).get("available_mb") or 0) > 0


def _is_admin_account(user: CurrentUser) -> bool:
    try:
        from api.routes_admin import is_admin_user

        return is_admin_user(user)
    except Exception:
        return False


def get_tool_usage(user: CurrentUser, client_ip: str | None = None) -> dict:
    """Retorna o uso restante das ferramentas PDF hoje (somente usuário logado)."""
    if _is_admin_account(user) or _has_paid_credits(user.user_id):
        return {
            "authenticated": True,
            "unlimited": True,
            "has_credits": _has_paid_credits(user.user_id),
            "is_admin": _is_admin_account(user),
            "used_today": 0,
            "limit": None,
            "remaining": None,
        }

    row = _load_user_row(user.user_id)
    used = _mem_count(f"user:{user.user_id}")
    if row:
        row = _reset_daily_counters_if_needed(row)
        db_used = int(row.get("pdf_tools_uses_today") or 0)
        used = max(used, db_used)

    ip = _usable_ip(client_ip)
    if ip is not None:
        used = max(used, _ip_tool_count(ip))

    remaining = max(0, LOGGED_TOOL_LIMIT - used)
    return {
        "authenticated": True,
        "unlimited": False,
        "has_credits": False,
        "is_admin": False,
        "used_today": used,
        "limit": LOGGED_TOOL_LIMIT,
        "remaining": remaining,
    }


def check_tool_limit(user: CurrentUser, client_ip: str | None = None) -> None:
    """Bloqueia se o limite diário das ferramentas foi atingido (conta ou IP)."""
    usage = get_tool_usage(user, client_ip)
    if usage.get("unlimited"):
        return
    if int(usage.get("remaining") or 0) <= 0:
        raise HTTPException(
            403,
            f"Limite diário das ferramentas atingido ({LOGGED_TOOL_LIMIT} usos/dia). "
            "Adquira créditos para uso ilimitado.",
        )


def consume_tool_use(user: CurrentUser, client_ip: str | None = None) -> None:
    """Incrementa o contador de uso das ferramentas após sucesso."""
    if _is_admin_account(user) or _has_paid_credits(user.user_id):
        return

    _mem_inc(f"user:{user.user_id}")
    try:
        from src.pdf_splitter.supabase_client import get_supabase

        row = _load_user_row(user.user_id) or {}
        row = _reset_daily_counters_if_needed(row)
        used = int(row.get("pdf_tools_uses_today") or 0) + 1
        get_supabase().table("users").update({
            "pdf_tools_uses_today": used,
            "pdf_tools_last_use": datetime.now().isoformat(),
        }).eq("id", user.user_id).execute()
    except Exception:
        pass

    ip = _usable_ip(client_ip)
    if ip is not None:
        _bump_ip_usage(
            ip=ip,
            user_id=user.user_id,
            email=user.email,
            tool_delta=1,
        )


class ToolQuota:
    """Checa o limite no início e consome após sucesso (usuário autenticado)."""

    def __init__(self, user: CurrentUser, request: Request | None = None) -> None:
        self.user = user
        self.client_ip = get_client_ip(request) if request is not None else None
        check_tool_limit(user, self.client_ip)

    def consume(self) -> None:
        consume_tool_use(self.user, self.client_ip)
