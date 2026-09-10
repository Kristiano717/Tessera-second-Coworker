import { useState } from 'react'
import { askRecall } from '../api.js'
import { friendlyError } from '../lib/errors.js'
import Markdown from '../components/Markdown.jsx'

// Milestone 5 ("recall works"): the last piece of the loop. User asks a
// question; the backend retrieves the relevant past sessions — by semantic
// similarity when pgvector is set up, otherwise by recency — and the LLM
// answers from that context alone, saying it doesn't know rather than
// guessing. `result.retrieval` says which path answered.
function sourceLabel(ts) {
  const date = new Date(ts)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  if (date.toDateString() === today.toDateString()) return 'Today'
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday'
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

/** One source per calendar day. Sources arrive newest-first, so the first
 *  seen for a day is its most recent session — the one a chip opens. */
function dedupeByDay(sources) {
  const seen = new Set()
  const out = []
  for (const s of sources) {
    const day = new Date(s.timestamp).toDateString()
    if (seen.has(day)) continue
    seen.add(day)
    out.push(s)
  }
  return out
}

export default function Recall({ onBack, onOpenSession }) {
  const [question, setQuestion] = useState('')
  const [state, setState] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Suggestion chips: a judge or first-time user has no idea what this
  // can answer. These three are chosen to land the differentiator against
  // the seeded story (see backend/seed_demo.py) — the first is CLAUDE.md's
  // demo-script question, the other two only have good answers if memory is
  // stitched across several meetings, which a transcript search can't do.
  const SUGGESTIONS = [
    "What did I decide in yesterday's meeting?",
    'What does the client want?',
    "What's still outstanding?",
  ]

  const ask = async (q) => {
    if (!q) return
    setQuestion(q)
    setState('loading')
    setError(null)
    try {
      const res = await askRecall(q)
      setResult(res)
      setState('done')
    } catch (err) {
      setError(err.message)
      setState('error')
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    ask(question.trim())
  }

  return (
    <div className="screen">
      <h1>Recall</h1>
      <p className="subtitle">
        Answered from stored memory objects — never by re-reading a transcript.
      </p>

      <form onSubmit={handleSubmit} className="recall-form">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What did I decide in yesterday's meeting?"
          aria-label="Recall question"
        />
        <button type="submit" disabled={state === 'loading' || !question.trim()}>
          {state === 'loading' ? 'Searching…' : 'Ask'}
        </button>
      </form>

      {state === 'idle' && (
        <div className="suggestions">
          {SUGGESTIONS.map((q) => (
            <button type="button" key={q} onClick={() => ask(q)}>{q}</button>
          ))}
        </div>
      )}

      {state === 'error' && <div className="error-banner">{friendlyError(error)}</div>}

      {state === 'done' && result && (
        <div className="recall-answer">
          <Markdown text={result.answer} />

          {/* The meetings recall looked in, made openable — a claim in the
              answer is one click from the stored memory behind it, so the
              trust the product rests on is checkable rather than asserted.
              Labelled "searched", not "drawn from": the model isn't asked
              which notes it used, and overclaiming the sources would
              undercut the very trustworthiness this is meant to show. One
              chip per day (several short sessions can share a date), newest
              first, opening that day's most recent session. */}
          {result.sources?.length > 0 && (
            <div className="recall-sources">
              <span className="recall-sources-label">
                Searched {result.sessions_searched} session{result.sessions_searched === 1 ? '' : 's'}
                {/* Which retrieval answered: similarity search (pgvector) or
                    the recency fallback when it isn't set up. */}
                {result.retrieval === 'semantic' && <em className="retrieval-tag"> · by meaning</em>}
              </span>
              {dedupeByDay(result.sources).map((s) => (
                <button
                  type="button"
                  key={s.id}
                  className="source-chip"
                  onClick={() => onOpenSession?.(s.id)}
                >
                  {sourceLabel(s.timestamp)}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="controls-row">
        <button className="secondary" onClick={onBack}>Back to Home</button>
      </div>
    </div>
  )
}
