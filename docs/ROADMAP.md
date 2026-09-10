# Second Coworker — Roadmap

The prototype's bet is **structured persistent memory**: a meeting doesn't
become a searchable transcript, it becomes typed memory objects (Task,
Decision, Preference, Requirement, Fact, Action Item) that can be recalled,
connected, and checked. Everything below compounds that one bet rather than
sprawling sideways — the pitch line is *competitors transcribe; we build a
memory that connects, contradicts, and warns.*

Items are ordered by how directly they deepen the moat, not by how flashy
they are. Each notes what it would cost and — where relevant — which locked
rule in [CLAUDE.md](../CLAUDE.md) it touches, so a future decision to build it
is made with eyes open.

---

## Shipped (beyond the core loop)

These started as roadmap items and were built with explicit sign-off. They
extend the memory without breaking the "nothing heavy runs live / one
automatic post-session call" rules — each runs after a meeting or read-only.

- **Six-category structured memory** — extraction returns typed
  `{category, text}` objects, surfaced in Summary, Review and the PDF, and
  persisted in a `memory` column. The differentiator, made literally true in
  storage.
- **Grounded recall with sources** — recall answers from stored facts *and*
  tasks, and shows the meetings it searched as clickable dated chips.
- **Contradiction detection** — on demand, flags where a session's decisions
  reverse an earlier meeting's ("launch moved February → March"). One LLM
  call, only when asked, so the automatic post-session flow stays single-call.
- **Pre-meeting briefing** — before a session, surfaces open commitments and
  established context from recent memory. Reads stored rows only, no AI call.
- **Per-session PDF export** — hand a meeting's memory to someone who won't
  open the app.

---

## Near-term — deepen the memory

- **Memory graph.** Link objects across meetings: this decision *supersedes*
  that one; this task *belongs to* the Acme project; this requirement was
  *satisfied* by that action item. Turns today's flat per-session lists into a
  connected structure you can traverse. *Cost:* a relations model + a graph
  view. *Currently out of scope in CLAUDE.md.*
- **Task lifecycle.** Tasks are captured but never closed — add done/blocked
  state so "what's still outstanding?" reflects reality instead of listing
  every task ever captured. *Cost:* a status column + UI; no AI.
- **Semantic recall.** Retrieval is recency-only today; embeddings would let
  recall find the *right* past meeting regardless of when it happened.
  *Breaks a locked rule:* CLAUDE.md's recall section says explicitly "no
  vector search, no embeddings," and "Vector database" is on the out-of-scope
  list — this needs a deliberate sign-off and adds an embedding pipeline.

## Mid-term — act on the memory

- **Proactive pre-meeting brief, sharpened.** The current briefing is
  rule-based; a synthesized, meeting-aware brief ("you're meeting Acme —
  here's the open thread and the last thing you promised them") would use one
  LLM call at session start.
- **Integrations (push).** Send captured tasks to Slack / Jira / a calendar;
  pull attendees from the calendar to scope recall. *Out of scope in
  CLAUDE.md*, and each is an OAuth + external-API surface — real work and a
  fragile dependency in a live demo.

## Long-term — broaden capture & platform

- **Live proactive alerts.** Mid-call, surface relevant history ("they asked
  about SSO last time"). *Breaks a locked rule:* CLAUDE.md forbids anything
  running continuously during a meeting beyond transcription + wake-phrase
  ("no per-sentence AI calls, no background extraction loop"). A real
  architectural change, not an increment.
- **Universal meeting capture + native audio.** A desktop app capturing
  system audio (WASAPI/CoreAudio) removes the tab-share dance and enables
  always-on/ambient capture. *Out of scope*; the current two-stream tab-share
  approach is the deliberate prototype-stage choice.
- **Auth & team memory.** Multi-user accounts and shared organizational
  memory — the path from a personal tool to "Memory OS." *Out of scope* for
  the unauthenticated prototype.

---

## Explicitly not planned

Kept here so they're not re-proposed: always-on listening as a default,
in-stream speaker diarization (telling apart voices *within one* microphone —
distinct from the two-stream `You`/`Them` tagging that already exists), and
continuous/real-time extraction every few seconds (extraction is once, after
the meeting).
