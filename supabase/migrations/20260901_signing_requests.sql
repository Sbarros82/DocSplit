-- Solicitações de assinatura por link e histórico de carimbos

create table if not exists public.signing_requests (
  id uuid primary key default gen_random_uuid(),
  token text unique not null,
  owner_user_id uuid not null references public.users(id) on delete cascade,
  recipient_email text not null,
  recipient_name text not null default '',
  owner_message text not null default '',
  status text not null default 'pending' check (status in ('pending', 'signed', 'expired')),
  page_number integer not null default -1,
  pos_x real not null default 0.62,
  pos_y real not null default 0.78,
  stamp_width real not null default 0.30,
  storage_path text not null,
  signed_storage_path text,
  original_filename text not null default 'documento.pdf',
  signer_info jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  signed_at timestamptz,
  signer_ip text
);

create index if not exists signing_requests_owner_idx on public.signing_requests (owner_user_id, created_at desc);
create index if not exists signing_requests_token_idx on public.signing_requests (token);

create table if not exists public.signature_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete set null,
  event_type text not null check (event_type in ('direct', 'link_sent', 'link_signed')),
  filename text not null default '',
  signer_name text not null default '',
  stamp_info jsonb not null default '{}'::jsonb,
  signing_request_id uuid references public.signing_requests(id) on delete set null,
  created_at timestamptz not null default now()
);

create index if not exists signature_events_user_idx on public.signature_events (user_id, created_at desc);

insert into storage.buckets (id, name, public)
values ('signing-docs', 'signing-docs', false)
on conflict (id) do nothing;
