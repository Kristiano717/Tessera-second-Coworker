import { useEffect, useState } from 'react'
import { fetchSessions } from '../api.js'

// Pre-meeting briefing: what you'd want in your head walking into the next
// call — the commitments you're already on the hook for, and the context the
// other side has established — pulled from stored memory.
//
// Deliberately runs NO AI call. It reads existing sessions the same way the
// Agenda does and aggregates them client-side, so it costs nothing and can't
// flake on a rate limit right before a meeting. That also keeps it clear of
// CLAUDE.md's "nothing heavy runs live" rule: this is a read of memory
// already stored, not a new model call.
//
// Renders null when there's no history yet, so a first session isn't fronted
// by an empty panel.

// How far back to look. A briefing is about what's still live in your head,
// not the whole archive — the last handful of meetings is the relevant window.
const LOOKBACK_SESSIONS = 6
const MAX_ITEMS = 5

function dedupe(strings) {
  const seen = new Set()
  const out = []
  for (const s of strings) {
    const key = (s || '').trim().toLowerCase()
    if (!key || seen.has(key)) continue
    seen.add(key)
    out.push(s.trim())
  }
  return out
}

function shortDate(ts) {
  return new Date(ts).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

/** Aggregate recent sessions into { commitments, context } for the briefing. */
export function briefingFrom(sessions) {
  const recent = sessions
    .filter((s) => (s.tasks?.length || 0) + (s.facts?.length || 0) > 0)
    .slice(0, LOOKBACK_SESSIONS)

  // Tasks are commitments you owe; facts are the standing context (decisions,
  // preferences, requirements) the meetings established. Each item keeps the
  // date of the meeting it came from, so the briefing is traceable.
  const commitments = []
  const context = []
  for (const s of recent) {
    for (const t of s.tasks || []) commitments.push({ text: t, at: s.timestamp })
    for (const f of s.facts || []) context.push({ text: f, at: s.timestamp })
  }

  // Dedupe on text (a commitment restated across meetings shouldn't list
  // twice), keeping the most recent occurrence since sessions are newest-first.
  const pick = (items) => {
    const seen = new Set()
    const out = []
    for (const it of items) {
      const key = it.text.trim().toLowerCase()
      if (!key || seen.has(key)) continue
      seen.add(key)
      out.push(it)
      if (out.length >= MAX_ITEMS) break
    }
    return out
  }

  return { commitments: pick(commitments), context: pick(context) }
}

export default function Briefing() {
  const [brief, setBrief] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetchSessions()
      .then((sessions) => {
        if (!cancelled) setBrief(briefingFrom(sessions))
      })
      // Silent: a briefing is a bonus. A failure here must not put an error
      // in front of someone who just wants to start recording.
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  if (!brief || (brief.commitments.length === 0 && brief.context.length === 0)) return null

  return (
    <section className="briefing">
      <span className="briefing-label">Before you start</span>
      <div className="briefing-cols">
        {brief.commitments.length > 0 && (
          <div className="briefing-col">
            <h3>You're on the hook for</h3>
            <ul>
              {brief.commitments.map((it, i) => (
                <li key={i}>
                  <span>{it.text}</span>
                  <em>{shortDate(it.at)}</em>
                </li>
              ))}
            </ul>
          </div>
        )}
        {brief.context.length > 0 && (
          <div className="briefing-col">
            <h3>What's been established</h3>
            <ul>
              {brief.context.map((it, i) => (
                <li key={i}>
                  <span>{it.text}</span>
                  <em>{shortDate(it.at)}</em>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  )
}
