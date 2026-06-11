# Wall-Trade-Backend

Professional FastAPI backend for Wall-Trade application with best practices and enterprise-grade architecture.

## Features

- ✅ **API Versioning**: Professional `/api/v1/` structure, easily extensible to v2, v3, etc.
- ✅ **Singleton Settings Class**: Centralized configuration management with Pydantic validation
- ✅ **Logging**: Structured JSON logging with rotation
- ✅ **Exception Handling**: Custom exception classes for domain-specific errors
- ✅ **Dependency Injection**: FastAPI dependencies for clean code
- ✅ **Authentication**: JWT token support with bcrypt password hashing
- ✅ **Database**: Supabase integration with connection pooling
- ✅ **CORS**: Configurable CORS middleware
- ✅ **Health Check**: Built-in health check endpoint
- ✅ **Project Structure**: Professional layering with separation of concerns

## Project Structure

```
Wall-Trade-Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application factory
│   ├── auth.py                 # Authentication service
│   ├── dependencies.py         # Dependency injection
│   ├── constants.py            # Application constants
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # ⭐ Singleton settings class
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logging_config.py   # Logging configuration
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py       # Database connection manager
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic schemas
│   ├── api/                    # ⭐ API versioning root
│   │   ├── __init__.py
│   │   └── v1/                 # ⭐ API v1 endpoints
│   │       ├── __init__.py
│   │       ├── router.py       # ⭐ V1 router
│   │       ├── schemas.py
│   │       └── endpoints/      # ⭐ V1 endpoints
│   │           ├── __init__.py
│   │           ├── companies.py
│   │           ├── macro.py
│   │           ├── prices.py
│   │           └── health.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base_service.py     # Base service class
│   │   ├── psx_service.py      # PSX service
│   │   └── capital_stake.py    # Capital stake service
│   └── utils/
│       ├── __init__.py
│       ├── decorators.py       # Utility decorators
│       ├── responses.py        # Response helpers
│       └── api.py              # API utilities
├── tests/                      # Test suite
├── run.py                      # Application entry point
├── cli.py                      # CLI utilities
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

1. **Clone or navigate to the project directory**
   ```bash
   cd Wall-Trade-Backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

   Or directly with uvicorn:
   ```bash
   uvicorn app:app --reload
   ```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Application
APP_NAME=Wall-Trade-Backend
ENVIRONMENT=development
DEBUG=True

# Server
HOST=0.0.0.0
PORT=8000

# Supabase
SUPABASE_URL=your_url
SUPABASE_KEY=your_key

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## API Endpoints

### Health Check
```bash
GET /api/v1/health
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

### Companies
```bash
GET /api/v1/companies              # List all companies
GET /api/v1/companies/{id}         # Get specific company
```

### Macro Data
```bash
GET /api/v1/macro/indicators       # Get macro indicators
```

### Prices
```bash
GET /api/v1/prices?symbol=ABC      # Get prices for symbol
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### Create Access Token
```python
from app.auth import AuthService

auth_service = AuthService()
token = auth_service.create_access_token(
    data={"sub": "user123"}
)
```

### Use Database Client
```python
from app.database import get_db_client

db = get_db_client()
# Use Supabase client
```

### Get Settings
```python
from app.config import get_settings

settings = get_settings()
print(settings.APP_NAME)
print(settings.is_production)
```

## Best Practices Implemented

1. **Singleton Settings**: Centralized configuration with validation
2. **Dependency Injection**: Clean code with FastAPI dependencies
3. **Exception Handling**: Domain-specific exceptions for better error handling
4. **Logging**: Structured logging with proper configuration
5. **Service Layer**: Business logic separated from routes
6. **Database Management**: Connection pooling and lifecycle management
7. **Security**: JWT tokens and password hashing
8. **Code Organization**: Clear separation of concerns
9. **Documentation**: Comprehensive docstrings and comments
10. **CORS Configuration**: Flexible and secure CORS setup

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
isort app/
```

### Type Checking
```bash
mypy app/
```

### Linting
```bash
flake8 app/
```

## Contributing

Follow these guidelines:
1. Use type hints for all functions
2. Add docstrings to all modules and functions
3. Keep functions focused and small
4. Use dependency injection instead of globals
5. Log important operations
6. Handle exceptions appropriately

## License

Proprietary - Wall-Trade

## Support

For issues and questions, please contact the development team.
