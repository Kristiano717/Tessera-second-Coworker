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
