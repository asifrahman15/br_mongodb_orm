# Installation & Setup

Complete guide to installing and configuring MongoDB ORM.

## Installation

### Basic Installation

```bash
pip install br_mongodb_orm
```

### Development Installation

For development with testing and linting tools:

```bash
pip install br_mongodb_orm[dev]
```

This includes:
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.0.0` - Coverage testing
- `black>=23.0.0` - Code formatting
- `flake8>=5.0.0` - Linting
- `mypy>=1.0.0` - Type checking
- `pre-commit>=3.0.0` - Git hooks

### Test-Only Installation

For testing environments:

```bash
pip install br_mongodb_orm[test]
```

## MongoDB Setup

### Local MongoDB

Install MongoDB locally:

```bash
# macOS (using Homebrew)
brew install mongodb-community

# Ubuntu/Debian
sudo apt-get install mongodb

# Start MongoDB service
brew services start mongodb-community  # macOS
sudo systemctl start mongod           # Linux
```

### MongoDB Atlas (Cloud)

1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a cluster
3. Get connection string
4. Whitelist your IP address

### Docker MongoDB

```bash
# Run MongoDB in Docker
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:latest

# Connection URI for Docker
export MONGO_URI="mongodb://admin:password@localhost:27017"
```

## Environment Configuration

### Required Environment Variables

```bash
# Minimum required configuration
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DATABASE="my_app_db"
```

### Complete Environment Configuration

```bash
# Database connection
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DATABASE="my_app_db"

# Connection pooling
export MONGO_MAX_POOL_SIZE="100"
export MONGO_MIN_POOL_SIZE="0"

# Timeouts (in milliseconds)
export MONGO_SERVER_SELECTION_TIMEOUT="5000"
export MONGO_CONNECT_TIMEOUT="10000"
export MONGO_SOCKET_TIMEOUT="5000"

# Additional options
export MONGO_RETRY_WRITES="true"
```

### Using .env Files

Create a `.env` file in your project root:

```env
# .env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=my_app_db
MONGO_MAX_POOL_SIZE=100
MONGO_MIN_POOL_SIZE=0
MONGO_SERVER_SELECTION_TIMEOUT=5000
MONGO_CONNECT_TIMEOUT=10000
MONGO_SOCKET_TIMEOUT=5000
MONGO_RETRY_WRITES=true
```

Load with python-dotenv:

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()

# Now use MongoDB ORM normally
from br_mongodb_orm import BaseModel
```

## Project Structure

### Recommended Structure

```
my_project/
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── post.py
│   └── base.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── post_service.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_services.py
├── .env
├── requirements.txt
└── main.py
```

### Example base.py

```python
# models/base.py
import os
from br_mongodb_orm import BaseModel, DatabaseConfig

# Custom base model with project-specific settings
class AppBaseModel(BaseModel):
    class Meta:
        # Custom settings for all models
        auto_create_indexes = True
        strict_mode = True
```

### Example model file

```python
# models/user.py
from typing import Optional, List
from .base import AppBaseModel

class User(AppBaseModel):
    name: str
    email: str
    age: Optional[int] = None
    tags: List[str] = []
    
    class Meta:
        collection_name = "users"  # Optional: defaults to "user"
```

### Example initialization

```python
# models/__init__.py
from .user import User
from .post import Post

__all__ = ["User", "Post"]
```

```python
# main.py
import asyncio
from br_mongodb_orm import register_all_models, setup_logging, close_all_connections

async def init_app():
    # Setup logging
    setup_logging(level="INFO")
    
    # Register all models
    import models
    await register_all_models("models")
    
    # Your app code here
    pass

async def shutdown():
    # Clean shutdown
    await close_all_connections()

if __name__ == "__main__":
    try:
        asyncio.run(init_app())
    except KeyboardInterrupt:
        asyncio.run(shutdown())
```

## Verification

### Test Your Setup

```python
# test_setup.py
import asyncio
from br_mongodb_orm import health_check, setup_logging

async def test_connection():
    setup_logging(level="INFO")
    
    # Test database connection
    is_healthy = await health_check()
    
    if is_healthy:
        print("✅ MongoDB connection successful!")
    else:
        print("❌ MongoDB connection failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
```

Run the test:

```bash
python test_setup.py
```

## Common Setup Issues

### Connection Issues

**Problem**: `ConnectionError: Failed to connect to MongoDB`

**Solutions**:
1. Check if MongoDB is running
2. Verify `MONGO_URI` format
3. Check firewall settings
4. Verify network connectivity

### Import Issues

**Problem**: `ImportError: No module named 'br_mongodb_orm'`

**Solutions**:
1. Install package: `pip install br_mongodb_orm`
2. Check virtual environment
3. Verify Python path

### Environment Variable Issues

**Problem**: Models not connecting to correct database

**Solutions**:
1. Check environment variables are set
2. Use `.env` file
3. Set variables in code:

```python
import os
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DATABASE"] = "my_db"
```

## Docker Setup

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - MONGO_URI=mongodb://mongo:27017
      - MONGO_DATABASE=app_db
    depends_on:
      - mongo
    volumes:
      - .:/app

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

## Next Steps

Now that you have MongoDB ORM installed and configured:

1. [Learn about model definition](03-model-definition.md)
2. [Understand configuration options](04-configuration.md)
3. [Explore CRUD operations](06-crud-operations.md)

---

**Previous:** [Quick Start Guide](01-quick-start.md) | **Next:** [Model Definition](03-model-definition.md)
