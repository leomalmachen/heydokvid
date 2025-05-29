import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "backend" / "backend"
sys.path.insert(0, str(backend_path))

try:
    # Import the FastAPI app
    from main import app
    
    # For Vercel, we need to export the app directly
    # Vercel will handle the ASGI interface
    def handler(request):
        return app(request.scope, request.receive, request.send)
    
    # Also export app directly for compatibility
    app = app
    
except ImportError as e:
    # Fallback if import fails
    from fastapi import FastAPI
    
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"error": f"Import failed: {str(e)}", "path": str(backend_path)}
    
    def handler(request):
        return app(request.scope, request.receive, request.send) 