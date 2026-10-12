"""Root-level entrypoint for FastAPI application.

Exposes `app` from `app.main` so that both:
  - uvicorn main:app --reload
  - uvicorn app.main:app --reload
work seamlessly.
"""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import app  # noqa: E402

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
