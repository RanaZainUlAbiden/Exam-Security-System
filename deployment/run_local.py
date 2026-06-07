"""Run the production WSGI dispatcher locally for integration testing."""

import os
import sys
from pathlib import Path

from werkzeug.serving import run_simple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deployment.app import application


if __name__ == "__main__":
    run_simple(
        os.getenv("HOST", "127.0.0.1"),
        int(os.getenv("PORT", "10000")),
        application,
        threaded=True,
    )
