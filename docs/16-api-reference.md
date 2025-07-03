# API Reference

Complete API reference for MongoDB ORM. This document provides comprehensive details about all classes, methods, properties, parameters, return types, and exceptions.

## Table of Contents

1. [Document Class](#document-class)
2. [Configuration](#configuration)
3. [Connection Management](#connection-management)
4. [Exceptions](#exceptions)
5. [Utility Functions](#utility-functions)
6. [Type Definitions](#type-definitions)
7. [Constants](#constants)

## Document Class

The main class for defining MongoDB documents.

### Class Definition

```python
from br_mongodb_orm import Document
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

class YourModel(Document):
    # Your fields here
    name: str
    email: str
    age: Optional[int] = None
    
    class Config:
        collection_name = "your_collection"  # Optional, defaults to class name
        auto_index = True  # Optional, defaults to True
        indexes = []  # Optional index definitions
```

### Built-in Fields

Every document automatically includes these fields:

```python
id: Optional[ObjectId] = Field(default=None, alias="_id")  # MongoDB ObjectId
created_at: datetime = Field(default_factory=datetime.utcnow)  # Creation timestamp
updated_at: datetime = Field(default_factory=datetime.utcnow)  # Last update timestamp
```

### Configuration Options

#### Config Class

```python
class Config:
    collection_name: Optional[str] = None    # Collection name (defaults to class name)
    auto_index: bool = True                  # Auto-create indexes
    indexes: List[IndexDefinition] = []      # Index definitions
    validate_assignment: bool = True         # Validate on field assignment
    use_enum_values: bool = True            # Use enum values in serialization
    allow_population_by_field_name: bool = True  # Allow field aliases
```

#### Index Definitions

```python
# Simple index (field name and direction)
indexes = [
    ("email", 1),           # Ascending index on email
    ("created_at", -1),     # Descending index on created_at
]

# Compound index
indexes = [
    [("status", 1), ("created_at", -1)],  # Compound index
]

# Advanced index with options
indexes = [
    {
        "key": [("email", 1)],
        "unique": True,
        "background": True,
        "sparse": True,
        "name": "email_unique_idx"
    }
]
```

### Class Methods

#### Database Setup

##### `configure_database(database_url, database_name, **kwargs)`

Configure the database connection for all models.

**Parameters:**
- `database_url` (str): MongoDB connection string
- `database_name` (str): Target database name
- `max_pool_size` (int, optional): Maximum connection pool size (default: 50)
- `min_pool_size` (int, optional): Minimum connection pool size (default: 5)
- `max_idle_time_ms` (int, optional): Maximum idle time for connections (default: 30000)
- `connect_timeout_ms` (int, optional): Connection timeout in milliseconds (default: 10000)
- `server_selection_timeout_ms` (int, optional): Server selection timeout (default: 30000)
- `write_concern_w` (Union[int, str], optional): Write concern (default: 1)
- `write_concern_j` (bool, optional): Journal writes (default: False)
- `read_preference` (str, optional): Read preference (default: "primary")

**Returns:** `None`

**Raises:**
- `ConnectionError`: If connection fails
- `ConfigurationError`: If configuration is invalid

**Example:**
```python
await configure_database(
    database_url="mongodb://localhost:27017",
    database_name="myapp",
    max_pool_size=100,
    write_concern_w="majority",
    read_preference="secondaryPreferred"
)
```

##### `get_database_client()`

Get the current database client.

**Returns:** `motor.motor_asyncio.AsyncIOMotorClient`

**Raises:**
- `ConnectionError`: If no client is configured

##### `get_database()`

Get the current database instance.

**Returns:** `motor.motor_asyncio.AsyncIOMotorDatabase`

**Raises:**
- `ConnectionError`: If no database is configured

##### `get_collection()`

Get the collection for this model.

**Returns:** `motor.motor_asyncio.AsyncIOMotorCollection`

**Raises:**
- `ModelNotInitializedError`: If model is not properly configured

#### Index Management

##### `create_indexes()`

Create all defined indexes for the model.

**Returns:** `List[str]` - List of created index names

**Raises:**
- `IndexError`: If index creation fails
- `ModelNotInitializedError`: If model is not initialized

**Example:**
```python
# Create indexes for User model
index_names = await User.create_indexes()
print(f"Created indexes: {index_names}")
```

##### `drop_indexes()`

Drop all indexes except the default `_id` index.

**Returns:** `None`

**Raises:**
- `IndexError`: If index deletion fails
- `ModelNotInitializedError`: If model is not initialized

##### `list_indexes()`

List all indexes for the collection.

**Returns:** `List[Dict[str, Any]]` - List of index information

**Example:**
```python
indexes = await User.list_indexes()
for index in indexes:
    print(f"Index: {index['name']}, Key: {index['key']}")
```

#### CRUD Operations

##### `save()`

Save the document to the database.

**Returns:** `Self` - The saved document instance

**Raises:**
- `ValidationError`: If document validation fails
- `DatabaseError`: If save operation fails
- `DuplicateKeyError`: If unique constraint is violated

**Behavior:**
- If `id` is None, performs insert operation
- If `id` exists, performs update operation
- Automatically updates `updated_at` field
- Sets `created_at` on first save

**Example:**
```python
user = User(name="John", email="john@example.com")
saved_user = await user.save()
print(f"Saved user with ID: {saved_user.id}")

# Update existing
saved_user.name = "John Doe"
updated_user = await saved_user.save()
```

##### `delete()`

Delete the current document from the database.

**Returns:** `bool` - True if document was deleted, False if not found

**Raises:**
- `DatabaseError`: If delete operation fails
- `ModelNotInitializedError`: If model is not initialized

**Example:**
```python
user = await User.find_by_id(user_id)
if user:
    deleted = await user.delete()
    print(f"Document deleted: {deleted}")
```

##### `reload()`

Reload the document from the database.

**Returns:** `Self` - The reloaded document instance

**Raises:**
- `DocumentNotFoundError`: If document no longer exists
- `DatabaseError`: If reload operation fails

**Example:**
```python
user = await User.find_by_id(user_id)
# Document might have been updated elsewhere
updated_user = await user.reload()
```

#### Query Methods

##### `find_by_id(document_id)`

Find a document by its ObjectId.

**Parameters:**
- `document_id` (Union[str, ObjectId]): Document ID

**Returns:** `Optional[Self]` - Found document or None

**Raises:**
- `DatabaseError`: If query fails
- `ValidationError`: If ID format is invalid

**Example:**
```python
user = await User.find_by_id("507f1f77bcf86cd799439011")
if user:
    print(f"Found user: {user.name}")
```

##### `find_one(filter_dict=None, projection=None, sort=None, **kwargs)`

Find a single document matching the criteria.

**Parameters:**
- `filter_dict` (Optional[Dict[str, Any]]): Query filter
- `projection` (Optional[Dict[str, int]]): Fields to include/exclude
- `sort` (Optional[List[Tuple[str, int]]]): Sort specification
- `**kwargs`: Additional Motor find_one parameters

**Returns:** `Optional[Self]` - Found document or None

**Raises:**
- `DatabaseError`: If query fails
- `ValidationError`: If document validation fails

**Example:**
```python
# Find by email
user = await User.find_one({"email": "john@example.com"})

# With projection
user = await User.find_one(
    {"status": "active"},
    projection={"name": 1, "email": 1}
)

# With sort
user = await User.find_one(
    {"status": "active"},
    sort=[("created_at", -1)]
)
```

##### `find(filter_dict=None, projection=None, sort=None, limit=None, skip=None, **kwargs)`

Find multiple documents matching the criteria.

**Parameters:**
- `filter_dict` (Optional[Dict[str, Any]]): Query filter
- `projection` (Optional[Dict[str, int]]): Fields to include/exclude  
- `sort` (Optional[List[Tuple[str, int]]]): Sort specification
- `limit` (Optional[int]): Maximum number of documents to return
- `skip` (Optional[int]): Number of documents to skip
- `**kwargs`: Additional Motor find parameters

**Returns:** `List[Self]` - List of found documents

**Raises:**
- `DatabaseError`: If query fails
- `ValidationError`: If document validation fails

**Example:**
```python
# Find all active users
users = await User.find({"status": "active"})

# With pagination
users = await User.find(
    {"status": "active"},
    sort=[("created_at", -1)],
    limit=20,
    skip=40
)

# With projection
users = await User.find(
    {"age": {"$gte": 18}},
    projection={"name": 1, "email": 1}
)
```

##### `count_documents(filter_dict=None, **kwargs)`

Count documents matching the criteria.

**Parameters:**
- `filter_dict` (Optional[Dict[str, Any]]): Query filter
- `**kwargs`: Additional Motor count_documents parameters

**Returns:** `int` - Number of matching documents

**Raises:**
- `DatabaseError`: If count operation fails

**Example:**
```python
# Count all users
total_users = await User.count_documents()

# Count active users
active_count = await User.count_documents({"status": "active"})
```

##### `exists(filter_dict)`

Check if any document matches the criteria.

**Parameters:**
- `filter_dict` (Dict[str, Any]): Query filter

**Returns:** `bool` - True if at least one document matches

**Raises:**
- `DatabaseError`: If query fails

**Example:**
```python
# Check if email exists
email_exists = await User.exists({"email": "john@example.com"})
if email_exists:
    print("Email already registered")
```

##### `distinct(field, filter_dict=None, **kwargs)`

Get distinct values for a field.

**Parameters:**
- `field` (str): Field name to get distinct values for
- `filter_dict` (Optional[Dict[str, Any]]): Query filter
- `**kwargs`: Additional Motor distinct parameters

**Returns:** `List[Any]` - List of distinct values

**Raises:**
- `DatabaseError`: If distinct operation fails

**Example:**
```python
# Get all distinct statuses
statuses = await User.distinct("status")

# Get distinct ages for active users
ages = await User.distinct("age", {"status": "active"})
```

#### Bulk Operations

##### `bulk_create(documents_data, ordered=True, **kwargs)`

Create multiple documents in a single operation.

**Parameters:**
- `documents_data` (List[Dict[str, Any]]): List of document data
- `ordered` (bool): Whether to stop on first error (default: True)
- `**kwargs`: Additional Motor insert_many parameters

**Returns:** `List[Self]` - List of created document instances

**Raises:**
- `ValidationError`: If any document validation fails
- `DatabaseError`: If bulk insert fails
- `DuplicateKeyError`: If unique constraints are violated

**Example:**
```python
users_data = [
    {"name": "User 1", "email": "user1@example.com"},
    {"name": "User 2", "email": "user2@example.com"},
]

users = await User.bulk_create(users_data)
print(f"Created {len(users)} users")
```

##### `update_many(filter_dict, update_dict, upsert=False, **kwargs)`

Update multiple documents.

**Parameters:**
- `filter_dict` (Dict[str, Any]): Query filter
- `update_dict` (Dict[str, Any]): Update operations
- `upsert` (bool): Create document if none match (default: False)
- `**kwargs`: Additional Motor update_many parameters

**Returns:** `pymongo.results.UpdateResult` - Update operation result

**Raises:**
- `DatabaseError`: If update operation fails

**Example:**
```python
# Update all inactive users
result = await User.update_many(
    {"status": "inactive"},
    {"$set": {"status": "archived", "updated_at": datetime.utcnow()}}
)
print(f"Updated {result.modified_count} users")
```

##### `delete_many(filter_dict, **kwargs)`

Delete multiple documents.

**Parameters:**
- `filter_dict` (Dict[str, Any]): Query filter
- `**kwargs`: Additional Motor delete_many parameters

**Returns:** `pymongo.results.DeleteResult` - Delete operation result

**Raises:**
- `DatabaseError`: If delete operation fails

**Example:**
```python
# Delete all inactive users
result = await User.delete_many({"status": "inactive"})
print(f"Deleted {result.deleted_count} users")
```

#### Aggregation

##### `aggregate(pipeline, **kwargs)`

Execute an aggregation pipeline.

**Parameters:**
- `pipeline` (List[Dict[str, Any]]): Aggregation pipeline stages
- `**kwargs`: Additional Motor aggregate parameters

**Returns:** `List[Dict[str, Any]]` - Aggregation results

**Raises:**
- `DatabaseError`: If aggregation fails

**Example:**
```python
# Group users by status
pipeline = [
    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]

results = await User.aggregate(pipeline)
for result in results:
    print(f"Status {result['_id']}: {result['count']} users")
```

### Instance Methods

#### Field Access and Modification

##### `dict(exclude_unset=False, exclude_none=False, by_alias=False, **kwargs)`

Convert document to dictionary.

**Parameters:**
- `exclude_unset` (bool): Exclude fields that weren't explicitly set
- `exclude_none` (bool): Exclude fields with None values
- `by_alias` (bool): Use field aliases in output
- `**kwargs`: Additional Pydantic dict parameters

**Returns:** `Dict[str, Any]` - Document as dictionary

**Example:**
```python
user = User(name="John", email="john@example.com")
user_dict = user.dict()
user_dict_clean = user.dict(exclude_unset=True, exclude_none=True)
```

##### `json(exclude_unset=False, exclude_none=False, by_alias=False, **kwargs)`

Convert document to JSON string.

**Parameters:**
- `exclude_unset` (bool): Exclude fields that weren't explicitly set
- `exclude_none` (bool): Exclude fields with None values  
- `by_alias` (bool): Use field aliases in output
- `**kwargs`: Additional Pydantic json parameters

**Returns:** `str` - Document as JSON string

**Example:**
```python
user = User(name="John", email="john@example.com")
user_json = user.json()
user_json_clean = user.json(exclude_unset=True)
```

##### `copy(update=None, deep=False, **kwargs)`

Create a copy of the document.

**Parameters:**
- `update` (Optional[Dict[str, Any]]): Fields to update in the copy
- `deep` (bool): Whether to make a deep copy
- `**kwargs`: Additional Pydantic copy parameters

**Returns:** `Self` - Copy of the document

**Example:**
```python
user = User(name="John", email="john@example.com")
user_copy = user.copy()
user_updated = user.copy(update={"name": "Jane"})
```

**Example:**
```python
await User.__initialize__()
# or with custom client
client = AsyncIOMotorClient("mongodb://localhost:27017")
await User.__initialize__(client=client)
```

#### Query Methods

##### `get(**kwargs)`

Get a single document by filter criteria.

**Parameters:**
- `**kwargs`: Filter criteria as keyword arguments

**Returns:** `Optional[T]` - Model instance or None

**Raises:**
- `ModelNotInitializedError`: If model not initialized
- `ValidationError`: If query fails

**Example:**
```python
user = await User.get(email="john@example.com")
user = await User.get(name="John", is_active=True)
```

##### `get_by_id(doc_id)`

Get a document by its ID.

**Parameters:**
- `doc_id` (int): Document ID

**Returns:** `Optional[T]` - Model instance or None

**Example:**
```python
user = await User.get_by_id(123)
```

##### `filter(**kwargs)`

Filter documents with advanced options.

**Parameters:**
- `sort_by` (Optional[Dict[str, int]]): Sort criteria, default: `{id_field: 1}`
- `limit` (int): Maximum documents to return, default: 0 (no limit)
- `skip` (int): Number of documents to skip, default: 0
- `projection` (Optional[Dict[str, int]]): Fields to include/exclude
- `**kwargs`: Filter criteria

**Returns:** `List[Union[T, Dict[str, Any]]]` - List of instances or dicts

**Example:**
```python
# Basic filtering
users = await User.filter(is_active=True)

# With sorting and limiting
users = await User.filter(
    is_active=True,
    sort_by={"created_at": -1},
    limit=10
)

# With projection
users = await User.filter(
## Configuration

### DatabaseConfig

Configuration class for database connection settings.

```python
class DatabaseConfig:
    database_url: str
    database_name: str
    max_pool_size: int = 50
    min_pool_size: int = 5
    max_idle_time_ms: int = 30000
    connect_timeout_ms: int = 10000
    server_selection_timeout_ms: int = 30000
    write_concern_w: Union[int, str] = 1
    write_concern_j: bool = False
    read_preference: str = "primary"
```

**Attributes:**
- `database_url`: MongoDB connection string
- `database_name`: Target database name
- `max_pool_size`: Maximum connections in pool
- `min_pool_size`: Minimum connections to maintain
- `max_idle_time_ms`: Idle timeout for connections
- `connect_timeout_ms`: Connection timeout
- `server_selection_timeout_ms`: Server selection timeout
- `write_concern_w`: Write concern level
- `write_concern_j`: Journal writes requirement
- `read_preference`: Read preference setting

### Connection Management Functions

#### `configure_database(**config)`

Configure the global database connection.

**Parameters:**
- `**config`: Configuration parameters (see DatabaseConfig)

**Returns:** `None`

**Raises:**
- `ConnectionError`: If connection fails
- `ConfigurationError`: If configuration is invalid

#### `get_database_client()`

Get the current database client.

**Returns:** `motor.motor_asyncio.AsyncIOMotorClient`

**Raises:**
- `ConnectionError`: If no client is configured

#### `get_database()`

Get the current database instance.

**Returns:** `motor.motor_asyncio.AsyncIOMotorDatabase`

#### `close_database_connection()`

Close the database connection and cleanup resources.

**Returns:** `None`

## Exceptions

### Base Exception Classes

#### `MongoDBORMError`

Base exception for all MongoDB ORM errors.

```python
class MongoDBORMError(Exception):
    """Base exception class for MongoDB ORM."""
    pass
```

#### `ConfigurationError`

Raised when there are configuration issues.

```python
class ConfigurationError(MongoDBORMError):
    """Raised when there are configuration issues."""
    pass
```

#### `ConnectionError`

Raised when database connection fails.

```python
class ConnectionError(MongoDBORMError):
    """Raised when database connection fails."""
    pass
```

#### `ModelNotInitializedError`

Raised when attempting to use an uninitialized model.

```python
class ModelNotInitializedError(MongoDBORMError):
    """Raised when model is not properly initialized."""
    pass
```

#### `ValidationError`

Raised when document validation fails.

```python
class ValidationError(MongoDBORMError):
    """Raised when document validation fails."""
    pass
```

#### `DocumentNotFoundError`

Raised when a requested document is not found.

```python
class DocumentNotFoundError(MongoDBORMError):
    """Raised when a document is not found."""
    pass
```

#### `DuplicateKeyError`

Raised when a unique constraint is violated.

```python
class DuplicateKeyError(MongoDBORMError):
    """Raised when a unique constraint is violated."""
    pass
```

#### `DatabaseError`

Raised for general database operation errors.

```python
class DatabaseError(MongoDBORMError):
    """Raised for database operation errors."""
    pass
```

#### `IndexError`

Raised when index operations fail.

```python
class IndexError(MongoDBORMError):
    """Raised when index operations fail."""
    pass
```

## Utility Functions

### Data Validation and Conversion

#### `validate_object_id(value)`

Validate and convert ObjectId values.

**Parameters:**
- `value` (Union[str, ObjectId, None]): Value to validate

**Returns:** `Optional[ObjectId]` - Validated ObjectId or None

**Raises:**
- `ValidationError`: If value is not a valid ObjectId

**Example:**
```python
from br_mongodb_orm.utils import validate_object_id

# Valid ObjectId string
oid = validate_object_id("507f1f77bcf86cd799439011")

# Invalid ObjectId
try:
    oid = validate_object_id("invalid")
except ValidationError:
    print("Invalid ObjectId")
```

#### `to_object_id(value)`

Convert value to ObjectId.

**Parameters:**
- `value` (Union[str, ObjectId]): Value to convert

**Returns:** `ObjectId` - Converted ObjectId

**Raises:**
- `ValidationError`: If conversion fails

#### `ensure_indexes(model_class)`

Ensure indexes are created for a model.

**Parameters:**
- `model_class` (Type[Document]): Model class

**Returns:** `List[str]` - List of created index names

**Raises:**
- `IndexError`: If index creation fails

#### `parse_sort_parameter(sort)`

Parse sort parameter into MongoDB format.

**Parameters:**
- `sort` (Union[str, List[Tuple[str, int]], Dict[str, int]]): Sort specification

**Returns:** `List[Tuple[str, int]]` - Parsed sort specification

**Example:**
```python
from br_mongodb_orm.utils import parse_sort_parameter

# String format
sort_spec = parse_sort_parameter("name")  # [("name", 1)]
sort_spec = parse_sort_parameter("-created_at")  # [("created_at", -1)]

# List format
sort_spec = parse_sort_parameter([("name", 1), ("age", -1)])

# Dict format
sort_spec = parse_sort_parameter({"name": 1, "age": -1})
```

#### `build_projection(include=None, exclude=None)`

Build projection dictionary for MongoDB queries.

**Parameters:**
- `include` (Optional[List[str]]): Fields to include
- `exclude` (Optional[List[str]]): Fields to exclude

**Returns:** `Dict[str, int]` - Projection specification

**Raises:**
- `ValidationError`: If both include and exclude are specified

**Example:**
```python
from br_mongodb_orm.utils import build_projection

# Include specific fields
proj = build_projection(include=["name", "email"])  # {"name": 1, "email": 1}

# Exclude specific fields  
proj = build_projection(exclude=["password", "secret"])  # {"password": 0, "secret": 0}
```

### Query Helpers

#### `build_filter_from_kwargs(**kwargs)`

Build MongoDB filter from keyword arguments.

**Parameters:**
- `**kwargs`: Filter criteria

**Returns:** `Dict[str, Any]` - MongoDB filter

**Example:**
```python
from br_mongodb_orm.utils import build_filter_from_kwargs

# Simple filters
filter_dict = build_filter_from_kwargs(name="John", age=25)
# Result: {"name": "John", "age": 25}

# Range filters
filter_dict = build_filter_from_kwargs(age__gte=18, age__lt=65)
# Result: {"age": {"$gte": 18, "$lt": 65}}
```

#### `apply_operators(field, value)`

Apply MongoDB operators based on field name.

**Parameters:**
- `field` (str): Field name with optional operator suffix
- `value` (Any): Field value

**Returns:** `Tuple[str, Any]` - Processed field name and value

**Supported Operators:**
- `field__eq` → `{"field": value}`
- `field__ne` → `{"field": {"$ne": value}}`
- `field__gt` → `{"field": {"$gt": value}}`
- `field__gte` → `{"field": {"$gte": value}}`
- `field__lt` → `{"field": {"$lt": value}}`
- `field__lte` → `{"field": {"$lte": value}}`
- `field__in` → `{"field": {"$in": value}}`
- `field__nin` → `{"field": {"$nin": value}}`
- `field__regex` → `{"field": {"$regex": value}}`
- `field__exists` → `{"field": {"$exists": value}}`
- `field__size` → `{"field": {"$size": value}}`

### Logging Utilities

#### `get_logger(name)`

Get a configured logger instance.

**Parameters:**
- `name` (str): Logger name

**Returns:** `logging.Logger` - Configured logger

**Example:**
```python
from br_mongodb_orm.utils import get_logger

logger = get_logger(__name__)
logger.info("Operation completed")
```

#### `log_query(operation, filter_dict, execution_time)`

Log query execution details.

**Parameters:**
- `operation` (str): Operation name
- `filter_dict` (Dict[str, Any]): Query filter
- `execution_time` (float): Execution time in seconds

**Returns:** `None`

### Serialization Utilities

#### `serialize_document(doc)`

Serialize document for JSON output.

**Parameters:**
- `doc` (Dict[str, Any]): Document to serialize

**Returns:** `Dict[str, Any]` - Serialized document

**Handles:**
- ObjectId → string conversion
- datetime → ISO format string
- Decimal128 → float conversion

#### `deserialize_document(doc, model_class)`

Deserialize document from database.

**Parameters:**
- `doc` (Dict[str, Any]): Raw document from database
- `model_class` (Type[Document]): Target model class

**Returns:** `Document` - Deserialized model instance

**Raises:**
- `ValidationError`: If deserialization fails

## Type Definitions

### Core Types

```python
from typing import Union, List, Dict, Any, Optional, Tuple
from bson import ObjectId
from datetime import datetime

# Common type aliases
ObjectIdType = Union[str, ObjectId]
FilterDict = Dict[str, Any]
ProjectionDict = Dict[str, int]
SortSpec = List[Tuple[str, int]]
IndexDefinition = Union[str, Tuple[str, int], List[Tuple[str, int]], Dict[str, Any]]
```

### Index Types

```python
# Simple index (field, direction)
SimpleIndex = Tuple[str, int]

# Compound index
CompoundIndex = List[Tuple[str, int]]

# Advanced index with options
AdvancedIndex = Dict[str, Any]

# All possible index definitions
IndexDefinition = Union[SimpleIndex, CompoundIndex, AdvancedIndex]
```

### Query Types

```python
# Filter specification
FilterSpec = Dict[str, Any]

# Projection specification  
ProjectionSpec = Dict[str, int]

# Sort specification
SortSpec = List[Tuple[str, int]]

# Aggregation pipeline
Pipeline = List[Dict[str, Any]]
```

### Result Types

```python
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult

# Bulk operation results
BulkWriteResult = pymongo.results.BulkWriteResult
InsertManyResult = pymongo.results.InsertManyResult
UpdateResult = pymongo.results.UpdateResult
DeleteResult = pymongo.results.DeleteResult
```

## Constants

### Default Values

```python
# Connection defaults
DEFAULT_MAX_POOL_SIZE = 50
DEFAULT_MIN_POOL_SIZE = 5
DEFAULT_CONNECT_TIMEOUT_MS = 10000
DEFAULT_SERVER_SELECTION_TIMEOUT_MS = 30000
DEFAULT_MAX_IDLE_TIME_MS = 30000

# Write concern defaults
DEFAULT_WRITE_CONCERN_W = 1
DEFAULT_WRITE_CONCERN_J = False

# Read preference options
READ_PREFERENCES = [
    "primary",
    "primaryPreferred", 
    "secondary",
    "secondaryPreferred",
    "nearest"
]
```

### MongoDB Operators

```python
# Comparison operators
COMPARISON_OPERATORS = {
    "eq": "$eq",
    "ne": "$ne", 
    "gt": "$gt",
    "gte": "$gte",
    "lt": "$lt",
    "lte": "$lte",
    "in": "$in",
    "nin": "$nin"
}

# Logical operators
LOGICAL_OPERATORS = {
    "and": "$and",
    "or": "$or", 
    "not": "$not",
    "nor": "$nor"
}

# Element operators
ELEMENT_OPERATORS = {
    "exists": "$exists",
    "type": "$type"
}

# Array operators
ARRAY_OPERATORS = {
    "all": "$all",
    "elemMatch": "$elemMatch",
    "size": "$size"
}
```

### Index Types

```python
# Index directions
INDEX_ASCENDING = 1
INDEX_DESCENDING = -1

# Special index types
INDEX_TEXT = "text"
INDEX_2D = "2d"
INDEX_2DSPHERE = "2dsphere"
INDEX_HASHED = "hashed"
```

## Complete Usage Example

Here's a comprehensive example showing all the major features:

```python
import asyncio
from datetime import datetime
from typing import List, Optional
from br_mongodb_orm import Document, configure_database
from br_mongodb_orm.utils import get_logger
from pydantic import Field, validator

# Configure logging
logger = get_logger(__name__)

# Define models
class User(Document):
    # Basic fields
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    age: Optional[int] = Field(None, ge=0, le=150)
    
    # Complex fields
    tags: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    
    # Model configuration
    class Config:
        collection_name = "users"
        auto_index = True
        indexes = [
            ("email", 1),  # Simple index
            [("name", 1), ("age", -1)],  # Compound index
            {
                "key": [("email", 1)],
                "unique": True,
                "background": True
            }
        ]
    
    # Custom validators
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()
    
    @validator('tags')
    def tags_must_be_unique(cls, v):
        return list(set(v))

class Post(Document):
    title: str
    content: str
    author_id: str
    published: bool = False
    
    class Config:
        collection_name = "posts"
        indexes = [
            ("author_id", 1),
            ("published", 1),
            [("published", 1), ("created_at", -1)]
        ]

async def main():
    # Configure database
    await configure_database(
        database_url="mongodb://localhost:27017",
        database_name="blog_app",
        max_pool_size=100
    )
    
    # Create indexes
    await User.create_indexes()
    await Post.create_indexes()
    
    # Create a user
    user = User(
        name="John Doe",
        email="JOHN@EXAMPLE.COM",  # Will be lowercased
        age=30,
        tags=["developer", "python", "developer"],  # Duplicates will be removed
        metadata={"location": "NYC", "timezone": "EST"}
    )
    
    saved_user = await user.save()
    logger.info(f"Created user: {saved_user.id}")
    
    # Create posts
    posts_data = [
        {
            "title": "First Post",
            "content": "Hello world!",
            "author_id": str(saved_user.id),
            "published": True
        },
        {
            "title": "Draft Post", 
            "content": "This is a draft",
            "author_id": str(saved_user.id),
            "published": False
        }
    ]
    
    posts = await Post.bulk_create(posts_data)
    logger.info(f"Created {len(posts)} posts")
    
    # Query examples
    
    # Find user by email
    found_user = await User.find_one({"email": "john@example.com"})
    
    # Find users with projection
    users = await User.find(
        filter_dict={"age": {"$gte": 18}},
        projection={"name": 1, "email": 1},
        sort=[("created_at", -1)],
        limit=10
    )
    
    # Count documents
    total_users = await User.count_documents()
    adult_users = await User.count_documents({"age": {"$gte": 18}})
    
    # Aggregation
    user_stats = await User.aggregate([
        {"$group": {
            "_id": None,
            "avg_age": {"$avg": "$age"},
            "total_users": {"$sum": 1}
        }}
    ])
    
    # Update operations
    await User.update_many(
        {"age": {"$lt": 18}},
        {"$set": {"tags": ["minor"]}}
    )
    
    # Find published posts by user
    published_posts = await Post.find({
        "author_id": str(saved_user.id),
        "published": True
    })
    
    # Cleanup (optional)
    await User.delete_many({"email": "john@example.com"})
    await Post.delete_many({"author_id": str(saved_user.id)})
    
    logger.info("Example completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive API reference covers all aspects of the MongoDB ORM library, providing complete details about every method, parameter, return type, and exception that users might encounter.

Create and save a new document.

**Parameters:**
- `**kwargs`: Document data

**Returns:** `T` - Created model instance

**Raises:**
- `ValidationError`: If document creation fails
- `DuplicateDocumentError`: If document with same ID exists

**Example:**
```python
user = await User.create(
    name="John Doe",
    email="john@example.com",
    age=30
)
```

##### `get_or_create(defaults=None, **kwargs)`

Get existing document or create new one.

**Parameters:**
- `defaults` (Optional[Dict[str, Any]]): Default values for creation
- `**kwargs`: Filter criteria for existing document

**Returns:** `tuple[T, bool]` - (instance, created) where created is True if new

**Example:**
```python
user, created = await User.get_or_create(
    email="john@example.com",
    defaults={"name": "John Doe", "age": 30}
)
```

##### `bulk_create(documents, ordered=True)`

Create multiple documents at once.

**Parameters:**
- `documents` (List[Dict[str, Any]]): List of document data
- `ordered` (bool): Stop on first error if True, default: True

**Returns:** `List[T]` - List of created instances

**Example:**
```python
users_data = [
    {"name": "John", "email": "john@example.com"},
    {"name": "Jane", "email": "jane@example.com"}
]
users = await User.bulk_create(users_data)
```

#### Deletion Methods

##### `delete_many(**kwargs)`

Delete multiple documents.

**Parameters:**
- `**kwargs`: Filter criteria

**Returns:** `int` - Number of deleted documents

**Example:**
```python
deleted_count = await User.delete_many(is_active=False)
```

#### Aggregation Methods

##### `aggregate(pipeline)`

Perform aggregation query.

**Parameters:**
- `pipeline` (List[Dict[str, Any]]): MongoDB aggregation pipeline

**Returns:** `List[Dict[str, Any]]` - Aggregation results

**Example:**
```python
pipeline = [
    {"$match": {"is_active": True}},
    {"$group": {"_id": "$role", "count": {"$sum": 1}}}
]
results = await User.aggregate(pipeline)
```

#### Index Methods

##### `create_index(field, unique=False, direction=1)`

Create index on a field.

**Parameters:**
- `field` (str): Field name
- `unique` (bool): Whether index should be unique, default: False
- `direction` (int): Index direction (1 or -1), default: 1

**Returns:** `bool` - True if created, False if already exists

**Example:**
```python
await User.create_index("email", unique=True)
await User.create_index("created_at", direction=-1)
```

##### `create_compound_index(fields, unique=False)`

Create compound index on multiple fields.

**Parameters:**
- `fields` (Dict[str, int]): Field names and directions
- `unique` (bool): Whether index should be unique, default: False

**Returns:** `bool` - True if created, False if already exists

**Example:**
```python
await User.create_compound_index({
    "role": 1,
    "is_active": 1,
    "created_at": -1
})
```

##### `drop_index(index_name)`

Drop an index.

**Parameters:**
- `index_name` (str): Name of index to drop

**Returns:** `bool` - True if dropped successfully

**Example:**
```python
await User.drop_index("email_1")
```

##### `list_indexes()`

List all indexes for the collection.

**Returns:** `Dict[str, Any]` - Index information

**Example:**
```python
indexes = await User.list_indexes()
```

#### Connection Methods

##### `close_connections()`

Close all database connections for this model.

**Returns:** `None`

**Example:**
```python
await User.close_connections()
```

### Instance Methods

#### Data Methods

##### `model_dump(**kwargs)`

Export model data as dictionary.

**Parameters:**
- `**kwargs`: Additional parameters for Pydantic model_dump

**Returns:** `Dict[str, Any]` - Model data

**Example:**
```python
user_data = user.model_dump()
user_data_partial = user.model_dump(include={"name", "email"})
```

##### `dict()`

Legacy method for compatibility.

**Returns:** `Dict[str, Any]` - Model data

##### `json()`

Legacy method for compatibility.

**Returns:** `str` - JSON string

#### Persistence Methods

##### `save(only_update=False)`

Save the instance to database.

**Parameters:**
- `only_update` (bool): Only update existing documents, default: False

**Returns:** `BaseModel` - Self instance

**Raises:**
- `ValidationError`: If save fails
- `DocumentNotFoundError`: If only_update=True and document not found

**Example:**
```python
user.name = "Updated Name"
await user.save()

# Only update existing
await user.save(only_update=True)
```

##### `delete()`

Delete the current document.

**Returns:** `bool` - True if deleted successfully

**Raises:**
- `DocumentNotFoundError`: If document has no ID
- `ValidationError`: If delete fails

**Example:**
```python
deleted = await user.delete()
```

##### `refresh_from_db()`

Refresh instance with data from database.

**Returns:** `Optional[BaseModel]` - Self if refreshed, None if not found

**Example:**
```python
refreshed = await user.refresh_from_db()
```

#### Utility Methods

##### `__repr__()`

String representation of the instance.

**Returns:** `str`

**Example:**
```python
print(user)  # <User(id=123)>
```

##### `__str__()`

String representation of the instance.

**Returns:** `str`

## Configuration Classes

### DatabaseConfig

Configuration for database connection.

```python
@dataclass
class DatabaseConfig:
    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "default_db"
    max_pool_size: int = 100
    min_pool_size: int = 0
    server_selection_timeout_ms: int = 5000
    connect_timeout_ms: int = 10000
    socket_timeout_ms: int = 5000
    retry_writes: bool = True
```

#### Methods

##### `to_motor_kwargs()`

Convert config to Motor client kwargs.

**Returns:** `Dict[str, Any]`

### ModelConfig

Configuration for model behavior.

```python
@dataclass
class ModelConfig:
    collection_name: Optional[str] = None
    auto_create_indexes: bool = True
    strict_mode: bool = True
    use_auto_id: bool = True
    id_field: str = "id"
```

## Connection Management

### ConnectionManager

Manages MongoDB connections with pooling and cleanup.

#### Methods

##### `get_instance()`

Get singleton instance.

**Returns:** `ConnectionManager`

**Example:**
```python
manager = await ConnectionManager.get_instance()
```

##### `get_client(config)`

Get or create client for configuration.

**Parameters:**
- `config` (DatabaseConfig): Database configuration

**Returns:** `AsyncIOMotorClient`

##### `get_database(config)`

Get or create database for configuration.

**Parameters:**
- `config` (DatabaseConfig): Database configuration

**Returns:** `AsyncIOMotorDatabase`

##### `close_all()`

Close all connections.

**Returns:** `None`

## Exceptions

### Exception Hierarchy

```
MongoDBORMError
├── ConnectionError
├── ModelNotInitializedError
├── ValidationError
├── DocumentNotFoundError
├── DuplicateDocumentError
└── ConfigurationError
```

### MongoDBORMError

Base exception for all MongoDB ORM errors.

### ConnectionError

Raised when connection to MongoDB fails.

### ModelNotInitializedError

Raised when using uninitialized model.

### ValidationError

Raised when model validation fails.

### DocumentNotFoundError

Raised when document is not found.

### DuplicateDocumentError

Raised when creating duplicate document.

### ConfigurationError

Raised when configuration is invalid.

## Utility Functions

### Model Registration

#### `register_model(cls, client=None, db_config=None)`

Register a single model.

**Parameters:**
- `cls` (Type): Model class
- `client` (Optional[AsyncIOMotorClient]): Pre-configured client
- `db_config` (Optional[DatabaseConfig]): Database configuration

**Returns:** `bool` - True if successful

#### `register_models(classes, client=None, db_config=None)`

Register multiple models.

**Parameters:**
- `classes` (List[Type]): List of model classes
- `client` (Optional[AsyncIOMotorClient]): Pre-configured client
- `db_config` (Optional[DatabaseConfig]): Database configuration

**Returns:** `List[bool]` - Results for each model

#### `register_all_models(module_name, client=None, db_config=None)`

Register all models in a module.

**Parameters:**
- `module_name` (str): Module name (usually `__name__`)
- `client` (Optional[AsyncIOMotorClient]): Pre-configured client
- `db_config` (Optional[DatabaseConfig]): Database configuration

**Returns:** `List[bool]` - Results for each model

### Connection Utilities

#### `close_all_connections()`

Close all database connections.

**Returns:** `None`

#### `health_check(client=None, db_config=None)`

Perform database health check.

**Parameters:**
- `client` (Optional[AsyncIOMotorClient]): Client to test
- `db_config` (Optional[DatabaseConfig]): Database configuration

**Returns:** `bool` - True if healthy

### Development Utilities

#### `setup_logging(level="INFO")`

Setup logging configuration.

**Parameters:**
- `level` (str): Logging level

**Returns:** `None`

#### `current_datetime()`

Get current UTC datetime.

**Returns:** `datetime`

#### `create_test_data(model_class, count=10, data_factory=None)`

Create test data for a model.

**Parameters:**
- `model_class` (Type): Model class
- `count` (int): Number of test documents
- `data_factory` (Optional[callable]): Function to generate test data

**Returns:** `List[Any]` - Created instances

## Type Definitions

### Type Variables

```python
T = TypeVar('T', bound='BaseModel')          # Generic model type
ModelType = TypeVar('ModelType', bound='BaseModel')
```

### Common Types

```python
DocumentType = Dict[str, Any]               # MongoDB document
FilterType = Dict[str, Any]                 # Filter criteria
ProjectionType = Dict[str, int]             # Projection specification
SortType = Dict[str, int]                   # Sort specification
PipelineType = List[Dict[str, Any]]         # Aggregation pipeline
```

### Result Types

```python
QueryResult = Union[ModelType, None]        # Single query result
QueryResults = List[ModelType]              # Multiple query results
AggregationResult = List[DocumentType]      # Aggregation results
BulkResult = List[ModelType]                # Bulk operation results
CountResult = int                           # Count result
DistinctResult = List[Any]                  # Distinct values result
```

---

**Previous:** [Migration Guide](15-migration-guide.md) | **Next:** [Examples](17-examples.md)
