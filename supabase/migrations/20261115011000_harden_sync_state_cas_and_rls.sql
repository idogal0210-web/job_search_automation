-- Migration: Harden public.sync_state with per-user user_id key, integer version CAS,
-- strict auth.uid() RLS policies, and a database-level guard against self-signup.

-- 1. Add user_id and version columns to public.sync_state (non-destructive)
alter table public.sync_state
  add column if not exists user_id uuid references auth.users(id) on delete cascade default auth.uid(),
  add column if not exists version bigint not null default 1;

-- 2. Backfill existing row(s) with the owner account UUID from auth.users
update public.sync_state
set user_id = (
  select u.id
  from auth.users u
  order by u.created_at asc
  limit 1
)
where user_id is null;

-- 3. Enforce one sync_state row per authenticated user_id
create unique index if not exists sync_state_user_id_idx on public.sync_state (user_id);

-- 4. Automatically increment version on every UPDATE
create or replace function public.bump_sync_state_version()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  new.version := coalesce(old.version, 0) + 1;
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_bump_sync_state_version on public.sync_state;
create trigger trg_bump_sync_state_version
  before update on public.sync_state
  for each row
  execute function public.bump_sync_state_version();

-- 5. Replace RLS policies to enforce strict user_id = (select auth.uid()) ownership
alter table public.sync_state enable row level security;
alter table public.sync_state force row level security;

drop policy if exists sync_state_owner_select on public.sync_state;
drop policy if exists sync_state_owner_insert on public.sync_state;
drop policy if exists sync_state_owner_update on public.sync_state;
drop policy if exists sync_state_owner_delete on public.sync_state;

create policy sync_state_owner_select
  on public.sync_state
  for select
  to authenticated
  using (user_id = (select auth.uid()));

create policy sync_state_owner_insert
  on public.sync_state
  for insert
  to authenticated
  with check (user_id = (select auth.uid()));

create policy sync_state_owner_update
  on public.sync_state
  for update
  to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

create policy sync_state_owner_delete
  on public.sync_state
  for delete
  to authenticated
  using (user_id = (select auth.uid()));

-- 6. Database-level guard blocking unauthorized self-signup when an owner account already exists
create or replace function public.block_unauthorized_signup()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if exists (select 1 from auth.users) then
    raise exception 'Self-signup is disabled for this personal dashboard.';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_block_unauthorized_signup on auth.users;
create trigger trg_block_unauthorized_signup
  before insert on auth.users
  for each row
  execute function public.block_unauthorized_signup();
