"""
Constants used throughout the application.
Centralizes all magic strings and numbers.
"""

# HTTP Status Code Messages
HTTP_201_CREATED_MESSAGE = "Resource created successfully"
HTTP_204_NO_CONTENT_MESSAGE = "Resource deleted successfully"
HTTP_400_BAD_REQUEST_MESSAGE = "Invalid request data"
HTTP_401_UNAUTHORIZED_MESSAGE = "Authentication required"
HTTP_403_FORBIDDEN_MESSAGE = "Access denied"
HTTP_404_NOT_FOUND_MESSAGE = "Resource not found"
HTTP_409_CONFLICT_MESSAGE = "Resource already exists"
HTTP_500_INTERNAL_SERVER_ERROR_MESSAGE = "An unexpected error occurred"

# Cache Configuration
CACHE_TTL_MINUTES = {
    "short": 5,
    "medium": 30,
    "long": 60 * 24,  # 1 day
}

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# Token Configuration
TOKEN_TYPE = "bearer"

# Date Formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
