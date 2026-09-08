import sys
import os
from pathlib import Path

# Add project root directory to sys.path so 'app' modules can be imported seamlessly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import FastAPI application
from app.main import app
