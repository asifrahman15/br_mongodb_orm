# Performance Tips & Optimization

This guide covers performance optimization strategies, benchmarking, and best practices for achieving optimal performance with MongoDB ORM.

## Table of Contents

1. [Connection Optimization](#connection-optimization)
2. [Query Optimization](#query-optimization)
3. [Indexing Strategies](#indexing-strategies)
4. [Bulk Operations](#bulk-operations)
5. [Memory Management](#memory-management)
6. [Monitoring & Profiling](#monitoring--profiling)
7. [Benchmarking](#benchmarking)
8. [Production Considerations](#production-considerations)

## Connection Optimization

### Connection Pooling

MongoDB ORM automatically manages connection pooling, but you can optimize it for your use case:

```python
from py_mongo_orm import configure_database

# Optimize connection pool settings
await configure_database(
    database_url="mongodb://localhost:27017",
    database_name="myapp",
    max_pool_size=100,  # Maximum connections in pool
    min_pool_size=10,   # Minimum connections to maintain
    max_idle_time_ms=30000,  # Close idle connections after 30s
    connect_timeout_ms=5000,  # Connection timeout
    server_selection_timeout_ms=5000,  # Server selection timeout
)
```

### Connection String Optimization

```python
# Optimized connection string for production
connection_string = (
    "mongodb://user:password@host1:27017,host2:27017,host3:27017/"
    "mydb?replicaSet=rs0"
    "&readPreference=secondaryPreferred"
    "&maxPoolSize=100"
    "&minPoolSize=10"
    "&maxIdleTimeMS=30000"
    "&connectTimeoutMS=5000"
    "&serverSelectionTimeoutMS=5000"
    "&retryWrites=true"
    "&w=majority"
)
```

## Query Optimization

### Use Projections

Only fetch the fields you need:

```python
# Fetch only specific fields
users = await User.find(
    filter_dict={"status": "active"},
    projection={"name": 1, "email": 1, "_id": 0}
)

# Using model methods with projection
user = await User.find_one(
    filter_dict={"_id": user_id},
    projection={"password": 0}  # Exclude sensitive fields
)
```

### Efficient Filtering

```python
# Use indexed fields in filters
users = await User.find({"email": "user@example.com"})  # If email is indexed

# Use compound queries efficiently
active_users = await User.find({
    "status": "active",
    "last_login": {"$gte": datetime.now() - timedelta(days=30)}
})

# Use $in for multiple values
user_ids = ["id1", "id2", "id3"]
users = await User.find({"_id": {"$in": user_ids}})
```

### Limit and Skip

```python
# Efficient pagination
page_size = 20
page_number = 5

users = await User.find(
    filter_dict={"status": "active"},
    sort=[("created_at", -1)],
    limit=page_size,
    skip=(page_number - 1) * page_size
)

# For large offsets, use cursor-based pagination
last_seen_id = "..."
users = await User.find(
    filter_dict={
        "status": "active",
        "_id": {"$gt": ObjectId(last_seen_id)}
    },
    sort=[("_id", 1)],
    limit=page_size
)
```

## Indexing Strategies

### Basic Indexing

```python
class User(Document):
    email: str
    username: str
    created_at: datetime
    
    class Config:
        collection_name = "users"
        auto_index = True
        indexes = [
            ("email", 1),  # Single field index
            ("username", 1),
            [("email", 1), ("username", 1)],  # Compound index
            ("created_at", -1),  # Descending index
        ]
```

### Advanced Indexing

```python
class Product(Document):
    name: str
    category: str
    price: float
    tags: List[str]
    location: Dict[str, float]  # {"lat": 40.7128, "lng": -74.0060}
    
    class Config:
        collection_name = "products"
        indexes = [
            # Text index for search
            [("name", "text"), ("description", "text")],
            
            # Compound index for category + price queries
            [("category", 1), ("price", 1)],
            
            # Multikey index for array fields
            ("tags", 1),
            
            # 2dsphere index for geospatial queries
            [("location", "2dsphere")],
            
            # Partial index (only index documents that match condition)
            {
                "key": [("price", 1)],
                "partialFilterExpression": {"price": {"$gt": 0}}
            },
            
            # TTL index (automatically delete documents after time)
            {
                "key": [("created_at", 1)],
                "expireAfterSeconds": 3600  # 1 hour
            }
        ]
```

### Index Analysis

```python
# Check which indexes are being used
await User.get_collection().explain().find({"email": "user@example.com"})

# Get index usage statistics
stats = await User.get_collection().index_stats()
for stat in stats:
    print(f"Index: {stat['name']}, Usage: {stat['accesses']['ops']}")
```

## Bulk Operations

### Bulk Inserts

```python
# Efficient bulk insert
users_data = [
    {"name": f"User {i}", "email": f"user{i}@example.com"}
    for i in range(1000)
]

# Using bulk_create (most efficient)
users = await User.bulk_create(users_data)

# Using Motor's bulk operations for maximum control
from pymongo import InsertOne

operations = [
    InsertOne(user_data) for user_data in users_data
]
result = await User.get_collection().bulk_write(operations, ordered=False)
```

### Bulk Updates

```python
# Bulk update using bulk operations
from pymongo import UpdateOne

operations = [
    UpdateOne(
        {"_id": user_id},
        {"$set": {"status": "active", "updated_at": datetime.utcnow()}}
    )
    for user_id in user_ids
]

result = await User.get_collection().bulk_write(operations, ordered=False)
```

### Bulk Deletes

```python
# Bulk delete
from pymongo import DeleteOne

operations = [
    DeleteOne({"_id": user_id})
    for user_id in inactive_user_ids
]

result = await User.get_collection().bulk_write(operations, ordered=False)
```

## Memory Management

### Streaming Large Result Sets

```python
# Use cursor for large datasets
async def process_all_users():
    cursor = User.get_collection().find({"status": "active"})
    
    async for user_doc in cursor:
        user = User(**user_doc)
        await process_user(user)
        # User object is garbage collected after each iteration

# Process in batches
async def process_users_in_batches(batch_size=1000):
    skip = 0
    while True:
        users = await User.find(
            filter_dict={"status": "active"},
            limit=batch_size,
            skip=skip
        )
        
        if not users:
            break
            
        for user in users:
            await process_user(user)
        
        skip += batch_size
```

### Memory-Efficient Aggregations

```python
# Use $out or $merge to write results to another collection
pipeline = [
    {"$match": {"status": "active"}},
    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    {"$out": "user_stats"}  # Write to another collection
]

await User.aggregate(pipeline)
```

## Monitoring & Profiling

### Enable Profiling

```python
# Enable MongoDB profiling
await User.get_database().run_command({
    "profile": 2,  # Profile all operations
    "slowms": 100  # Log operations slower than 100ms
})

# View profiler data
profiler_data = await User.get_database().system.profile.find().to_list(100)
```

### Application-Level Monitoring

```python
import time
import logging
from functools import wraps

def monitor_query_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logging.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper

# Usage
@monitor_query_time
async def get_user_stats():
    return await User.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ])
```

### Performance Metrics

```python
class PerformanceMonitor:
    def __init__(self):
        self.query_times = []
        self.query_counts = {}
    
    async def track_query(self, operation_name, query_func):
        start_time = time.time()
        try:
            result = await query_func()
            execution_time = time.time() - start_time
            
            self.query_times.append(execution_time)
            self.query_counts[operation_name] = self.query_counts.get(operation_name, 0) + 1
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"Query {operation_name} failed after {execution_time:.3f}s")
            raise
    
    def get_stats(self):
        if not self.query_times:
            return {}
        
        return {
            "total_queries": len(self.query_times),
            "average_time": sum(self.query_times) / len(self.query_times),
            "max_time": max(self.query_times),
            "min_time": min(self.query_times),
            "query_breakdown": self.query_counts
        }

# Usage
monitor = PerformanceMonitor()

async def get_dashboard_data():
    users = await monitor.track_query(
        "find_active_users",
        lambda: User.find({"status": "active"}, limit=100)
    )
    
    stats = await monitor.track_query(
        "user_aggregation",
        lambda: User.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}])
    )
    
    return {"users": users, "stats": stats}
```

## Benchmarking

### Simple Benchmark Example

```python
import asyncio
import time
from typing import List

class Benchmark:
    @staticmethod
    async def time_operation(operation, iterations=1000):
        """Time an async operation over multiple iterations."""
        times = []
        
        for _ in range(iterations):
            start = time.time()
            await operation()
            end = time.time()
            times.append(end - start)
        
        return {
            "iterations": iterations,
            "total_time": sum(times),
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "operations_per_second": iterations / sum(times)
        }
    
    @staticmethod
    async def benchmark_crud_operations():
        """Benchmark basic CRUD operations."""
        
        # Setup test data
        test_users = [
            {"name": f"User {i}", "email": f"user{i}@test.com"}
            for i in range(100)
        ]
        
        # Benchmark creation
        async def create_user():
            user = User(**test_users[0])
            await user.save()
            await user.delete()
        
        create_stats = await Benchmark.time_operation(create_user, 100)
        print(f"Create: {create_stats['operations_per_second']:.2f} ops/sec")
        
        # Setup users for read/update tests
        users = await User.bulk_create(test_users)
        user_ids = [str(user.id) for user in users]
        
        # Benchmark reading
        async def read_user():
            await User.find_by_id(user_ids[0])
        
        read_stats = await Benchmark.time_operation(read_user, 1000)
        print(f"Read: {read_stats['operations_per_second']:.2f} ops/sec")
        
        # Benchmark updating
        async def update_user():
            user = await User.find_by_id(user_ids[0])
            user.name = "Updated Name"
            await user.save()
        
        update_stats = await Benchmark.time_operation(update_user, 100)
        print(f"Update: {update_stats['operations_per_second']:.2f} ops/sec")
        
        # Cleanup
        await User.delete_many({"_id": {"$in": [user.id for user in users]}})

# Run benchmark
await Benchmark.benchmark_crud_operations()
```

## Production Considerations

### Configuration for Production

```python
# production_config.py
import os
from py_mongo_orm import configure_database

async def setup_production_database():
    await configure_database(
        database_url=os.getenv("MONGODB_URL"),
        database_name=os.getenv("DATABASE_NAME"),
        
        # Connection pool optimization
        max_pool_size=int(os.getenv("MAX_POOL_SIZE", "100")),
        min_pool_size=int(os.getenv("MIN_POOL_SIZE", "10")),
        max_idle_time_ms=int(os.getenv("MAX_IDLE_TIME_MS", "30000")),
        
        # Timeouts
        connect_timeout_ms=int(os.getenv("CONNECT_TIMEOUT_MS", "5000")),
        server_selection_timeout_ms=int(os.getenv("SERVER_SELECTION_TIMEOUT_MS", "5000")),
        
        # Write concern for data safety
        write_concern_w="majority",
        write_concern_j=True,  # Journal writes
        
        # Read preference
        read_preference="secondaryPreferred",
    )
```

### Health Checks

```python
async def database_health_check():
    """Check database connectivity and performance."""
    try:
        # Test basic connectivity
        start_time = time.time()
        await User.get_database().admin.command("ping")
        ping_time = time.time() - start_time
        
        # Test read performance
        start_time = time.time()
        await User.count_documents({})
        read_time = time.time() - start_time
        
        # Test write performance
        start_time = time.time()
        test_doc = User(name="health_check", email="test@example.com")
        await test_doc.save()
        await test_doc.delete()
        write_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "ping_time": ping_time,
            "read_time": read_time,
            "write_time": write_time,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
```

### Error Recovery

```python
import asyncio
from py_mongo_orm.exceptions import ConnectionError

async def resilient_operation(operation, max_retries=3, delay=1.0):
    """Execute operation with automatic retry on connection errors."""
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except ConnectionError as e:
            if attempt == max_retries:
                raise
            
            logging.warning(f"Connection error on attempt {attempt + 1}: {e}")
            await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
    
# Usage
async def get_critical_data():
    return await resilient_operation(
        lambda: User.find({"critical": True}),
        max_retries=3
    )
```

### Resource Cleanup

```python
import atexit
from py_mongo_orm import get_database_client

def register_cleanup():
    """Register cleanup functions for graceful shutdown."""
    
    async def cleanup():
        client = get_database_client()
        if client:
            client.close()
            logging.info("Database connections closed")
    
    atexit.register(lambda: asyncio.run(cleanup()))

# Call during application startup
register_cleanup()
```

## Performance Checklist

### Development Phase
- [ ] Enable query profiling during development
- [ ] Use appropriate indexes for your query patterns
- [ ] Test with realistic data volumes
- [ ] Monitor memory usage during bulk operations
- [ ] Use projections to limit data transfer

### Pre-Production
- [ ] Load test with expected traffic patterns
- [ ] Optimize connection pool settings
- [ ] Set up monitoring and alerting
- [ ] Test failover scenarios
- [ ] Verify index effectiveness

### Production
- [ ] Monitor query performance continuously
- [ ] Set up database health checks
- [ ] Implement circuit breakers for resilience
- [ ] Regular index maintenance
- [ ] Monitor connection pool metrics

By following these performance optimization strategies, you can ensure your MongoDB ORM application runs efficiently at scale while maintaining data consistency and reliability.
