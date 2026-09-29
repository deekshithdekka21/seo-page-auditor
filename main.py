import logging
import os

import httpx
import psycopg
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field, HttpUrl, ValidationError

logger = logging.getLogger(__name__)

load_dotenv()
client = genai.Client()   # created once, reused for every request

# Optional: when DATABASE_URL isn't set, audits simply aren't saved
DATABASE_URL = os.environ.get("DATABASE_URL")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # the front end's origin
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditRequest(BaseModel):
    url: HttpUrl


class SEOSuggestion(BaseModel):
    suggested_title: str = Field(description="An improved page title, 60 characters or fewer.")
    suggested_meta_description: str = Field(
        description="An improved meta description, 160 characters or fewer."
    )
    suggested_h1: str = Field(description="One main H1 heading that states the page's topic.")
    reasoning: str = Field(description="One or two sentences explaining the changes.")


def fetch_page(url):
    """Visit the page and return the response. Raises httpx errors on failure."""
    return httpx.get(str(url), timeout=10, follow_redirects=True)


def find_issues(title, meta_description, h1):
    """Check extracted SEO data against simple rules. Returns a list of issue messages."""
    issues = []

    if not title:
        issues.append("Title is missing.")
    elif len(title) > 60:
        issues.append(f"Title is too long ({len(title)} characters). Aim for 60 or fewer.")

    if not meta_description:
        issues.append("Meta description is missing.")
    elif len(meta_description) > 160:
        issues.append(
            f"Meta description is too long ({len(meta_description)} characters). Aim for 160 or fewer."
        )

    if len(h1) == 0:
        issues.append("No H1 heading found.")
    elif len(h1) > 1:
        issues.append(f"Multiple H1 headings found ({len(h1)}). Use one main H1.")

    return issues


def suggest_improvements(title, meta_description, h1, issues):
    """Ask Gemini for a better title, meta description and H1. Returns a validated SEOSuggestion."""
    prompt = f"""You are an SEO assistant. Improve this page's title, meta description, and main H1 heading.

Current title: {title}
Current meta description: {meta_description}
H1 headings: {h1}
Issues found: {issues}

Keep the title to 60 characters or fewer and the meta description to 160 or fewer.
Suggest exactly one main H1 that describes what the page is about.
Base your suggestions only on the information given."""

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": SEOSuggestion.model_json_schema(),
        },
    )
    return SEOSuggestion.model_validate_json(interaction.output_text)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audits (
    id         SERIAL PRIMARY KEY,
    url        TEXT NOT NULL,
    result     JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def save_audit(result):
    """Store one audit result in Postgres. Does nothing if no database is configured."""
    if not DATABASE_URL:
        return
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.execute(
            "INSERT INTO audits (url, result) VALUES (%s, %s)",
            (result["url"], Jsonb(result)),
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/audit",
    responses={
        502: {"description": "Could not reach the website"},
        504: {"description": "The website took too long to respond"},
    },
)
def audit(request: AuditRequest):
    try:
        response = fetch_page(request.url)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="The website took too long to respond")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach the website")

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.string if soup.title else None

    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_tag.get("content") if meta_tag else None

    h1 = [tag.get_text(strip=True) for tag in soup.find_all("h1")]

    issues = find_issues(title, meta_description, h1)

    suggestion = None
    suggestion_issues = None
    suggestion_error = None

    if issues:   # only ask the AI when there's something to fix
        try:
            result = suggest_improvements(title, meta_description, h1, issues)
            suggestion = result.model_dump()
            # Check the AI's suggestions against our own rules
            suggestion_issues = find_issues(
                result.suggested_title,
                result.suggested_meta_description,
                [result.suggested_h1],
            )
        except ValidationError:
            suggestion_error = "The AI returned an invalid response."
        except Exception as error:
            logger.warning("AI suggestion failed: %s", error)
            suggestion_error = "AI suggestions are unavailable right now."

    audit_result = {
        "url": str(request.url),
        "final_url": str(response.url),
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type"),
        "title": title,
        "meta_description": meta_description,
        "h1": h1,
        "issues": issues,
        "suggestion": suggestion,
        "suggestion_issues": suggestion_issues,
        "suggestion_error": suggestion_error,
    }

    try:
        save_audit(audit_result)
    except psycopg.Error as error:
        logger.warning("Could not save audit: %s", error)

    return audit_result


@app.get("/audits")
@app.get("/audits")
def list_audits(limit: int = 20):
    """Return the most recent audits, newest first."""
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="No database is configured.")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        conn.execute(CREATE_TABLE_SQL)
        rows = conn.execute(
            "SELECT id, created_at, result FROM audits ORDER BY created_at DESC LIMIT %s",
            (limit,),
        ).fetchall()
    return rows