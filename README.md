# SEO Page Auditor

Paste a URL and get an SEO check of its title, meta description and H1 headings, plus AI-suggested improvements from Google Gemini. Every audit is saved to Postgres and shown in a "recent audits" list.

## How it works

```
Next.js frontend (localhost:3000)
      │  POST /audit {"url": ...}
      ▼
FastAPI backend (Docker, port 8000)
      ├─► checks the address is public (SSRF protection)
      ├─► fetches the page with httpx, parses it with BeautifulSoup
      ├─► rule-based checks (missing/too-long title and meta, H1 count)
      ├─► if issues found: Gemini suggests a better title, meta description and H1
      │     (structured JSON output, validated with Pydantic, then re-checked by the same rules)
      └─► saves the result to Postgres (JSONB)
```

- **Rules first, AI second:** plain Python rules find the problems, and the AI is only asked to fix them. Its suggestions are then run through the same rules to catch over-long output.
- **Graceful degradation:** if Gemini is rate-limited or returns invalid JSON, the audit still returns the rule-based results with a `suggestion_error` message instead of failing.
- **Optional database:** if `DATABASE_URL` isn't set, audits still work and just aren't saved.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router), React, TypeScript |
| Backend | Python 3.12, FastAPI, Pydantic |
| Fetching / parsing | httpx, BeautifulSoup |
| AI | Google Gemini API (`google-genai`), structured JSON output |
| Database | PostgreSQL 17, psycopg 3 |
| Containers | Docker, Docker Compose |
| Tests | pytest |

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/audit` | Body `{"url": "https://..."}`. Returns the audit result |
| GET | `/audits?limit=20` | Most recent saved audits |

Error responses: `400` address not allowed, `422` invalid URL, `502` site unreachable or too many redirects, `504` site timed out, `503` no database configured (for `/audits`).

Interactive docs: http://localhost:8000/docs

## Run locally

1. Get a free Gemini API key from Google AI Studio.
2. Copy `.env.example` to `.env` and add your key (`.env` is git-ignored).
3. Start the API and database:
```bash
   docker compose up --build
```
4. In another terminal, start the frontend:
```bash
   cd frontend
   npm install
   npm run dev
```
5. Open http://localhost:3000

## Tests and evaluation

```bash
python -m pytest        # unit tests for the SEO rules and address checks
python evaluate.py      # runs the Gemini prompt against 6 invented test pages and scores the output
```
`evaluate.py` makes real API calls (6 requests), so it counts against the Gemini free-tier daily limit.

## Security: SSRF protection

Because the server fetches any URL a user gives it, it could be tricked into requesting internal addresses such as `localhost`, the Docker database (`db:5432`), private networks, or cloud metadata (`169.254.169.254`). To prevent this:

- Before each request, the hostname is resolved with DNS, and the request is refused with `400` unless **every** resulting IP is a public internet address (`ipaddress.is_global`).
- Automatic redirects are turned off. Redirects are followed manually (maximum 5), and **each hop** is checked the same way, so a public site can't redirect the server to an internal address.

**Known limitation:** DNS rebinding. The check and the actual request do separate DNS lookups, so a malicious DNS server could answer differently each time. Fully closing this would mean connecting to the exact IP that was checked.

## Other limitations

- Gemini's free tier allows a limited number of requests per day. When the limit is reached, audits return without AI suggestions.
- CORS currently allows only `http://localhost:3000`. This needs updating for a deployed frontend.
- Only the title, meta description and H1s are checked.

![Tests](https://github.com/deekshithdekka21/seo-page-auditor/actions/workflows/tests.yml/badge.svg)