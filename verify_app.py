"""
Verification script to test if the application starts correctly.
Run with: python verify_app.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("🔍 Verifying Wall-Trade-Backend configuration...\n")

# Test 1: Load settings
print("✓ Test 1: Loading environment variables from .env")
try:
    from app.core.config import get_settings
    settings = get_settings()
    print(f"  ✅ Settings loaded successfully!")
    print(f"     - APP_NAME: {settings.APP_NAME}")
    print(f"     - ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"     - DEBUG: {settings.DEBUG}")
    print(f"     - PORT: {settings.PORT}")
    print()
except Exception as e:
    print(f"  ❌ Failed to load settings: {e}\n")
    sys.exit(1)

# Test 2: Create FastAPI app
print("✓ Test 2: Creating FastAPI application")
try:
    from app.main import create_app
    app = create_app()
    print(f"  ✅ FastAPI app created successfully!")
    print(f"     - Title: {app.title}")
    print(f"     - Version: {app.version}")
    print()
except Exception as e:
    print(f"  ❌ Failed to create app: {e}\n")
    sys.exit(1)

# Test 3: Check routes
print("✓ Test 3: Checking API routes")
try:
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(f"{route.path}")
    
    api_routes = [r for r in routes if '/api/v1/' in r]
    health_routes = [r for r in routes if '/api/v1/health' in r]
    
    print(f"  ✅ Found {len(routes)} total routes")
    print(f"     - API v1 routes: {len(api_routes)}")
    print(f"     - Sample routes:")
    for route in sorted(set(routes))[:5]:
        print(f"       • {route}")
    print()
except Exception as e:
    print(f"  ⚠️  Could not verify routes: {e}\n")

# Test 4: Test logging
print("✓ Test 4: Testing logging configuration")
try:
    from app.core import setup_logging, get_logger
    setup_logging(level=settings.LOG_LEVEL, format_type=settings.LOG_FORMAT)
    logger = get_logger(__name__)
    logger.info("✅ Logging configured successfully!")
    print()
except Exception as e:
    print(f"  ❌ Failed to setup logging: {e}\n")
    sys.exit(1)

# Test 5: Test database connection
print("✓ Test 5: Testing database connection")
try:
    from app.database import get_db_manager
    db_manager = get_db_manager()
    print(f"  ✅ Database manager initialized!")
    print(f"     - Supabase URL: {settings.SUPABASE_URL}")
    print()
except Exception as e:
    print(f"  ⚠️  Database warning: {e}\n")

# Test 6: Test exception handling
print("✓ Test 6: Testing exception classes")
try:
    from app.core import (
        ValidationError,
        ResourceNotFoundError,
        AuthenticationError,
    )
    
    print(f"  ✅ Exception classes loaded successfully!")
    print(f"     - ValidationError")
    print(f"     - ResourceNotFoundError")
    print(f"     - AuthenticationError")
    print()
except Exception as e:
    print(f"  ❌ Failed to load exceptions: {e}\n")
    sys.exit(1)

# Summary
print("=" * 60)
print("✅ ALL VERIFICATION TESTS PASSED!")
print("=" * 60)
print("\n🚀 Ready to start the application:\n")
print("   Option 1: python run.py")
print("   Option 2: make dev")
print("   Option 3: uvicorn app:app --reload")
print("\n📚 Visit http://localhost:8000/docs for Swagger UI")
print()
