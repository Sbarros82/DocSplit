-- DocSplit — Schema Supabase
-- Execute no SQL Editor do painel Supabase

-- ========================================
-- 1. EXTENSÕES
-- ========================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- 2. TABELA DE USUÁRIOS
-- ========================================
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Créditos
  total_credits_mb INTEGER DEFAULT 0,
  used_credits_mb INTEGER DEFAULT 0,
  
  -- Limite gratuito
  last_free_use TIMESTAMP WITH TIME ZONE,
  free_uses_today INTEGER DEFAULT 0,
  
  -- Metadata
  display_name TEXT,
  avatar_url TEXT,
  
  CONSTRAINT credits_valid CHECK (used_credits_mb >= 0 AND used_credits_mb <= total_credits_mb)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- ========================================
-- 3. TABELA DE TRANSAÇÕES
-- ========================================
CREATE TABLE IF NOT EXISTS public.transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  
  -- Pagamento
  amount_brl DECIMAL(10,2) NOT NULL,
  credits_mb INTEGER NOT NULL,
  payment_method TEXT NOT NULL, -- 'mercadopago' | 'pagseguro'
  payment_id TEXT UNIQUE NOT NULL, -- ID do Mercado Pago
  payment_status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected' | 'cancelled'
  
  -- Datas
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE, -- created_at + 90 dias
  approved_at TIMESTAMP WITH TIME ZONE,
  
  -- Metadata do pagamento
  payment_metadata JSONB,
  
  CONSTRAINT amount_positive CHECK (amount_brl > 0),
  CONSTRAINT credits_positive CHECK (credits_mb > 0)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON public.transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_payment_id ON public.transactions(payment_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON public.transactions(payment_status);

-- ========================================
-- 4. TABELA DE JOBS (processamentos)
-- ========================================
CREATE TABLE IF NOT EXISTS public.jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
  
  -- Arquivo
  filename TEXT NOT NULL,
  file_size_mb DECIMAL(10,2) NOT NULL,
  pages_count INTEGER,
  documents_count INTEGER,
  
  -- Status
  status TEXT NOT NULL DEFAULT 'processing', -- 'processing' | 'completed' | 'failed'
  error_message TEXT,
  
  -- Performance
  processing_time_seconds INTEGER,
  used_ocr BOOLEAN DEFAULT FALSE,
  
  -- Datas
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  
  -- Metadata
  ip_address TEXT,
  user_agent TEXT,
  
  CONSTRAINT file_size_positive CHECK (file_size_mb > 0),
  CONSTRAINT pages_positive CHECK (pages_count IS NULL OR pages_count > 0)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON public.jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON public.jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON public.jobs(created_at DESC);

-- ========================================
-- 5. FUNÇÕES AUXILIARES
-- ========================================

-- Função para calcular créditos disponíveis (descontando expirados)
CREATE OR REPLACE FUNCTION get_available_credits(user_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
  total_unexpired INTEGER;
BEGIN
  -- Soma créditos de transações aprovadas não expiradas
  SELECT COALESCE(SUM(credits_mb), 0) INTO total_unexpired
  FROM public.transactions
  WHERE user_id = user_uuid
    AND payment_status = 'approved'
    AND (expires_at IS NULL OR expires_at > NOW());
  
  -- Subtrai créditos usados
  RETURN total_unexpired - (
    SELECT COALESCE(used_credits_mb, 0)
    FROM public.users
    WHERE id = user_uuid
  );
END;
$$ LANGUAGE plpgsql;

-- Função para descontar créditos
CREATE OR REPLACE FUNCTION consume_credits(user_uuid UUID, mb_to_consume DECIMAL)
RETURNS BOOLEAN AS $$
DECLARE
  available INTEGER;
BEGIN
  available := get_available_credits(user_uuid);
  
  IF available >= mb_to_consume THEN
    UPDATE public.users
    SET used_credits_mb = used_credits_mb + mb_to_consume
    WHERE id = user_uuid;
    RETURN TRUE;
  ELSE
    RETURN FALSE;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Função para resetar usos gratuitos diários (rodar a cada meia-noite via cron)
CREATE OR REPLACE FUNCTION reset_daily_free_uses()
RETURNS VOID AS $$
BEGIN
  UPDATE public.users
  SET free_uses_today = 0
  WHERE last_free_use < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 6. ROW LEVEL SECURITY (RLS)
-- ========================================

-- Habilitar RLS em todas as tabelas
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Políticas para USERS
CREATE POLICY "Users can view own data"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own data"
  ON public.users FOR UPDATE
  USING (auth.uid() = id);

-- Políticas para TRANSACTIONS
CREATE POLICY "Users can view own transactions"
  ON public.transactions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "System can insert transactions"
  ON public.transactions FOR INSERT
  WITH CHECK (true); -- Webhook/backend cria transações

-- Políticas para JOBS
CREATE POLICY "Users can view own jobs"
  ON public.jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs"
  ON public.jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- ========================================
-- 7. TRIGGERS
-- ========================================

-- Trigger para criar usuário quando auth.users é criado
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, display_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'display_name',
    NEW.raw_user_meta_data->>'avatar_url'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ========================================
-- 8. DADOS INICIAIS (opcional)
-- ========================================

-- Pacotes de créditos disponíveis (pode ser uma tabela ou config no frontend)
COMMENT ON TABLE public.transactions IS 'Histórico de compras de créditos. Valores sugeridos: R$5=50MB, R$15=200MB, R$30=500MB, R$50=1GB';

-- ========================================
-- 9. VISUALIZAÇÕES ÚTEIS
-- ========================================

-- View para dashboard do usuário
CREATE OR REPLACE VIEW public.user_dashboard AS
SELECT 
  u.id,
  u.email,
  u.display_name,
  get_available_credits(u.id) AS available_credits_mb,
  u.used_credits_mb,
  u.total_credits_mb,
  u.free_uses_today,
  COUNT(j.id) AS total_jobs,
  COUNT(CASE WHEN j.status = 'completed' THEN 1 END) AS completed_jobs,
  SUM(CASE WHEN j.status = 'completed' THEN j.file_size_mb ELSE 0 END) AS total_mb_processed
FROM public.users u
LEFT JOIN public.jobs j ON j.user_id = u.id
GROUP BY u.id;

-- Grant acesso à view
GRANT SELECT ON public.user_dashboard TO authenticated;

-- ========================================
-- CONCLUÍDO
-- ========================================
-- Execute este arquivo inteiro no SQL Editor do Supabase
-- Depois configure as variáveis de ambiente no backend
