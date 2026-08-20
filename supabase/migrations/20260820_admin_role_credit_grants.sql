-- Admin role + manual invoice credits (mirror of remote migration)
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';

ALTER TABLE public.users
  DROP CONSTRAINT IF EXISTS users_role_check;

ALTER TABLE public.users
  ADD CONSTRAINT users_role_check CHECK (role IN ('user', 'admin'));

CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);

ALTER TABLE public.transactions
  DROP CONSTRAINT IF EXISTS amount_positive;

ALTER TABLE public.transactions
  DROP CONSTRAINT IF EXISTS amount_non_negative;

ALTER TABLE public.transactions
  ADD CONSTRAINT amount_non_negative CHECK (amount_brl >= 0);

CREATE TABLE IF NOT EXISTS public.credit_grants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  granted_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
  credits_mb INTEGER NOT NULL CHECK (credits_mb > 0),
  amount_brl DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (amount_brl >= 0),
  note TEXT,
  transaction_id UUID REFERENCES public.transactions(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_credit_grants_user_id ON public.credit_grants(user_id);

ALTER TABLE public.credit_grants ENABLE ROW LEVEL SECURITY;

UPDATE public.users
SET role = 'admin'
WHERE lower(email) = lower('sbarros1982@gmail.com');
