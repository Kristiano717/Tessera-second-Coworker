// The typed memory objects — the product's actual differentiator, shown as
// what it is: not one "tasks" pile and one "facts" pile, but every extracted
// item carrying its category across the six fixed kinds. Each row wears its
// category tag, so a glance says "this meeting became structured memory",
// which "just summarize the transcript" can't claim.
//
// Two colour families rather than six, on purpose: actionable kinds (Action
// Item, Task) take the task colour, the settled/known kinds (Decision,
// Requirement, Preference, Fact) take the fact colour. The specific category
// is carried by the tag *label*; a six-colour rainbow would read as noise and
// break the app's near-monochrome restraint.

// Canonical display order: what you must do first, then what was settled,
// then what's simply known. Also the order used to sort a mixed list so the
// same categories cluster.
const CATEGORY_ORDER = ['Action Item', 'Task', 'Decision', 'Requirement', 'Preference', 'Fact']
const ACTIONABLE = new Set(['Action Item', 'Task'])

function rank(category) {
  const i = CATEGORY_ORDER.indexOf(category)
  return i === -1 ? CATEGORY_ORDER.length : i
}

export default function Memory({ items, label = 'Memory', empty = 'None extracted.' }) {
  // Keep only well-formed objects, then order by category so the list reads
  // as grouped structure rather than the order the model happened to emit.
  const clean = (items || []).filter((m) => m && m.category && m.text)
  const ordered = [...clean].sort((a, b) => rank(a.category) - rank(b.category))

  return (
    <div className="tray">
      <h2>
        {label} {ordered.length > 0 && <span className="count">{ordered.length}</span>}
      </h2>
      {ordered.length === 0 ? (
        <p className="hint">{empty}</p>
      ) : (
        <ul className="records is-memory">
          {ordered.map((m, i) => (
            <li
              key={i}
              style={{ animationDelay: `${Math.min(i, 6) * 45}ms` }}
              data-family={ACTIONABLE.has(m.category) ? 'action' : 'knowledge'}
            >
              <span className="tag">{m.category}</span>
              <span>{m.text}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
