-- Múltiplos signatários por documento

create table if not exists public.signing_recipients (
  id uuid primary key default gen_random_uuid(),
  request_id uuid not null references public.signing_requests(id) on delete cascade,
  token text unique not null,
  email text not null,
  name text not null default '',
  sign_order integer not null default 1,
  page_number integer not null default -1,
  pos_x real not null default 0.62,
  pos_y real not null default 0.78,
  status text not null default 'pending' check (status in ('pending', 'signed')),
  signer_info jsonb not null default '{}'::jsonb,
  signed_at timestamptz,
  signer_ip text,
  created_at timestamptz not null default now()
);

create index if not exists signing_recipients_request_idx on public.signing_recipients (request_id, sign_order);
create index if not exists signing_recipients_token_idx on public.signing_recipients (token);

alter table public.signing_requests drop constraint if exists signing_requests_status_check;
alter table public.signing_requests
  add constraint signing_requests_status_check
  check (status in ('pending', 'partial', 'signed', 'completed', 'expired'));
