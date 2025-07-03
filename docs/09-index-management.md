# Index Management

MongoDB ORM provides comprehensive index management capabilities to optimize query performance and ensure data integrity.

## Table of Contents

- [Overview](#overview)
- [Automatic Index Creation](#automatic-index-creation)
- [Manual Index Creation](#manual-index-creation)
- [Index Types](#index-types)
- [Index Performance](#index-performance)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

Indexes are crucial for MongoDB performance. They provide:

- **Fast Query Execution**: Dramatically improve query performance
- **Unique Constraints**: Ensure data uniqueness
- **Sorting Optimization**: Speed up sort operations
- **Text Search**: Enable full-text search capabilities

MongoDB ORM automatically manages indexes while providing full control when needed.

## Automatic Index Creation

### Default Indexes

Every model automatically gets:

1. **ID Index**: Unique index on the ID field (default: `id`)
2. **Timestamp Indexes**: Indexes on `created_at` and `updated_at`

```python
from mongodb_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        auto_create_indexes = True  # Default: True

# Automatically creates:
# - Unique index on 'id'
# - Index on 'created_at'  
# - Index on 'updated_at'
await User.__initialize__()
```

### Disabling Automatic Indexes

```python
class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        auto_create_indexes = False  # Disable automatic indexes

await User.__initialize__()
```

## Manual Index Creation

### Single Field Indexes

Create indexes on individual fields:

```python
# Create simple index
await User.create_index("email")

# Create unique index
await User.create_index("email", unique=True)

# Create index in descending order
await User.create_index("created_at", direction=-1)

# Create partial index (with condition)
await User.create_index(
    "email",
    unique=True,
    partial_filter_expression={"is_active": True}
)

# Create sparse index (ignores null values)
await User.create_index("phone", sparse=True)
```

**Parameters:**
- `field` (str): Field name to index
- `unique` (bool): Whether index should enforce uniqueness
- `direction` (int): Sort direction (1 for ascending, -1 for descending)
- `sparse` (bool): Whether to ignore documents with null values
- `partial_filter_expression` (Dict): Condition for partial indexes

### Compound Indexes

Create indexes on multiple fields:

```python
# Basic compound index
await User.create_compound_index({
    "city": 1,      # Ascending
    "age": -1       # Descending
})

# Unique compound index
await User.create_compound_index(
    {"first_name": 1, "last_name": 1},
    unique=True
)

# Compound index with partial filter
await User.create_compound_index(
    {"status": 1, "created_at": -1},
    partial_filter_expression={"is_active": True}
)
```

**Parameters:**
- `fields` (Dict[str, int]): Field names and sort directions
- `unique` (bool): Whether index should enforce uniqueness
- `partial_filter_expression` (Dict): Condition for partial indexes

### Text Indexes

Create full-text search indexes:

```python
class Article(BaseModel):
    title: str
    content: str
    tags: List[str]

# Single field text index
await Article.create_index("title", index_type="text")

# Multiple field text index
await Article.create_compound_index({
    "title": "text",
    "content": "text"
})

# Text index with weights
await Article.create_compound_index({
    "title": "text",
    "content": "text"
}, text_weights={
    "title": 10,      # Higher weight for title
    "content": 1
})
```

## Index Types

### 1. Single Field Indexes

```python
# Basic field index
await User.create_index("email")

# Unique field index  
await User.create_index("username", unique=True)

# Descending order index
await User.create_index("created_at", direction=-1)
```

### 2. Compound Indexes

```python
# Multiple fields
await User.create_compound_index({
    "status": 1,
    "created_at": -1,
    "priority": 1
})

# For queries like:
# User.filter(status="active", sort_by={"created_at": -1})
```

### 3. Multikey Indexes

Automatically created for array fields:

```python
class User(BaseModel):
    tags: List[str]    # Automatically gets multikey index
    roles: List[str]

# Create explicit multikey index
await User.create_index("tags")
await User.create_index("roles")
```

### 4. Text Indexes

For full-text search:

```python
class Article(BaseModel):
    title: str
    content: str

# Text search index
await Article.create_index("title", index_type="text")
await Article.create_index("content", index_type="text")

# Use for text search
articles = await Article.filter({
    "$text": {"$search": "mongodb python"}
})
```

### 5. Geospatial Indexes

For location-based queries:

```python
class Location(BaseModel):
    name: str
    coordinates: List[float]  # [longitude, latitude]

# 2dsphere index for GeoJSON
await Location.create_index("coordinates", index_type="2dsphere")

# Use for geospatial queries
nearby = await Location.filter({
    "coordinates": {
        "$near": {
            "$geometry": {"type": "Point", "coordinates": [-73.9857, 40.7484]},
            "$maxDistance": 1000  # meters
        }
    }
})
```

### 6. TTL Indexes

For automatic document expiration:

```python
class Session(BaseModel):
    user_id: int
    expires_at: datetime

# TTL index - documents expire after specified time
await Session.create_index(
    "expires_at",
    expire_after_seconds=3600  # 1 hour
)
```

## Index Performance

### Query Performance Analysis

Monitor index usage and performance:

```python
import time

async def analyze_query_performance():
    """Analyze query performance with and without indexes"""
    
    # Query without index
    start = time.time()
    users = await User.filter(city="New York")
    no_index_time = time.time() - start
    
    # Create index
    await User.create_index("city")
    
    # Query with index
    start = time.time()
    users = await User.filter(city="New York")
    with_index_time = time.time() - start
    
    print(f"Without index: {no_index_time:.3f}s")
    print(f"With index: {with_index_time:.3f}s")
    print(f"Improvement: {no_index_time/with_index_time:.1f}x faster")
```

### Index Usage Guidelines

1. **Index Frequently Queried Fields**
   ```python
   # If you often query by email
   await User.create_index("email", unique=True)
   ```

2. **Compound Indexes for Multi-Field Queries**
   ```python
   # For queries with multiple conditions
   await User.create_compound_index({"status": 1, "city": 1})
   ```

3. **Sort Optimization**
   ```python
   # Index fields used in sorting
   await User.create_index("created_at", direction=-1)
   ```

### Index Maintenance

```python
class User(BaseModel):
    name: str
    email: str
    
    @classmethod
    async def setup_indexes(cls):
        """Set up all required indexes for this model"""
        # Unique constraints
        await cls.create_index("email", unique=True)
        
        # Query optimization
        await cls.create_index("status")
        await cls.create_compound_index({"status": 1, "created_at": -1})
        
        # Text search
        await cls.create_index("name", index_type="text")

# Call during initialization
await User.__initialize__()
await User.setup_indexes()
```

## Best Practices

### 1. Index Strategy

```python
class User(BaseModel):
    email: str
    status: str
    city: str
    age: int
    
    @classmethod
    async def create_production_indexes(cls):
        """Create all indexes needed for production"""
        
        # Unique constraints (data integrity)
        await cls.create_index("email", unique=True)
        
        # Single field queries
        await cls.create_index("status")
        await cls.create_index("city")
        
        # Compound queries (most specific first)
        await cls.create_compound_index({
            "status": 1,
            "city": 1,
            "age": 1
        })
        
        # Sorting optimization
        await cls.create_compound_index({
            "status": 1,
            "created_at": -1
        })
```

### 2. Index Naming and Documentation

```python
class Product(BaseModel):
    name: str
    category: str
    price: float
    tags: List[str]
    
    @classmethod
    async def setup_indexes(cls):
        """
        Set up indexes for Product model:
        - Unique name constraint
        - Category filtering
        - Price range queries
        - Tag searching
        - Text search on name
        """
        
        # Business constraints
        await cls.create_index("name", unique=True)
        
        # Query optimization
        await cls.create_index("category")
        await cls.create_compound_index({"category": 1, "price": 1})
        
        # Array field indexing
        await cls.create_index("tags")
        
        # Text search
        await cls.create_index("name", index_type="text")
```

### 3. Environment-Specific Indexes

```python
import os

class User(BaseModel):
    email: str
    status: str
    
    @classmethod
    async def setup_environment_indexes(cls):
        """Set up indexes based on environment"""
        
        # Always create unique constraints
        await cls.create_index("email", unique=True)
        
        if os.environ.get("ENVIRONMENT") == "production":
            # Production-specific indexes
            await cls.create_index("status")
            await cls.create_compound_index({
                "status": 1,
                "created_at": -1
            })
        elif os.environ.get("ENVIRONMENT") == "development":
            # Development might need text search for testing
            await cls.create_index("email", index_type="text")
```

## Examples

### E-commerce Indexes

```python
class User(BaseModel):
    email: str
    status: str
    city: str
    age: int
    
    @classmethod
    async def setup_indexes(cls):
        # User authentication
        await cls.create_index("email", unique=True)
        
        # User queries
        await cls.create_index("status")
        await cls.create_compound_index({"city": 1, "age": 1})

class Product(BaseModel):
    name: str
    category: str
    price: float
    brand: str
    tags: List[str]
    
    @classmethod
    async def setup_indexes(cls):
        # Product catalog
        await cls.create_index("category")
        await cls.create_index("brand")
        
        # Price filtering
        await cls.create_compound_index({"category": 1, "price": 1})
        
        # Search functionality
        await cls.create_index("name", index_type="text")
        await cls.create_index("tags")

class Order(BaseModel):
    user_id: int
    status: str
    total_amount: float
    
    @classmethod
    async def setup_indexes(cls):
        # User order history
        await cls.create_compound_index({"user_id": 1, "created_at": -1})
        
        # Order management
        await cls.create_index("status")
        
        # Analytics
        await cls.create_compound_index({
            "status": 1,
            "created_at": -1,
            "total_amount": -1
        })
```

### Content Management Indexes

```python
class Article(BaseModel):
    title: str
    author_id: int
    category: str
    status: str
    tags: List[str]
    published_at: Optional[datetime]
    
    @classmethod
    async def setup_indexes(cls):
        # Publishing workflow
        await cls.create_compound_index({
            "status": 1,
            "published_at": -1
        })
        
        # Author content
        await cls.create_compound_index({
            "author_id": 1,
            "published_at": -1
        })
        
        # Category browsing
        await cls.create_compound_index({
            "category": 1,
            "published_at": -1
        })
        
        # Search functionality
        await cls.create_compound_index({
            "title": "text",
            "content": "text"
        }, text_weights={"title": 10, "content": 1})
        
        # Tag filtering
        await cls.create_index("tags")

class Comment(BaseModel):
    article_id: int
    author_id: int
    content: str
    status: str
    
    @classmethod
    async def setup_indexes(cls):
        # Article comments
        await cls.create_compound_index({
            "article_id": 1,
            "created_at": 1
        })
        
        # User comments
        await cls.create_compound_index({
            "author_id": 1,
            "created_at": -1
        })
        
        # Moderation
        await cls.create_index("status")
```

### Analytics Indexes

```python
class Event(BaseModel):
    user_id: int
    event_type: str
    session_id: str
    properties: Dict[str, Any]
    
    @classmethod
    async def setup_indexes(cls):
        # User analytics
        await cls.create_compound_index({
            "user_id": 1,
            "created_at": -1
        })
        
        # Event type analytics
        await cls.create_compound_index({
            "event_type": 1,
            "created_at": -1
        })
        
        # Session analysis
        await cls.create_compound_index({
            "session_id": 1,
            "created_at": 1
        })
        
        # Time-based analytics
        await cls.create_index("created_at", direction=-1)

class UserSession(BaseModel):
    user_id: int
    session_id: str
    ip_address: str
    user_agent: str
    expires_at: datetime
    
    @classmethod
    async def setup_indexes(cls):
        # Session lookup
        await cls.create_index("session_id", unique=True)
        
        # User sessions
        await cls.create_compound_index({
            "user_id": 1,
            "created_at": -1
        })
        
        # TTL for session cleanup
        await cls.create_index("expires_at", expire_after_seconds=0)
```

### Performance Testing

```python
import asyncio
import time
from typing import List

async def benchmark_indexes():
    """Benchmark query performance with different index configurations"""
    
    # Create test data
    users = []
    for i in range(10000):
        users.append(User(
            name=f"User {i}",
            email=f"user{i}@example.com",
            city=["New York", "Los Angeles", "Chicago"][i % 3],
            age=20 + (i % 50)
        ))
    
    # Insert test data
    for user in users:
        await user.save()
    
    # Test 1: Query without index
    start = time.time()
    result1 = await User.filter(city="New York", age={"$gte": 30})
    time_no_index = time.time() - start
    
    # Test 2: Create single field index
    await User.create_index("city")
    start = time.time()
    result2 = await User.filter(city="New York", age={"$gte": 30})
    time_single_index = time.time() - start
    
    # Test 3: Create compound index
    await User.create_compound_index({"city": 1, "age": 1})
    start = time.time()
    result3 = await User.filter(city="New York", age={"$gte": 30})
    time_compound_index = time.time() - start
    
    print(f"Results: {len(result1)} documents")
    print(f"No index: {time_no_index:.3f}s")
    print(f"Single index: {time_single_index:.3f}s ({time_no_index/time_single_index:.1f}x faster)")
    print(f"Compound index: {time_compound_index:.3f}s ({time_no_index/time_compound_index:.1f}x faster)")

# Run benchmark
await benchmark_indexes()
```
