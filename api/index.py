"""Vercel ASGI entry point for FastAPI application."""
from app.main import create_app

app = create_app()
