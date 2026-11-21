from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from .config import FRONTEND_FILE
from .db import Base, engine
from .routes import auth, data, lost

Base.metadata.create_all(engine)    # creates the tables on first start (no migrations yet)

app = FastAPI(title="LOST API", description="Backend for the LOST student app")


@app.middleware("http")
async def security_guard(request: Request, call_next):
    # Block cross-site writes: browsers always send Origin on cross-site POST/PUT/DELETE.
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and urlparse(origin).netloc != request.headers.get("host", ""):
            return JSONResponse({"detail": "Cross-origin request blocked"}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


app.include_router(auth.router)
app.include_router(data.router)
app.include_router(lost.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"ok": True}


@app.get("/", include_in_schema=False)
def index():
    if not FRONTEND_FILE.exists():
        raise HTTPException(404, f"Front not found. Expected it at {FRONTEND_FILE}")
    return FileResponse(FRONTEND_FILE, headers={"Cache-Control": "no-store"})
