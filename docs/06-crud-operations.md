# CRUD Operations

Complete guide to Create, Read, Update, and Delete operations with MongoDB ORM.

## Table of Contents

- [Create Operations](#create-operations)
- [Read Operations](#read-operations)
- [Update Operations](#update-operations)
- [Delete Operations](#delete-operations)
- [Advanced Patterns](#advanced-patterns)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)

## Create Operations

### Basic Creation

#### `create(**kwargs)`

Create and save a new document.

```python
from br_mongodb_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True

# Create a single user
user = await User.create(
    name="John Doe",
    email="john@example.com",
    age=30
)
print(f"Created user with ID: {user.id}")
print(f"Created at: {user.created_at}")
```

**Returns:** The created model instance with auto-generated ID and timestamps.

**Raises:**
- `ValidationError`: If data validation fails
- `DuplicateDocumentError`: If unique constraint violated

### Bulk Creation

#### `bulk_create(documents, ordered=True)`

Create multiple documents efficiently.

```python
# Prepare data
users_data = [
    {"name": "Alice", "email": "alice@example.com", "age": 25},
    {"name": "Bob", "email": "bob@example.com", "age": 30},
    {"name": "Charlie", "email": "charlie@example.com", "age": 35}
]

# Bulk create
users = await User.bulk_create(users_data)
print(f"Created {len(users)} users")

# With error handling
try:
    users = await User.bulk_create(users_data, ordered=False)
except ValidationError as e:
    print(f"Some documents failed: {e}")
```

**Parameters:**
- `documents`: List of dictionaries with document data
- `ordered`: If True, stop on first error; if False, continue with remaining documents

**Returns:** List of created model instances

### Get or Create

#### `get_or_create(defaults=None, **kwargs)`

Get existing document or create if not found.

```python
# Try to get user by email, create if not exists
user, created = await User.get_or_create(
    email="john@example.com",
    defaults={
        "name": "John Doe",
        "age": 30,
        "is_active": True
    }
)

if created:
    print("New user created")
else:
    print("Existing user found")
```

**Parameters:**
- `defaults`: Values to use when creating new document
- `**kwargs`: Filter criteria for existing document

**Returns:** Tuple of (instance, created) where created is boolean

## Read Operations

### Single Document Retrieval

#### `get(**kwargs)`

Get a single document by filter criteria.

```python
# Get by single field
user = await User.get(email="john@example.com")

# Get by multiple fields
user = await User.get(name="John Doe", is_active=True)

# Get with None result
user = await User.get(email="nonexistent@example.com")
if user is None:
    print("User not found")
```

#### `get_by_id(doc_id)`

Get document by its ID (convenience method).

```python
user = await User.get_by_id(123)
if user:
    print(f"Found user: {user.name}")
```

### Multiple Document Retrieval

#### `filter(**kwargs)`

Filter documents with various options.

```python
# Basic filtering
active_users = await User.filter(is_active=True)

# With sorting
users = await User.filter(
    is_active=True,
    sort_by={"created_at": -1}  # Newest first
)

# With pagination
users = await User.filter(
    is_active=True,
    skip=0,
    limit=10
)

# With field projection
users = await User.filter(
    is_active=True,
    projection={"name": 1, "email": 1}  # Only name and email
)
```

**Parameters:**
- `sort_by`: Dictionary of field: direction (1 for ascending, -1 for descending)
- `limit`: Maximum number of documents to return
- `skip`: Number of documents to skip (for pagination)
- `projection`: Fields to include (1) or exclude (0)
- `**kwargs`: Filter criteria

#### `all()`

Get all documents in the collection.

```python
all_users = await User.all()
print(f"Total users: {len(all_users)}")
```

### Counting Documents

#### `count(**kwargs)`

Count documents matching criteria.

```python
# Count all documents
total_users = await User.count()

# Count with filter
active_users_count = await User.count(is_active=True)
adult_users_count = await User.count(age__gte=18)  # age >= 18
```

### Distinct Values

#### `distinct(field, **kwargs)`

Get unique values for a field.

```python
# Get all unique ages
ages = await User.distinct("age")

# Get unique roles for active users
roles = await User.distinct("role", is_active=True)
```

## Update Operations

### Instance Updates

#### `save(only_update=False)`

Save changes to an existing instance.

```python
# Get and modify user
user = await User.get_by_id(123)
user.name = "Updated Name"
user.age = 31

# Save changes
await user.save()

# Only update if document exists
try:
    await user.save(only_update=True)
except DocumentNotFoundError:
    print("Document not found for update")
```

**Parameters:**
- `only_update`: If True, only update existing documents (don't create new)

**Automatic Updates:**
- `updated_at` field is automatically set to current timestamp
- All field validation is performed

### Bulk Updates

For bulk updates, use MongoDB's native update operations through aggregation:

```python
# Update multiple documents (example using aggregation)
pipeline = [
    {"$match": {"is_active": False}},
    {"$set": {"status": "inactive", "updated_at": datetime.now(UTC)}}
]

# Note: Direct bulk update will be added in future versions
```

## Delete Operations

### Single Document Deletion

#### `delete()`

Delete the current instance.

```python
user = await User.get_by_id(123)
if user:
    deleted = await user.delete()
    if deleted:
        print("User deleted successfully")
```

**Returns:** Boolean indicating success

### Bulk Deletion

#### `delete_many(**kwargs)`

Delete multiple documents matching criteria.

```python
# Delete inactive users
deleted_count = await User.delete_many(is_active=False)
print(f"Deleted {deleted_count} inactive users")

# Delete users older than specific date
from datetime import datetime, UTC, timedelta
cutoff_date = datetime.now(UTC) - timedelta(days=365)
deleted_count = await User.delete_many(created_at__lt=cutoff_date)
```

**Returns:** Number of deleted documents

## Advanced Patterns

### Refresh from Database

#### `refresh_from_db()`

Reload instance data from database.

```python
user = await User.get_by_id(123)

# Data might have changed in database
await user.refresh_from_db()
print(f"Refreshed user: {user.name}")
```

### Conditional Operations

```python
# Create only if doesn't exist
user, created = await User.get_or_create(
    email="unique@example.com",
    defaults={"name": "Unique User"}
)

# Update only if exists
user = await User.get(email="existing@example.com")
if user:
    user.last_login = datetime.now(UTC)
    await user.save(only_update=True)
```

### Transactions (Manual)

```python
# For complex operations, use Motor's transaction support
from motor.motor_asyncio import AsyncIOMotorClient

async def transfer_operation():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    
    async with await client.start_session() as session:
        async with session.start_transaction():
            # Perform multiple operations
            user1 = await User.get_by_id(1)
            user2 = await User.get_by_id(2)
            
            user1.balance -= 100
            user2.balance += 100
            
            await user1.save()
            await user2.save()
```

### Optimistic Locking

```python
class User(BaseModel):
    name: str
    email: str
    version: int = 1  # Version field for optimistic locking
    
    async def save_with_version_check(self):
        """Save with version-based optimistic locking"""
        current_version = self.version
        self.version += 1
        
        # Update only if version matches
        result = await self._collection.update_one(
            {"id": self.id, "version": current_version},
            {"$set": self.model_dump()}
        )
        
        if result.matched_count == 0:
            raise ValueError("Document was modified by another process")
```

## Error Handling

### Common Exceptions

```python
from br_mongodb_orm import (
    ValidationError,
    DocumentNotFoundError,
    DuplicateDocumentError
)

try:
    # Create operation
    user = await User.create(
        name="",  # Invalid: empty name
        email="invalid-email"  # Invalid: bad email format
    )
except ValidationError as e:
    print(f"Validation failed: {e}")

try:
    # Get operation
    user = await User.get_by_id(999999)
    if not user:
        raise DocumentNotFoundError("User not found")
except DocumentNotFoundError as e:
    print(f"Not found: {e}")

try:
    # Duplicate creation
    await User.create(email="existing@example.com")
except DuplicateDocumentError as e:
    print(f"Duplicate document: {e}")
```

### Validation Errors

```python
# Handle field-specific validation
try:
    user = await User.create(
        name="John",
        email="john@example.com",
        age=-5  # Invalid age
    )
except ValidationError as e:
    # Parse validation details
    for error in e.errors():
        field = error['loc'][0]
        message = error['msg']
        print(f"Field '{field}': {message}")
```

## Performance Tips

### 1. Use Projections

```python
# Only fetch needed fields
users = await User.filter(
    is_active=True,
    projection={"name": 1, "email": 1}
)
```

### 2. Use Indexes

```python
# Create indexes for frequently queried fields
await User.create_index("email", unique=True)
await User.create_index("created_at")
await User.create_compound_index({"role": 1, "is_active": 1})
```

### 3. Batch Operations

```python
# Use bulk_create for multiple documents
users = await User.bulk_create(user_data_list)

# Use delete_many for bulk deletions
await User.delete_many(is_active=False)
```

### 4. Efficient Pagination

```python
async def get_users_page(page: int, size: int = 20):
    """Efficient pagination"""
    skip = (page - 1) * size
    users = await User.filter(
        is_active=True,
        sort_by={"id": 1},
        skip=skip,
        limit=size
    )
    return users

# Get first page
first_page = await get_users_page(1)

# Get second page
second_page = await get_users_page(2)
```

### 5. Use Aggregation for Complex Queries

```python
# Complex filtering with aggregation
pipeline = [
    {"$match": {"is_active": True}},
    {"$lookup": {
        "from": "posts",
        "localField": "id",
        "foreignField": "author_id",
        "as": "posts"
    }},
    {"$addFields": {"post_count": {"$size": "$posts"}}},
    {"$match": {"post_count": {"$gt": 5}}},
    {"$sort": {"post_count": -1}}
]

active_authors = await User.aggregate(pipeline)
```

## Best Practices

### 1. Always Handle None Results

```python
user = await User.get(email="unknown@example.com")
if user is None:
    # Handle case when user doesn't exist
    return {"error": "User not found"}
```

### 2. Use Type Hints

```python
from typing import Optional, List

async def get_active_users() -> List[User]:
    return await User.filter(is_active=True)

async def find_user_by_email(email: str) -> Optional[User]:
    return await User.get(email=email)
```

### 3. Validate Before Operations

```python
async def update_user(user_id: int, data: dict) -> User:
    user = await User.get_by_id(user_id)
    if not user:
        raise DocumentNotFoundError(f"User {user_id} not found")
    
    # Update fields
    for field, value in data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    return await user.save()
```

### 4. Use Transactions for Related Operations

```python
async def create_user_with_profile(user_data: dict, profile_data: dict):
    """Create user and profile atomically"""
    user = await User.create(**user_data)
    
    try:
        profile_data["user_id"] = user.id
        profile = await UserProfile.create(**profile_data)
        return user, profile
    except Exception:
        # Rollback user creation
        await user.delete()
        raise
```

---

**Previous:** [Connection Management](05-connection-management.md) | **Next:** [Query Methods](07-query-methods.md)
