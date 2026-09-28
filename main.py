from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

app = FastAPI()


class AuditRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/audit")
def audit(request: AuditRequest):
    return {"url": str(request.url), "status": "received"}