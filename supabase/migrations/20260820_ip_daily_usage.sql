-- Daily free/tool usage counters keyed by client IP (anti multi-account abuse)
CREATE TABLE IF NOT EXISTS public.ip_daily_usage (
  ip TEXT NOT NULL,
  usage_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  free_process_count INTEGER NOT NULL DEFAULT 0,
  tool_use_count INTEGER NOT NULL DEFAULT 0,
  last_user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
  last_email TEXT,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (ip, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_ip_daily_usage_date ON public.ip_daily_usage(usage_date DESC);

ALTER TABLE public.ip_daily_usage ENABLE ROW LEVEL SECURITY;
