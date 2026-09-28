from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import httpx

app = FastAPI()


class AuditRequest(BaseModel):
    url: HttpUrl


def get_response(req):
    res = httpx.get(str(req.url), timeout=10, follow_redirects=True)
    return res


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/audit")
def audit(request: AuditRequest):
    try:
        response = get_response(request)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="the other site took too long")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="I tried to reach the other site, and it failed")


    return {"url": str(request.url), "final_url": str(response.url), "status_code": response.status_code,
            "content_type": response.headers.get("content-type")}
