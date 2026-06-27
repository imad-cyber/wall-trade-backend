"""Cross-cutting middleware registration helpers."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing import TimingMiddleware


def register_middleware(app: FastAPI, settings: Settings) -> None:
    """Register all application middleware in correct order."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIDMiddleware)
