# Best Practices

Comprehensive guide to best practices when using MongoDB ORM.

## Table of Contents

- [Model Design](#model-design)
- [Performance Optimization](#performance-optimization)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Security](#security)
- [Code Organization](#code-organization)
- [Production Deployment](#production-deployment)

## Model Design

### 1. Keep Models Simple and Focused

**Good:**
```python
class User(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool = True
```

**Avoid:**
```python
class User(BaseModel):
    # Too many responsibilities
    username: str
    email: str
    # ... 20+ more fields
    billing_address: Dict[str, str]
    shipping_address: Dict[str, str]
    order_history: List[Dict]  # Should be separate model
    preferences: Dict[str, Any]  # Should be separate model
```

### 2. Use Proper Field Types and Validation

**Good:**
```python
from pydantic import Field, EmailStr, validator
from typing import Optional
from datetime import datetime

class User(BaseModel):
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)
    username: str = Field(..., min_length=3, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric')
        return v.lower()
```

### 3. Design for Relationships

**One-to-Many with IDs:**
```python
class User(BaseModel):
    username: str
    email: str

class Post(BaseModel):
    title: str
    content: str
    author_id: int  # Reference to User
    
    async def get_author(self) -> Optional[User]:
        return await User.get_by_id(self.author_id)
```

**Many-to-Many with Lists:**
```python
class Post(BaseModel):
    title: str
    content: str
    tag_ids: List[int] = Field(default_factory=list)
    
    async def get_tags(self) -> List[Tag]:
        if not self.tag_ids:
            return []
        # Use aggregation for better performance
        pipeline = [
            {"$match": {"id": {"$in": self.tag_ids}}},
            {"$sort": {"name": 1}}
        ]
        tag_docs = await Tag.aggregate(pipeline)
        return [Tag(**doc) for doc in tag_docs]
```

### 4. Use Enums for Status Fields

```python
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(BaseModel):
    customer_id: int
    status: OrderStatus = OrderStatus.PENDING
    total_amount: Decimal
```

### 5. Implement Soft Deletes When Needed

```python
class SoftDeleteMixin:
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    async def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)
        await self.save()

class User(BaseModel, SoftDeleteMixin):
    username: str
    email: str
    
    @classmethod
    async def get_active(cls, **kwargs):
        kwargs['is_deleted'] = False
        return await cls.filter(**kwargs)
```

## Performance Optimization

### 1. Create Appropriate Indexes

```python
async def init_models():
    await register_all_models(__name__)
    
    # Single field indexes for frequent queries
    await User.create_index("email", unique=True)
    await User.create_index("username", unique=True)
    await User.create_index("created_at")
    
    # Compound indexes for complex queries
    await Post.create_compound_index({
        "author_id": 1,
        "status": 1,
        "created_at": -1
    })
    
    # Text indexes for search
    await Post.create_index("title")  # For text search
```

### 2. Use Projections to Limit Data

```python
# Only fetch needed fields
users = await User.filter(
    is_active=True,
    projection={"username": 1, "email": 1, "last_login": 1}
)

# For API responses
user_summaries = await User.filter(
    is_active=True,
    projection={"id": 1, "username": 1, "avatar_url": 1}
)
```

### 3. Implement Efficient Pagination

```python
class PaginationResult:
    def __init__(self, items: List[Any], total: int, page: int, size: int):
        self.items = items
        self.total = total
        self.page = page
        self.size = size
        self.has_next = (page * size) < total
        self.has_prev = page > 1

async def paginate_users(page: int = 1, size: int = 20, 
                        filters: Dict[str, Any] = None) -> PaginationResult:
    filters = filters or {}
    
    # Count total items
    total = await User.count(**filters)
    
    # Calculate skip
    skip = (page - 1) * size
    
    # Fetch page items
    items = await User.filter(
        **filters,
        skip=skip,
        limit=size,
        sort_by={"created_at": -1}
    )
    
    return PaginationResult(items, total, page, size)
```

### 4. Use Aggregation for Complex Queries

```python
async def get_user_statistics():
    """Get user statistics using aggregation"""
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"}
            },
            "count": {"$sum": 1},
            "avg_age": {"$avg": "$age"}
        }},
        {"$sort": {"_id.year": -1, "_id.month": -1}},
        {"$limit": 12}
    ]
    
    return await User.aggregate(pipeline)

async def get_top_authors():
    """Get authors with most posts"""
    pipeline = [
        {"$lookup": {
            "from": "post",
            "localField": "id",
            "foreignField": "author_id",
            "as": "posts"
        }},
        {"$addFields": {"post_count": {"$size": "$posts"}}},
        {"$match": {"post_count": {"$gt": 0}}},
        {"$sort": {"post_count": -1}},
        {"$limit": 10},
        {"$project": {
            "username": 1,
            "email": 1,
            "post_count": 1
        }}
    ]
    
    return await User.aggregate(pipeline)
```

### 5. Batch Operations

```python
# Use bulk_create for multiple inserts
users_data = [
    {"username": f"user{i}", "email": f"user{i}@example.com"}
    for i in range(1000)
]
users = await User.bulk_create(users_data)

# Use delete_many for bulk deletions
await User.delete_many(is_active=False, created_at__lt=cutoff_date)
```

## Error Handling

### 1. Use Specific Exception Handling

```python
from mongodb_orm import (
    ValidationError,
    DocumentNotFoundError,
    DuplicateDocumentError,
    ConnectionError
)

async def create_user_safely(user_data: dict) -> dict:
    try:
        user = await User.create(**user_data)
        return {"success": True, "user": user}
        
    except ValidationError as e:
        return {
            "success": False,
            "error": "validation_error",
            "details": [
                {"field": err["loc"][0], "message": err["msg"]}
                for err in e.errors()
            ]
        }
        
    except DuplicateDocumentError:
        return {
            "success": False,
            "error": "duplicate_user",
            "message": "User with this email already exists"
        }
        
    except ConnectionError:
        return {
            "success": False,
            "error": "database_error",
            "message": "Unable to connect to database"
        }
```

### 2. Implement Retry Logic

```python
import asyncio
from typing import Callable, Any

async def retry_operation(operation: Callable, max_retries: int = 3, 
                         delay: float = 1.0) -> Any:
    """Retry an operation with exponential backoff"""
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries:
                raise e
            
            wait_time = delay * (2 ** attempt)
            await asyncio.sleep(wait_time)

# Usage
async def get_user_with_retry(user_id: int) -> Optional[User]:
    return await retry_operation(
        lambda: User.get_by_id(user_id),
        max_retries=3
    )
```

### 3. Validate Input Data

```python
from pydantic import BaseModel as PydanticModel, ValidationError

class UserCreateRequest(PydanticModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

async def create_user_endpoint(request_data: dict):
    try:
        # Validate input
        validated_data = UserCreateRequest(**request_data)
        
        # Create user
        user = await User.create(**validated_data.dict())
        
        return {"success": True, "user_id": user.id}
        
    except ValidationError as e:
        return {"success": False, "errors": e.errors()}
```

## Testing

### 1. Use Test Database

```python
# test_config.py
import os
from mongodb_orm import DatabaseConfig

TEST_DB_CONFIG = DatabaseConfig(
    mongo_uri="mongodb://localhost:27017",
    database_name="test_db"
)

async def setup_test_db():
    """Setup test database"""
    await User.__initialize__(db_config=TEST_DB_CONFIG)
    # Clear test data
    await User.delete_many()
```

### 2. Write Comprehensive Tests

```python
# test_user_model.py
import pytest
from mongodb_orm import ValidationError, DocumentNotFoundError
from models.user import User

@pytest.fixture
async def clean_db():
    """Clean database before each test"""
    await User.delete_many()
    yield
    await User.delete_many()

class TestUserModel:
    
    async def test_create_user_success(self, clean_db):
        """Test successful user creation"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        user = await User.create(**user_data)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.created_at is not None
    
    async def test_create_user_validation_error(self, clean_db):
        """Test user creation with invalid data"""
        with pytest.raises(ValidationError):
            await User.create(
                username="",  # Invalid: too short
                email="invalid-email",  # Invalid: not an email
                first_name="Test",
                last_name="User"
            )
    
    async def test_get_user_by_id(self, clean_db):
        """Test getting user by ID"""
        user = await User.create(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        found_user = await User.get_by_id(user.id)
        assert found_user is not None
        assert found_user.username == "testuser"
    
    async def test_get_nonexistent_user(self, clean_db):
        """Test getting non-existent user"""
        user = await User.get_by_id(999999)
        assert user is None
    
    async def test_update_user(self, clean_db):
        """Test updating user"""
        user = await User.create(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        original_updated_at = user.updated_at
        
        user.first_name = "Updated"
        await user.save()
        
        assert user.first_name == "Updated"
        assert user.updated_at > original_updated_at
    
    async def test_delete_user(self, clean_db):
        """Test deleting user"""
        user = await User.create(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        user_id = user.id
        deleted = await user.delete()
        
        assert deleted is True
        
        found_user = await User.get_by_id(user_id)
        assert found_user is None
```

### 3. Test Data Factories

```python
# test_factories.py
from typing import Dict, Any
import random
from models.user import User
from models.post import Post

class UserFactory:
    @staticmethod
    def build(**kwargs) -> Dict[str, Any]:
        """Build user data without saving"""
        defaults = {
            "username": f"user{random.randint(1000, 9999)}",
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    async def create(**kwargs) -> User:
        """Create and save user"""
        user_data = UserFactory.build(**kwargs)
        return await User.create(**user_data)
    
    @staticmethod
    async def create_batch(count: int, **kwargs) -> List[User]:
        """Create multiple users"""
        users = []
        for i in range(count):
            user_data = UserFactory.build(**kwargs)
            user_data["username"] = f"user{i}_{random.randint(1000, 9999)}"
            user_data["email"] = f"user{i}_{random.randint(1000, 9999)}@example.com"
            user = await User.create(**user_data)
            users.append(user)
        return users

# Usage in tests
async def test_user_listing():
    users = await UserFactory.create_batch(5)
    all_users = await User.all()
    assert len(all_users) == 5
```

## Security

### 1. Input Validation and Sanitization

```python
import html
import re
from typing import Any

def sanitize_string(value: str) -> str:
    """Sanitize string input"""
    # Remove HTML tags
    value = html.escape(value)
    # Remove potentially dangerous characters
    value = re.sub(r'[<>"\']', '', value)
    return value.strip()

class SecureBaseModel(BaseModel):
    def __setattr__(self, name: str, value: Any) -> None:
        # Sanitize string fields
        if isinstance(value, str):
            value = sanitize_string(value)
        super().__setattr__(name, value)

class User(SecureBaseModel):
    username: str
    email: str
    bio: Optional[str] = None
```

### 2. Rate Limiting for Operations

```python
import time
from collections import defaultdict
from typing import Dict

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record current request
        self.requests[identifier].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter(max_requests=1000, window_seconds=3600)

async def rate_limited_create_user(user_data: dict, client_ip: str) -> dict:
    if not rate_limiter.is_allowed(client_ip):
        return {
            "success": False,
            "error": "rate_limit_exceeded",
            "message": "Too many requests"
        }
    
    return await create_user_safely(user_data)
```

### 3. Environment-based Configuration

```python
# config.py
import os
from mongodb_orm import DatabaseConfig

def get_database_config() -> DatabaseConfig:
    """Get database configuration based on environment"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        return DatabaseConfig(
            mongo_uri=os.getenv("MONGO_URI"),
            database_name=os.getenv("MONGO_DATABASE"),
            max_pool_size=int(os.getenv("MONGO_MAX_POOL_SIZE", "100")),
            min_pool_size=int(os.getenv("MONGO_MIN_POOL_SIZE", "10")),
            # Enable SSL for production
            ssl=True,
            ssl_cert_reqs="required"
        )
    elif environment == "testing":
        return DatabaseConfig(
            mongo_uri="mongodb://localhost:27017",
            database_name="test_db",
            max_pool_size=10
        )
    else:  # development
        return DatabaseConfig(
            mongo_uri="mongodb://localhost:27017",
            database_name="dev_db"
        )
```

## Code Organization

### 1. Project Structure

```
my_project/
├── models/
│   ├── __init__.py
│   ├── base.py          # Base models and mixins
│   ├── user.py          # User-related models
│   ├── blog.py          # Blog-related models
│   └── ecommerce.py     # E-commerce models
├── services/
│   ├── __init__.py
│   ├── user_service.py  # User business logic
│   ├── blog_service.py  # Blog business logic
│   └── email_service.py # Email functionality
├── repositories/        # Data access layer (optional)
│   ├── __init__.py
│   └── user_repository.py
├── api/
│   ├── __init__.py
│   ├── dependencies.py  # FastAPI dependencies
│   ├── user_routes.py   # User API endpoints
│   └── blog_routes.py   # Blog API endpoints
├── tests/
│   ├── __init__.py
│   ├── test_models/
│   ├── test_services/
│   └── test_api/
├── migrations/          # Database migrations
├── config/
│   ├── __init__.py
│   ├── settings.py      # Application settings
│   └── database.py      # Database configuration
├── .env                 # Environment variables
├── requirements.txt     # Dependencies
└── main.py             # Application entry point
```

### 2. Service Layer Pattern

```python
# services/user_service.py
from typing import List, Optional, Dict, Any
from models.user import User
from repositories.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.repository = UserRepository()
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create new user with business logic"""
        # Check if username is available
        existing_user = await self.repository.get_by_username(user_data["username"])
        if existing_user:
            raise ValueError("Username already taken")
        
        # Hash password (if provided)
        if "password" in user_data:
            user_data["password_hash"] = self._hash_password(user_data.pop("password"))
        
        # Create user
        user = await self.repository.create(user_data)
        
        # Send welcome email (async task)
        await self._send_welcome_email(user)
        
        return user
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile with additional data"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
        
        # Get additional data
        post_count = await self._get_user_post_count(user_id)
        last_activity = await self._get_last_activity(user_id)
        
        return {
            "user": user,
            "post_count": post_count,
            "last_activity": last_activity
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password securely"""
        # Use bcrypt or similar
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    async def _send_welcome_email(self, user: User):
        """Send welcome email (implement async)"""
        # Integrate with email service
        pass
```

### 3. Repository Pattern (Optional)

```python
# repositories/user_repository.py
from typing import List, Optional, Dict, Any
from models.user import User

class UserRepository:
    """Data access layer for User model"""
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await User.get_by_id(user_id)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await User.get(username=username)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await User.get(email=email)
    
    async def create(self, user_data: Dict[str, Any]) -> User:
        """Create new user"""
        return await User.create(**user_data)
    
    async def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """Update user"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        return await user.save()
    
    async def get_active_users(self, limit: int = 50) -> List[User]:
        """Get active users"""
        return await User.filter(is_active=True, limit=limit)
    
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by username or email"""
        # Simple search - in production use text search
        users = await User.filter(is_active=True)
        return [
            user for user in users
            if query.lower() in user.username.lower() 
            or query.lower() in user.email.lower()
        ][:limit]
```

## Production Deployment

### 1. Environment Configuration

```python
# config/settings.py
import os
from typing import Optional
from pydantic import BaseSettings
from mongodb_orm import DatabaseConfig

class Settings(BaseSettings):
    # Application
    app_name: str = "My App"
    debug: bool = False
    environment: str = "production"
    
    # Database
    mongo_uri: str
    mongo_database: str
    mongo_max_pool_size: int = 100
    mongo_min_pool_size: int = 10
    
    # Security
    secret_key: str
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

def get_database_config() -> DatabaseConfig:
    return DatabaseConfig(
        mongo_uri=settings.mongo_uri,
        database_name=settings.mongo_database,
        max_pool_size=settings.mongo_max_pool_size,
        min_pool_size=settings.mongo_min_pool_size
    )
```

### 2. Graceful Shutdown

```python
# main.py
import asyncio
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI
from mongodb_orm import register_all_models, close_all_connections, setup_logging
from config.settings import settings, get_database_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(level=settings.log_level)
    
    # Initialize database
    await register_all_models("models", db_config=get_database_config())
    
    yield
    
    # Shutdown
    await close_all_connections()

app = FastAPI(lifespan=lifespan)

# Handle shutdown signals
def signal_handler(signum, frame):
    asyncio.create_task(close_all_connections())

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

### 3. Health Checks

```python
# api/health.py
from fastapi import APIRouter, HTTPException
from mongodb_orm import health_check
from config.settings import get_database_config

router = APIRouter()

@router.get("/health")
async def health_check_endpoint():
    """Health check endpoint"""
    try:
        # Check database connectivity
        db_healthy = await health_check(db_config=get_database_config())
        
        if not db_healthy:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")

@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    # Add any readiness checks here
    return {"status": "ready"}
```

### 4. Monitoring and Logging

```python
# config/logging.py
import logging
import sys
from mongodb_orm import setup_logging

def setup_production_logging():
    """Setup production logging"""
    setup_logging(level="INFO")
    
    # Add structured logging for production
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler (optional)
    file_handler = logging.FileHandler('/var/log/app/app.log')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

Following these best practices will help you build robust, scalable, and maintainable applications with MongoDB ORM.

---

**Previous:** [Examples](17-examples.md) | **Next:** [Performance Tips](19-performance.md)
