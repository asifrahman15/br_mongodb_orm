# Error Handling

MongoDB ORM provides comprehensive error handling with custom exception types, detailed error messages, and recovery strategies.

## Table of Contents

- [Overview](#overview)
- [Exception Hierarchy](#exception-hierarchy)
- [Common Error Scenarios](#common-error-scenarios)
- [Error Recovery Strategies](#error-recovery-strategies)
- [Logging and Debugging](#logging-and-debugging)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

MongoDB ORM uses a structured approach to error handling that provides:

- **Specific Exception Types**: Clear categorization of different error types
- **Detailed Error Messages**: Informative messages for debugging
- **Error Context**: Additional information about the error circumstances
- **Recovery Strategies**: Built-in retry mechanisms and fallback options
- **Logging Integration**: Comprehensive logging for monitoring and debugging

## Exception Hierarchy

### Base Exceptions

```python
from py_mongo_orm.exceptions import (
    MongoDBORMError,           # Base exception
    ModelNotInitializedError,   # Model not initialized
    ValidationError,           # Data validation errors
    DocumentNotFoundError,     # Document not found
    DuplicateDocumentError,    # Duplicate key violations
    ConnectionError,           # Connection issues
    BulkWriteError            # Bulk operation errors
)
```

### Exception Details

#### MongoDBORMError

Base exception for all MongoDB ORM errors:

```python
try:
    user = await User.get(id=123)
except MongoDBORMError as e:
    # Catches any MongoDB ORM related error
    logger.error(f"MongoDB ORM error: {e}")
```

#### ModelNotInitializedError

Raised when attempting operations on uninitialized models:

```python
try:
    user = await User.get(id=123)
except ModelNotInitializedError as e:
    # Model needs initialization
    await User.__initialize__()
    user = await User.get(id=123)
```

#### ValidationError

Raised when data validation fails:

```python
try:
    user = User(name="", email="invalid-email")  # Invalid data
    await user.save()
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Handle validation errors
```

#### DocumentNotFoundError

Raised when a required document is not found:

```python
try:
    user = await User.get_by_id(999)  # Non-existent ID
    if user is None:
        raise DocumentNotFoundError("User not found")
except DocumentNotFoundError as e:
    print(f"Document not found: {e}")
```

#### DuplicateDocumentError

Raised on unique constraint violations:

```python
try:
    user = User(email="existing@example.com")  # Duplicate email
    await user.save()
except DuplicateDocumentError as e:
    print(f"Duplicate document: {e}")
    # Handle duplicate data
```

#### ConnectionError

Raised on database connection issues:

```python
try:
    await User.__initialize__()
except ConnectionError as e:
    print(f"Connection failed: {e}")
    # Implement retry or fallback logic
```

## Common Error Scenarios

### 1. Model Initialization Errors

```python
from py_mongo_orm.exceptions import ModelNotInitializedError

async def safe_model_operation():
    """Safely perform model operations with initialization check"""
    try:
        users = await User.all()
        return users
    except ModelNotInitializedError:
        # Initialize model and retry
        await User.__initialize__()
        return await User.all()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### 2. Data Validation Errors

```python
from py_mongo_orm.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError

async def create_user_safely(user_data: dict):
    """Create user with comprehensive validation error handling"""
    try:
        user = User(**user_data)
        await user.save()
        return user
    except (ValidationError, PydanticValidationError) as e:
        # Extract validation details
        if hasattr(e, 'errors'):
            errors = e.errors()
            for error in errors:
                field = error.get('loc', ['unknown'])[0]
                message = error.get('msg', 'Invalid value')
                print(f"Validation error in '{field}': {message}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating user: {e}")
        raise
```

### 3. Connection and Network Errors

```python
import asyncio
from py_mongo_orm.exceptions import ConnectionError
from pymongo.errors import ServerSelectionTimeoutError, NetworkTimeout

async def robust_database_operation(operation_func, *args, **kwargs):
    """Execute database operation with retry logic"""
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            return await operation_func(*args, **kwargs)
        except (ConnectionError, ServerSelectionTimeoutError, NetworkTimeout) as e:
            if attempt == max_retries - 1:
                logger.error(f"All retry attempts failed: {e}")
                raise
            
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
    
    raise ConnectionError("Maximum retry attempts exceeded")

# Usage
users = await robust_database_operation(User.all)
```

### 4. Unique Constraint Violations

```python
from py_mongo_orm.exceptions import DuplicateDocumentError
from pymongo.errors import DuplicateKeyError

async def handle_duplicate_user(email: str, name: str):
    """Handle duplicate user creation gracefully"""
    try:
        user = User(email=email, name=name)
        await user.save()
        return user, False  # New user created
    except (DuplicateDocumentError, DuplicateKeyError):
        # User already exists, return existing user
        existing_user = await User.get(email=email)
        return existing_user, True  # Existing user returned
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

## Error Recovery Strategies

### 1. Automatic Retry with Exponential Backoff

```python
import asyncio
import random
from functools import wraps

def retry_on_error(max_retries=3, backoff_factor=1.0, exceptions=(Exception,)):
    """Decorator for automatic retry with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        raise
                    
                    # Calculate backoff delay with jitter
                    delay = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

# Usage
@retry_on_error(max_retries=3, exceptions=(ConnectionError, NetworkTimeout))
async def fetch_user_data(user_id: int):
    return await User.get_by_id(user_id)
```

### 2. Circuit Breaker Pattern

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise ConnectionError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._reset()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _reset(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

# Global circuit breaker for database operations
db_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)

async def safe_db_operation(operation, *args, **kwargs):
    """Execute database operation with circuit breaker"""
    return await db_circuit_breaker.call(operation, *args, **kwargs)

# Usage
user = await safe_db_operation(User.get_by_id, 123)
```

### 3. Fallback Mechanisms

```python
async def get_user_with_fallback(user_id: int):
    """Get user with multiple fallback strategies"""
    
    # Primary: Get from database
    try:
        user = await User.get_by_id(user_id)
        if user:
            return user
    except Exception as e:
        logger.warning(f"Primary database lookup failed: {e}")
    
    # Fallback 1: Try cache
    try:
        cached_user = await get_user_from_cache(user_id)
        if cached_user:
            logger.info(f"Retrieved user {user_id} from cache")
            return cached_user
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")
    
    # Fallback 2: Default user object
    logger.warning(f"Creating default user object for {user_id}")
    return User(
        id=user_id,
        name="Unknown User",
        email=f"user{user_id}@unknown.com",
        is_active=False
    )

async def get_user_from_cache(user_id: int):
    """Get user from cache (placeholder implementation)"""
    # Implementation would depend on your caching solution
    pass
```

## Logging and Debugging

### 1. Comprehensive Error Logging

```python
import logging
import traceback
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class ErrorLogger:
    @staticmethod
    def log_error(error: Exception, context: Optional[dict] = None):
        """Log error with context and stack trace"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "stack_trace": traceback.format_exc()
        }
        
        if context:
            error_info["context"] = context
        
        logger.error(f"Error occurred: {error_info}")
        return error_info

# Usage in model operations
async def monitored_user_creation(user_data: dict):
    """Create user with comprehensive error logging"""
    try:
        user = User(**user_data)
        await user.save()
        logger.info(f"User created successfully: {user.id}")
        return user
    except Exception as e:
        ErrorLogger.log_error(e, {
            "operation": "user_creation",
            "user_data": user_data,
            "function": "monitored_user_creation"
        })
        raise
```

### 2. Debug Mode and Verbose Logging

```python
import os

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

class DebugLogger:
    @staticmethod
    def debug_query(model_name: str, operation: str, params: dict):
        """Log query details in debug mode"""
        if DEBUG:
            logger.debug(f"[{model_name}] {operation}: {params}")
    
    @staticmethod
    def debug_result(model_name: str, operation: str, result_count: int):
        """Log result details in debug mode"""
        if DEBUG:
            logger.debug(f"[{model_name}] {operation} returned {result_count} results")

# Enhanced model with debug logging
class DebugUser(User):
    @classmethod
    async def get(cls, **kwargs):
        DebugLogger.debug_query(cls.__name__, "get", kwargs)
        result = await super().get(**kwargs)
        DebugLogger.debug_result(cls.__name__, "get", 1 if result else 0)
        return result
    
    @classmethod
    async def filter(cls, **kwargs):
        DebugLogger.debug_query(cls.__name__, "filter", kwargs)
        results = await super().filter(**kwargs)
        DebugLogger.debug_result(cls.__name__, "filter", len(results))
        return results
```

### 3. Performance Monitoring

```python
import time
import asyncio
from functools import wraps

def monitor_performance(threshold_seconds=1.0):
    """Decorator to monitor operation performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > threshold_seconds:
                    logger.warning(f"Slow operation: {func.__name__} took {duration:.3f}s")
                else:
                    logger.debug(f"Operation: {func.__name__} took {duration:.3f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Failed operation: {func.__name__} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator

# Usage
@monitor_performance(threshold_seconds=0.5)
async def complex_user_query():
    return await User.filter(
        age={"$gte": 18},
        city="New York",
        sort_by={"created_at": -1},
        limit=100
    )
```

## Best Practices

### 1. Graceful Error Handling

```python
async def robust_user_service():
    """Example of robust service with proper error handling"""
    
    class UserService:
        def __init__(self):
            self.circuit_breaker = CircuitBreaker()
        
        async def get_user(self, user_id: int) -> Optional[User]:
            """Get user with comprehensive error handling"""
            try:
                return await self.circuit_breaker.call(User.get_by_id, user_id)
            except DocumentNotFoundError:
                logger.info(f"User {user_id} not found")
                return None
            except ConnectionError as e:
                logger.error(f"Database connection failed: {e}")
                # Return cached user or None
                return await self._get_cached_user(user_id)
            except Exception as e:
                logger.error(f"Unexpected error getting user {user_id}: {e}")
                raise
        
        async def create_user(self, user_data: dict) -> tuple[Optional[User], list[str]]:
            """Create user with validation and error collection"""
            errors = []
            
            try:
                user = User(**user_data)
                await user.save()
                return user, errors
            except ValidationError as e:
                errors = [f"Validation error: {e}"]
                return None, errors
            except DuplicateDocumentError:
                errors = ["User with this email already exists"]
                return None, errors
            except Exception as e:
                logger.error(f"Unexpected error creating user: {e}")
                errors = ["Internal server error"]
                return None, errors
        
        async def _get_cached_user(self, user_id: int) -> Optional[User]:
            """Get user from cache (fallback)"""
            # Implementation depends on caching solution
            return None

# Usage
service = UserService()
user, errors = await service.create_user(user_data)
```

### 2. Error Context Management

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def error_context(operation: str, **context):
    """Context manager for error handling with additional context"""
    start_time = time.time()
    try:
        logger.info(f"Starting {operation}")
        yield
        duration = time.time() - start_time
        logger.info(f"Completed {operation} in {duration:.3f}s")
    except Exception as e:
        duration = time.time() - start_time
        error_context = {
            "operation": operation,
            "duration": duration,
            **context
        }
        ErrorLogger.log_error(e, error_context)
        raise

# Usage
async def process_user_data(user_data: dict):
    async with error_context("user_data_processing", user_count=len(user_data)):
        for data in user_data:
            async with error_context("individual_user_creation", email=data.get("email")):
                user = User(**data)
                await user.save()
```

## Examples

### 1. API Error Handling

```python
from typing import Union, Dict, Any

async def api_create_user(user_data: dict) -> Dict[str, Any]:
    """API endpoint with comprehensive error handling"""
    try:
        # Validate input
        if not user_data.get("email"):
            return {
                "success": False,
                "error": "Email is required",
                "error_code": "VALIDATION_ERROR"
            }
        
        # Create user
        user = User(**user_data)
        await user.save()
        
        return {
            "success": True,
            "data": user.model_dump(),
            "message": "User created successfully"
        }
        
    except ValidationError as e:
        return {
            "success": False,
            "error": "Invalid user data",
            "error_code": "VALIDATION_ERROR",
            "details": str(e)
        }
    
    except DuplicateDocumentError:
        return {
            "success": False,
            "error": "User with this email already exists",
            "error_code": "DUPLICATE_USER"
        }
    
    except ConnectionError:
        return {
            "success": False,
            "error": "Database temporarily unavailable",
            "error_code": "SERVICE_UNAVAILABLE"
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in api_create_user: {e}")
        return {
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
```

### 2. Batch Processing with Error Recovery

```python
async def process_user_batch_with_recovery(users_data: list[dict]):
    """Process batch of users with individual error handling"""
    
    results = {
        "successful": [],
        "failed": [],
        "errors": []
    }
    
    for i, user_data in enumerate(users_data):
        try:
            async with error_context("batch_user_processing", index=i, email=user_data.get("email")):
                user = User(**user_data)
                await user.save()
                results["successful"].append({
                    "index": i,
                    "user_id": user.id,
                    "email": user.email
                })
                
        except ValidationError as e:
            error_info = {
                "index": i,
                "email": user_data.get("email"),
                "error": "Validation failed",
                "details": str(e)
            }
            results["failed"].append(error_info)
            results["errors"].append(error_info)
            
        except DuplicateDocumentError:
            error_info = {
                "index": i,
                "email": user_data.get("email"),
                "error": "Duplicate user"
            }
            results["failed"].append(error_info)
            results["errors"].append(error_info)
            
        except Exception as e:
            logger.error(f"Unexpected error processing user {i}: {e}")
            error_info = {
                "index": i,
                "email": user_data.get("email"),
                "error": "Internal error"
            }
            results["failed"].append(error_info)
            results["errors"].append(error_info)
    
    return results
```

### 3. Health Check with Error Detection

```python
async def database_health_check() -> Dict[str, Any]:
    """Comprehensive database health check"""
    health_status = {
        "status": "healthy",
        "checks": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Check 1: Basic connectivity
    try:
        await User.count()
        health_status["checks"]["connectivity"] = {"status": "ok", "message": "Database accessible"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["connectivity"] = {"status": "error", "message": str(e)}
    
    # Check 2: Read performance
    try:
        start = time.time()
        await User.filter(limit=1)
        duration = time.time() - start
        
        if duration > 1.0:
            health_status["checks"]["read_performance"] = {"status": "warning", "duration": duration}
        else:
            health_status["checks"]["read_performance"] = {"status": "ok", "duration": duration}
    except Exception as e:
        health_status["status"] = "unhealthy" 
        health_status["checks"]["read_performance"] = {"status": "error", "message": str(e)}
    
    # Check 3: Write performance
    try:
        start = time.time()
        test_user = User(name="Health Check", email=f"health_{int(time.time())}@test.com")
        await test_user.save()
        await test_user.delete()
        duration = time.time() - start
        
        if duration > 2.0:
            health_status["checks"]["write_performance"] = {"status": "warning", "duration": duration}
        else:
            health_status["checks"]["write_performance"] = {"status": "ok", "duration": duration}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["write_performance"] = {"status": "error", "message": str(e)}
    
    return health_status
```
