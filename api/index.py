import sys
import os
from pathlib import Path

# Add project root directory to sys.path so 'app' modules can be imported seamlessly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import FastAPI application with resilient exception boundary
try:
    from app.main import app
except Exception as e:
    import traceback
    err_trace = traceback.format_exc()
    print("CRITICAL STARTUP ERROR IN APP.MAIN:", err_trace)
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    app = FastAPI(title="Salsabeel Academy Recovery")
    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def fallback_handler(full_path: str):
        return HTMLResponse(
            f"<html><body style='font-family:monospace;padding:24px;background:#111;color:#f88;'>"
            f"<h2>Serverless Function Initialization Error</h2>"
            f"<pre style='background:#222;color:#eee;padding:16px;border-radius:8px;overflow-x:auto;'>{err_trace}</pre>"
            f"</body></html>",
            status_code=500
        )
