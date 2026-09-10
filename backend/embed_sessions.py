"""Backfills semantic-recall embeddings for sessions that don't have one.

New sessions are embedded automatically at summarize time (see main.py), but
sessions that were summarised *before* the pgvector migration have a null
`embedding`, so similarity search can't find them. Run this once after
enabling pgvector (database/schema.sql) to embed the backlog:

    python embed_sessions.py

Safe to re-run — it only touches rows that are summarised and not yet
embedded, so a second run is a near no-op. Add --all to re-embed every
summarised session (e.g. after changing the embedding model or dimension).
"""

import sys

from ai import EMBED_DIM, embed_text, session_embedding_text
from db import get_client, has_semantic_search


def main():
    if not has_semantic_search(EMBED_DIM):
        print(
            "Semantic recall isn't set up yet: the `embedding` column and "
            "match_sessions() function are missing.\nRun the pgvector block in "
            "database/schema.sql in the Supabase SQL Editor first, then re-run this."
        )
        return

    reembed_all = "--all" in sys.argv
    client = get_client()

    # Pull the fields the embedding is built from. `embedding` is selected so
    # already-embedded rows can be skipped without a second query.
    rows = (
        client.table("sessions")
        .select("id,summary,facts,embedding")
        .not_.is_("summary", "null")
        .execute()
    ).data

    todo = [r for r in rows if reembed_all or not r.get("embedding")]
    if not todo:
        print(f"Nothing to do — all {len(rows)} summarised session(s) already embedded.")
        return

    print(f"Embedding {len(todo)} session(s)…")
    done = 0
    for r in todo:
        text = session_embedding_text(r.get("summary") or "", r.get("facts") or [])
        if not text:
            continue
        try:
            vector = embed_text(text, is_query=False)
        except Exception as exc:
            print(f"  {r['id'][:8]} — skipped ({exc})")
            continue
        if not vector:
            continue
        client.table("sessions").update({"embedding": vector}).eq("id", r["id"]).execute()
        done += 1
        print(f"  {r['id'][:8]} — embedded")

    print(f"Done. Embedded {done} session(s).")


if __name__ == "__main__":
    main()
