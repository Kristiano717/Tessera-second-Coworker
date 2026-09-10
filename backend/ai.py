"""The LLM calls this prototype makes, per CLAUDE.md's AI Behavior Rules:

1. generate_summary() — one call after a session ends, returning
   {summary, memory, tasks, facts}.
2. answer_recall() — one call when the user asks about past meetings,
   answering strictly from retrieved session notes (plain text, no schema).
3. detect_contradictions() — an on-demand call (signed-off roadmap feature,
   not in the automatic loop) that flags where a session's decisions conflict
   with earlier ones. It never runs during a meeting and never fires as part
   of the post-session flow, so the "exactly one call after a meeting ends"
   rule is untouched — this only happens when the user explicitly asks.

Provider is picked by which key is set in backend/.env (GEMINI_API_KEY vs
OPENAI_API_KEY), per CLAUDE.md's rule to check the .env rather than assume.
Both branches share the same prompts (loaded from prompts/*.md), so
swapping providers is just an .env change.

NOTE ON MODEL CHOICE: CLAUDE.md names gemini-2.0-flash / gemini-2.5-flash
for the dev-time Gemini path. As of this build, both are retired for new
API keys (Google's API returns 404 pointing at a replacement). Verified
against the live API before picking: gemini-3.5-flash-lite is used — see the
GEMINI_MODEL note below for why flash-lite over plain flash (the free-tier
daily request cap). It was confirmed working with the current
{summary, memory, tasks, facts} schema. Flagging this here
since it's a deviation from the locked spec's exact model name, forced by
the models no longer existing rather than a discretionary swap.

The GPT-5 (OpenAI) branches below are implemented for when billing is set
up, but are UNVERIFIED — this environment has no OPENAI_API_KEY to test.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# gemini-3.5-flash-lite, not gemini-3.6-flash. The 3.6-flash free tier caps at
# 20 requests/day (GenerateRequestsPerDayPerProjectPerModel-FreeTier), which is
# far too tight for a demo that recalls a few times — one rehearsal exhausts it
# and the next call 429s on stage. The free daily limit is *per model*, and the
# flash-lite tier is much more generous; verified 3.5-flash-lite returns this
# exact {summary, memory, tasks, facts} schema in ~2s with correct
# categorisation. Pinned (not `-latest`) so the demo stays deterministic.
GEMINI_MODEL = "gemini-3.5-flash-lite"
OPENAI_MODEL = "gpt-5"

# Realtime speech-to-text, used for live transcription of both sides of a
# call. Separate from GEMINI_MODEL: it's a dedicated STT model that holds a
# bidirectional WebSocket rather than answering one-shot prompts, and it's
# free on the Gemini free tier. The browser connects to it directly, using
# a short-lived token minted by create_live_token() below.
GEMINI_LIVE_MODEL = "gemini-3.5-transcribe-live"

# Embeddings, for semantic recall (see database/schema.sql's pgvector setup).
# 768 dims: gemini-embedding-001 defaults to 3072 but takes an explicit
# output_dimensionality, and 768 is the sweet spot — small enough to index
# and store cheaply, large enough that retrieval quality holds at this scale.
# The number is fixed here AND in the `vector(768)` column; they must match.
# (text-embedding-004 is 404 for new keys, same as the retired flash models.)
GEMINI_EMBED_MODEL = "gemini-embedding-001"
OPENAI_EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 768

# Cap on the model's hidden reasoning, and the single biggest lever on how
# long a session takes to summarise.
#
# gemini-3.6-flash is a thinking model. Left unbounded it spent 584-1015
# thinking tokens to produce ~105 tokens of output — roughly 89% of the work
# invisible — which measured 15-38s per extraction. Capped at 128 the same
# call returned in 2s, and the output held up: correct speaker attribution,
# only the user's own commitment classified as a task, four well-formed facts.
#
# 128 is the floor worth using: thinking_budget=0 is rejected outright by
# this model (400 INVALID_ARGUMENT), so thinking can be bounded but not
# switched off. Raise it if extraction quality regresses on longer
# transcripts — 512 measured ~7s and is the next step up.
GEMINI_THINKING_BUDGET = 128

# The six fixed memory categories, per CLAUDE.md's differentiator. The order
# is the order they're shown in — actionable first (Action Item, Task), then
# the settled/known kinds. Kept here as the single source of truth for both
# the response schema's enum and the post-hoc normalisation below.
MEMORY_CATEGORIES = ["Action Item", "Task", "Decision", "Requirement", "Preference", "Fact"]
_TASK_CATEGORIES = {"Task", "Action Item"}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        # The structured heart of the extraction: typed memory objects, not
        # just flattened strings. tasks/facts below are views of this.
        "memory": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": MEMORY_CATEGORIES},
                    "text": {"type": "string"},
                },
                "required": ["category", "text"],
            },
        },
        "tasks": {"type": "array", "items": {"type": "string"}},
        "facts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "memory", "tasks", "facts"],
}


def _load_system_instruction(filename: str) -> str:
    text = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    marker = "## SYSTEM_INSTRUCTION"
    idx = text.index(marker)
    return text[idx + len(marker) :].strip()


EXTRACTION_INSTRUCTION = _load_system_instruction("extraction_prompt.md")
RECALL_INSTRUCTION = _load_system_instruction("recall_prompt.md")
CONTRADICTION_INSTRUCTION = _load_system_instruction("contradiction_prompt.md")

# One conflict between a current statement and a prior one. `prior_date` is
# optional so the model isn't forced to fabricate one when the input didn't
# carry it.
CONTRADICTION_SCHEMA = {
    "type": "object",
    "properties": {
        "contradictions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "current": {"type": "string"},
                    "prior": {"type": "string"},
                    "prior_date": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["current", "prior", "note"],
            },
        }
    },
    "required": ["contradictions"],
}


def _active_provider() -> str:
    """Returns 'gemini' or 'openai' based on .env. Raises if ambiguous."""
    has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))

    if has_gemini and has_openai:
        raise RuntimeError(
            "Both GEMINI_API_KEY and OPENAI_API_KEY are set in backend/.env — "
            "comment one out so the provider isn't ambiguous."
        )
    if has_gemini:
        return "gemini"
    if has_openai:
        return "openai"
    raise RuntimeError(
        "No AI provider configured. Set GEMINI_API_KEY or OPENAI_API_KEY in backend/.env."
    )


def _call_gemini(system_instruction: str, user_content: str, schema: dict | None) -> str:
    from google import genai as google_genai
    from google.genai import types

    client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        # Deterministic demo per CLAUDE.md's engineering principles — no
        # temperature > 0 without a specific reason.
        temperature=0,
        thinking_config=types.ThinkingConfig(thinking_budget=GEMINI_THINKING_BUDGET),
    )
    if schema is not None:
        config.response_mime_type = "application/json"
        config.response_schema = schema

    return client.models.generate_content(
        model=GEMINI_MODEL, contents=user_content, config=config
    ).text


def _call_openai(system_instruction: str, user_content: str, schema: dict | None) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    kwargs = {
        "model": OPENAI_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ],
    }
    if schema is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "structured_output", "schema": schema, "strict": True},
        }
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


# Transient failures worth one more try: the free tier's per-minute rate
# limit (429) and the provider being briefly overloaded or unavailable (500/
# 503). A demo firing a couple of calls in quick succession can trip the rate
# limit, and a bare error banner mid-demo is the worst possible moment for
# one. Deliberately narrow: a 400 (bad request / invalid schema) is a bug
# that retrying only hides, so those re-raise immediately.
_TRANSIENT_MARKERS = (
    "429", "resource_exhausted", "rate limit", "rate_limit",
    "500", "503", "unavailable", "overloaded", "internal error", "deadline",
)
_RETRY_BACKOFFS = (1.5, 4.0)  # seconds; two retries, longer the second time


def _is_transient(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)


def _call_llm(system_instruction: str, user_content: str, schema: dict | None = None) -> str:
    call = _call_gemini if _active_provider() == "gemini" else _call_openai
    # temperature is 0 on both calls, so a retry returns the same answer —
    # this only rescues a transient failure, it doesn't make the demo
    # nondeterministic (CLAUDE.md engineering principle #3).
    for backoff in (*_RETRY_BACKOFFS, None):
        try:
            return call(system_instruction, user_content, schema)
        except Exception as exc:
            if backoff is None or not _is_transient(exc):
                raise
            time.sleep(backoff)


def _normalize_memory(extracted: dict) -> None:
    """Cleans the `memory` array in place and guarantees the contract holds.

    The model is asked to keep `tasks`/`facts` as views of `memory`, but a
    prototype shouldn't trust that blindly on every call. This drops memory
    objects with an unknown category or empty text, and — the important part
    — backfills `memory` from `tasks`/`facts` if the model returned those but
    not the structured list, so an older-style response still yields typed
    objects (Task/Fact) rather than an empty categories view downstream.
    """
    valid = set(MEMORY_CATEGORIES)
    memory = []
    for obj in extracted.get("memory") or []:
        if not isinstance(obj, dict):
            continue
        category = (obj.get("category") or "").strip()
        text = (obj.get("text") or "").strip()
        if category in valid and text:
            memory.append({"category": category, "text": text})

    if not memory:
        # Fall back to the flat views: every task becomes a Task, every fact
        # a Fact. Coarser than the model's own categorisation, but never
        # empty when there was actually content.
        memory = [{"category": "Task", "text": t} for t in (extracted.get("tasks") or []) if t]
        memory += [{"category": "Fact", "text": f} for f in (extracted.get("facts") or []) if f]

    extracted["memory"] = memory


def generate_summary(transcript: str) -> dict:
    """One post-session call. Returns {summary, memory, tasks, facts} where
    `memory` is the typed [{category, text}] list and tasks/facts are its
    flattened views."""
    raw = _call_llm(EXTRACTION_INSTRUCTION, f"Transcript:\n{transcript}", EXTRACTION_SCHEMA)
    extracted = json.loads(raw)
    _normalize_memory(extracted)
    return extracted


def embed_text(text: str, *, is_query: bool) -> list[float]:
    """One embedding vector for semantic recall.

    `is_query` picks the task type: a stored session is a RETRIEVAL_DOCUMENT,
    the recall question a RETRIEVAL_QUERY. Asymmetric task types are how
    embedding models earn their retrieval quality — a question and the
    document that answers it don't look alike as plain text, and telling the
    model which side it's embedding lets it place them near each other anyway.

    Returns a list of EMBED_DIM floats. Retries on transient errors like the
    LLM calls do (embeddings have their own, separate quota).
    """
    text = (text or "").strip()
    if not text:
        return []
    provider = _active_provider()
    for backoff in (*_RETRY_BACKOFFS, None):
        try:
            if provider == "gemini":
                return _embed_gemini(text, is_query)
            return _embed_openai(text)
        except Exception as exc:
            if backoff is None or not _is_transient(exc):
                raise
            time.sleep(backoff)


def _embed_gemini(text: str, is_query: bool) -> list[float]:
    from google import genai as google_genai
    from google.genai import types

    client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    result = client.models.embed_content(
        model=GEMINI_EMBED_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBED_DIM,
            task_type="RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT",
        ),
    )
    return list(result.embeddings[0].values)


def _embed_openai(text: str) -> list[float]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    # text-embedding-3-* support a shorter dimensions param, so the vector
    # matches the column regardless of provider. OpenAI has no query/document
    # task-type split — the same call serves both.
    resp = client.embeddings.create(
        model=OPENAI_EMBED_MODEL, input=text, dimensions=EMBED_DIM
    )
    return list(resp.data[0].embedding)


def session_embedding_text(summary: str, facts: list[str]) -> str:
    """The text a session is embedded from: its summary plus its facts. Both
    matter for retrieval — the summary carries the gist, the facts carry the
    specific decisions a question might key on."""
    parts = [(summary or "").strip()]
    parts += [f for f in (facts or []) if f]
    return "\n".join(p for p in parts if p)


def format_session_context(sessions: list[dict]) -> str:
    """Renders retrieved session rows into the notes block the recall
    prompt expects. Oldest first, so 'yesterday' vs 'last week' ordering
    reads naturally to the model."""
    blocks = []
    for s in sessions:
        # timestamp is an ISO string from Supabase; date portion is enough
        # context for questions like "what did I decide yesterday?".
        date = (s.get("timestamp") or "")[:10]
        summary = (s.get("summary") or "").strip() or "(no summary generated for this session)"
        facts = s.get("facts") or []
        tasks = s.get("tasks") or []
        lines = [f"Meeting on {date}:", f"Summary: {summary}"]
        if facts:
            lines.append("Facts:")
            lines.extend(f"- {f}" for f in facts)
        # Open tasks are given as their own labelled block so "what's still
        # outstanding?" is answered from stored tasks, not reconstructed from
        # the summary prose.
        if tasks:
            lines.append("Open tasks:")
            lines.extend(f"- {t}" for t in tasks)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def answer_recall(question: str, sessions: list[dict]) -> str:
    """Answers a question using only the given past sessions. Returns
    plain text — no schema, since the answer is prose."""
    if not sessions:
        # Don't spend an LLM call to say "nothing stored" — and don't let
        # the model improvise an answer from an empty context either.
        return "I don't have any past sessions stored yet, so there's nothing to recall."

    # Today's date has to be stated explicitly: the model has no clock, so
    # without it a question like "what did I decide yesterday?" can't be
    # resolved against the dated notes and it hedges across every session.
    today = datetime.now(timezone.utc).date().isoformat()
    context = format_session_context(sessions)
    user_content = (
        f"Today's date is {today}.\n\n"
        f"Past session notes:\n\n{context}\n\n"
        f"Question: {question}"
    )
    return _call_llm(RECALL_INSTRUCTION, user_content, schema=None).strip()


def detect_contradictions(current_items: list[str], past_sessions: list[dict]) -> list[dict]:
    """Finds where a session's decisions/facts conflict with earlier ones.

    On-demand only — never part of the automatic post-session flow, so the
    "exactly one LLM call after a meeting ends" rule stays intact. Returns a
    list of {current, prior, prior_date, note}. Short-circuits without a call
    when there's nothing on either side to compare.
    """
    current_items = [c.strip() for c in current_items if c and c.strip()]
    if not current_items or not past_sessions:
        return []

    # Prior context: each earlier meeting's facts, dated, oldest first so the
    # model reads history forward. Only facts/decisions matter here — an open
    # task isn't something a later meeting contradicts.
    prior_blocks = []
    for s in past_sessions:
        facts = [f for f in (s.get("facts") or []) if f]
        if not facts:
            continue
        date = (s.get("timestamp") or "")[:10]
        prior_blocks.append(
            f"Meeting on {date}:\n" + "\n".join(f"- {f}" for f in facts)
        )
    if not prior_blocks:
        return []

    user_content = (
        "PRIOR MEMORY (earlier meetings):\n\n"
        + "\n\n".join(prior_blocks)
        + "\n\nCURRENT MEETING (the one being checked):\n"
        + "\n".join(f"- {c}" for c in current_items)
    )
    raw = _call_llm(CONTRADICTION_INSTRUCTION, user_content, CONTRADICTION_SCHEMA)
    result = json.loads(raw)
    # Keep only well-formed conflicts, so a stray shape can't reach the UI.
    out = []
    for c in result.get("contradictions") or []:
        if isinstance(c, dict) and (c.get("current") or "").strip() and (c.get("prior") or "").strip():
            out.append(
                {
                    "current": c["current"].strip(),
                    "prior": c["prior"].strip(),
                    "prior_date": (c.get("prior_date") or "").strip(),
                    "note": (c.get("note") or "").strip(),
                }
            )
    return out


# ---------------------------------------------------------------------------
# Realtime transcription tokens
# ---------------------------------------------------------------------------

# How long a minted token stays usable for sending audio. Live sessions cap
# at 10 minutes, so this gives comfortable headroom for one full session
# without leaving a long-lived credential lying around.
LIVE_TOKEN_TTL_MINUTES = 20

# How long the browser has to actually open the socket after asking for a
# token. Short on purpose: the frontend requests one immediately before
# connecting, so anything longer is just a wider window for a leaked token.
LIVE_TOKEN_START_WINDOW_MINUTES = 2


def create_live_token() -> dict:
    """Mints a short-lived token for one Gemini Live WebSocket connection.

    The browser connects to Gemini directly — audio never round-trips
    through this backend, which is what keeps latency at sub-second. That
    means the browser needs a credential, and it must not be
    GEMINI_API_KEY. Ephemeral tokens exist for exactly this: they're
    scoped to a single session and expire in minutes.

    Deliberately `uses=1`, one token per connection. A call has two audio
    sources (microphone and the other participant), and each Live session
    is capped at 10 minutes, so the frontend asks for a fresh token per
    socket rather than sharing one — a token that can open N sessions is a
    token worth stealing.
    """
    provider = _active_provider()
    if provider != "gemini":
        raise RuntimeError(
            f"Live transcription needs the Gemini provider, but {provider} is "
            "configured. Set GEMINI_API_KEY in backend/.env."
        )

    from google import genai as google_genai

    client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    now = datetime.now(timezone.utc)
    token = client.auth_tokens.create(
        config={
            "uses": 1,
            "expire_time": now + timedelta(minutes=LIVE_TOKEN_TTL_MINUTES),
            "new_session_expire_time": now
            + timedelta(minutes=LIVE_TOKEN_START_WINDOW_MINUTES),
        }
    )

    # The model name travels with the token so the browser never hardcodes
    # it — swapping STT models stays a backend-only change, matching how
    # GEMINI_MODEL works for the one-shot calls.
    return {"token": token.name, "model": GEMINI_LIVE_MODEL}
