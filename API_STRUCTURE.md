# Updated Project Structure with Proper API Versioning

```
Wall-Trade-Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory
│   ├── auth.py                    # Authentication service
│   ├── dependencies.py            # Dependency injection
│   ├── constants.py               # Application constants
│   │
│   ├── config/                    # Configuration
│   │   ├── __init__.py
│   │   └── settings.py            # ⭐ Singleton settings class
│   │
│   ├── core/                      # Core functionality
│   │   ├── __init__.py
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── logging_config.py      # Logging configuration
│   │
│   ├── database/                  # Database layer
│   │   ├── __init__.py
│   │   └── connection.py          # Database manager (singleton)
│   │
│   ├── models/                    # Data models & schemas
│   │   ├── __init__.py
│   │   └── schemas.py             # Base Pydantic schemas
│   │
│   ├── api/                       # ⭐ API versioning root
│   │   ├── __init__.py
│   │   └── v1/                    # ⭐ API v1 (versioned)
│   │       ├── __init__.py
│   │       ├── router.py          # ⭐ V1 router aggregator
│   │       ├── schemas.py         # V1-specific schemas
│   │       └── endpoints/         # ⭐ V1 endpoints
│   │           ├── __init__.py
│   │           ├── companies.py   # Company endpoints
│   │           ├── macro.py       # Macro endpoints
│   │           ├── prices.py      # Prices endpoints
│   │           └── health.py      # Health check endpoint
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── base_service.py        # Base service class
│   │   ├── psx_service.py         # PSX service
│   │   └── capital_stake.py       # Capital stake service
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── decorators.py          # Decorators
│       ├── responses.py           # Response helpers
│       ├── api.py                 # API utilities
│       └── __init__.py
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_main.py
│   ├── test_auth.py
│   └── test_config.py
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD
│
├── .vscode/
│   ├── settings.json
│   └── extensions.json
│
├── run.py                         # Entry point
├── cli.py                         # CLI utilities
├── conftest.py                    # Pytest configuration
├── pyproject.toml                 # Project metadata
├── Dockerfile                     # Container configuration
├── docker-compose.yml             # Docker compose
├── Makefile                       # Common commands
├── .gitignore                     # Git exclusions
├── .env.example                   # Environment template
├── requirements.txt               # Dependencies
├── README.md                      # Full documentation
├── QUICKSTART.md                  # Quick setup guide
├── ARCHITECTURE.md                # Architecture details
├── CONTRIBUTING.md                # Development guidelines
└── API_STRUCTURE.md              # API versioning guide (this file)
```

## Why This Structure?

### ✅ API Versioning Benefits

1. **Future-Proof**: Easily add `/api/v2/`, `/api/v3/` without affecting v1
2. **Backward Compatibility**: Keep v1 stable while introducing breaking changes in v2
3. **Parallel Versions**: Support multiple API versions simultaneously
4. **Professional**: Industry standard used by Google, Microsoft, AWS, etc.

### ✅ Better Organization

- **Endpoints**: Each route file is focused and easy to maintain
- **Schemas**: API-specific schemas can be organized by version
- **Router**: Centralized router makes it easy to see all v1 routes
- **Scalability**: Grows naturally as API expands

## API Routes

### Health Check
```
GET /api/v1/health
```

### Companies
```
GET    /api/v1/companies              # List companies
GET    /api/v1/companies/{id}         # Get specific company
POST   /api/v1/companies              # Create company (add when ready)
PUT    /api/v1/companies/{id}         # Update company (add when ready)
DELETE /api/v1/companies/{id}         # Delete company (add when ready)
```

### Macro Data
```
GET /api/v1/macro/indicators          # Get macro indicators
```

### Prices
```
GET /api/v1/prices?symbol=ABC         # Get prices
```

## Adding New Endpoints

### Step 1: Create Endpoint File
```python
# app/api/v1/endpoints/new_feature.py
from fastapi import APIRouter, Depends, status
from app.dependencies import get_db_dependency
from app.models.schemas import ResponseSchema

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.get("")
async def get_data(db=Depends(get_db_dependency)):
    return ResponseSchema(success=True, message="Success", data=[])
```

### Step 2: Update Router
```python
# app/api/v1/router.py
from app.api.v1.endpoints import new_feature

api_router.include_router(new_feature.router)
```

Done! The new endpoints are automatically available at `/api/v1/new-feature/`

## Adding a New API Version

When you need to introduce breaking changes:

### Step 1: Create v2 Directory
```bash
mkdir -p app/api/v2/endpoints
```

### Step 2: Create v2 Router
```python
# app/api/v2/router.py
from fastapi import APIRouter
from app.api.v2.endpoints import companies, macro, prices

api_router = APIRouter(prefix="/api/v2")
api_router.include_router(companies.router)
# ... etc
```

### Step 3: Include in Main App
```python
# app/main.py
from app.api.v1 import api_router as v1_router
from app.api.v2 import api_router as v2_router

app.include_router(v1_router)
app.include_router(v2_router)
```

Now both `/api/v1/` and `/api/v2/` are available!

## Directory Navigation

- **Add endpoint**: `app/api/v1/endpoints/`
- **Versioned schemas**: `app/api/v1/schemas.py`
- **Setup routes**: `app/api/v1/router.py`
- **Root API config**: `app/api/__init__.py`

## Swagger Documentation

When you visit http://localhost:8000/docs:
- All v1 endpoints appear with `/api/v1` prefix
- Grouped by tags (companies, macro, prices, health)
- Full request/response documentation
- Try-it-out functionality

## Best Practices

✅ Each endpoint file handles one logical feature
✅ Router combines all endpoints into versioned API
✅ Use tags for logical grouping in Swagger
✅ Keep schemas organized by version
✅ Support multiple API versions simultaneously
✅ Clear prefix structure: `/api/v{N}/resource/`
