# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using MongoDB ORM.

## Table of Contents

1. [Connection Issues](#connection-issues)
2. [Authentication Problems](#authentication-problems)
3. [Model Definition Errors](#model-definition-errors)
4. [Query Issues](#query-issues)
5. [Performance Problems](#performance-problems)
6. [Validation Errors](#validation-errors)
7. [Index Issues](#index-issues)
8. [Async/Await Problems](#asyncawait-problems)
9. [Configuration Issues](#configuration-issues)
10. [Debugging Techniques](#debugging-techniques)

## Connection Issues

### Problem: Cannot Connect to MongoDB

**Symptoms:**
```
br_mongodb_orm.exceptions.ConnectionError: Could not connect to MongoDB
```

**Solutions:**

1. **Check MongoDB Server Status**
   ```bash
   # Check if MongoDB is running
   sudo systemctl status mongod  # Linux
   brew services list | grep mongodb  # macOS
   ```

2. **Verify Connection String**
   ```python
   # Correct format
   await configure_database(
       database_url="mongodb://localhost:27017",  # Local
       # OR
       database_url="mongodb://user:pass@host:port/db",  # Remote
       database_name="your_database"
   )
   ```

3. **Test Connection Manually**
   ```python
   import motor.motor_asyncio

   async def test_connection():
       client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
       try:
           await client.admin.command('ping')
           print("Connection successful!")
       except Exception as e:
           print(f"Connection failed: {e}")
       finally:
           client.close()
   ```

### Problem: Connection Timeout

**Symptoms:**
```
pymongo.errors.ServerSelectionTimeoutError: No servers available
```

**Solutions:**

1. **Increase Timeout Values**
   ```python
   await configure_database(
       database_url="mongodb://localhost:27017",
       database_name="mydb",
       connect_timeout_ms=10000,  # 10 seconds
       server_selection_timeout_ms=10000
   )
   ```

2. **Check Network Connectivity**
   ```bash
   # Test network connectivity
   telnet your-mongodb-host 27017
   # OR
   nc -zv your-mongodb-host 27017
   ```

3. **Firewall Issues**
   - Ensure MongoDB port (default 27017) is open
   - Check cloud provider security groups/firewall rules

### Problem: Connection Pool Exhaustion

**Symptoms:**
```
pymongo.errors.ConnectionFailure: connection pool paused
```

**Solutions:**

1. **Increase Pool Size**
   ```python
   await configure_database(
       database_url="mongodb://localhost:27017",
       database_name="mydb",
       max_pool_size=100,  # Increase from default 50
       min_pool_size=10
   )
   ```

2. **Ensure Proper Connection Cleanup**
   ```python
   # Always close cursors and connections
   async def process_data():
       try:
           cursor = User.get_collection().find({})
           async for doc in cursor:
               # Process document
               pass
       finally:
           # Cursor is automatically closed, but you can be explicit
           pass
   ```

## Authentication Problems

### Problem: Authentication Failed

**Symptoms:**
```
pymongo.errors.OperationFailure: Authentication failed
```

**Solutions:**

1. **Check Credentials**
   ```python
   # URL encoding for special characters
   from urllib.parse import quote_plus

   username = quote_plus("user@domain.com")
   password = quote_plus("p@ssw0rd!")

   url = f"mongodb://{username}:{password}@host:27017/db"
   ```

2. **Verify Authentication Database**
   ```python
   # Specify auth database if different from target database
   url = "mongodb://user:pass@host:27017/mydb?authSource=admin"
   ```

3. **SSL/TLS Issues**
   ```python
   # For MongoDB Atlas or SSL-enabled instances
   url = "mongodb+srv://user:pass@cluster.mongodb.net/mydb?retryWrites=true&w=majority"
   ```

## Model Definition Errors

### Problem: Field Validation Errors

**Symptoms:**
```
pydantic.ValidationError: 1 validation error for User
email
  field required (type=value_error.missing)
```

**Solutions:**

1. **Check Required Fields**
   ```python
   class User(Document):
       name: str
       email: str  # Required by default
       age: Optional[int] = None  # Optional field
   ```

2. **Use Field Validation**
   ```python
   from pydantic import Field, validator

   class User(Document):
       email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
       age: int = Field(..., ge=0, le=150)

       @validator('email')
       def validate_email(cls, v):
           if not v.strip():
               raise ValueError('Email cannot be empty')
           return v.lower()
   ```

### Problem: Collection Name Conflicts

**Symptoms:**
```
Multiple models using the same collection name
```

**Solutions:**

1. **Explicit Collection Names**
   ```python
   class User(Document):
       name: str

       class Config:
           collection_name = "users"  # Explicit name

   class UserProfile(Document):
       user_id: str

       class Config:
           collection_name = "user_profiles"  # Different name
   ```

### Problem: Index Creation Failures

**Symptoms:**
```
pymongo.errors.OperationFailure: Index already exists with different options
```

**Solutions:**

1. **Drop and Recreate Indexes**
   ```python
   # Drop existing indexes
   await User.get_collection().drop_indexes()

   # Recreate with new definition
   await User.create_indexes()
   ```

2. **Use Index Options Carefully**
   ```python
   class User(Document):
       email: str

       class Config:
           indexes = [
               {
                   "key": [("email", 1)],
                   "unique": True,
                   "background": True  # Create in background
               }
           ]
   ```

## Query Issues

### Problem: No Results When Expected

**Symptoms:**
```python
users = await User.find({"name": "John"})
print(len(users))  # 0, but you expect results
```

**Solutions:**

1. **Check Case Sensitivity**
   ```python
   # Case-insensitive search
   users = await User.find({"name": {"$regex": "john", "$options": "i"}})

   # Or use text search if you have a text index
   users = await User.find({"$text": {"$search": "john"}})
   ```

2. **Debug Query**
   ```python
   # Log the actual query
   import logging
   logging.basicConfig(level=logging.DEBUG)

   # Check what's actually in the database
   all_users = await User.find({})
   print([user.name for user in all_users])
   ```

3. **Check Data Types**
   ```python
   # Wrong: searching string field with int
   users = await User.find({"age": "25"})  # Won't match age: 25

   # Correct: match data types
   users = await User.find({"age": 25})
   ```

### Problem: ObjectId Query Issues

**Symptoms:**
```python
user = await User.find_by_id("507f1f77bcf86cd799439011")  # Returns None
```

**Solutions:**

1. **Use Proper ObjectId Format**
   ```python
   from bson import ObjectId

   # If you have a string ID
   user_id_str = "507f1f77bcf86cd799439011"
   user = await User.find_by_id(ObjectId(user_id_str))

   # Or let the method handle conversion
   user = await User.find_by_id(user_id_str)
   ```

2. **Validate ObjectId Format**
   ```python
   from bson import ObjectId
   from bson.errors import InvalidId

   def is_valid_objectid(oid):
       try:
           ObjectId(oid)
           return True
       except InvalidId:
           return False

   if is_valid_objectid(user_id_str):
       user = await User.find_by_id(user_id_str)
   ```

## Performance Problems

### Problem: Slow Queries

**Symptoms:**
- Queries taking longer than expected
- High CPU usage
- Timeout errors

**Solutions:**

1. **Add Indexes**
   ```python
   # Find slow queries
   db.setProfilingLevel(2, {slowms: 100})

   # Add appropriate indexes
   class User(Document):
       email: str
       status: str
       created_at: datetime

       class Config:
           indexes = [
               ("email", 1),  # For email lookups
               ("status", 1),  # For status filters
               [("status", 1), ("created_at", -1)],  # Compound index
           ]
   ```

2. **Use Projections**
   ```python
   # Don't fetch unnecessary fields
   users = await User.find(
       filter_dict={"status": "active"},
       projection={"name": 1, "email": 1}  # Only fetch name and email
   )
   ```

3. **Optimize Aggregation Pipelines**
   ```python
   # Put $match stages early to reduce data processed
   pipeline = [
       {"$match": {"status": "active"}},  # Filter first
       {"$group": {"_id": "$category", "count": {"$sum": 1}}},
       {"$sort": {"count": -1}},
       {"$limit": 10}
   ]
   ```

### Problem: Memory Issues with Large Results

**Symptoms:**
```
MemoryError: Unable to allocate memory
```

**Solutions:**

1. **Use Cursor Iteration**
   ```python
   # Instead of loading all at once
   all_users = await User.find({})  # Loads everything into memory

   # Use cursor iteration
   cursor = User.get_collection().find({})
   async for user_doc in cursor:
       user = User(**user_doc)
       # Process one at a time
   ```

2. **Implement Pagination**
   ```python
   async def process_all_users(batch_size=1000):
       skip = 0
       while True:
           users = await User.find({}, limit=batch_size, skip=skip)
           if not users:
               break

           for user in users:
               # Process user
               pass

           skip += batch_size
   ```

## Validation Errors

### Problem: Pydantic Validation Failures

**Symptoms:**
```
pydantic.ValidationError: 2 validation errors for User
age
  ensure this value is greater than or equal to 0
email
  field required
```

**Solutions:**

1. **Handle Validation Gracefully**
   ```python
   from pydantic import ValidationError

   try:
       user = User(name="John", age=-5)  # Invalid age
   except ValidationError as e:
       print("Validation errors:")
       for error in e.errors():
           print(f"Field: {error['loc'][0]}, Error: {error['msg']}")
   ```

2. **Custom Validators**
   ```python
   from pydantic import validator

   class User(Document):
       email: str
       age: int

       @validator('age')
       def validate_age(cls, v):
           if v < 0:
               raise ValueError('Age must be non-negative')
           if v > 150:
               raise ValueError('Age must be realistic')
           return v

       @validator('email')
       def validate_email(cls, v):
           if '@' not in v:
               raise ValueError('Invalid email format')
           return v.lower()
   ```

## Index Issues

### Problem: Duplicate Key Error

**Symptoms:**
```
pymongo.errors.DuplicateKeyError: E11000 duplicate key error
```

**Solutions:**

1. **Handle Duplicates Gracefully**
   ```python
   from pymongo.errors import DuplicateKeyError

   try:
       user = User(email="existing@example.com")
       await user.save()
   except DuplicateKeyError as e:
       print(f"User with this email already exists: {e}")
       # Handle duplicate case
   ```

2. **Use Upsert Operations**
   ```python
   # Update if exists, create if not
   await User.get_collection().update_one(
       {"email": "user@example.com"},
       {"$set": {"name": "John", "updated_at": datetime.utcnow()}},
       upsert=True
   )
   ```

### Problem: Index Not Being Used

**Symptoms:**
- Queries still slow despite having indexes
- `explain()` shows collection scan

**Solutions:**

1. **Check Index Usage**
   ```python
   # Explain query execution
   explain_result = await User.get_collection().find(
       {"email": "user@example.com"}
   ).explain()

   print(explain_result['executionStats']['executionSuccess'])
   print(explain_result['executionStats']['winningPlan'])
   ```

2. **Verify Index Exists**
   ```python
   # List all indexes
   indexes = await User.get_collection().list_indexes().to_list(100)
   for index in indexes:
       print(f"Index: {index['name']}, Key: {index['key']}")
   ```

3. **Check Query Pattern Matches Index**
   ```python
   # Index: [("status", 1), ("created_at", -1)]

   # This will use the index
   users = await User.find({"status": "active"})

   # This will also use the index
   users = await User.find({
       "status": "active",
       "created_at": {"$gte": some_date}
   })

   # This might not use the index efficiently
   users = await User.find({"created_at": {"$gte": some_date}})  # Missing status
   ```

## Async/Await Problems

### Problem: Event Loop Issues

**Symptoms:**
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Solutions:**

1. **Proper Async Context**
   ```python
   # In Jupyter notebooks or existing async context
   import nest_asyncio
   nest_asyncio.apply()

   # Or use await directly if already in async context
   users = await User.find({})
   ```

2. **Correct Async Usage**
   ```python
   # Wrong: mixing sync and async
   def sync_function():
       users = User.find({})  # This won't work

   # Correct: all async
   async def async_function():
       users = await User.find({})
       return users
   ```

### Problem: Not Awaiting Async Operations

**Symptoms:**
```python
users = User.find({})  # Returns coroutine object, not results
print(users)  # <coroutine object...>
```

**Solutions:**

1. **Always Await Async Operations**
   ```python
   # Correct
   users = await User.find({})
   user = await User.find_by_id(user_id)
   await user.save()
   await user.delete()
   ```

## Configuration Issues

### Problem: Environment Variables Not Loading

**Symptoms:**
- Database connection fails
- Configuration values are None

**Solutions:**

1. **Check Environment Variables**
   ```python
   import os
   print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
   print(f"DATABASE_NAME: {os.getenv('DATABASE_NAME')}")
   ```

2. **Use .env Files**
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # Load .env file

   # Now environment variables are available
   await configure_database(
       database_url=os.getenv("DATABASE_URL"),
       database_name=os.getenv("DATABASE_NAME")
   )
   ```

3. **Provide Defaults**
   ```python
   await configure_database(
       database_url=os.getenv("DATABASE_URL", "mongodb://localhost:27017"),
       database_name=os.getenv("DATABASE_NAME", "default_db")
   )
   ```

## Debugging Techniques

### Enable Detailed Logging

```python
import logging

# Enable MongoDB ORM logging
logging.getLogger('br_mongodb_orm').setLevel(logging.DEBUG)

# Enable Motor/PyMongo logging
logging.getLogger('motor').setLevel(logging.DEBUG)
logging.getLogger('pymongo').setLevel(logging.DEBUG)

# Configure logging format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Debug Database Operations

```python
# Monitor all database commands
import motor.motor_asyncio

async def setup_debug_monitoring():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")

    # Enable command monitoring
    def command_logger(event):
        if hasattr(event, 'command'):
            print(f"Command: {event.command}")
        if hasattr(event, 'reply'):
            print(f"Reply: {event.reply}")

    client.add_command_logger(command_logger)
    return client
```

### Query Analysis

```python
async def analyze_query_performance():
    # Enable profiling
    await User.get_database().run_command({"profile": 2, "slowms": 0})

    # Run your query
    users = await User.find({"status": "active"})

    # Check profiling data
    profile_data = await User.get_database().system.profile.find().to_list(10)
    for operation in profile_data:
        print(f"Duration: {operation.get('ts')}")
        print(f"Command: {operation.get('command')}")
        print(f"Duration: {operation.get('millis')}ms")
        print("---")
```

### Memory Usage Monitoring

```python
import psutil
import os

def log_memory_usage(operation_name):
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"{operation_name}: RSS={memory_info.rss / 1024 / 1024:.2f}MB")

# Usage
log_memory_usage("Before query")
users = await User.find({})
log_memory_usage("After query")
```

### Testing Database State

```python
async def debug_database_state():
    """Print detailed database state for debugging."""

    # Check connection
    try:
        await User.get_database().admin.command('ping')
        print("✓ Database connection: OK")
    except Exception as e:
        print(f"✗ Database connection: {e}")
        return

    # Check collections
    collections = await User.get_database().list_collection_names()
    print(f"Collections: {collections}")

    # Check document counts
    for collection_name in collections:
        try:
            count = await User.get_database()[collection_name].count_documents({})
            print(f"  {collection_name}: {count} documents")
        except Exception as e:
            print(f"  {collection_name}: Error counting - {e}")

    # Check indexes
    if "users" in collections:
        indexes = await User.get_collection().list_indexes().to_list(100)
        print("Indexes on 'users':")
        for index in indexes:
            print(f"  {index['name']}: {index['key']}")

# Run debug check
await debug_database_state()
```

## Common Error Messages and Solutions

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `ConnectionError: Could not connect to MongoDB` | MongoDB server not running or wrong URL | Check MongoDB status, verify connection string |
| `ValidationError: field required` | Missing required field in model | Add required field or make it optional |
| `DuplicateKeyError: E11000 duplicate key` | Violating unique constraint | Handle duplicate or use upsert operation |
| `ServerSelectionTimeoutError` | Network/connectivity issue | Check network, increase timeout, verify MongoDB is accessible |
| `OperationFailure: Authentication failed` | Wrong credentials or auth database | Verify username/password, check authSource |
| `TypeError: Object of type ObjectId is not JSON serializable` | Trying to serialize ObjectId | Convert to string: `str(object_id)` |
| `RuntimeError: Event loop is running` | Incorrect async usage | Use proper async context or nest_asyncio |

## When to Seek Help

If you've tried the solutions above and still have issues:

1. **Check the GitHub Issues**: Search existing issues for similar problems
2. **Create a Minimal Reproduction**: Isolate the problem with minimal code
3. **Gather Environment Info**: Python version, MongoDB version, package versions
4. **Enable Debug Logging**: Include relevant log output in your issue report
5. **Share Configuration**: Sanitized connection strings and model definitions

Remember to never share sensitive information like passwords or production connection strings when seeking help.
