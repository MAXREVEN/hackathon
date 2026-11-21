"""Settings. Values come from environment variables or backend/.env."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent      # .../backend
ROOT_DIR = BASE_DIR.parent                              # repo root
FRONTEND_FILE = ROOT_DIR / "frontend" / "app.html"


def _load_dotenv() -> None:
    """Tiny .env reader (so beginners need no extra package)."""
    path = BASE_DIR / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

ENV = os.getenv("LOST_ENV", "development")
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{(BASE_DIR / 'lost.db').as_posix()}"

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if ENV == "production":
        raise RuntimeError("SECRET_KEY must be set when LOST_ENV=production")
    SECRET_KEY = "dev-only-secret-change-me-dev-only-secret"
    print("WARNING: using the insecure development SECRET_KEY. Set SECRET_KEY in backend/.env")

COOKIE_NAME = "lost_session"
COOKIE_SECURE = ENV == "production"      # cookie only over https in production
SESSION_DAYS = 14

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
MAX_AUDIO_BYTES = 15 * 1024 * 1024
MAX_ITEMS = 2000                          # max rows per collection per user
