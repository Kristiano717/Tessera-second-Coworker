// Turns a raw backend/LLM error into something a person (or a judge watching a
// demo) should see. The provider's rate-limit error is a wall of JSON with
// quota metric names and a docs link — accurate, and exactly the wrong thing
// to surface on screen. Everything else passes through unchanged, since the
// real message is usually the useful one.

/** A friendly, one-line version of an error message. */
export function friendlyError(message) {
  const raw = String(message || '')
  // Gemini/OpenAI rate limits: 429 + RESOURCE_EXHAUSTED / "quota" / "rate limit".
  if (/\b429\b|resource_exhausted|quota|rate limit/i.test(raw)) {
    return 'The AI provider is rate-limited right now. Give it a moment and try again.'
  }
  return raw
}
