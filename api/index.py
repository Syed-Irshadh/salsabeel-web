import sys
import os
from pathlib import Path

# Add project root directory to sys.path so 'app' modules can be imported seamlessly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import FastAPI application directly at top-level so Vercel's static analyzer detects it
from app.main import app

# Explicit top-level bindings for Vercel Serverless
handler = app
application = app
