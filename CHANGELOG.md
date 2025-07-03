# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-07-03

### Added
- Complete rewrite with full async/await support
- Enhanced error handling with custom exception classes
- Proper connection management with automatic cleanup
- Type safety improvements with Pydantic v2 integration
- Comprehensive logging throughout the library
- Advanced query methods with better filtering options
- Index management utilities
- Bulk operations support
- Health check functionality
- Test utilities and data factories
- Configuration management with environment variable support
- Connection pooling with configurable parameters
- Proper documentation and examples

### Changed
- **BREAKING**: All methods are now async and require await
- **BREAKING**: Changed from synchronous to asynchronous initialization
- **BREAKING**: Updated method signatures for better type safety
- **BREAKING**: Renamed and reorganized configuration options
- Improved error messages and exception hierarchy
- Enhanced validation with Pydantic v2
- Better performance with optimized queries
- Updated dependencies to latest versions

### Removed
- **BREAKING**: Removed synchronous operation support
- **BREAKING**: Removed legacy method names and parameters
- **BREAKING**: Removed direct print statements in favor of logging

### Fixed
- Memory leaks with unclosed database connections
- Race conditions in concurrent operations
- Inconsistent error handling
- Type annotation issues
- Documentation inconsistencies

### Security
- Improved connection security with proper timeout handling
- Enhanced validation to prevent injection attacks
- Better error message sanitization

## [1.0.4] - Previous Release

### Features
- Basic MongoDB ORM functionality
- Synchronous operations
- Simple model definition
- Basic CRUD operations
- Auto-incrementing ID support
- Index creation utilities

### Known Issues
- Memory leaks with unclosed connections
- Limited error handling
- No async support
- Thread safety concerns
- Basic validation only

---

## Migration Guide from v1.x to v2.0

### 1. Update Dependencies
```bash
pip install py_mongo_orm>=2.0.0
```

### 2. Update Model Initialization
**Before (v1.x):**
```python
from py_mongo_orm.utils import register_all_models
register_all_models(__name__)  # Synchronous
```

**After (v2.0):**
```python
from py_mongo_orm import register_all_models
await register_all_models(__name__)  # Async
```

### 3. Update Method Calls
**Before (v1.x):**
```python
user = User.create(name="John")  # Synchronous
posts = Post.filter(author_id=user.id)  # Synchronous
```

**After (v2.0):**
```python
user = await User.create(name="John")  # Async
posts = await Post.filter(author_id=user.id)  # Async
```

### 4. Update Error Handling
**Before (v1.x):**
```python
try:
    user = User.get(id=123)
except Exception as e:
    print(f"Error: {e}")
```

**After (v2.0):**
```python
from py_mongo_orm import DocumentNotFoundError, ValidationError

try:
    user = await User.get_by_id(123)
except DocumentNotFoundError:
    print("User not found")
except ValidationError as e:
    print(f"Validation error: {e}")
```

### 5. Update Configuration
**Before (v1.x):**
```python
class User(BaseModel):
    class Meta:
        mongo_uri = "mongodb://localhost:27017"
        database_name = "mydb"
```

**After (v2.0):**
```python
# Use environment variables or DatabaseConfig
import os
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DATABASE"] = "mydb"

class User(BaseModel):
    class Meta:
        collection_name = "users"
        auto_create_indexes = True
```

### 6. Add Proper Cleanup
**New in v2.0:**
```python
from py_mongo_orm import close_all_connections

# At application shutdown
await close_all_connections()
```
