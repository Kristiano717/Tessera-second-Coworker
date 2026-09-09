-- Second Coworker — Supabase schema
-- Run this once in the Supabase SQL Editor (Project → SQL Editor → New query).
-- Don't add columns here without updating CLAUDE.md's schema section too.

create table if not exists sessions (
  id uuid primary key default gen_random_uuid(),
  transcript text not null,
  -- Nullable: a session row is created at "save works" (Milestone 2) with
  -- the transcript only; summary is filled in later by Milestone 4's LLM call.
  summary text,
  -- DEVIATION from CLAUDE.md's locked schema, added deliberately with
  -- sign-off: the spec's sessions table has no home for the `facts` array
  -- the extraction call returns. Folding facts into the summary text works
  -- but throws away their structure, which is exactly the product
  -- differentiator ("structured memory objects, not raw text"). Stored as
  -- jsonb array of strings.
  facts jsonb not null default '[]'::jsonb,
  -- The fully typed memory objects: a jsonb array of {category, text}, where
  -- category is one of the six fixed kinds (Task, Decision, Preference,
  -- Requirement, Fact, Action Item). `facts` and the tasks table stay as the
  -- flat, category-less views the tray and older code read; this column is
  -- what makes "structured memory objects, not raw text" literally true in
  -- storage. Nullable/default-empty so rows written before it existed, and
  -- projects that haven't run the migration below, both stay valid — the
  -- backend only reads/writes it when the column is present (db.has_memory_column).
  memory jsonb not null default '[]'::jsonb,
  "timestamp" timestamptz not null default now()
);

create table if not exists tasks (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references sessions(id) on delete cascade,
  text text not null,
  "timestamp" timestamptz not null default now()
);

-- Recall (Milestone 5) retrieves past sessions by recency — no vector
-- search per CLAUDE.md, so a plain index on timestamp is all this needs.
create index if not exists sessions_timestamp_idx on sessions ("timestamp" desc);
create index if not exists tasks_session_id_idx on tasks (session_id);

-- Migration for projects created before the facts column existed. Safe to
-- re-run; no-ops if the column is already there.
alter table sessions add column if not exists facts jsonb not null default '[]'::jsonb;

-- Migration for the typed memory column. Run this one line in the Supabase
-- SQL Editor to turn on persisted categories: once it's present, the backend
-- detects it on the next start and begins storing/serving `memory`, so the
-- Review screen shows the six categories for every newly summarised session.
-- Until then the app runs fine without it. Safe to re-run.
alter table sessions add column if not exists memory jsonb not null default '[]'::jsonb;
