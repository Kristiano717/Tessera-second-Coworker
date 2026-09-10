# Deploy — Second Coworker

Goal: a live, installable URL you can put a QR code to on a slide. ~20 minutes.

The architecture that makes this painless: **the frontend always calls
`/api/...` same-origin.** In dev, Vite proxies that to `localhost:8000`; in
prod, Vercel rewrites it to the Render backend. So there's no CORS to configure
and no backend URL baked into the frontend build.

```
GitHub repo ──┬─► Render   (FastAPI backend)      ← secrets live here
              └─► Vercel   (static React build)   ← rewrites /api → Render
                              │
                              ▼
                         Supabase (Postgres + pgvector)
```

## 0 · Prerequisites

- The repo is on GitHub (it is: `Kristiano717/iqoo`).
- Supabase project exists and the migrations are run — base tables plus, if you
  want the full feature set, the `memory` column and the pgvector block from
  [../database/schema.sql](../database/schema.sql). (Already done for the current
  project.)
- Your `GEMINI_API_KEY`. Note the hosted instance is **public and
  unauthenticated** — demo data only.

## 1 · Backend → Render

1. In Render, **New → Blueprint**, point it at the repo. It reads
   [../render.yaml](../render.yaml) and picks up the build/start commands and
   `rootDir: backend`.
2. Set the env vars in the dashboard (they're `sync: false`, never in the repo):
   `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`.
3. Deploy. When it's live, copy the service URL, e.g.
   `https://second-coworker-api.onrender.com`.
4. Sanity check: open `<that URL>/health` → `{"status":"ok"}`, and `<that
   URL>/docs` for the live API explorer.

> The free plan **sleeps after ~15 min idle** and takes ~50s to wake. Hit the
> URL once right before any demo so the first real request isn't the cold start.

## 2 · Frontend → Vercel

1. In Vercel, **Add New → Project**, import the repo.
2. Set **Root Directory** to `frontend`. Vercel auto-detects Vite (build
   `npm run build`, output `dist`).
3. **Point the rewrite at your backend:** edit
   [../frontend/vercel.json](../frontend/vercel.json) and replace
   `REPLACE-ME.onrender.com` with the Render host from step 1 (host only, no
   `https://`, no trailing slash). Commit and push — Vercel redeploys.

   ```json
   { "rewrites": [ { "source": "/api/:path*",
     "destination": "https://second-coworker-api.onrender.com/:path*" } ] }
   ```

4. Open the Vercel URL. Recall and Review should work immediately (they only
   read). To test capture you'll grant the mic prompt.

## 3 · Make it installable (PWA)

Open the Vercel URL in Chrome → **⋮ → Install / Add to Home Screen**. It should
say **Install**, not "Add shortcut" — a shortcut means the manifest wasn't
accepted (you'd get a browser tab, not an app). Then generate a QR code to the
Vercel URL for your slide.

## 4 · Smoke test the deployed build

- `…/api/health` via the Vercel URL (proves the rewrite reaches Render).
- Recall a seeded question → an answer with source chips.
- Open a session in Review → memory/tasks render.
- Record a short session → Summary shows the six categories.

## Gotchas

- **`REPLACE-ME` left in** → every `/api` call 404s from Vercel. This is the #1
  deploy mistake; check it first if the deployed app can't reach the backend.
- **Cold Render start** → first request after idle takes ~50s and can look like
  a hang. Warm it before demoing.
- **Secrets** are only ever in the Render/Vercel dashboards and `backend/.env`
  (git-ignored) — never commit them. The repo being public makes this
  non-negotiable.
- **Migrations are per-project** — a fresh Supabase needs schema.sql (and the
  optional blocks) run before categories/semantic recall work; the app falls
  back cleanly until then.
