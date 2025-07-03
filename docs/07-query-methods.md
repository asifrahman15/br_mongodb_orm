# Query Methods

MongoDB ORM provides a comprehensive set of query methods for finding, filtering, and retrieving documents from your MongoDB collections.

## Table of Contents

- [Overview](#overview)
- [Basic Query Methods](#basic-query-methods)
- [Filtering and Sorting](#filtering-and-sorting)
- [Pagination](#pagination)
- [Advanced Queries](#advanced-queries)
- [Query Performance](#query-performance)
- [Examples](#examples)

## Overview

All query methods are asynchronous and return properly typed model instances. The query system supports:

- **Simple Queries**: Direct field matching
- **Complex Filters**: Multiple conditions, operators
- **Sorting**: Single and multi-field sorting
- **Pagination**: Limit, skip, and cursor-based pagination
- **Aggregation**: Complex data processing pipelines

## Basic Query Methods

### get(**kwargs)

Find a single document matching the criteria:

```python
# Get user by email
user = await User.get(email="john@example.com")

# Get with multiple conditions
user = await User.get(name="John", is_active=True)

# Returns None if not found
user = await User.get(email="nonexistent@example.com")
```

**Parameters:**
- `**kwargs`: Field-value pairs for filtering

**Returns:** `Optional[T]` - Model instance or None

### get_by_id(doc_id)

Find a document by its ID:

```python
user = await User.get_by_id(123)
product = await Product.get_by_id(456)
```

**Parameters:**
- `doc_id` (int): Document ID

**Returns:** `Optional[T]` - Model instance or None

### all()

Get all documents in the collection:

```python
all_users = await User.all()
all_products = await Product.all()
```

**Returns:** `List[T]` - List of all model instances

### count(**kwargs)

Count documents matching criteria:

```python
# Count all users
total_users = await User.count()

# Count active users
active_count = await User.count(is_active=True)

# Count with multiple conditions
admin_count = await User.count(role="admin", is_active=True)
```

**Parameters:**
- `**kwargs`: Field-value pairs for filtering

**Returns:** `int` - Number of matching documents

## Filtering and Sorting

### filter()

Advanced filtering with sorting and pagination:

```python
# Basic filtering
users = await User.filter(is_active=True)

# With sorting (ascending)
users = await User.filter(
    is_active=True,
    sort_by={"name": 1}
)

# With sorting (descending by creation date)
users = await User.filter(
    sort_by={"created_at": -1}
)

# With multiple sort fields
users = await User.filter(
    sort_by={"role": 1, "name": 1}
)

# With pagination
users = await User.filter(
    is_active=True,
    sort_by={"name": 1},
    limit=10,
    skip=20
)
```

**Parameters:**
- `sort_by` (Optional[Dict[str, int]]): Sort criteria (`1` for ascending, `-1` for descending)
- `limit` (Optional[int]): Maximum number of results
- `skip` (Optional[int]): Number of documents to skip
- `**kwargs`: Field-value pairs for filtering

**Returns:** `List[T]` - List of matching model instances

### MongoDB Query Operators

Use MongoDB operators for advanced filtering:

```python
# Greater than
products = await Product.filter(price={"$gt": 100})

# Range query
products = await Product.filter(
    price={"$gte": 50, "$lte": 200}
)

# In list
users = await User.filter(
    role={"$in": ["admin", "moderator"]}
)

# Not equal
users = await User.filter(
    status={"$ne": "deleted"}
)

# Regex matching
users = await User.filter(
    email={"$regex": r".*@company\.com$", "$options": "i"}
)

# Array contains
posts = await Post.filter(
    tags={"$in": ["python", "mongodb"]}
)
```

## Pagination

### Simple Pagination

```python
# Page 1: First 10 users
page1 = await User.filter(limit=10, skip=0)

# Page 2: Next 10 users  
page2 = await User.filter(limit=10, skip=10)

# Page 3: Next 10 users
page3 = await User.filter(limit=10, skip=20)
```

### Pagination Helper Function

```python
async def paginate_users(page: int, page_size: int = 10):
    """Get paginated users"""
    skip = (page - 1) * page_size
    users = await User.filter(
        sort_by={"created_at": -1},
        limit=page_size,
        skip=skip
    )
    total = await User.count()
    
    return {
        "users": users,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size
    }

# Usage
result = await paginate_users(page=2, page_size=20)
```

### Cursor-Based Pagination

For better performance with large datasets:

```python
async def get_users_after(last_id: Optional[int] = None, limit: int = 10):
    """Get users after a specific ID (cursor-based pagination)"""
    query = {}
    if last_id:
        query["id"] = {"$gt": last_id}
    
    return await User.filter(
        sort_by={"id": 1},
        limit=limit,
        **query
    )

# Usage
# First page
first_batch = await get_users_after(limit=10)

# Next page using last ID from previous batch
if first_batch:
    last_id = first_batch[-1].id
    next_batch = await get_users_after(last_id=last_id, limit=10)
```

## Advanced Queries

### distinct()

Get distinct values for a field:

```python
# Get all unique roles
roles = await User.distinct("role")

# Get unique categories for active products
categories = await Product.distinct(
    "category", 
    is_active=True
)
```

**Parameters:**
- `field` (str): Field name to get distinct values for
- `**kwargs`: Filter criteria

**Returns:** `List[Any]` - List of distinct values

### Complex Filtering

```python
# Multiple conditions with operators
users = await User.filter(
    age={"$gte": 18, "$lte": 65},
    role={"$in": ["user", "premium"]},
    is_active=True,
    sort_by={"last_login": -1}
)

# Date range queries
from datetime import datetime, timedelta

last_week = datetime.now() - timedelta(days=7)
recent_users = await User.filter(
    created_at={"$gte": last_week},
    sort_by={"created_at": -1}
)

# Text search (requires text index)
users = await User.filter(
    {"$text": {"$search": "john smith"}}
)
```

### Nested Field Queries

```python
# Query nested document fields
users = await User.filter(
    {"profile.address.city": "New York"}
)

# Query array elements
posts = await Post.filter(
    {"comments.author": "john"}
)
```

## Query Performance

### Indexing for Queries

Create indexes for commonly queried fields:

```python
class User(BaseModel):
    name: str
    email: str
    age: int
    role: str
    
    class Meta:
        auto_create_indexes = True

# Create additional indexes for performance
await User.create_index("email", unique=True)
await User.create_index("role")
await User.create_compound_index({"role": 1, "age": 1})
```

### Query Optimization Tips

1. **Use Indexes**: Always index frequently queried fields
2. **Limit Results**: Use `limit` to avoid large result sets
3. **Project Fields**: Only select needed fields (use aggregation)
4. **Avoid Skip**: Use cursor-based pagination for large offsets
5. **Use Compound Indexes**: For multi-field queries

### Performance Monitoring

```python
import time

async def time_query(query_func, *args, **kwargs):
    """Measure query execution time"""
    start = time.time()
    result = await query_func(*args, **kwargs)
    duration = time.time() - start
    print(f"Query took {duration:.3f} seconds")
    return result

# Usage
users = await time_query(
    User.filter,
    is_active=True,
    sort_by={"name": 1},
    limit=100
)
```

## Examples

### User Management Queries

```python
class User(BaseModel):
    name: str
    email: str
    age: int
    role: str
    is_active: bool
    last_login: Optional[datetime] = None

# Get all admin users
admins = await User.filter(role="admin")

# Get active users sorted by name
active_users = await User.filter(
    is_active=True,
    sort_by={"name": 1}
)

# Get recent users (last 30 days)
thirty_days_ago = datetime.now() - timedelta(days=30)
recent_users = await User.filter(
    created_at={"$gte": thirty_days_ago},
    sort_by={"created_at": -1}
)

# Get users by age range
young_adults = await User.filter(
    age={"$gte": 18, "$lt": 25},
    is_active=True
)

# Search users by email domain
company_users = await User.filter(
    email={"$regex": r".*@company\.com$"}
)
```

### E-commerce Queries

```python
class Product(BaseModel):
    name: str
    price: float
    category: str
    tags: List[str]
    in_stock: bool
    rating: float

# Get products by category, sorted by rating
electronics = await Product.filter(
    category="electronics",
    in_stock=True,
    sort_by={"rating": -1}
)

# Get products in price range
affordable_products = await Product.filter(
    price={"$gte": 10, "$lte": 100},
    in_stock=True,
    sort_by={"price": 1}
)

# Get highly rated products
top_rated = await Product.filter(
    rating={"$gte": 4.5},
    in_stock=True,
    sort_by={"rating": -1},
    limit=20
)

# Search products by tags
python_products = await Product.filter(
    tags={"$in": ["python", "programming"]},
    sort_by={"rating": -1}
)
```

### Blog/Content Queries

```python
class Post(BaseModel):
    title: str
    content: str
    author_id: int
    tags: List[str]
    published: bool
    views: int

# Get published posts by author
author_posts = await Post.filter(
    author_id=123,
    published=True,
    sort_by={"created_at": -1}
)

# Get popular posts
popular_posts = await Post.filter(
    published=True,
    views={"$gte": 1000},
    sort_by={"views": -1},
    limit=10
)

# Get posts by multiple tags
tech_posts = await Post.filter(
    tags={"$all": ["technology", "programming"]},
    published=True,
    sort_by={"created_at": -1}
)

# Get recent posts with pagination
recent_posts = await Post.filter(
    published=True,
    sort_by={"created_at": -1},
    limit=20,
    skip=0
)
```

### Analytics Queries

```python
class Event(BaseModel):
    user_id: int
    event_type: str
    properties: Dict[str, Any]
    timestamp: datetime

# Get events for a user
user_events = await Event.filter(
    user_id=123,
    sort_by={"timestamp": -1}
)

# Get events by type in date range
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 31)

login_events = await Event.filter(
    event_type="login",
    timestamp={"$gte": start_date, "$lte": end_date},
    sort_by={"timestamp": 1}
)

# Get unique event types
event_types = await Event.distinct("event_type")

# Count events by type
login_count = await Event.count(event_type="login")
signup_count = await Event.count(event_type="signup")
```
