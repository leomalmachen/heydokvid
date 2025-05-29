"""
Heydok Video - Simple FastAPI Application Entry Point
This file serves as a simple entry point that redirects to the main application
"""

from app.main import app

# Re-export the app for deployment
__all__ = ["app"] 