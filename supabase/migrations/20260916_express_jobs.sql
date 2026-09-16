-- DocSplit Rápido: jobs avulsos pagos por página
create table if not exists public.express_jobs (
  id uuid primary key default gen_random_uuid(),
  token text not null unique,
  status text not null default 'awaiting_payment',
  whatsapp text not null,
  email text,
  original_filename text,
  storage_path text not null,
  result_storage_path text,
  pages_count integer not null default 0,
  file_size_mb numeric(12,2) not null default 0,
  amount_brl numeric(12,2) not null,
  price_per_page_brl numeric(12,4) not null,
  preference_id text,
  payment_id text,
  payment_status text,
  download_token text unique,
  whatsapp_share_url text,
  error_message text,
  paid_at timestamptz,
  completed_at timestamptz,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_express_jobs_status on public.express_jobs(status);
create index if not exists idx_express_jobs_payment on public.express_jobs(payment_id);
create index if not exists idx_express_jobs_token on public.express_jobs(token);

alter table public.express_jobs enable row level security;
