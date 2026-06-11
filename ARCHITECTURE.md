# ARCHITECTURE GUIDE

## System Architecture

Wall-Trade-Backend follows a layered architecture pattern that ensures scalability, maintainability, and professional code organization.

### Architecture Layers

```
┌─────────────────────────────────────────────────┐
│   API Versioning Layer (/api/v1/, /api/v2/)    │ ← API Routes by Version
├─────────────────────────────────────────────────┤
│         Endpoints & Request Handlers            │ ← FastAPI Endpoints
├─────────────────────────────────────────────────┤
│        Dependency Injection Layer               │ ← FastAPI Dependencies
├─────────────────────────────────────────────────┤
│         Business Logic (Services)               │ ← Service Classes
├─────────────────────────────────────────────────┤
│      Data Access (Database Layer)               │ ← Supabase Client
├─────────────────────────────────────────────────┤
│    Cross-Cutting Concerns                       │ ← Logging, Exception Handling
└─────────────────────────────────────────────────┘
```

### Directory Structure Explained

```
app/
├── __init__.py                      # Package initialization
├── main.py                          # FastAPI app factory
├── auth.py                          # Authentication service
├── dependencies.py                  # Dependency injection
├── constants.py                     # Application constants
│
├── config/                          # Configuration management
│   ├── settings.py                  # Singleton settings class (MAIN CONFIG)
│   └── __init__.py
│
├── core/                            # Core functionality
│   ├── exceptions.py                # Custom exception hierarchy
│   ├── logging_config.py            # Centralized logging setup
│   └── __init__.py
│
├── database/                        # Database layer
│   ├── connection.py                # Database manager (singleton)
│   └── __init__.py
│
├── models/                          # Data models & schemas
│   ├── schemas.py                   # Base Pydantic schemas
│   └── __init__.py
│
├── api/                             # ⭐ API versioning root
│   ├── __init__.py
│   └── v1/                          # ⭐ API v1 (easily add v2, v3, etc)
│       ├── __init__.py
│       ├── router.py                # ⭐ V1 router aggregator
│       ├── schemas.py               # V1-specific schemas
│       └── endpoints/               # ⭐ V1 endpoints container
│           ├── __init__.py
│           ├── companies.py         # Company endpoints
│           ├── macro.py             # Macro/Market endpoints
│           ├── prices.py            # Stock prices endpoints
│           └── health.py            # Health check endpoint
│
├── services/                        # Business logic layer
│   ├── base_service.py              # Base service class
│   ├── psx_service.py               # PSX service
│   ├── capital_stake.py             # Capital stake service
│   └── __init__.py
│
└── utils/                           # Utilities
    ├── decorators.py                # Decorators (timing, retry)
    ├── responses.py                 # Response helpers
    ├── api.py                       # API utilities
    └── __init__.py
```

## Design Patterns Used

### 1. **Singleton Pattern** (Settings)
- **Location**: `app/config/settings.py`
- **Purpose**: Ensures only one instance of settings exists
- **Benefit**: Single source of truth for configuration
- **Usage**: `from app.config import get_settings; settings = get_settings()`

### 2. **Dependency Injection Pattern**
- **Location**: `app/dependencies.py`
- **Purpose**: Loose coupling between components
- **Benefit**: Easy testing and flexibility
- **Usage**: `@app.get("/") async def route(db=Depends(get_db_dependency))`

### 3. **Service Layer Pattern**
- **Location**: `app/services/`
- **Purpose**: Encapsulate business logic
- **Benefit**: Reusability and testability
- **Usage**: `service = PSXService(); data = service.get_market_data()`

### 4. **Factory Pattern**
- **Location**: `app/main.py`
- **Purpose**: Create FastAPI application instance
- **Benefit**: Flexible application configuration
- **Usage**: `app = create_app()`

### 5. **Exception Handler Pattern**
- **Location**: `app/core/exceptions.py`
- **Purpose**: Domain-specific exception handling
- **Benefit**: Clear error semantics and consistent responses
- **Usage**: `raise ResourceNotFoundError("User")`

## Data Flow

```
Request
   │
   ├──→ FastAPI Middleware (CORS, etc)
   │
   ├──→ Route Handler (@app.get("/path"))
   │      │
   │      ├──→ Dependency Injection (get_db, get_settings)
   │      │
   │      └──→ Service Layer (Business Logic)
   │             │
   │             ├──→ Database Layer (Supabase Client)
   │             │
   │             └──→ External APIs
   │
   ├──→ Response Formatting
   │
   └──→ Exception Handler (if error)
         │
         └──→ Error Response

```

## Configuration Management

### Settings Class Features

```python
from app.config import get_settings

settings = get_settings()

# Access settings
print(settings.SUPABASE_URL)
print(settings.is_production)

# Settings are automatically validated on load
# Invalid values raise errors
```

### Environment Variables

Settings are loaded from:
1. `.env` file (local development)
2. Environment variables (production/Docker)

Priority order: Environment variables > .env file > defaults

## Error Handling Strategy

```
AppException (Base)
├── ValidationError
├── DatabaseError
├── AuthenticationError
├── AuthorizationError
├── ResourceNotFoundError
├── ConflictError
└── ExternalServiceError
```

Each exception automatically:
- Sets appropriate HTTP status codes
- Includes error codes for client handling
- Logs to centralized logger
- Returns standardized error response

## Logging Strategy

```
Logger Configuration
├── Console Handler (development)
├── File Handler with Rotation (production)
└── JSON Formatting (structured logging)

Usage:
    logger = get_logger(__name__)
    logger.info("User logged in")
    logger.error("Database connection failed", exc_info=True)
```

## Security Considerations

1. **Settings Validation**: All settings validated on load
2. **Password Hashing**: bcrypt with passlib
3. **JWT Tokens**: Secure token creation and validation
4. **CORS**: Configurable CORS policies
5. **Dependency Injection**: Prevents unauthorized access
6. **Error Messages**: No sensitive info leaked in responses

## Testing Strategy

```
tests/
├── test_main.py          # Main app tests
├── test_auth.py          # Auth tests
├── test_config.py        # Config tests
└── test_services.py      # Service tests
```

Run tests:
```bash
pytest                    # Run all tests
pytest -v               # Verbose
pytest --cov           # With coverage
pytest -k test_name    # Specific test
```

## Performance Considerations

1. **Connection Pooling**: Database connections are managed
2. **Caching**: Settings are cached (LRU cache)
3. **Logging**: Non-blocking logging
4. **Async/Await**: Async operations throughout
5. **Decorators**: Timing and retry logic available

## Scalability Features

1. **Stateless Design**: Each request is independent
2. **Horizontal Scaling**: Can run multiple instances
3. **Load Balancing**: Works with load balancers
4. **Docker Support**: Containerized deployment
5. **Database Abstraction**: Easy to swap Supabase for other DBs

## Development Workflow

### Local Development
```bash
# Setup
make install
cp .env.example .env
# Edit .env with your values

# Run
python run.py
# Or
make dev

# Test
make test

# Format
make format

# Lint
make lint
```

### Production Deployment
```bash
# Docker
make docker-build
make docker-run

# Or with docker-compose
docker-compose up -d
```

## Best Practices Summary

✅ **Configuration**: Centralized settings with validation
✅ **Dependency Injection**: Loose coupling throughout
✅ **Error Handling**: Semantic exceptions with proper codes
✅ **Logging**: Structured logging for debugging
✅ **Type Hints**: Full type annotation for IDE support
✅ **Documentation**: Comprehensive docstrings
✅ **Testing**: Test suite with fixtures
✅ **Security**: Password hashing and JWT tokens
✅ **Structure**: Clear separation of concerns
✅ **Scalability**: Async/await and stateless design

## Next Steps

1. Implement routes with actual business logic
2. Add service methods for data operations
3. Create database models/tables
4. Write comprehensive tests
5. Deploy to production with Docker
