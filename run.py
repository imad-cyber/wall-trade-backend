"""
Run script for local development.
This script sets up and runs the FastAPI application.
"""
import os
import socket
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"

# If launched with system Python, re-run inside the project virtualenv.
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON:
    raise SystemExit(
        subprocess.call([str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])
    )

# Add project root to Python path
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import create_app
from app.core.config import get_settings
import uvicorn


def _can_bind(host: str, port: int) -> bool:
    """Return True when host:port can be bound by this process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _find_available_port(host: str, preferred_port: int) -> int:
    """Find an available local port, starting at the configured port."""
    for port in range(preferred_port, preferred_port + 100):
        if _can_bind(host, port):
            return port
    raise RuntimeError(
        f"No available port found from {preferred_port} to {preferred_port + 99}"
    )


def main():
    """Main entry point for the application."""
    settings = get_settings()

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Use a loopback host for local development to avoid Windows socket ACL issues.
    host = os.getenv("LOCAL_HOST") or (
        "127.0.0.1"
        if settings.is_development and settings.HOST in {"0.0.0.0", "::"}
        else settings.HOST
    )
    port = _find_available_port(host, settings.PORT)

    if port != settings.PORT:
        print(
            f"Port {settings.PORT} is unavailable on {host}; "
            f"starting {settings.APP_NAME} on port {port} instead."
        )

    print(f"Starting {settings.APP_NAME} at http://{host}:{port}")
    print(f"Swagger docs: http://{host}:{port}/docs")

    # Run the application
    uvicorn.run(
        "app.main:create_app",
        host=host,
        port=port,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        factory=True,
    )


if __name__ == "__main__":
    main()
