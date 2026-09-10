"""Supabase client, shared across endpoints.

Reads SUPABASE_URL / SUPABASE_KEY from backend/.env (see .env.example).
Kept as a single lazily-created client rather than a class/abstraction —
there's exactly one backend process talking to exactly one Supabase
project for this prototype, so a module-level singleton is enough.
"""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_KEY not set. Copy backend/.env.example "
                "to backend/.env and fill them in."
            )
        _client = create_client(url, key)
    return _client


# Whether sessions has the `memory` jsonb column (database/schema.sql). It was
# added after the original schema, and DDL can't be run through the REST
# client this backend uses — so a project that hasn't run the migration yet
# simply doesn't have it. Everything that touches `memory` checks this first,
# so the app runs identically with or without the column: without it, typed
# categories still show on the fresh Summary screen (straight from the
# extraction response) but aren't persisted for Review. Probed once and
# cached, since the schema doesn't change under a running process.
_has_memory_column: bool | None = None


def has_memory_column() -> bool:
    global _has_memory_column
    if _has_memory_column is None:
        try:
            get_client().table("sessions").select("memory").limit(1).execute()
            _has_memory_column = True
        except Exception:
            # PostgREST 400s when the column is unknown — treat any failure
            # here as "not present" and carry on without persistence.
            _has_memory_column = False
    return _has_memory_column


# Whether the pgvector setup for semantic recall exists — the `embedding`
# column and the match_sessions() function (database/schema.sql). Same story
# as the memory column: it needs a SQL migration this REST-only backend can't
# run, so recall falls back to recency-ordered retrieval until it's present.
# Probed by calling the search function with a zero vector; a missing function
# or extension makes that fail, which we read as "not set up".
_has_semantic_search: bool | None = None


def has_semantic_search(embed_dim: int) -> bool:
    global _has_semantic_search
    if _has_semantic_search is None:
        try:
            get_client().rpc(
                "match_sessions",
                {"query_embedding": [0.0] * embed_dim, "match_count": 1},
            ).execute()
            _has_semantic_search = True
        except Exception:
            _has_semantic_search = False
    return _has_semantic_search
