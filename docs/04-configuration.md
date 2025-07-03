# Configuration

MongoDB ORM provides flexible configuration options through environment variables, configuration classes, and model-specific settings.

## Table of Contents

- [Overview](#overview)
- [Environment Variables](#environment-variables)
- [DatabaseConfig Class](#databaseconfig-class)
- [ModelConfig Class](#modelconfig-class)
- [Configuration Priority](#configuration-priority)
- [Examples](#examples)

## Overview

The configuration system follows a hierarchical approach:

1. **Environment Variables** (lowest priority)
2. **DatabaseConfig** (medium priority)
3. **Model Meta class** (highest priority)

This allows for flexible deployment configurations while maintaining model-specific overrides.

## Environment Variables

MongoDB ORM reads the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DATABASE` | `default_db` | Default database name |
| `MONGO_MAX_POOL_SIZE` | `10` | Maximum connection pool size |
| `MONGO_MIN_POOL_SIZE` | `1` | Minimum connection pool size |
| `MONGO_MAX_IDLE_TIME_MS` | `30000` | Maximum idle time for connections |
| `MONGO_CONNECT_TIMEOUT_MS` | `5000` | Connection timeout in milliseconds |
| `MONGO_SERVER_SELECTION_TIMEOUT_MS` | `5000` | Server selection timeout |

### Setting Environment Variables

```bash
# In your shell or .env file
export MONGO_URI="mongodb://user:password@localhost:27017/myapp"
export MONGO_DATABASE="production_db"
export MONGO_MAX_POOL_SIZE=20
```

## DatabaseConfig Class

The `DatabaseConfig` class provides programmatic configuration:

```python
from br_mongodb_orm import DatabaseConfig

# Basic configuration
config = DatabaseConfig(
    mongo_uri="mongodb://localhost:27017",
    database_name="my_app_db"
)

# Advanced configuration with connection pooling
config = DatabaseConfig(
    mongo_uri="mongodb://user:password@cluster.mongodb.net/",
    database_name="production_db",
    max_pool_size=50,
    min_pool_size=5,
    max_idle_time_ms=60000,
    connect_timeout_ms=10000,
    server_selection_timeout_ms=10000
)
```

### DatabaseConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mongo_uri` | `str` | From env | MongoDB connection URI |
| `database_name` | `str` | From env | Database name |
| `max_pool_size` | `int` | `10` | Maximum connections in pool |
| `min_pool_size` | `int` | `1` | Minimum connections in pool |
| `max_idle_time_ms` | `int` | `30000` | Max idle time for connections |
| `connect_timeout_ms` | `int` | `5000` | Connection timeout |
| `server_selection_timeout_ms` | `int` | `5000` | Server selection timeout |

## ModelConfig Class

Model-specific configuration through the `Meta` class:

```python
from br_mongodb_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        collection_name = "users"           # Custom collection name
        auto_create_indexes = True          # Auto-create indexes
        strict_mode = True                  # Strict validation
        use_auto_id = True                  # Use auto-generated IDs
        id_field = "id"                     # ID field name
```

### ModelConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collection_name` | `str` | Class name | MongoDB collection name |
| `auto_create_indexes` | `bool` | `True` | Auto-create default indexes |
| `strict_mode` | `bool` | `True` | Enable strict validation |
| `use_auto_id` | `bool` | `True` | Use auto-generated IDs |
| `id_field` | `str` | `"id"` | Primary key field name |

## Configuration Priority

When multiple configuration sources are present, they are applied in order:

1. **Environment variables** are loaded first
2. **DatabaseConfig** overrides environment variables
3. **Model Meta class** overrides both

Example priority resolution:

```python
# Environment: MONGO_DATABASE=env_db
# DatabaseConfig: database_name=config_db
# Model Meta: collection_name=users

# Result: Uses config_db as database, users as collection
```

## Examples

### Basic Setup with Environment Variables

```python
import os
from br_mongodb_orm import BaseModel

# Set environment variables
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DATABASE"] = "my_app"

class User(BaseModel):
    name: str
    email: str

# Initialize with environment config
await User.__initialize__()
```

### Custom Database Configuration

```python
from br_mongodb_orm import BaseModel, DatabaseConfig

# Create custom config
db_config = DatabaseConfig(
    mongo_uri="mongodb://cluster.mongodb.net/",
    database_name="production",
    max_pool_size=25
)

class User(BaseModel):
    name: str
    email: str

# Initialize with custom config
await User.__initialize__(db_config=db_config)
```

### Model-Specific Configuration

```python
from br_mongodb_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        collection_name = "app_users"       # Custom collection name
        auto_create_indexes = False         # Disable auto-indexing
        strict_mode = False                 # Allow extra fields

class Product(BaseModel):
    name: str
    price: float
    
    class Meta:
        collection_name = "inventory"       # Different collection
        use_auto_id = False                 # Use MongoDB ObjectId
        id_field = "_id"                    # Use _id as primary key
```

### Multiple Database Support

```python
from br_mongodb_orm import BaseModel, DatabaseConfig

# User database config
user_config = DatabaseConfig(
    mongo_uri="mongodb://user-cluster/",
    database_name="users_db"
)

# Analytics database config
analytics_config = DatabaseConfig(
    mongo_uri="mongodb://analytics-cluster/",
    database_name="analytics_db"
)

class User(BaseModel):
    name: str
    email: str

class Event(BaseModel):
    user_id: int
    event_type: str
    timestamp: datetime

# Initialize with different configs
await User.__initialize__(db_config=user_config)
await Event.__initialize__(db_config=analytics_config)
```

### Production Configuration Example

```python
from br_mongodb_orm import BaseModel, DatabaseConfig
import os

# Production configuration
production_config = DatabaseConfig(
    mongo_uri=os.environ["MONGO_URI"],      # From secrets/env
    database_name="production_app",
    max_pool_size=50,                       # Higher pool for production
    min_pool_size=10,
    max_idle_time_ms=120000,                # 2 minutes
    connect_timeout_ms=15000,               # 15 seconds
    server_selection_timeout_ms=15000
)

class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        collection_name = "users"
        auto_create_indexes = True
        strict_mode = True

# Initialize for production
await User.__initialize__(db_config=production_config)
```

## Best Practices

1. **Use Environment Variables** for deployment-specific settings (URIs, credentials)
2. **Use DatabaseConfig** for application-level settings
3. **Use Model Meta** for model-specific behavior
4. **Keep Sensitive Data** in environment variables or secrets management
5. **Use Connection Pooling** appropriately for your load
6. **Test Configuration** in development environments first

## Troubleshooting

### Common Configuration Issues

**Issue: Connection timeout**
```python
# Solution: Increase timeout values
config = DatabaseConfig(
    connect_timeout_ms=30000,
    server_selection_timeout_ms=30000
)
```

**Issue: Too many connections**
```python
# Solution: Adjust pool sizes
config = DatabaseConfig(
    max_pool_size=100,
    min_pool_size=20
)
```

**Issue: Configuration not applied**
```python
# Ensure initialization happens before any operations
await MyModel.__initialize__(db_config=config)
```
