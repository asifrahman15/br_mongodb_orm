# Model Definition

Complete guide to defining MongoDB models with MongoDB ORM.

## Table of Contents

- [Basic Model Definition](#basic-model-definition)
- [Field Types](#field-types)
- [Field Validation](#field-validation)
- [Default Values](#default-values)
- [Meta Configuration](#meta-configuration)
- [Inheritance](#inheritance)
- [Custom Methods](#custom-methods)
- [Model Validation](#model-validation)

## Basic Model Definition

### Minimal Model

```python
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
```

This automatically provides:
- `id`: Auto-incrementing integer ID
- `created_at`: Timestamp when document was created
- `updated_at`: Timestamp when document was last modified
- Collection name: `"user"` (derived from class name)

### Model with Optional Fields

```python
from typing import Optional, List
from py_mongo_orm import BaseModel

class User(BaseModel):
    # Required fields
    name: str
    email: str
    
    # Optional fields
    age: Optional[int] = None
    bio: Optional[str] = None
    tags: List[str] = []
    is_active: bool = True
```

## Field Types

### Basic Types

```python
from typing import Optional, List, Dict, Union
from datetime import datetime, date
from decimal import Decimal
from py_mongo_orm import BaseModel

class Product(BaseModel):
    # String types
    name: str
    description: Optional[str] = None
    
    # Numeric types
    price: float
    quantity: int
    discount: Optional[Decimal] = None
    
    # Boolean
    is_available: bool = True
    
    # Date and time
    release_date: Optional[date] = None
    last_stocked: Optional[datetime] = None
    
    # Collections
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    categories: List[int] = []
    
    # Union types
    identifier: Union[str, int]
```

### Pydantic Field Types

```python
from pydantic import Field, EmailStr, HttpUrl, UUID4
from typing import Annotated
from py_mongo_orm import BaseModel

class User(BaseModel):
    # Email validation
    email: EmailStr
    
    # URL validation
    website: Optional[HttpUrl] = None
    
    # UUID
    external_id: Optional[UUID4] = None
    
    # String with constraints
    username: Annotated[str, Field(min_length=3, max_length=50)]
    
    # Number with constraints
    age: Annotated[int, Field(ge=0, le=150)]
    
    # List with constraints
    tags: Annotated[List[str], Field(max_items=10)]
```

### Custom Field Types

```python
from typing import NewType
from enum import Enum
from py_mongo_orm import BaseModel

# Enum types
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# Custom types
UserId = NewType('UserId', int)

class User(BaseModel):
    name: str
    status: UserStatus = UserStatus.ACTIVE
    friend_ids: List[UserId] = []
```

## Field Validation

### Built-in Validators

```python
from pydantic import Field, validator, root_validator
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=150)
    password: str = Field(..., min_length=8)
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip().title()
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
    
    @root_validator
    def validate_age_email(cls, values):
        age = values.get('age')
        email = values.get('email')
        
        if age and age < 13 and email:
            raise ValueError('Users under 13 cannot have email')
        
        return values
```

### Custom Validators

```python
from typing import Any
from pydantic import validator
from py_mongo_orm import BaseModel

class Post(BaseModel):
    title: str
    content: str
    author_id: int
    
    @validator('title')
    def title_validation(cls, v: str) -> str:
        """Custom title validation"""
        if len(v.split()) < 2:
            raise ValueError('Title must contain at least 2 words')
        return v.strip()
    
    @validator('content')
    def content_validation(cls, v: str) -> str:
        """Custom content validation"""
        if len(v) < 10:
            raise ValueError('Content must be at least 10 characters')
        if 'spam' in v.lower():
            raise ValueError('Content cannot contain spam')
        return v
```

## Default Values

### Static Defaults

```python
from datetime import datetime, UTC
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    is_active: bool = True
    signup_date: datetime = datetime.now(UTC)
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
```

### Dynamic Defaults

```python
from pydantic import Field
from py_mongo_orm import BaseModel, current_datetime

class User(BaseModel):
    name: str
    email: str
    
    # Dynamic timestamp
    signup_date: datetime = Field(default_factory=current_datetime)
    
    # Dynamic list (avoid mutable default)
    tags: List[str] = Field(default_factory=list)
    
    # Dynamic dict
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Custom factory
    unique_code: str = Field(default_factory=lambda: f"user_{uuid4().hex[:8]}")
```

## Meta Configuration

### Basic Meta Options

```python
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        # Collection name (default: class name lowercased)
        collection_name = "users"
        
        # Auto-create indexes (default: True)
        auto_create_indexes = True
        
        # Strict mode for validation (default: True)
        strict_mode = True
        
        # Use auto-incrementing ID (default: True)
        use_auto_id = True
        
        # ID field name (default: "id")
        id_field = "id"
```

### Database Configuration

```python
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        # Custom database settings
        mongo_uri = "mongodb://localhost:27017"
        database_name = "users_db"
        collection_name = "users"
        
        # Connection pool settings
        max_pool_size = 100
        min_pool_size = 0
```

### Without Meta Class

```python
# Simplest form - everything is automatic
class User(BaseModel):
    name: str
    email: str
    # Collection will be "user"
    # All defaults apply
```

## Inheritance

### Model Inheritance

```python
from py_mongo_orm import BaseModel
from typing import Optional

# Base model with common fields
class TimestampedModel(BaseModel):
    is_active: bool = True
    notes: Optional[str] = None
    
    class Meta:
        # This is an abstract base - no collection
        abstract = True

# Inherit from custom base
class User(TimestampedModel):
    name: str
    email: str
    
    class Meta:
        collection_name = "users"

class Post(TimestampedModel):
    title: str
    content: str
    author_id: int
    
    class Meta:
        collection_name = "posts"
```

### Mixin Classes

```python
from typing import Optional

class AuditMixin:
    """Mixin for audit fields"""
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    version: int = 1

class SoftDeleteMixin:
    """Mixin for soft delete"""
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

class User(BaseModel, AuditMixin, SoftDeleteMixin):
    name: str
    email: str
```

## Custom Methods

### Instance Methods

```python
from typing import List
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    
    def full_name(self) -> str:
        """Get formatted full name"""
        return self.name.title()
    
    def is_adult(self) -> bool:
        """Check if user is adult"""
        return self.age >= 18 if self.age else False
    
    async def get_posts(self) -> List['Post']:
        """Get all posts by this user"""
        from .post import Post  # Avoid circular import
        return await Post.filter(author_id=self.id)
    
    async def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False
        await self.save()
```

### Class Methods

```python
from typing import List, Optional
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
    
    @classmethod
    async def get_active_users(cls) -> List['User']:
        """Get all active users"""
        return await cls.filter(is_active=True)
    
    @classmethod
    async def get_by_email(cls, email: str) -> Optional['User']:
        """Get user by email"""
        return await cls.get(email=email)
    
    @classmethod
    async def create_admin(cls, name: str, email: str) -> 'User':
        """Create admin user"""
        return await cls.create(
            name=name,
            email=email,
            is_admin=True,
            is_active=True
        )
```

### Property Methods

```python
from py_mongo_orm import BaseModel

class User(BaseModel):
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    
    @property
    def full_name(self) -> str:
        """Full name property"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> Optional[int]:
        """Calculate age from birth date"""
        if not self.birth_date:
            return None
        
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
```

## Model Validation

### Custom Model Validation

```python
from pydantic import root_validator
from py_mongo_orm import BaseModel

class Order(BaseModel):
    product_id: int
    quantity: int
    price: float
    discount: float = 0.0
    
    @root_validator
    def validate_order(cls, values):
        quantity = values.get('quantity', 0)
        price = values.get('price', 0)
        discount = values.get('discount', 0)
        
        # Validate quantity
        if quantity <= 0:
            raise ValueError('Quantity must be positive')
        
        # Validate price
        if price <= 0:
            raise ValueError('Price must be positive')
        
        # Validate discount
        if discount < 0 or discount > price:
            raise ValueError('Invalid discount amount')
        
        return values
    
    @property
    def total_price(self) -> float:
        """Calculate total price after discount"""
        return (self.price - self.discount) * self.quantity
```

### Pre/Post Save Hooks

```python
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str
    email: str
    slug: Optional[str] = None
    
    async def save(self, **kwargs):
        """Override save with pre/post hooks"""
        # Pre-save hook
        if not self.slug:
            self.slug = self.name.lower().replace(' ', '-')
        
        # Call parent save
        result = await super().save(**kwargs)
        
        # Post-save hook (example: send notification)
        await self._send_notification()
        
        return result
    
    async def _send_notification(self):
        """Send notification after save"""
        # Implementation depends on your notification system
        pass
```

## Advanced Examples

### Complex Model with All Features

```python
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
from pydantic import Field, validator, root_validator, EmailStr
from py_mongo_orm import BaseModel

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class User(BaseModel):
    # Basic fields
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    
    # Optional fields with validation
    age: Optional[int] = Field(None, ge=0, le=150)
    bio: Optional[str] = Field(None, max_length=500)
    
    # Enum field
    role: UserRole = UserRole.USER
    
    # Complex fields
    preferences: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list, max_items=20)
    
    # Status fields
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    
    class Meta:
        collection_name = "users"
        auto_create_indexes = True
    
    @validator('first_name', 'last_name')
    def name_validation(cls, v):
        return v.strip().title()
    
    @validator('tags')
    def tags_validation(cls, v):
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    @root_validator
    def validate_admin_requirements(cls, values):
        role = values.get('role')
        is_verified = values.get('is_verified')
        
        if role == UserRole.ADMIN and not is_verified:
            raise ValueError('Admin users must be verified')
        
        return values
    
    # Custom methods
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    async def verify_account(self) -> None:
        """Verify user account"""
        self.is_verified = True
        await self.save()
    
    @classmethod
    async def get_admins(cls) -> List['User']:
        """Get all admin users"""
        return await cls.filter(role=UserRole.ADMIN)
```

## Best Practices

### 1. Field Organization

```python
class User(BaseModel):
    # Group related fields together
    # 1. Identity fields
    first_name: str
    last_name: str
    email: EmailStr
    
    # 2. Profile fields
    age: Optional[int] = None
    bio: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    
    # 3. Settings
    preferences: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    
    # 4. Metadata
    tags: List[str] = Field(default_factory=list)
```

### 2. Validation Best Practices

```python
class User(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with _ or -)')
        return v.lower()
```

### 3. Method Organization

```python
class User(BaseModel):
    # ... fields ...
    
    # Properties first
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    # Instance methods
    async def change_password(self, new_password: str) -> None:
        # Implementation
        pass
    
    # Class methods last
    @classmethod
    async def get_by_username(cls, username: str) -> Optional['User']:
        return await cls.get(username=username)
```

---

**Previous:** [Installation & Setup](02-installation.md) | **Next:** [Configuration](04-configuration.md)
