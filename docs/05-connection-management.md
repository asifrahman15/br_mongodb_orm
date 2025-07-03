# Connection Management

MongoDB ORM provides robust connection management with automatic pooling, cleanup, and error handling through the `ConnectionManager` class.

## Table of Contents

- [Overview](#overview)
- [ConnectionManager Class](#connectionmanager-class)
- [Connection Lifecycle](#connection-lifecycle)
- [Connection Pooling](#connection-pooling)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The `ConnectionManager` handles all aspects of MongoDB connections:

- **Automatic Connection Pooling**: Efficient connection reuse
- **Graceful Cleanup**: Proper connection closure on shutdown
- **Error Recovery**: Automatic reconnection on failures
- **Health Monitoring**: Connection health checks
- **Resource Management**: Memory and connection leak prevention

## ConnectionManager Class

The connection manager is automatically initialized when you initialize your models:

```python
from br_mongodb_orm import BaseModel, DatabaseConfig

class User(BaseModel):
    name: str
    email: str

# ConnectionManager is created automatically
await User.__initialize__()

# Access the connection manager if needed
connection_manager = User._connection_manager
```

### Manual Connection Manager Usage

```python
from br_mongodb_orm import ConnectionManager, DatabaseConfig

# Create configuration
config = DatabaseConfig(
    mongo_uri="mongodb://localhost:27017",
    database_name="my_app"
)

# Create connection manager
connection_manager = ConnectionManager(config)

# Get client and database
client = await connection_manager.get_client()
database = await connection_manager.get_database()

# Close connections when done
await connection_manager.close()
```

## Connection Lifecycle

### 1. Initialization

When a model is first initialized:

```python
await User.__initialize__()
```

The following happens:
1. `ConnectionManager` is created with configuration
2. Motor client is initialized with connection pooling
3. Database and collections are set up
4. Health check is performed

### 2. Active Usage

During normal operations:
- Connections are reused from the pool
- Failed connections trigger automatic retry
- Pool size adjusts based on demand

### 3. Cleanup

When the application shuts down:

```python
# Manual cleanup (recommended for clean shutdown)
await User._connection_manager.close()

# Or cleanup all models
from br_mongodb_orm.connection import ConnectionManager
await ConnectionManager.close_all()
```

## Connection Pooling

### Pool Configuration

Connection pools are configured via `DatabaseConfig`:

```python
config = DatabaseConfig(
    mongo_uri="mongodb://localhost:27017",
    database_name="my_app",
    max_pool_size=50,        # Maximum connections
    min_pool_size=5,         # Minimum connections
    max_idle_time_ms=60000   # Max idle time (1 minute)
)
```

### Pool Behavior

- **Initial Size**: Starts with `min_pool_size` connections
- **Growth**: Creates new connections up to `max_pool_size`
- **Shrinkage**: Closes idle connections after `max_idle_time_ms`
- **Reuse**: Efficiently reuses existing connections

### Monitoring Pool Usage

```python
# Get connection manager
manager = User._connection_manager

# Check pool status (if available in Motor)
client = await manager.get_client()
# Pool information depends on Motor version

# Monitor through logging
import logging
logging.getLogger('motor').setLevel(logging.DEBUG)
```

## Error Handling

### Connection Failures

The connection manager handles various failure scenarios:

```python
try:
    await User.__initialize__()
except ConnectionFailure as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    # Implement retry logic or fallback

try:
    user = await User.get(id=1)
except ServerSelectionTimeoutError as e:
    logger.error(f"Server selection timeout: {e}")
    # Handle timeout
```

### Automatic Retry

Built-in retry logic for transient failures:

```python
# Automatic retry is built into operations
user = await User.get(email="john@example.com")
# Will automatically retry on transient network errors
```

### Custom Error Handling

```python
from br_mongodb_orm.exceptions import ConnectionError

class User(BaseModel):
    name: str
    email: str

    @classmethod
    async def safe_get(cls, **kwargs):
        """Get with custom error handling"""
        try:
            return await cls.get(**kwargs)
        except ConnectionError:
            # Implement fallback logic
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
```

## Best Practices

### 1. Proper Initialization

Always initialize models before use:

```python
async def setup_database():
    """Initialize all models at application startup"""
    await User.__initialize__()
    await Product.__initialize__()
    await Order.__initialize__()

# Call during app startup
await setup_database()
```

### 2. Graceful Shutdown

Implement proper cleanup:

```python
async def shutdown_database():
    """Clean shutdown of database connections"""
    if User._connection_manager:
        await User._connection_manager.close()

    # Or close all connections
    from br_mongodb_orm.connection import ConnectionManager
    await ConnectionManager.close_all()

# Call during app shutdown
await shutdown_database()
```

### 3. Connection Pool Sizing

Choose appropriate pool sizes:

```python
# For high-traffic applications
config = DatabaseConfig(
    max_pool_size=100,
    min_pool_size=20,
    max_idle_time_ms=120000  # 2 minutes
)

# For low-traffic applications
config = DatabaseConfig(
    max_pool_size=10,
    min_pool_size=2,
    max_idle_time_ms=30000   # 30 seconds
)
```

### 4. Environment-Based Configuration

```python
import os

def get_db_config():
    """Get database config based on environment"""
    if os.environ.get("ENVIRONMENT") == "production":
        return DatabaseConfig(
            mongo_uri=os.environ["MONGO_URI"],
            max_pool_size=50,
            min_pool_size=10
        )
    else:
        return DatabaseConfig(
            mongo_uri="mongodb://localhost:27017",
            max_pool_size=5,
            min_pool_size=1
        )

await User.__initialize__(db_config=get_db_config())
```

### 5. Health Checks

Implement connection health monitoring:

```python
async def check_database_health():
    """Check if database connections are healthy"""
    try:
        # Simple health check
        await User.count()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Use in application health endpoints
is_healthy = await check_database_health()
```

## Advanced Configuration

### Multiple Database Connections

```python
# Users database
user_config = DatabaseConfig(
    mongo_uri="mongodb://user-cluster/",
    database_name="users"
)

# Analytics database
analytics_config = DatabaseConfig(
    mongo_uri="mongodb://analytics-cluster/",
    database_name="analytics"
)

class User(BaseModel):
    name: str
    email: str

class Event(BaseModel):
    user_id: int
    event_type: str

# Initialize with different connections
await User.__initialize__(db_config=user_config)
await Event.__initialize__(db_config=analytics_config)
```

### Custom Client Configuration

```python
from motor.motor_asyncio import AsyncIOMotorClient

# Create custom client with additional options
client = AsyncIOMotorClient(
    "mongodb://localhost:27017",
    maxPoolSize=100,
    minPoolSize=10,
    maxIdleTimeMS=60000,
    connectTimeoutMS=5000,
    serverSelectionTimeoutMS=5000,
    retryWrites=True,
    retryReads=True
)

# Use with models
await User.__initialize__(client=client)
```

## Troubleshooting

### Common Connection Issues

**Issue: Connection timeout**
```python
# Increase timeout values
config = DatabaseConfig(
    connect_timeout_ms=30000,
    server_selection_timeout_ms=30000
)
```

**Issue: Too many connections**
```python
# Check and adjust pool size
config = DatabaseConfig(
    max_pool_size=20,  # Reduce if too high
    min_pool_size=5
)
```

**Issue: Connection leaks**
```python
# Ensure proper cleanup
async def cleanup():
    await User._connection_manager.close()

# Always call cleanup on shutdown
```

**Issue: Authentication failures**
```python
# Check URI format and credentials
mongo_uri = "mongodb://username:password@host:port/database"
```

### Debugging Connection Issues

Enable debug logging:

```python
import logging

# Enable Motor debug logging
logging.getLogger('motor').setLevel(logging.DEBUG)

# Enable pymongo debug logging
logging.getLogger('pymongo').setLevel(logging.DEBUG)

# Enable br_mongodb_orm debug logging
logging.getLogger('br_mongodb_orm').setLevel(logging.DEBUG)
```

### Performance Monitoring

Monitor connection performance:

```python
import time
from br_mongodb_orm import BaseModel

class PerformanceUser(BaseModel):
    name: str

    @classmethod
    async def timed_operation(cls, **kwargs):
        """Measure operation time"""
        start = time.time()
        try:
            result = await cls.get(**kwargs)
            duration = time.time() - start
            logger.info(f"Operation took {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"Operation failed after {duration:.3f}s: {e}")
            raise
```
