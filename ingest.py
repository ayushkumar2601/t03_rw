"""Root-level entrypoint for document ingestion.

Delegates directly to scripts.ingest.main so that both:
  - python ingest.py
  - python -m scripts.ingest
work seamlessly.
"""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from scripts.ingest import main  # noqa: E402

if __name__ == "__main__":
    main()
