# Second Coworker — Pitch

## The one line

**Meetings produce decisions; almost none survive. Transcription tools give you
a filing cabinet. We give you a memory that connects, contradicts, and warns.**

## The problem

Every meeting creates decisions, commitments, and constraints — and they
evaporate. The current answer is transcription (Fireflies, Granola, Fathom,
Otter): record the room, hand back a wall of text with a summary on top. That's
a better filing cabinet, not a better memory. To find what you forgot, you have
to already know which meeting to open.

The question that actually matters is never *"what was said?"* It's **"what did
we decide, and why?"** — asked weeks later, by someone who doesn't remember
which meeting to look in.

## The bet

**Store structured memory, not transcripts.** When a meeting ends, one model
call extracts it into six fixed categories — Task, Decision, Preference,
Requirement, Fact, Action Item — and *those typed objects* are what persist.
Every later feature reads the structure, never the raw text.

|  | Transcription tools | Second Coworker |
|---|---|---|
| Stores | Raw text + a summary | Typed memory objects |
| Retrieval | Search the meeting you already remembered | Ask a question across all meetings, by meaning |
| "Why did we drop X?" | A timestamp to go read | The decision, and the meeting it came from |
| Over time | The archive grows | The memory grows |

## Why it's defensible

Three things a transcript search structurally cannot do:

1. **Semantic recall** — vector search over stored memory finds the *relevant*
   meetings, not the recent ones. Ask "what does the client want?" and it weaves
   three meetings, cited.
2. **Contradiction detection** — it notices when a new decision *reverses* an
   old one ("launch moved February → March") and tells you which changed, when.
3. **Trustworthy by construction** — recall answers only from retrieved memory
   and says "I don't have that" rather than inventing. Every answer links to its
   sources.

For the "why won't Apple/Google just kill you?" question — how this differs from
a general assistant like iPhone 18's Siri AI — see [POSITIONING.md](POSITIONING.md).

## What's built (not slideware)

The full loop runs end to end, live: capture (both sides, speaker-labelled) →
wake-phrase tasks → one-call extraction into six categories → semantic
cross-session recall with citations → contradiction detection → pre-meeting
briefing → PDF export. React + FastAPI + Supabase/pgvector + Gemini. See the
status table in [../README.md](../README.md).

## The demo (90 seconds of it)

Record a meeting → task drops in on "Hey Coworker…" → end it → **six typed
categories** appear → ask a question and get an answer **woven across meetings,
by meaning, with sources** → hit "check for conflicts" and watch it **catch a
reversed decision**. Full script: [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

## Ask / roadmap

This is a working prototype of the core loop plus the memory layer that proves
the bet. Next: a memory *graph* (decisions linked to the requirements and people
they touch), task lifecycle, and proactive pre-meeting briefs. Full plan in
[ROADMAP.md](ROADMAP.md).
