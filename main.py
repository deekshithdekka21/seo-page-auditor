import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI()


class AuditRequest(BaseModel):
    url: HttpUrl


def fetch_page(url):
    """Visit the page and return the response. Raises httpx errors on failure."""
    return httpx.get(str(url), timeout=10, follow_redirects=True)


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

    return {
        "url": str(request.url),
        "final_url": str(response.url),
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type"),
        "title": title,
        "meta_description": meta_description,
        "h1": h1,
    }