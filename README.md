# MongoDB ORM

A modern, async MongoDB Object-Relational Mapping library for Python, built on top of Motor and Pydantic.

## About This Project

This is an improved and enhanced version of the original [mongodb_orm](https://github.com/jarvisinfinity/mongodb_orm) project. This fork includes significant improvements, bug fixes, and new features to provide a more robust and user-friendly MongoDB ORM experience.

## Features

- ✨ **Fully Async**: Built from the ground up with async/await support
- 🔒 **Type Safe**: Leverages Pydantic for robust data validation and type hints
- 🚀 **High Performance**: Uses Motor for efficient async MongoDB operations
- 🛡️ **Error Handling**: Comprehensive exception handling with custom exception types
- 🔧 **Flexible Configuration**: Environment-based configuration with sensible defaults
- 📊 **Connection Management**: Automatic connection pooling and cleanup
- 🗃️ **Rich Query API**: Intuitive methods for CRUD operations and aggregations
- 📈 **Indexing Support**: Easy index creation and management
- 🧪 **Testing Utilities**: Built-in utilities for testing and development

## Installation

```bash
pip install br_mongodb_orm
```

For development dependencies:
```bash
pip install br_mongodb_orm[dev]
```

## Quick Start

### 1. Environment Setup

Set your MongoDB connection details:

```bash
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DATABASE="my_app_db"
```

### 2. Define Your Models

```python
import asyncio
from datetime import datetime
from typing import Optional
from br_mongodb_orm import BaseModel, register_all_models

# Simple models - no Meta class required!
class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
    # created_at and updated_at are automatically added

class BlogPost(BaseModel):
    title: str
    content: str
    author_id: int
    tags: list[str] = []
    published: bool = False
    # Collection name will be "blog_post" automatically

# Optional: Use Meta class only if you need custom settings
class CustomModel(BaseModel):
    name: str

    class Meta:
        collection_name = "my_custom_collection"  # Override default
        auto_create_indexes = False  # Disable auto-indexing

# Register all models
async def setup_models():
    await register_all_models(__name__)

asyncio.run(setup_models())
```

**Key Benefits:**
- ✅ **No Meta class required** for basic usage
- ✅ **Auto-generated collection names** (User → "user", BlogPost → "blog_post")
- ✅ **Automatic index creation** enabled by default
- ✅ **Smart naming conversion** (CamelCase → snake_case)

### 3. Basic Operations

```python
async def main():
    # Create a new user (collection "user" created automatically)
    user = await User.create(
        name="John Doe",
        email="john@example.com",
        age=30
    )
    print(f"Created user: {user}")

    # Get user by ID
    found_user = await User.get_by_id(user.id)

    # Update user
    found_user.age = 31
    await found_user.save()

    # Query users (returns async cursor for memory efficiency)
    async for user in User.filter(is_active=True):
        print(f"Active user: {user.name}")

    # Or convert to list if needed
    active_users = await User.filter(is_active=True).to_list()

    # Create a blog post (collection "blog_post" created automatically)
    post = await BlogPost.create(
        title="My First Post",
        content="This is the content of my first post.",
        author_id=user.id,
        tags=["introduction", "first-post"],
        published=True
    )

    # Get posts by author (memory-efficient iteration)
    async for post in BlogPost.filter(author_id=user.id):
        print(f"Post: {post.title}")

    # Or get as list
    user_posts = await BlogPost.filter(author_id=user.id).to_list()

    # Delete post
    await post.delete()

asyncio.run(main())
```

**What happens automatically:**
- ✅ Collections are created with smart names
- ✅ Indexes are created on id, created_at, updated_at fields
- ✅ Timestamps are managed automatically
- ✅ Data validation with Pydantic

## Advanced Usage

### Automatic Collection Naming

The ORM automatically converts your class names to collection names using snake_case:

```python
class User(BaseModel):          # → collection: "user"
    pass

class BlogPost(BaseModel):      # → collection: "blog_post"
    pass

class ShoppingCart(BaseModel):  # → collection: "shopping_cart"
    pass

class APIKey(BaseModel):        # → collection: "api_key"
    pass

class XMLDocument(BaseModel):   # → collection: "xml_document"
    pass
```

### Custom Configuration

Only use Meta class when you need to override defaults:

```python
class User(BaseModel):
    name: str
    email: str

    class Meta:
        collection_name = "users"           # Override auto-generated name
        auto_create_indexes = False         # Disable automatic indexing
        strict_mode = True                  # Enable strict validation
        use_auto_id = True                  # Use auto-increment IDs
        id_field = "user_id"               # Custom ID field name
```

## Requirements

- Python 3.8+
- motor>=3.5.1
- pydantic>=2.8.2
- pymongo>=4.0.0

## License

MIT License