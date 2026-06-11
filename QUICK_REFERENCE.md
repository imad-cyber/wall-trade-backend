# Quick Reference Card

## Essential Commands

### Running the App
```bash
# Start development server
python run.py

# Or using make
make dev

# Or direct uvicorn
uvicorn app:app --reload
```

### Verification
```bash
# Verify configuration
python verify_app.py
```

### Testing
```bash
# Run all tests
pytest

# Verbose mode
pytest -v

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_main.py
```

### Code Quality
```bash
# Format code
make format
# Or: black app && isort app

# Lint code
make lint
# Or: flake8 app && mypy app

# Clean cache
make clean
```

### Docker
```bash
# Build image
docker build -t wall-trade-backend:latest .

# Run container
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop container
docker-compose down
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "application": "Wall-Trade-Backend",
  "version": "1.0.0",
  "environment": "development"
}
```

### Get All Companies
```bash
curl http://localhost:8000/api/v1/companies
```

### Get Company by ID
```bash
curl http://localhost:8000/api/v1/companies/123
```

### Get Macro Indicators
```bash
curl http://localhost:8000/api/v1/macro/indicators
```

### Get Prices
```bash
curl http://localhost:8000/api/v1/prices?symbol=ABC
```

## Settings

### Available Settings (from `.env`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| APP_NAME | string | Wall-Trade-Backend | Application name |
| ENVIRONMENT | string | development | Environment (development/staging/production) |
| DEBUG | bool | True | Debug mode |
| PORT | int | 8000 | Server port |
| SUPABASE_URL | string | - | Supabase project URL |
| SUPABASE_KEY | string | - | Supabase API key |
| SECRET_KEY | string | - | JWT secret key |
| LOG_LEVEL | string | INFO | Logging level |

### Access Settings in Code
```python
from app.config import get_settings

settings = get_settings()
print(settings.SUPABASE_URL)
print(settings.is_production)
```

## Common Tasks

### Add New Endpoint
1. Create file: `app/api/v1/endpoints/feature.py`
2. Define router with endpoints
3. Register in: `app/api/v1/router.py`

Example:
```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, status
from app.models.schemas import ResponseSchema

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
async def list_users(db=Depends(get_db_dependency)):
    return ResponseSchema(success=True, data=[])
```

Then in `app/api/v1/router.py`:
```python
from app.api.v1.endpoints import users
api_router.include_router(users.router)
```

### Raise Exception
```python
from app.core import (
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
)

raise ValidationError("Invalid email")
raise ResourceNotFoundError("User")
raise AuthenticationError("Invalid token")
```

### Use Logger
```python
from app.core import get_logger

logger = get_logger(__name__)
logger.info("User logged in")
logger.warning("Rate limit approaching")
logger.error("Database error", exc_info=True)
```

### Get Database Client
```python
from app.database import get_db_client

db = get_db_client()
response = db.table("users").select("*").execute()
```

### Dependency Injection
```python
from fastapi import Depends
from app.dependencies import (
    get_db_dependency,
    get_settings_dependency,
)

@app.get("/example")
async def my_route(
    db=Depends(get_db_dependency),
    settings=Depends(get_settings_dependency),
):
    return {"status": "ok"}
```

## File Structure

```
app/
├── config/           # Settings (singleton)
├── core/            # Exceptions & logging
├── database/        # DB connection
├── models/          # Schemas
├── api/v1/endpoints/ # Endpoints
│   ├── companies.py
│   ├── macro.py
│   ├── prices.py
│   └── health.py
├── services/        # Business logic
├── utils/           # Helpers
├── auth.py          # Auth service
├── dependencies.py  # DI
└── main.py          # App factory
```

## Documentation

- [README.md](README.md) - Full docs
- [QUICKSTART.md](QUICKSTART.md) - 5-min setup
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [API_STRUCTURE.md](API_STRUCTURE.md) - API versioning
- [CONTRIBUTING.md](CONTRIBUTING.md) - Dev guidelines
- [GETTING_STARTED.md](GETTING_STARTED.md) - Getting started

## Useful Links

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/api/v1/health

## Shortcuts

```bash
# Save these as aliases
alias wall-dev="cd ~/projects/Wall-Trade-Backend && make dev"
alias wall-test="cd ~/projects/Wall-Trade-Backend && make test"
alias wall-lint="cd ~/projects/Wall-Trade-Backend && make lint"
```

## Troubleshooting

### Port 8000 in use?
Change in `.env`: `PORT=8001`

### Import errors?
Reinstall: `pip install -r requirements.txt`

### Settings not loading?
Check `.env` exists and is readable

### Can't connect to Supabase?
Verify URL and key in `.env`
