# Development Guidelines

## Code Style

### Python Style Guide (PEP 8)
- Line length: 100 characters
- Use 4 spaces for indentation
- Use type hints for all functions

### Formatting Tools
- **Black**: Code formatter (automatic on save)
- **isort**: Import organizer
- **flake8**: Linter
- **mypy**: Type checker

```bash
# Format all code
make format

# Check code quality
make lint
```

### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Private classes**: `_PrivateClass`

### Type Hints
```python
# ✅ Good
def process_data(data: dict, count: int) -> bool:
    """Process data and return status."""
    pass

# ❌ Bad
def process_data(data, count):
    pass
```

### Docstrings
Use Google-style docstrings:

```python
def calculate_total(items: list[float], tax_rate: float = 0.1) -> float:
    """
    Calculate total with tax.
    
    Args:
        items: List of item prices
        tax_rate: Tax rate (default 0.1)
        
    Returns:
        float: Total price with tax
        
    Raises:
        ValueError: If tax_rate is negative
    """
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    return sum(items) * (1 + tax_rate)
```

## Code Organization

### Imports Order
```python
# 1. Standard library
import os
import sys
from datetime import datetime

# 2. Third-party libraries
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# 3. Local imports
from app.config import get_settings
from app.core import get_logger
```

### File Structure
```python
"""
Module docstring explaining purpose.
"""
# Imports
from typing import Optional
from fastapi import APIRouter

# Constants
DEFAULT_TIMEOUT = 30

# Classes
class MyClass:
    pass

# Functions
def my_function():
    pass

# Main execution
if __name__ == "__main__":
    pass
```

## Error Handling

### Do's
- ✅ Use specific exception classes
- ✅ Log errors with context
- ✅ Return meaningful error messages
- ✅ Document expected exceptions

```python
# ✅ Good
async def get_user(user_id: str):
    """
    Get user by ID.
    
    Raises:
        ResourceNotFoundError: If user not found
    """
    user = await db.users.get(user_id)
    if not user:
        raise ResourceNotFoundError("User")
    return user
```

### Don'ts
- ❌ Catch all exceptions
- ❌ Silently ignore errors
- ❌ Return error info in success responses
- ❌ Include stack traces in API responses

```python
# ❌ Bad
try:
    result = risky_operation()
except:  # Too broad
    pass

# ❌ Bad  
try:
    result = risky_operation()
except Exception:  # Still too broad
    return {"status": "error", "traceback": str(e)}
```

## Dependency Injection

### Using Dependencies
```python
from fastapi import Depends
from app.dependencies import get_db_dependency

@app.get("/items")
async def get_items(db = Depends(get_db_dependency)):
    # db is automatically injected
    return db.table("items").select("*")
```

### Creating New Dependencies
```python
# app/dependencies.py
async def get_api_key(request) -> str:
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    return api_key

# Usage
@app.get("/protected")
async def protected(api_key = Depends(get_api_key)):
    pass
```

## Logging Best Practices

### When to Log

Log:
- ✅ Application startup/shutdown
- ✅ Important business logic
- ✅ External API calls
- ✅ Database operations
- ✅ Errors and warnings

Don't log:
- ❌ Every single operation
- ❌ Sensitive data (passwords, tokens)
- ❌ Large data structures

### Usage
```python
from app.core import get_logger

logger = get_logger(__name__)

# Info level
logger.info(f"Processing user {user_id}")

# Warning level
logger.warning(f"Retry attempt {attempt} for {service}")

# Error level
logger.error("Database connection failed", exc_info=True)
```

## Testing Guidelines

### Test Structure
```python
# tests/test_feature.py
import pytest
from app.feature import get_data

class TestFeature:
    """Test feature module."""
    
    @pytest.fixture
    def mock_db(self):
        """Setup mock database."""
        pass
    
    def test_get_data_success(self, mock_db):
        """Test get_data returns data."""
        result = get_data()
        assert result is not None
    
    def test_get_data_empty(self, mock_db):
        """Test get_data with no data."""
        result = get_data()
        assert result == []
```

### Test Naming
- **File**: `test_module_name.py`
- **Class**: `TestFeatureName`
- **Method**: `test_specific_behavior`

### Coverage Goals
- Aim for >80% code coverage
- Test happy paths and edge cases
- Test error conditions

```bash
pytest --cov=app --cov-report=html
```

## Git Workflow

### Commit Messages
```
[TYPE] Short description (50 chars max)

Detailed explanation of changes (70 chars per line)

- Bullet point 1
- Bullet point 2

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Branch Naming
- `feature/user-authentication`
- `bugfix/login-error`
- `docs/api-documentation`
- `refactor/database-layer`

## Documentation

### Module Documentation
```python
"""
Authentication module.

This module handles JWT token creation, validation, and user
authentication operations. It provides:
- Token creation and validation
- Password hashing and verification
- User authorization checks

Example:
    >>> from app.auth import AuthService
    >>> auth = AuthService()
    >>> token = auth.create_access_token({"sub": "user123"})
"""
```

### API Documentation
- Keep OpenAPI docstrings updated
- Document request/response examples
- Document error codes and messages

```python
@app.post("/users", response_model=UserSchema)
async def create_user(user: UserCreateSchema):
    """
    Create a new user.
    
    Args:
        user: User data to create
        
    Returns:
        UserSchema: Created user with ID
        
    Raises:
        409 ConflictError: If email already exists
        422 ValidationError: If data invalid
    """
    pass
```

## Performance Considerations

### Async/Await
Always use async functions for I/O operations:
```python
# ✅ Good
async def get_user(user_id: str):
    user = await db.users.get(user_id)
    return user

# ❌ Bad
def get_user(user_id: str):
    user = db.users.get(user_id)  # Blocks event loop
    return user
```

### Database Queries
```python
# ✅ Good - Only get needed fields
response = db.table("users").select("id,name").eq("id", user_id).execute()

# ❌ Bad - Gets all fields
response = db.table("users").select("*").execute()
```

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_settings():
    """Settings cached after first call."""
    return Settings()
```

## Security Practices

### Authentication
- ✅ Use strong SECRET_KEY
- ✅ Hash passwords with bcrypt
- ✅ Use JWT tokens with expiration
- ✅ Validate tokens on protected routes

### Input Validation
- ✅ Validate all inputs with Pydantic
- ✅ Use type hints
- ✅ Set max lengths for strings
- ✅ Whitelist allowed values

```python
from pydantic import BaseModel, Field, validator

class UserSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    
    @validator("email")
    def validate_email(cls, v):
        if not v.endswith(".com"):
            raise ValueError("Only .com emails allowed")
        return v
```

### Error Messages
- ✅ Give helpful messages to users
- ❌ Don't expose system details
- ❌ Don't reveal sensitive information

```python
# ✅ Good
raise ResourceNotFoundError("User")  # Returns: "User not found"

# ❌ Bad
raise Exception("SELECT * FROM users failed: table not found")
```

## Adding New Endpoints

### Step 1: Create Endpoint File
Create a new file in `app/api/v1/endpoints/`:

```python
# app/api/v1/endpoints/new_feature.py
"""
API v1 endpoints for new feature.
"""
from fastapi import APIRouter, Depends, status
from app.dependencies import get_db_dependency
from app.models.schemas import ResponseSchema

router = APIRouter(prefix="/new-feature", tags=["new-feature"])


@router.get("")
async def get_new_feature(db=Depends(get_db_dependency)):
    """Get new feature data."""
    return ResponseSchema(
        success=True,
        message="Data retrieved",
        data=[]
    )
```

### Step 2: Register in Router
Update `app/api/v1/router.py`:

```python
from app.api.v1.endpoints import new_feature

api_router.include_router(new_feature.router)
```

### Step 3: Done!
Your endpoint is automatically available at: `GET /api/v1/new-feature/`

## API Versioning Strategy

### Current Structure
```
/api/v1/
├── /companies
├── /macro
├── /prices
└── /health
```

### Adding API v2 (for breaking changes)
Create `app/api/v2/` following the same pattern, then include both in `app/main.py`:

```python
from app.api.v1 import api_router as v1_router
from app.api.v2 import api_router as v2_router

app.include_router(v1_router)
app.include_router(v2_router)
```

Now both `/api/v1/` and `/api/v2/` work simultaneously!

## Deployment Checklist

Before deploying:
- [ ] All tests pass: `pytest`
- [ ] No linting errors: `make lint`
- [ ] Code formatted: `make format`
- [ ] Type checking passes: `mypy app`
- [ ] Documentation updated
- [ ] .env variables configured
- [ ] CORS origins updated for production
- [ ] DEBUG=False in production
- [ ] SECRET_KEY is unique and strong
- [ ] Logs directory exists
- [ ] Database backups configured

## Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/)
- [Python async/await](https://docs.python.org/3/library/asyncio.html)
