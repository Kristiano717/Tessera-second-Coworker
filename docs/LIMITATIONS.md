# Limitations & Scaling — Second Coworker

Written to be *talked from* in an interview. Nothing here is hidden in the
code; owning it reads as more senior than pretending it isn't there. Each item
is: **why it's fine at prototype scale → what breaks as data grows → the fix.**

The recurring theme: this is a deliberate prototype. Almost every limit is a
conscious "don't build it until it's needed" call, and each has a clear,
bounded path to production — not a rewrite.

---

## 1 · Recall only sees a fixed window (`RECALL_SESSION_LIMIT = 10`)

**Now.** Recall retrieves at most 10 sessions as context ([backend/main.py](../backend/main.py)).
With pgvector on, those are the 10 *most similar* to the question; without it,
the 10 *most recent*. A small, bounded prompt keeps recall fast, cheap, and
deterministic.

**At 10k sessions.** Semantic search still surfaces relevant meetings, so this
degrades gracefully — but a question whose answer is spread across 30 meetings
only ever sees 10 of them, and the recency fallback becomes near-useless (the
right meeting is almost never in the last 10).

**Fix.** Raise the limit (costs prompt tokens + latency, and eventually the
context window); add a re-ranking pass over a larger candidate set; or
hierarchical retrieval — retrieve, summarize the retrieved set, then answer.
The retrieval seam is already isolated in one function, so this is a localized
change.

## 2 · The pgvector index is approximate and untuned for scale

**Now.** `ivfflat (embedding vector_cosine_ops) with (lists = 100)`
([database/schema.sql](../database/schema.sql)). Below a few thousand rows
Postgres just sequential-scans anyway, so the index barely matters — and with
23 rows it's doing nothing.

**At 10k → 1M sessions.** `ivfflat` is **approximate** — it can miss the true
nearest neighbour, and recall quality depends on the `lists`/`probes` tuning.
`lists = 100` is a rule-of-thumb for ~100k rows (≈ rows/1000); it's oversized
now and undersized past ~100k. ivfflat also needs an `ANALYZE` after data lands
to build good centroids, and rebuilding on heavy writes is a maintenance cost.

**Fix.** Tune `lists` to the row count and set `ivfflat.probes` to trade recall
for latency; or switch to an **HNSW** index (better recall, no ANALYZE step,
more memory and slower builds). Both are one-line index swaps — the query
(`match_sessions`) doesn't change.

## 3 · Queries are single-round-trip, but unpaginated

**Now.** `list_sessions` deliberately avoids the obvious N+1: instead of a
task-count query per session, it pulls every task in **one** `in_(session_id, ids)`
query and derives counts client-side — and it never selects the giant
`transcript` column for the list. `SESSION_LIST_LIMIT = 50` caps the payload.

**At 10k sessions.** The review list is hard-capped at 50 with **no pagination**
— older sessions simply aren't reachable from the list (recall/semantic search
still finds them, but you can't browse to them). And a single `in_(...)` over
thousands of ids would eventually be a large query.

**Fix.** Cursor pagination on `list_sessions` (order by timestamp, `lt(cursor)`),
which the timestamp index already supports; batch the task lookup per page.

## 4 · Embedding backfill is serial and unbatched

**Now.** [backend/embed_sessions.py](../backend/embed_sessions.py) embeds each
un-embedded session with one API call and one `UPDATE`, in a loop. New sessions
are embedded **synchronously** inside the summarize request (best-effort, so a
failure doesn't fail the summary).

**At 10k sessions.** Backfilling 10k rows is 10k sequential embedding calls —
slow, and it hits per-minute rate limits. Synchronous embedding also adds
latency and a failure surface to the summarize path.

**Fix.** Batch embeddings (`embed_content` takes multiple inputs per call);
move both backfill and per-session embedding to a **background job / queue** so
summarize returns immediately and embedding is eventually-consistent (recall
reaches un-embedded rows by recency until they're indexed — already the
designed fallback).

## 5 · No auth, RLS off — single-tenant by design

**Now.** There is no `user_id`, no authentication, and Supabase **RLS is
intentionally off** (enabling it without policies would deny every insert). The
hosted instance is public: anyone with the URL reads and writes all memory.
Fine for a demo with demo data — and flagged loudly in the README.

**At any real multi-user scale.** This is the **first** thing to fix, and it's
not additive — memory is currently global.

**Fix.** Add auth (Supabase Auth), a `user_id`/`org_id` column on `sessions`
and `tasks`, and RLS policies scoping every row to its owner. Recall, review,
and `match_sessions` all gain a `user_id` filter. Straightforward, but it
touches every query — which is exactly why it's deferred, not faked.

## 6 · Extraction & contradiction checks are bounded the same way

**Now.** Extraction is **one call per session** with a capped thinking budget
(`GEMINI_THINKING_BUDGET = 128`) — fast and cheap. Contradiction detection
compares a session against the `RECALL_SESSION_LIMIT` most recent prior
sessions.

**At scale.** A very long meeting can exceed the context window or extract worse
under the thinking cap (no chunking). Contradiction detection won't catch a
conflict with a meeting 500 sessions ago — it's windowed like recall. And the
`tasks` table has **no lifecycle**: every task ever captured stays "open"
forever, so "what's outstanding?" grows without bound.

**Fix.** Map-reduce extraction for long transcripts; use vector similarity
(not recency) to pick contradiction candidates; add a task status
(`open`/`done`/`dropped`) column and filter on it.

## 7 · Cost & caching

**Now.** Per session: one extraction call + one embedding. Per recall: one
embedding + one generation. At demo volume this fits the free tier (on
`gemini-3.5-flash-lite`); there is **no caching**, so re-summarizing or a
repeated identical recall re-calls the model.

**At scale.** Cost grows linearly with meetings and recall volume, and the free
tier is nowhere near enough. Repeated work is paid for twice.

**Fix.** Cache extraction by transcript hash and recall by (question, memory
version); add billing; the provider abstraction (`.env`-selected, prompts as
files) means moving to a cheaper/self-hosted model is a config change.

---

## The 30-second version (for when they ask)

> "It's a deliberate single-tenant prototype. The three things I'd fix first
> for production, in order: **auth + RLS** (memory is global today), **move
> embedding off the request path** into a batched background job, and **swap
> recall's fixed window for re-ranking over a larger candidate set** so it
> scales past the top-10. The vector index is approximate and untuned on
> purpose — it's a one-line HNSW swap when row counts justify it. Everything
> degrades gracefully in the meantime, which was the design goal: features ship
> gated and light up when the infrastructure is ready."
