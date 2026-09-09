-- pdf_tool_events: usage log for Central de PDF / signing tools
create table if not exists public.pdf_tool_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete set null,
  tool text not null,
  filename text,
  file_size_mb numeric(12,2) not null default 0,
  credits_charged_mb numeric(12,2) not null default 0,
  mode text not null default 'free',
  created_at timestamptz not null default now()
);

create index if not exists idx_pdf_tool_events_user_created
  on public.pdf_tool_events (user_id, created_at desc);

create index if not exists idx_pdf_tool_events_created
  on public.pdf_tool_events (created_at desc);

alter table public.pdf_tool_events enable row level security;

drop policy if exists "Users read own pdf_tool_events" on public.pdf_tool_events;
create policy "Users read own pdf_tool_events"
  on public.pdf_tool_events for select
  using (auth.uid() = user_id);
