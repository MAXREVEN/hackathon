"""Start the LOST server from the repo root:  python run.py"""
import sys
from pathlib import Path

import uvicorn

BACKEND = Path(__file__).resolve().parent / "backend"

if __name__ == "__main__":      # this guard is required on Windows when reload is on
    sys.path.insert(0, str(BACKEND))
    uvicorn.run("app.main:app", app_dir=str(BACKEND), reload=True, reload_dirs=[str(BACKEND)])
