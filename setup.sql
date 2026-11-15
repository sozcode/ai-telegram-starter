-- Run this once in Supabase > SQL Editor > New query > Run

-- 1. Which OpenAI conversation belongs to which Telegram chat
create table if not exists public.chats (
  chat_id bigint primary key,
  conversation_id text not null,
  updated_at timestamptz default now()
);

-- 2. Every message (for the demo-day leaderboard)
create table if not exists public.messages (
  id bigint generated always as identity primary key,
  chat_id bigint not null,
  user_name text,
  role text not null check (role in ('user', 'bot')),
  text text,
  created_at timestamptz default now()
);

-- 3. Security: turn on Row Level Security with NO policies,
--    so the public (anon) key can't read anyone's chats.
alter table public.chats enable row level security;
alter table public.messages enable row level security;

-- 4. New Supabase projects (since 2026) don't expose tables automatically.
--    Give ONLY the server-side secret key (service_role) access.
grant select, insert, update, delete on public.chats to service_role;
grant select, insert on public.messages to service_role;

-- 5. Keep updated_at fresh
create or replace function public.touch_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists chats_touch on public.chats;
create trigger chats_touch before update on public.chats
for each row execute function public.touch_updated_at();

-- Demo day leaderboard (run any time):
-- select user_name, count(*) as messages
-- from public.messages where role = 'user'
-- group by user_name order by messages desc;
