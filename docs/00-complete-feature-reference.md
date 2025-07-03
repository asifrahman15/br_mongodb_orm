# MongoDB ORM Complete Feature Reference

This document provides a comprehensive overview of all features, methods, and capabilities available in MongoDB ORM.

## Document Class Features

### Core Functionality

| Feature | Method/Property | Description | Example |
|---------|-----------------|-------------|---------|
| **Document Creation** | `Document(**data)` | Create new document instance | `user = User(name="John", email="john@example.com")` |
| **Save Document** | `await doc.save()` | Save document to database | `saved_user = await user.save()` |
| **Delete Document** | `await doc.delete()` | Delete document from database | `deleted = await user.delete()` |
| **Reload Document** | `await doc.reload()` | Reload document from database | `fresh_user = await user.reload()` |
| **Auto Timestamps** | `created_at`, `updated_at` | Automatic timestamp fields | Always included in every document |

### Query Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `find_by_id()` | `document_id: Union[str, ObjectId]` | `Optional[Self]` | Find document by ID |
| `find_one()` | `filter_dict=None, projection=None, sort=None, **kwargs` | `Optional[Self]` | Find single document |
| `find()` | `filter_dict=None, projection=None, sort=None, limit=None, skip=None, **kwargs` | `List[Self]` | Find multiple documents |
| `count_documents()` | `filter_dict=None, **kwargs` | `int` | Count matching documents |
| `exists()` | `filter_dict: Dict[str, Any]` | `bool` | Check if documents exist |
| `distinct()` | `field: str, filter_dict=None, **kwargs` | `List[Any]` | Get distinct field values |

### Bulk Operations

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `bulk_create()` | `documents_data: List[Dict], ordered=True` | `List[Self]` | Create multiple documents |
| `update_many()` | `filter_dict: Dict, update_dict: Dict, upsert=False` | `UpdateResult` | Update multiple documents |
| `delete_many()` | `filter_dict: Dict` | `DeleteResult` | Delete multiple documents |

### Aggregation

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `aggregate()` | `pipeline: List[Dict], **kwargs` | `List[Dict]` | Execute aggregation pipeline |

### Index Management

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `create_indexes()` | None | `List[str]` | Create all defined indexes |
| `drop_indexes()` | None | `None` | Drop all indexes (except _id) |
| `list_indexes()` | None | `List[Dict]` | List all collection indexes |

## Configuration Options

### Database Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database_url` | `str` | Required | MongoDB connection string |
| `database_name` | `str` | Required | Target database name |
| `max_pool_size` | `int` | `50` | Maximum connections in pool |
| `min_pool_size` | `int` | `5` | Minimum connections to maintain |
| `max_idle_time_ms` | `int` | `30000` | Idle timeout for connections |
| `connect_timeout_ms` | `int` | `10000` | Connection timeout |
| `server_selection_timeout_ms` | `int` | `30000` | Server selection timeout |
| `write_concern_w` | `Union[int, str]` | `1` | Write concern level |
| `write_concern_j` | `bool` | `False` | Journal writes requirement |
| `read_preference` | `str` | `"primary"` | Read preference setting |

### Model Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `collection_name` | `Optional[str]` | Class name lowercase | Collection name |
| `auto_index` | `bool` | `True` | Auto-create indexes on startup |
| `indexes` | `List[IndexDefinition]` | `[]` | Index definitions |

## Index Types and Definitions

### Simple Indexes

```python
# Single field, ascending
("field_name", 1)

# Single field, descending  
("field_name", -1)

# Text index
("field_name", "text")

# Geospatial indexes
("location", "2dsphere")
("location", "2d")

# Hashed index
("field_name", "hashed")
```

### Compound Indexes

```python
# Multiple fields
[("field1", 1), ("field2", -1), ("field3", 1)]

# Mixed types
[("category", 1), ("price", -1), ("name", "text")]
```

### Advanced Index Options

```python
{
    "key": [("field", 1)],
    "unique": True,           # Unique constraint
    "sparse": True,           # Sparse index
    "background": True,       # Build in background
    "name": "custom_name",    # Custom index name
    "partialFilterExpression": {"status": "active"},  # Partial index
    "expireAfterSeconds": 3600  # TTL index
}
```

## Query Operators and Filters

### Comparison Operators

| Operator | MongoDB | Description | Example |
|----------|---------|-------------|---------|
| Equal | `$eq` | Equals | `{"age": 25}` |
| Not Equal | `$ne` | Not equals | `{"age": {"$ne": 25}}` |
| Greater Than | `$gt` | Greater than | `{"age": {"$gt": 18}}` |
| Greater or Equal | `$gte` | Greater than or equal | `{"age": {"$gte": 18}}` |
| Less Than | `$lt` | Less than | `{"age": {"$lt": 65}}` |
| Less or Equal | `$lte` | Less than or equal | `{"age": {"$lte": 65}}` |
| In Array | `$in` | Value in array | `{"status": {"$in": ["active", "pending"]}}` |
| Not In Array | `$nin` | Value not in array | `{"status": {"$nin": ["deleted", "banned"]}}` |

### Logical Operators

| Operator | MongoDB | Description | Example |
|----------|---------|-------------|---------|
| And | `$and` | All conditions true | `{"$and": [{"age": {"$gt": 18}}, {"status": "active"}]}` |
| Or | `$or` | Any condition true | `{"$or": [{"email": "user@example.com"}, {"username": "user"}]}` |
| Not | `$not` | Condition false | `{"age": {"$not": {"$lt": 18}}}` |
| Nor | `$nor` | No conditions true | `{"$nor": [{"status": "deleted"}, {"status": "banned"}]}` |

### Element Operators

| Operator | MongoDB | Description | Example |
|----------|---------|-------------|---------|
| Exists | `$exists` | Field exists | `{"email": {"$exists": True}}` |
| Type | `$type` | Field type | `{"age": {"$type": "int"}}` |

### Array Operators

| Operator | MongoDB | Description | Example |
|----------|---------|-------------|---------|
| All | `$all` | Array contains all values | `{"tags": {"$all": ["python", "mongodb"]}}` |
| Element Match | `$elemMatch` | Array element matches | `{"scores": {"$elemMatch": {"$gt": 80, "$lt": 90}}}` |
| Size | `$size` | Array size | `{"tags": {"$size": 3}}` |

### Text and Regex

| Operator | MongoDB | Description | Example |
|----------|---------|-------------|---------|
| Text Search | `$text` | Full-text search | `{"$text": {"$search": "mongodb python"}}` |
| Regex | `$regex` | Regular expression | `{"email": {"$regex": "gmail\\.com$", "$options": "i"}}` |

## Validation and Field Types

### Pydantic Field Types

| Type | Description | Example |
|------|-------------|---------|
| `str` | String field | `name: str` |
| `int` | Integer field | `age: int` |
| `float` | Float field | `price: float` |
| `bool` | Boolean field | `is_active: bool` |
| `datetime` | DateTime field | `created_at: datetime` |
| `List[T]` | List of type T | `tags: List[str]` |
| `Dict[K, V]` | Dictionary | `metadata: Dict[str, Any]` |
| `Optional[T]` | Optional field | `bio: Optional[str]` |
| `Union[T, U]` | Union type | `identifier: Union[str, int]` |
| `Enum` | Enumeration | `status: UserStatus` |

### Field Validation

| Validator | Description | Example |
|-----------|-------------|---------|
| `min_length` | Minimum string length | `Field(..., min_length=3)` |
| `max_length` | Maximum string length | `Field(..., max_length=100)` |
| `regex` | Regex pattern | `Field(..., regex=r'^[a-zA-Z]+$')` |
| `gt` | Greater than | `Field(..., gt=0)` |
| `ge` | Greater or equal | `Field(..., ge=0)` |
| `lt` | Less than | `Field(..., lt=100)` |
| `le` | Less or equal | `Field(..., le=100)` |

### Custom Validators

```python
@validator('email')
def validate_email(cls, v):
    if '@' not in v:
        raise ValueError('Invalid email')
    return v.lower()

@validator('tags')
def validate_tags(cls, v):
    return list(set(v))  # Remove duplicates
```

## Error Handling

### Exception Hierarchy

```
MongoDBORMError (Base)
├── ConfigurationError
├── ConnectionError
├── ModelNotInitializedError
├── ValidationError
├── DocumentNotFoundError
├── DuplicateKeyError
├── DatabaseError
└── IndexError
```

### Exception Usage

| Exception | When Raised | Example |
|-----------|-------------|---------|
| `ConfigurationError` | Invalid configuration | Wrong connection parameters |
| `ConnectionError` | Database connection fails | MongoDB server down |
| `ValidationError` | Document validation fails | Invalid field values |
| `DocumentNotFoundError` | Document not found | ID doesn't exist |
| `DuplicateKeyError` | Unique constraint violated | Duplicate email |
| `DatabaseError` | Database operation fails | Network issues |
| `IndexError` | Index operation fails | Invalid index definition |

## Utility Functions

### Data Validation

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `validate_object_id()` | `value: Union[str, ObjectId, None]` | `Optional[ObjectId]` | Validate ObjectId |
| `to_object_id()` | `value: Union[str, ObjectId]` | `ObjectId` | Convert to ObjectId |
| `parse_sort_parameter()` | `sort: Union[str, List, Dict]` | `List[Tuple[str, int]]` | Parse sort specification |
| `build_projection()` | `include=None, exclude=None` | `Dict[str, int]` | Build projection dict |

### Query Helpers

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `build_filter_from_kwargs()` | `**kwargs` | `Dict[str, Any]` | Build filter from kwargs |
| `apply_operators()` | `field: str, value: Any` | `Tuple[str, Any]` | Apply query operators |

### Field Operators

| Suffix | MongoDB Operator | Example |
|--------|------------------|---------|
| `__eq` | `$eq` | `age__eq=25` |
| `__ne` | `$ne` | `age__ne=25` |
| `__gt` | `$gt` | `age__gt=18` |
| `__gte` | `$gte` | `age__gte=18` |
| `__lt` | `$lt` | `age__lt=65` |
| `__lte` | `$lte` | `age__lte=65` |
| `__in` | `$in` | `status__in=["active", "pending"]` |
| `__nin` | `$nin` | `status__nin=["deleted"]` |
| `__regex` | `$regex` | `email__regex="gmail"` |
| `__exists` | `$exists` | `email__exists=True` |
| `__size` | `$size` | `tags__size=3` |

## Performance Features

### Connection Optimization

- Connection pooling with configurable pool sizes
- Automatic connection cleanup and resource management
- Connection timeout and retry logic
- Read preference configuration for replica sets

### Query Optimization

- Projection support to fetch only needed fields
- Efficient pagination with limit/skip
- Cursor iteration for large result sets
- Query explain support for optimization

### Indexing Features

- Automatic index creation on model initialization
- Support for all MongoDB index types
- Background index creation
- Index usage analysis and monitoring

### Bulk Operations

- Efficient bulk inserts with ordered/unordered options
- Bulk updates with proper error handling
- Bulk deletes with result reporting
- Batch processing utilities

## Production Features

### Monitoring and Logging

- Comprehensive logging with configurable levels
- Query execution time tracking
- Database operation monitoring
- Error tracking and reporting

### Error Recovery

- Automatic retry logic for transient failures
- Circuit breaker pattern for resilience
- Graceful degradation strategies
- Connection pooling health checks

### Security

- Secure connection string handling
- Environment variable configuration
- Input validation and sanitization
- SQL injection prevention

### Scalability

- Async/await throughout for high concurrency
- Efficient memory usage with streaming
- Connection pool optimization
- Query performance monitoring

## Complete Usage Patterns

### Basic CRUD

```python
# Create
user = User(name="John", email="john@example.com")
saved_user = await user.save()

# Read
user = await User.find_by_id(user_id)
users = await User.find({"status": "active"})

# Update
user.name = "John Doe"
await user.save()

# Delete
await user.delete()
```

### Advanced Queries

```python
# Complex filtering
users = await User.find({
    "$and": [
        {"age": {"$gte": 18}},
        {"$or": [
            {"status": "premium"},
            {"loyalty_points": {"$gt": 1000}}
        ]}
    ]
})

# Aggregation
stats = await User.aggregate([
    {"$match": {"status": "active"}},
    {"$group": {"_id": "$country", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
])

# Text search
results = await Product.find({
    "$text": {"$search": "laptop gaming"},
    "price": {"$lt": 2000}
})
```

### Bulk Operations

```python
# Bulk create
users_data = [{"name": f"User {i}", "email": f"user{i}@example.com"} for i in range(100)]
users = await User.bulk_create(users_data)

# Bulk update
await User.update_many(
    {"last_login": {"$lt": datetime.now() - timedelta(days=30)}},
    {"$set": {"status": "inactive"}}
)

# Bulk delete
await User.delete_many({"status": "deleted"})
```

This comprehensive feature reference covers every aspect of MongoDB ORM, providing developers with a complete understanding of all available capabilities, methods, and usage patterns.
