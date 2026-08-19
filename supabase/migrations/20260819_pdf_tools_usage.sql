-- Contadores diários das ferramentas PDF (Central de PDF)
alter table public.users
  add column if not exists pdf_tools_uses_today integer not null default 0;

alter table public.users
  add column if not exists pdf_tools_last_use timestamptz;
