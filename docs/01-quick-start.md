# Quick Start Guide

Get up and running with MongoDB ORM in minutes!

## Installation

```bash
pip install mongodb_orm
```

## Basic Setup

### 1. Environment Configuration

Set your MongoDB connection details:

```bash
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DATABASE="my_app_db"
```

### 2. Define Your First Model

```python
# models.py
import asyncio
from datetime import datetime
from typing import Optional, List
from mongodb_orm import BaseModel, register_all_models

class User(BaseModel):
    # Required fields
    name: str
    email: str
    
    # Optional fields with defaults
    age: Optional[int] = None
    is_active: bool = True
    tags: List[str] = []
    
    # created_at and updated_at are automatically added!

# Initialize models
async def setup():
    await register_all_models(__name__)

asyncio.run(setup())
```

### 3. Basic Operations

```python
# app.py
import asyncio
from models import User

async def main():
    # Create a user
    user = await User.create(
        name="Alice Johnson",
        email="alice@example.com",
        age=28,
        tags=["developer", "python"]
    )
    print(f"Created: {user}")
    
    # Find user by ID
    found_user = await User.get_by_id(user.id)
    print(f"Found: {found_user}")
    
    # Update user
    found_user.age = 29
    await found_user.save()
    print(f"Updated age: {found_user.age}")
    
    # Query users
    active_users = await User.filter(is_active=True)
    print(f"Active users: {len(active_users)}")
    
    # Delete user
    await user.delete()
    print("User deleted")

asyncio.run(main())
```

## That's It!

You now have a fully functional MongoDB ORM setup with:

- ✅ Automatic ID generation
- ✅ Timestamp tracking (`created_at`, `updated_at`)
- ✅ Type validation with Pydantic
- ✅ Async operations
- ✅ Error handling
- ✅ Connection management

## What's Automatically Provided

Every model gets these features without any configuration:

1. **Auto-incrementing ID field** (`id`)
2. **Timestamp fields** (`created_at`, `updated_at`)
3. **Collection name** (derived from class name: `User` → `users`)
4. **Database indexes** (automatically created on ID and timestamp fields)
5. **Connection pooling** and cleanup
6. **Type validation** and serialization
7. **Error handling** with meaningful exceptions

## Next Steps

- [Learn about model definition](03-model-definition.md)
- [Explore CRUD operations](06-crud-operations.md)
- [Check out query methods](07-query-methods.md)
- [See complete examples](17-examples.md)

---

**Previous:** [Documentation Home](README.md) | **Next:** [Installation & Setup](02-installation.md)
