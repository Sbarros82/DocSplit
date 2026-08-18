"""Teste de conexão com Supabase"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("Verificando variaveis de ambiente...")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NAO DEFINIDA')}")
print(f"SUPABASE_SERVICE_ROLE_KEY: {'OK Definida' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'ERRO Nao definida'}")
print()

try:
    from src.pdf_splitter.supabase_client import get_supabase
    
    client = get_supabase()
    print("[OK] Supabase conectado com sucesso!")
    print(f"URL: {client.supabase_url}")
    
    # Teste de consulta
    result = client.table("users").select("*").limit(1).execute()
    print(f"[OK] Query test OK (users: {len(result.data)} linhas)")
    
except Exception as e:
    print(f"[ERRO] {e}")
