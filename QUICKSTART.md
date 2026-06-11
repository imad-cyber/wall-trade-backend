# Quick Start Guide

## 5-Minute Setup

### 1. Clone/Navigate to Project
```bash
cd Wall-Trade-Backend
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env - add your Supabase credentials and SECRET_KEY
```

### 5. Run Application
```bash
python run.py
```

Visit: http://localhost:8000/docs (Swagger UI)

---

## Project Overview

### Key Features
- ✅ FastAPI web framework
- ✅ Singleton settings management
- ✅ JWT authentication
- ✅ Supabase integration
- ✅ Structured logging
- ✅ Custom exception handling
- ✅ Dependency injection
- ✅ Docker support

### File Organization
- **config/**: Settings and configuration
- **core/**: Exceptions and logging
- **database/**: Database connection management
- **models/**: Pydantic schemas
- **api/v1/**: ⭐ API v1 endpoints and versioned routes
- **services/**: Business logic
- **utils/**: Helper functions

---

## Common Commands

```bash
# Development
python run.py
make dev

# Testing
pytest
pytest -v --cov

# Code Quality
make format
make lint

# Docker
make docker-build
make docker-run

# CLI Utilities
python cli.py init-project
python cli.py health-check
```

---

## API Structure

### Standard Response Format
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response Format
```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "details": {...}
}
```

### Available Endpoints (v1)
```
GET  /api/v1/health                    # Health check
GET  /api/v1/companies                 # List companies
GET  /api/v1/companies/{id}            # Get company
GET  /api/v1/macro/indicators          # Get macro indicators
GET  /api/v1/prices?symbol=ABC         # Get prices
```

---

## Adding New Endpoints

### Step 1: Create Endpoint File
Create a file in `app/api/v1/endpoints/`:

```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, status
from app.dependencies import get_db_dependency
from app.models.schemas import ResponseSchema

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
async def list_users(db=Depends(get_db_dependency)):
    return ResponseSchema(success=True, message="Users retrieved", data=[])
```

### Step 2: Register in Router
Update `app/api/v1/router.py`:

```python
from app.api.v1.endpoints import users

api_router.include_router(users.router)
```

### Step 3: Use It!
Endpoint is now available at: `GET /api/v1/users`

Check Swagger: http://localhost:8000/docs

---

## Using the Settings

```python
from app.config import get_settings

settings = get_settings()

# Access settings
print(settings.SUPABASE_URL)
print(settings.is_production)
print(settings.ALGORITHM)

# Settings are validated automatically
```

---

## Authentication

### Create Token
```python
from app.auth import AuthService

auth_service = AuthService()
token = auth_service.create_access_token(
    data={"sub": "user123"}
)
```

### Use Token in Route
```python
from fastapi import Depends
from app.auth import get_current_user

@app.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    return {"user_id": current_user["user_id"]}
```

---

## Exception Handling

### Raise Exceptions
```python
from app.core import (
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
)

# Validation error
raise ValidationError("Invalid email format")

# Not found
raise ResourceNotFoundError("User")

# Auth error
raise AuthenticationError("Invalid credentials")
```

### Exceptions Auto-Handled
All exceptions are automatically caught and return proper HTTP responses with error codes.

---

## Database Usage

```python
from app.database import get_db_client

# In a route/service
db = get_db_client()

# Use Supabase client
response = db.table("users").select("*").execute()
```

---

## Dependency Injection

```python
from fastapi import Depends
from app.dependencies import (
    get_db_dependency,
    get_settings_dependency,
)

@app.get("/example")
async def example_route(
    db = Depends(get_db_dependency),
    settings = Depends(get_settings_dependency),
):
    # db and settings are automatically injected
    return {"status": "ok"}
```

---

## Logging

```python
from app.core import get_logger

logger = get_logger(__name__)

logger.info("User action")
logger.warning("Unusual activity")
logger.error("An error occurred", exc_info=True)
```

Logs are written to:
- Console (development)
- `logs/app.log` (file with rotation)

---

## Testing

### Run Tests
```bash
pytest
pytest -v              # Verbose
pytest --cov          # With coverage
pytest tests/test_auth.py  # Specific file
```

### Write Test
```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client():
    return TestClient(create_app())

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
```

---

## Docker Deployment

### Build
```bash
docker build -t wall-trade-backend:latest .
```

### Run
```bash
docker-compose up -d
```

### Logs
```bash
docker-compose logs -f app
```

---

## Troubleshooting

### Import Errors
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

### Settings Not Loading
- Check `.env` file exists
- Verify required variables are set
- Run: `python cli.py health-check`

### Database Connection Failed
- Verify `SUPABASE_URL` and `SUPABASE_KEY`
- Check internet connection
- Check Supabase project status

### Port Already in Use
- Change PORT in `.env`
- Or: `python run.py --port 8001`

---

## Resources

- 📚 [FastAPI Docs](https://fastapi.tiangolo.com/)
- 📚 [Pydantic Docs](https://docs.pydantic.dev/)
- 📚 [Supabase Docs](https://supabase.com/docs)
- 📄 [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture guide
- 📄 [README.md](README.md) - Full documentation

---

## Support

For issues, check:
1. `.env` configuration
2. Virtual environment is activated
3. Dependencies installed: `pip install -r requirements.txt`
4. Check logs: `tail -f logs/app.log`

---

**Happy coding! 🚀**
