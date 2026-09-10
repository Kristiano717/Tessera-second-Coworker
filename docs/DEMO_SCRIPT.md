# Demo Script — Second Coworker

A rehearsed 3-minute run that shows the *differentiator*, not just the app.
The order matters: each beat sets up the next, and the last one is the beat
judges remember. Practise it end to end at least twice before presenting.

**Before you walk on:**

- Backend + frontend running (or the deployed URL open). Hit the backend once
  first if it's on Render's free tier — it sleeps and takes ~50s to wake.
- Seed the story so recall has something to weave: `cd backend && python
  seed_demo.py --reset`.
- Chrome (not Firefox/Safari — tab-audio capture is Chrome/Edge only).
- One rehearsal earlier in the day is fine now — `gemini-3.5-flash-lite` has a
  generous daily limit, so you won't 429 mid-demo.

---

## The 4 beats

### 1 · Capture — "it listens to both sides" (~40s)

> "Every meeting produces decisions. Almost none survive. Watch what we keep."

- **Start a session.** Speak a couple of lines of a fake meeting — a decision
  and a preference. The transcript renders live, speaker-labelled `You` / `Them`.
- Say the wake phrase: **"Hey Coworker, remind me to send the deck."** The task
  drops into the tray *instantly*.

> "That's a regex on the transcript — no second model running in the
> background. The heavy thinking happens once, after the meeting."

### 2 · Structure — "we store memory, not a transcript" (~30s)

- **End the session.** The Summary appears with the **six typed categories** —
  Decision, Requirement, Preference, Task, Action Item, Fact — not a wall of prose.

> "This is the whole bet. Competitors store the transcript and a summary. We
> throw the prose away and keep the *structure* — typed memory objects. That's
> what makes the next part possible."

### 3 · Recall — "ask across every meeting" (~50s)

- Go to **Recall**. Ask **"What does the client want?"**
- The answer weaves several meetings, **grouped by date**, and shows the
  meetings it searched as **clickable source chips** with "**· by meaning**".

> "It didn't search one meeting I remembered — it searched all of them by
> *meaning*, using vector similarity, and answered only from what's stored. If
> it isn't in the memory, it says so instead of making it up. Every claim is
> one click from the meeting it came from."

- Click a source chip → it opens that meeting. "Checkable, not taken on faith."

### 4 · The kill shot — "it catches contradictions" (~40s)

- Open the **design-review** session in Review (or the one you just recorded if
  it reverses something). Press **"Check against past decisions."**
- It flags: **now** "launch pushed to March" · **was** "launch target February"
  (Sep 3).

> "This is the thing no transcription tool can do. It didn't just remember the
> two meetings — it noticed they *disagree*, and told me which decision changed
> and when. That's a memory that connects, contradicts, and warns."

**Close:**

> "Meetings give you decisions. We're the layer that makes sure they survive —
> and tells you when they change."

---

## If something goes wrong

- **A call 429s** → the friendly banner says "rate-limited, try again". Say "the
  free tier's catching its breath" and re-ask; it's deterministic, same answer.
- **Live transcript won't start** → it falls back to microphone-only Web Speech
  automatically; carry on, the rest of the demo is unaffected.
- **Recall says it doesn't know** → that's a feature, not a bug. "It refuses to
  guess — that's the point of a memory you can trust." Then ask a question the
  seeded story covers ("what did we decide about the launch?").

## One-line answers to the questions judges ask

- *"How is this different from Otter/Fireflies?"* — They give you a searchable
  transcript. We give you structured memory you can query, and that flags its
  own contradictions.
- *"Does it run AI during the call?"* — No. Only transcription + a wake-phrase
  regex. Extraction is one call, after the meeting. Cost scales with meetings,
  not minutes.
- *"How does it know which meeting to look in?"* — It doesn't need to. Semantic
  search finds the relevant meetings; you just ask the question.
- *"What's stopping hallucination?"* — Recall answers only from retrieved stored
  memory and is told to say "I don't have that" rather than infer.
