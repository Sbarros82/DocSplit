-- Script alternativo: Limpa tudo e recria do zero
-- Use SOMENTE se quiser recomeçar (apaga todos os dados!)

-- ========================================
-- 1. LIMPAR TUDO (CUIDADO: APAGA DADOS!)
-- ========================================

DROP VIEW IF EXISTS public.user_dashboard;
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS reset_daily_free_uses();
DROP FUNCTION IF EXISTS consume_credits(UUID, DECIMAL);
DROP FUNCTION IF EXISTS get_available_credits(UUID);
DROP TABLE IF EXISTS public.jobs CASCADE;
DROP TABLE IF EXISTS public.transactions CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- ========================================
-- 2. AGORA EXECUTE O schema.sql NORMAL
-- ========================================

-- Após limpar, volte ao SQL Editor e execute d:\Snap\supabase\schema.sql
