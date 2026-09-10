import { useState } from 'react'
import { checkContradictions } from '../api.js'

// On-demand conflict check for one session: does anything decided here
// contradict an earlier meeting? This is the thing a transcription tool
// can't do — not "what was said" but "heads up, this reverses what you
// decided on the 3rd".
//
// A button, not automatic: it spends an LLM call, so it runs only when the
// user asks. That also keeps the post-session flow at exactly one automatic
// call (the summary), per CLAUDE.md.

function fmtDate(d) {
  if (!d) return null
  const parsed = new Date(d)
  if (Number.isNaN(parsed.getTime())) return d
  return parsed.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function Contradictions({ sessionId }) {
  const [state, setState] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const run = async () => {
    setState('loading')
    setError(null)
    try {
      setResult(await checkContradictions(sessionId))
      setState('done')
    } catch (err) {
      setError(err.message)
      setState('error')
    }
  }

  const conflicts = result?.contradictions || []

  return (
    <div className="contradictions">
      {state !== 'done' && (
        <button type="button" className="secondary" onClick={run} disabled={state === 'loading'}>
          {state === 'loading' ? 'Checking past decisions…' : 'Check against past decisions'}
        </button>
      )}

      {state === 'error' && <div className="error-banner">{error}</div>}

      {state === 'done' && conflicts.length === 0 && (
        <p className="hint conflict-clear">
          No conflicts — nothing here reverses an earlier decision
          {result.compared_against > 0
            ? ` across ${result.compared_against} past session${result.compared_against === 1 ? '' : 's'}.`
            : '. No earlier sessions to compare against yet.'}
        </p>
      )}

      {state === 'done' && conflicts.length > 0 && (
        <div className="conflict-list">
          <h2>
            Conflicts with earlier decisions <span className="count">{conflicts.length}</span>
          </h2>
          {conflicts.map((c, i) => (
            <div key={i} className="conflict">
              <p className="conflict-now">
                <span className="conflict-tag">now</span>
                {c.current}
              </p>
              <p className="conflict-then">
                <span className="conflict-tag then">was</span>
                {c.prior}
                {fmtDate(c.prior_date) && <em> · {fmtDate(c.prior_date)}</em>}
              </p>
              {c.note && <p className="conflict-note">{c.note}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
