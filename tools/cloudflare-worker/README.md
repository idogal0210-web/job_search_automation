# Job liveness checker (Cloudflare Worker)

Enables the live "check all jobs" button in the dashboard's closed-jobs dialog.
Browsers cannot read job pages from other sites (CORS), so this worker fetches the page
and returns a verdict.

## One-time deploy (about 5 minutes)

1. Create a free account at https://dash.cloudflare.com and open Workers & Pages.
2. Create a Worker, choose "Edit code", paste the content of `job-check.js`, and deploy.
3. Copy the worker URL (for example `https://job-check.<name>.workers.dev`).
4. In the dashboard open the closed-jobs dialog, paste the URL in the setup field and save.
   The URL is stored only in this browser (`localStorage`).

If you serve the dashboard from a different origin, add it in the worker settings as the
variable `ALLOWED_ORIGINS` (comma separated).

## API

`GET /?u=<encoded job url>` returns `{ "state": "inactive" | "active" | "unknown", "reason": "...", "status": 200 }`.

`unknown` is returned when the site blocks the request, rate limits it, fails or times out.
Unknown jobs are never counted as active.
