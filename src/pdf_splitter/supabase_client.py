"""
Cliente Supabase para autenticação e banco de dados.
"""

import os
from supabase import create_client, Client
from .config import settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Retorna cliente Supabase singleton."""
    global _supabase_client
    
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar definidas"
            )
        
        _supabase_client = create_client(url, key)
    
    return _supabase_client


def get_user_credits(user_id: str) -> dict:
    """
    Retorna créditos disponíveis do usuário.
    
    Returns:
        {
            "available_mb": int,
            "total_mb": int,
            "used_mb": int,
            "free_uses_today": int
        }
    """
    supabase = get_supabase()
    
    # Buscar dados do usuário
    response = supabase.table("users").select("*").eq("id", user_id).single().execute()
    user = response.data
    
    if not user:
        raise ValueError(f"Usuário {user_id} não encontrado")
    
    # Calcular créditos disponíveis (função SQL)
    available_response = supabase.rpc("get_available_credits", {"user_uuid": user_id}).execute()
    available_mb = available_response.data or 0
    
    return {
        "available_mb": available_mb,
        "total_mb": user.get("total_credits_mb", 0),
        "used_mb": user.get("used_credits_mb", 0),
        "free_uses_today": user.get("free_uses_today", 0),
    }


def consume_credits(user_id: str, mb_to_consume: float) -> bool:
    """
    Desconta créditos do usuário.
    
    Returns:
        True se tinha crédito suficiente, False caso contrário.
    """
    supabase = get_supabase()
    
    response = supabase.rpc(
        "consume_credits",
        {"user_uuid": user_id, "mb_to_consume": mb_to_consume}
    ).execute()
    
    return response.data is True


def check_free_limit(user_id: str, file_size_mb: float) -> tuple[bool, str]:
    """
    Verifica se usuário pode usar o plano gratuito.
    
    Returns:
        (pode_usar, mensagem_erro)
    """
    supabase = get_supabase()
    
    response = supabase.table("users").select("*").eq("id", user_id).single().execute()
    user = response.data
    
    if not user:
        return False, "Usuário não encontrado"
    
    # Limites do plano gratuito
    MAX_FREE_USES_DAY = 3
    MAX_FREE_FILE_SIZE_MB = 2
    MAX_FREE_PAGES = 10
    
    if user.get("free_uses_today", 0) >= MAX_FREE_USES_DAY:
        return False, f"Limite gratuito diário atingido ({MAX_FREE_USES_DAY} arquivos/dia). Adquira créditos para continuar."
    
    if file_size_mb > MAX_FREE_FILE_SIZE_MB:
        return False, f"Arquivo muito grande para o plano gratuito (máx {MAX_FREE_FILE_SIZE_MB} MB). Adquira créditos para arquivos maiores."
    
    return True, ""


def increment_free_use(user_id: str) -> None:
    """Incrementa contador de usos gratuitos do dia."""
    from datetime import datetime

    supabase = get_supabase()
    response = supabase.table("users").select("free_uses_today").eq("id", user_id).single().execute()
    current = int((response.data or {}).get("free_uses_today") or 0)
    supabase.table("users").update({
        "free_uses_today": current + 1,
        "last_free_use": datetime.now().isoformat(),
    }).eq("id", user_id).execute()


def create_job(
    user_id: str | None,
    filename: str,
    file_size_mb: float,
    pages_count: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    """
    Cria um registro de job no banco.
    
    Returns:
        job_id (UUID)
    """
    supabase = get_supabase()
    
    response = supabase.table("jobs").insert({
        "user_id": user_id,
        "filename": filename,
        "file_size_mb": file_size_mb,
        "pages_count": pages_count,
        "status": "processing",
        "ip_address": ip_address,
        "user_agent": user_agent,
    }).execute()
    
    return response.data[0]["id"]


def complete_job(
    job_id: str,
    documents_count: int,
    processing_time_seconds: int,
    used_ocr: bool = False,
) -> None:
    """Marca job como concluído."""
    supabase = get_supabase()
    
    from datetime import datetime
    
    supabase.table("jobs").update({
        "status": "completed",
        "documents_count": documents_count,
        "processing_time_seconds": processing_time_seconds,
        "used_ocr": used_ocr,
        "completed_at": datetime.now().isoformat(),
    }).eq("id", job_id).execute()


def fail_job(job_id: str, error_message: str) -> None:
    """Marca job como falho."""
    supabase = get_supabase()
    
    supabase.table("jobs").update({
        "status": "failed",
        "error_message": error_message,
    }).eq("id", job_id).execute()
