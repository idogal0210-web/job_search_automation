-- Migration: Initial creation of public.sync_state table for cloud triage state synchronization
-- Remote version: 20261109222817

create table if not exists public.sync_state (
  id text primary key,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamp with time zone not null default now()
);

-- Enable Row Level Security
alter table public.sync_state enable row level security;
