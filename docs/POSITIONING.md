# Positioning — vs. general assistants (Siri AI, etc.)

The question every judge and interviewer asks: *"Why won't Apple/Google just
kill you?"* This is the honest answer, written to be spoken from. Pretending
the overlap away is the fastest way to lose the room — name it, then show where
you actually go deeper.

## What a general assistant now does (iPhone 18 Siri AI, Sept 2026)

Apple's "Siri AI" is a real leap, built on **personal context understanding**:
it surfaces details from your **messages, emails, photos, notes, and on-screen
content** to answer practical requests — retrieve a hotel confirmation, find a
restaurant a friend texted, turn a brainstorm into a Notes entry. Plus
on-screen/camera visual intelligence, a dedicated **Siri app** that keeps past
conversations (synced via iCloud), and an **on-device + Private Cloud Compute**
privacy architecture. (Reporting says Apple Intelligence is now partly
**Gemini-powered** — the same model family we use.)

On the surface that sounds like our pitch: "an assistant that remembers your
stuff and answers questions about it." That overlap is real. Here's the part
that isn't.

## The real differences

| | General assistant (Siri) | This project |
|---|---|---|
| **Memory source** | Reads what's *already written down* — emails, texts, notes | Creates memory from **live conversation that was never written down** — decisions spoken in a meeting that live in no email |
| **What it stores** | Retrieves / summarizes existing content on demand | Extracts **typed memory objects** (Decision, Requirement, …) and persists them |
| **Reasoning over memory** | Answers "what did the text say?" | Answers *and* **flags contradictions** across meetings ("this reverses March's decision") |
| **Meeting capture** | None — it isn't in your call | Captures the call (your side + the other participant) and structures it |
| **Scope** | Personal assistant, your device, your data | Work **meetings and decisions over time** — cross-person, team memory (roadmap) |
| **Reach** | Apple hardware only (iPhone 18, 12 GB RAM, rolling out) | Any browser, any device, installable PWA |

**The sharpest line:** *Siri remembers what you wrote. We remember what was
said and decided in a meeting* — the single biggest source of decisions that
never get captured anywhere. Siri can't tell you what a client agreed to on
Tuesday's call, because that conversation exists in no email or note for it to
read. That's our whole territory.

The one capability that's genuinely ours: **contradiction detection.** Retrieval
assistants surface what was said; none of them tell you that two meetings
*disagree*. That's reasoning over structured memory, not a search feature.

## The honest part (say this too — it builds credibility)

- **Siri wins on privacy** (on-device / Private Cloud Compute) and on being
  **free, built-in, and ubiquitous** for Apple users. We're cloud-based and a
  separate app. Don't claim otherwise.
- **"Won't they just add meeting capture?"** Maybe. But the moat isn't the
  capture — it's the **structured-decision memory + contradiction layer** on
  top, delivered as a **cross-person, cross-meeting, platform-neutral** tool,
  not locked to one person's phone. Apple's incentive is personal-device
  breadth; ours is meeting depth.
- Our edge is **depth in one vertical**, not breadth. That is the correct
  answer to "why won't a big assistant kill you": a general assistant will
  never go as deep into meetings and their decisions as a tool built only for
  that.

## One-liner for the pitch

> **"Siri remembers what you wrote down. We remember what your team decided —
> and warn you when a new decision contradicts an old one."**

---

_Sources (verified Sept 2026):_
[Apple — Siri AI](https://www.apple.com/newsroom/2026/06/apple-introduces-siri-ai-a-profoundly-more-capable-and-personal-assistant/),
[Apple — iPhone 18 Pro preview](https://www.apple.com/newsroom/2026/09/get-ready-to-experience-iphone-18-pro-the-new-apple-watch-lineup-and-airpods-5/),
[Business Standard — Gemini-powered Apple Intelligence](https://www.business-standard.com/amp/technology/tech-news/wwdc-2026-apple-unveils-siri-ai-gemini-powered-apple-intelligence-more-126060900042_1.html),
[Yahoo Tech — personal-context understanding](https://tech.yahoo.com/ai/apple-intelligence/articles/siri-ai-may-privacy-first-051500606.html),
[MacRumors — 12 GB RAM for Siri](https://www.macrumors.com/2026/06/16/iphone-18-to-pack-12gb-of-ram/).
