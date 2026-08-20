-- Refund fields on transactions + audit log
ALTER TABLE public.transactions
  ADD COLUMN IF NOT EXISTS fee_brl NUMERIC(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS net_amount_brl NUMERIC(10,2),
  ADD COLUMN IF NOT EXISTS refunded_amount_brl NUMERIC(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS refunded_credits_mb INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS refund_note TEXT;

UPDATE public.transactions
SET net_amount_brl = GREATEST(0, amount_brl - COALESCE(fee_brl, 0))
WHERE net_amount_brl IS NULL;

CREATE TABLE IF NOT EXISTS public.refund_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  requested_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'completed',
  amount_brl NUMERIC(10,2) NOT NULL DEFAULT 0,
  fee_brl NUMERIC(10,2) NOT NULL DEFAULT 0,
  credits_mb INTEGER NOT NULL DEFAULT 0,
  mp_refund_id TEXT,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refund_requests_tx ON public.refund_requests(transaction_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON public.transactions(created_at DESC);
