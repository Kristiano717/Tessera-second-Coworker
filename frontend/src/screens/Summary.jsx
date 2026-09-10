import { useEffect, useState } from 'react'
import { summarizeSession, sessionReportUrl } from '../api.js'
import Records from '../components/Records.jsx'
import Memory from '../components/Memory.jsx'
import Contradictions from '../components/Contradictions.jsx'
import DateCalendar from '../components/DateCalendar.jsx'

// Milestone 4 ("summary works"): calls the backend's single end-of-session
// LLM extraction once this screen mounts. Kept here rather than in
// LiveSession — that screen's job ends at persisting the raw session +
// wake-phrase tasks; turning that into an AI summary is this screen's job.
export default function Summary({ session, onRestart, onRecall }) {
  const { transcript, sessionId, tasks: liveTasks = [], saveError, taskSaveError } = session
  const [aiState, setAiState] = useState(sessionId ? 'loading' : 'skipped') // loading | done | error | skipped
  const [aiResult, setAiResult] = useState(null)
  const [aiError, setAiError] = useState(null)

  useEffect(() => {
    if (!sessionId) return // nothing to summarize if the session itself never saved
    let cancelled = false
    summarizeSession(sessionId)
      .then((result) => {
        if (cancelled) return
        setAiResult(result)
        setAiState('done')
      })
      .catch((err) => {
        if (cancelled) return
        setAiError(err.message)
        setAiState('error')
      })
    return () => {
      cancelled = true
    }
  }, [sessionId])

  return (
    <div className="screen">
      <h1>Summary</h1>

      {sessionId ? (
        <div className="saved-note">
          <span className="ok">saved</span>
          <code>{sessionId}</code>
          <span>{transcript.length} chars</span>
        </div>
      ) : (
        <div className="error-banner">
          Save failed{saveError ? `: ${saveError}` : ''}. The transcript is still shown below but
          wasn't stored, so it can't be summarized.
        </div>
      )}

      {taskSaveError && <div className="error-banner">Task save failed: {taskSaveError}</div>}

      {/* Extraction is a single call that can take the better part of a
          minute. Everything already known — the wake-phrase tasks and the
          transcript — is rendered immediately, in the position the final
          results will occupy, so the screen fills in rather than sitting
          empty. A bare spinner over a blank page reads as a hang. */}
      {aiState === 'loading' && (
        <>
          <div className="working">
            <span className="pulse" aria-hidden="true" />
            <span>
              Reading the transcript for decisions, tasks and facts. This runs once per
              session and can take up to a minute.
            </span>
          </div>
          {liveTasks.length > 0 && (
            <Records
              items={liveTasks}
              kind="live"
              label="Tasks captured live"
              empty="None yet."
            />
          )}
        </>
      )}
      {aiState === 'error' && <div className="error-banner">Summary generation failed: {aiError}</div>}

      {aiState === 'done' && (
        <>
          <p>{aiResult.summary}</p>

          {/* Reference is now: Summary is only ever shown for a session that
              just ended, and LiveSession's onEnd payload carries no
              timestamp. Renders nothing when no record names a real day. */}
          <DateCalendar
            records={[...aiResult.tasks, ...aiResult.facts]}
            sessionAt={Date.now()}
          />

          {/* The typed memory objects — the differentiator, shown in full
              rather than split into a tasks pile and a facts pile. Supersedes
              the two flat Records lists that used to sit here. */}
          <Memory items={aiResult.memory} label="Extracted memory" />

          {/* On-demand: does anything decided here reverse an earlier
              meeting? A separate LLM call, run only if the user asks. */}
          <Contradictions sessionId={sessionId} />
        </>
      )}

      {aiState === 'done' && liveTasks.length > 0 && (
        <details>
          <summary>Captured live by wake phrase ({liveTasks.length})</summary>
          <ul className="records is-live">
            {liveTasks.map((t, i) => (
              <li key={i}><span className="tag">task</span><span>{t}</span></li>
            ))}
          </ul>
        </details>
      )}

      <details>
        <summary>Raw transcript</summary>
        <div className="transcript-box">{transcript || '(empty — no speech captured)'}</div>
      </details>

      <div className="controls-row">
        <button className="secondary" onClick={onRestart}>Back to Home</button>
        <button className="secondary" onClick={onRecall}>Ask About Past Sessions</button>
        {/* Only once extraction has stored the summary and facts — before
            that the PDF would render a half-empty session. Opens in a new
            tab so a backend error can't navigate this screen away and lose
            the just-finished session (see the note in Review.jsx). */}
        {aiState === 'done' && (
          <a
            className="report-link report-link-btn"
            href={sessionReportUrl(sessionId)}
            target="_blank"
            rel="noopener"
          >
            Download PDF ↓
          </a>
        )}
      </div>
    </div>
  )
}
