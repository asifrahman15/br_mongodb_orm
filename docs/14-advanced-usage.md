# Advanced Usage

MongoDB ORM supports advanced patterns and techniques for complex applications and specialized use cases.

## Table of Contents

- [Overview](#overview)
- [Custom Model Behaviors](#custom-model-behaviors)
- [Advanced Queries](#advanced-queries)
- [Model Inheritance](#model-inheritance)
- [Custom Field Types](#custom-field-types)
- [Hooks and Events](#hooks-and-events)
- [Advanced Aggregation](#advanced-aggregation)
- [Multi-Database Setup](#multi-database-setup)
- [Performance Optimization](#performance-optimization)
- [Examples](#examples)

## Overview

Advanced usage of MongoDB ORM includes:

- **Custom Model Behaviors**: Extending models with domain-specific logic
- **Complex Queries**: Advanced filtering and aggregation patterns
- **Model Inheritance**: Sharing behavior across model hierarchies
- **Custom Fields**: Creating specialized field types
- **Event Hooks**: Responding to model lifecycle events
- **Multi-Database**: Working with multiple databases
- **Performance**: Advanced optimization techniques

## Custom Model Behaviors

### Domain-Specific Methods

```python
from br_mongodb_orm import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

class User(BaseModel):
    name: str
    email: str
    last_login: Optional[datetime] = None
    login_count: int = 0
    is_active: bool = True
    
    # Domain-specific methods
    async def login(self) -> bool:
        """Handle user login"""
        self.last_login = datetime.now(UTC)
        self.login_count += 1
        await self.save()
        return True
    
    async def logout(self) -> bool:
        """Handle user logout"""
        # Additional logout logic could go here
        return True
    
    def is_recent_login(self, hours: int = 24) -> bool:
        """Check if user logged in recently"""
        if not self.last_login:
            return False
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return self.last_login > cutoff
    
    async def deactivate(self, reason: str = None) -> None:
        """Deactivate user account"""
        self.is_active = False
        # Log deactivation reason
        await UserAuditLog.create(
            user_id=self.id,
            action="deactivate",
            reason=reason
        )
        await self.save()
    
    @classmethod
    async def find_inactive_users(cls, days: int = 30) -> List['User']:
        """Find users inactive for specified days"""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return await cls.filter(
            last_login={"$lt": cutoff},
            is_active=True
        )
    
    @classmethod
    async def get_user_stats(cls) -> dict:
        """Get user statistics"""
        pipeline = [
            {"$group": {
                "_id": None,
                "total_users": {"$sum": 1},
                "active_users": {
                    "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
                },
                "avg_login_count": {"$avg": "$login_count"}
            }}
        ]
        
        result = await cls.aggregate(pipeline)
        return result[0] if result else {}
```

### State Machine Pattern

```python
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(BaseModel):
    user_id: int
    items: List[dict]
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    
    class Meta:
        collection_name = "orders"
    
    async def confirm(self) -> bool:
        """Confirm order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order in {self.status} status")
        
        # Business logic for confirmation
        self.status = OrderStatus.CONFIRMED
        await self.save()
        
        # Trigger events
        await self._send_confirmation_email()
        await self._update_inventory()
        
        return True
    
    async def ship(self, tracking_number: str = None) -> bool:
        """Ship order"""
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError(f"Cannot ship order in {self.status} status")
        
        self.status = OrderStatus.SHIPPED
        if tracking_number:
            self.tracking_number = tracking_number
        
        await self.save()
        await self._send_shipping_notification()
        
        return True
    
    async def cancel(self, reason: str = None) -> bool:
        """Cancel order"""
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError(f"Cannot cancel order in {self.status} status")
        
        self.status = OrderStatus.CANCELLED
        await self.save()
        
        # Revert inventory changes
        await self._revert_inventory()
        await self._process_refund()
        
        return True
    
    async def _send_confirmation_email(self):
        """Send confirmation email (placeholder)"""
        pass
    
    async def _update_inventory(self):
        """Update inventory (placeholder)"""
        pass
    
    async def _send_shipping_notification(self):
        """Send shipping notification (placeholder)"""
        pass
    
    async def _revert_inventory(self):
        """Revert inventory changes (placeholder)"""
        pass
    
    async def _process_refund(self):
        """Process refund (placeholder)"""
        pass
```

## Advanced Queries

### Dynamic Query Building

```python
class AdvancedUserQueries:
    """Advanced query patterns for User model"""
    
    @staticmethod
    async def search_users(
        name: Optional[str] = None,
        email: Optional[str] = None,
        age_range: Optional[tuple] = None,
        cities: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_direction: int = -1,
        limit: int = 50,
        skip: int = 0
    ) -> List[User]:
        """Dynamic user search with multiple optional filters"""
        
        # Build query dynamically
        query = {}
        
        if name:
            query["name"] = {"$regex": name, "$options": "i"}
        
        if email:
            query["email"] = {"$regex": email, "$options": "i"}
        
        if age_range:
            min_age, max_age = age_range
            query["age"] = {"$gte": min_age, "$lte": max_age}
        
        if cities:
            query["city"] = {"$in": cities}
        
        if is_active is not None:
            query["is_active"] = is_active
        
        if created_after:
            query["created_at"] = {"$gte": created_after}
        
        return await User.filter(
            **query,
            sort_by={sort_by: sort_direction},
            limit=limit,
            skip=skip
        )
    
    @staticmethod
    async def get_user_analytics(
        date_range: Optional[tuple] = None,
        group_by: str = "day"
    ) -> List[dict]:
        """Get user analytics with flexible grouping"""
        
        match_stage = {}
        if date_range:
            start_date, end_date = date_range
            match_stage["created_at"] = {"$gte": start_date, "$lte": end_date}
        
        # Group by different time periods
        if group_by == "day":
            group_id = {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"},
                "day": {"$dayOfMonth": "$created_at"}
            }
        elif group_by == "month":
            group_id = {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"}
            }
        elif group_by == "year":
            group_id = {"year": {"$year": "$created_at"}}
        else:
            group_id = None
        
        pipeline = []
        
        if match_stage:
            pipeline.append({"$match": match_stage})
        
        if group_id:
            pipeline.append({
                "$group": {
                    "_id": group_id,
                    "user_count": {"$sum": 1},
                    "active_count": {
                        "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
                    }
                }
            })
            pipeline.append({"$sort": {"_id": 1}})
        else:
            pipeline.append({
                "$group": {
                    "_id": None,
                    "total_users": {"$sum": 1},
                    "active_users": {
                        "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
                    }
                }
            })
        
        return await User.aggregate(pipeline)
```

### Geospatial Queries

```python
class Location(BaseModel):
    name: str
    coordinates: List[float]  # [longitude, latitude]
    address: str
    
    class Meta:
        collection_name = "locations"
    
    @classmethod
    async def setup_geospatial_indexes(cls):
        """Set up geospatial indexes"""
        await cls.create_index("coordinates", index_type="2dsphere")
    
    @classmethod
    async def find_nearby(
        cls,
        longitude: float,
        latitude: float,
        max_distance: int = 1000  # meters
    ) -> List['Location']:
        """Find locations near a point"""
        query = {
            "coordinates": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "$maxDistance": max_distance
                }
            }
        }
        return await cls.filter(**query)
    
    @classmethod
    async def find_within_polygon(
        cls,
        polygon_coordinates: List[List[float]]
    ) -> List['Location']:
        """Find locations within a polygon"""
        query = {
            "coordinates": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [polygon_coordinates]
                    }
                }
            }
        }
        return await cls.filter(**query)
```

## Model Inheritance

### Abstract Base Models

```python
from abc import ABC, abstractmethod

class TimestampedModel(BaseModel, ABC):
    """Abstract base model with timestamps"""
    
    class Meta:
        abstract = True  # This would be implemented in your framework
    
    @abstractmethod
    async def custom_validation(self) -> bool:
        """Abstract method for custom validation"""
        pass
    
    async def save(self, **kwargs) -> 'TimestampedModel':
        """Override save with custom validation"""
        if not await self.custom_validation():
            raise ValidationError("Custom validation failed")
        
        return await super().save(**kwargs)

class AuditableModel(TimestampedModel):
    """Model with audit trail"""
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    async def save(self, user_id: Optional[int] = None, **kwargs):
        """Save with audit information"""
        if user_id:
            if self.id is None:  # New record
                self.created_by = user_id
            self.updated_by = user_id
        
        return await super().save(**kwargs)

class SoftDeleteModel(AuditableModel):
    """Model with soft delete capability"""
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    
    async def delete(self, user_id: Optional[int] = None) -> bool:
        """Soft delete implementation"""
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)
        if user_id:
            self.deleted_by = user_id
        
        await self.save()
        return True
    
    async def hard_delete(self) -> bool:
        """Actual deletion"""
        return await super().delete()
    
    @classmethod
    async def filter(cls, include_deleted: bool = False, **kwargs):
        """Filter excluding soft-deleted records by default"""
        if not include_deleted:
            kwargs["is_deleted"] = {"$ne": True}
        
        return await super().filter(**kwargs)

# Concrete models using inheritance
class Product(SoftDeleteModel):
    name: str
    price: float
    category: str
    
    async def custom_validation(self) -> bool:
        """Implement abstract method"""
        return self.price > 0 and len(self.name) > 0
```

### Mixin Pattern

```python
class CacheableMixin:
    """Mixin for caching model instances"""
    
    _cache = {}  # Simple in-memory cache
    
    @classmethod
    async def get_cached(cls, **kwargs):
        """Get instance with caching"""
        cache_key = cls._make_cache_key(kwargs)
        
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        instance = await cls.get(**kwargs)
        if instance:
            cls._cache[cache_key] = instance
        
        return instance
    
    @classmethod
    def _make_cache_key(cls, kwargs):
        """Create cache key from kwargs"""
        return f"{cls.__name__}:{hash(frozenset(kwargs.items()))}"
    
    async def save(self, **kwargs):
        """Save and update cache"""
        result = await super().save(**kwargs)
        
        # Update cache
        cache_key = self._make_cache_key({"id": self.id})
        self._cache[cache_key] = self
        
        return result

class VersionedMixin:
    """Mixin for model versioning"""
    
    version: int = 1
    
    async def save(self, **kwargs):
        """Save with version increment"""
        if self.id is not None:  # Updating existing record
            self.version += 1
        
        return await super().save(**kwargs)

class User(BaseModel, CacheableMixin, VersionedMixin):
    name: str
    email: str
    
    # Inherits caching and versioning behavior
```

## Custom Field Types

### Encrypted Fields

```python
from cryptography.fernet import Fernet
import base64

class EncryptedField:
    """Custom field type for encrypted data"""
    
    def __init__(self, key: bytes = None):
        if key is None:
            key = Fernet.generate_key()
        self.cipher = Fernet(key)
    
    def encrypt(self, value: str) -> str:
        """Encrypt value"""
        if value is None:
            return None
        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt value"""
        if encrypted_value is None:
            return None
        encrypted_bytes = base64.b64decode(encrypted_value.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()

class UserWithEncryption(BaseModel):
    name: str
    email: str
    _encrypted_ssn: Optional[str] = None  # Store encrypted
    
    def __init__(self, **data):
        self._encryption = EncryptedField()
        super().__init__(**data)
    
    @property
    def ssn(self) -> Optional[str]:
        """Get decrypted SSN"""
        if self._encrypted_ssn:
            return self._encryption.decrypt(self._encrypted_ssn)
        return None
    
    @ssn.setter
    def ssn(self, value: Optional[str]):
        """Set encrypted SSN"""
        if value:
            self._encrypted_ssn = self._encryption.encrypt(value)
        else:
            self._encrypted_ssn = None
```

### JSON Field

```python
import json
from typing import Any, Dict

class JSONField:
    """Custom JSON field type"""
    
    @staticmethod
    def serialize(value: Any) -> str:
        """Serialize Python object to JSON string"""
        if value is None:
            return None
        return json.dumps(value, default=str)
    
    @staticmethod
    def deserialize(value: str) -> Any:
        """Deserialize JSON string to Python object"""
        if value is None:
            return None
        return json.loads(value)

class UserProfile(BaseModel):
    user_id: int
    _metadata_json: Optional[str] = None
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata as Python dict"""
        if self._metadata_json:
            return JSONField.deserialize(self._metadata_json)
        return {}
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        """Set metadata from Python dict"""
        self._metadata_json = JSONField.serialize(value)
    
    def set_metadata(self, key: str, value: Any):
        """Set specific metadata key"""
        current = self.metadata
        current[key] = value
        self.metadata = current
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get specific metadata key"""
        return self.metadata.get(key, default)
```

## Hooks and Events

### Model Lifecycle Hooks

```python
from typing import Callable, List
from functools import wraps

class HookMixin:
    """Mixin for model lifecycle hooks"""
    
    _pre_save_hooks: List[Callable] = []
    _post_save_hooks: List[Callable] = []
    _pre_delete_hooks: List[Callable] = []
    _post_delete_hooks: List[Callable] = []
    
    @classmethod
    def register_pre_save_hook(cls, hook: Callable):
        """Register pre-save hook"""
        cls._pre_save_hooks.append(hook)
    
    @classmethod
    def register_post_save_hook(cls, hook: Callable):
        """Register post-save hook"""
        cls._post_save_hooks.append(hook)
    
    async def save(self, **kwargs):
        """Save with hooks"""
        # Pre-save hooks
        for hook in self._pre_save_hooks:
            await hook(self)
        
        # Actual save
        result = await super().save(**kwargs)
        
        # Post-save hooks
        for hook in self._post_save_hooks:
            await hook(self)
        
        return result
    
    async def delete(self, **kwargs):
        """Delete with hooks"""
        # Pre-delete hooks
        for hook in self._pre_delete_hooks:
            await hook(self)
        
        # Actual delete
        result = await super().delete(**kwargs)
        
        # Post-delete hooks
        for hook in self._post_delete_hooks:
            await hook(self)
        
        return result

# Usage
class User(BaseModel, HookMixin):
    name: str
    email: str

# Register hooks
async def audit_user_save(user):
    """Audit hook for user saves"""
    await AuditLog.create(
        model_name="User",
        model_id=user.id,
        action="save",
        timestamp=datetime.now(UTC)
    )

async def send_welcome_email(user):
    """Send welcome email for new users"""
    if user.id is None:  # New user
        # Send welcome email
        pass

User.register_post_save_hook(audit_user_save)
User.register_post_save_hook(send_welcome_email)
```

### Event System

```python
from typing import Dict, List, Callable
import asyncio

class EventSystem:
    """Simple event system for model events"""
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, callback: Callable):
        """Register event listener"""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    async def emit(self, event: str, *args, **kwargs):
        """Emit event to all listeners"""
        if event in self._listeners:
            tasks = []
            for callback in self._listeners[event]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(*args, **kwargs))
                else:
                    callback(*args, **kwargs)
            
            if tasks:
                await asyncio.gather(*tasks)

# Global event system
events = EventSystem()

class EventedModel(BaseModel):
    """Model with event system integration"""
    
    async def save(self, **kwargs):
        """Save with events"""
        is_new = self.id is None
        
        await events.emit("before_save", self)
        result = await super().save(**kwargs)
        
        if is_new:
            await events.emit("after_create", self)
        else:
            await events.emit("after_update", self)
        
        await events.emit("after_save", self)
        return result

# Usage
class User(EventedModel):
    name: str
    email: str

# Register event handlers
@events.on("after_create")
async def user_created(user):
    print(f"New user created: {user.name}")

@events.on("after_update") 
async def user_updated(user):
    print(f"User updated: {user.name}")
```

## Advanced Aggregation

### Complex Analytics Pipeline

```python
class AdvancedAnalytics:
    """Advanced analytics using aggregation pipelines"""
    
    @staticmethod
    async def user_engagement_report(days: int = 30) -> Dict:
        """Comprehensive user engagement report"""
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        
        pipeline = [
            # Match recent activities
            {"$match": {"created_at": {"$gte": cutoff_date}}},
            
            # Lookup user information
            {"$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user"
            }},
            
            # Unwind user array
            {"$unwind": "$user"},
            
            # Group by user with engagement metrics
            {"$group": {
                "_id": "$user_id",
                "user_name": {"$first": "$user.name"},
                "user_email": {"$first": "$user.email"},
                "total_actions": {"$sum": 1},
                "unique_days": {
                    "$addToSet": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    }
                },
                "action_types": {"$addToSet": "$action_type"},
                "first_action": {"$min": "$created_at"},
                "last_action": {"$max": "$created_at"}
            }},
            
            # Calculate engagement score
            {"$addFields": {
                "unique_day_count": {"$size": "$unique_days"},
                "action_type_count": {"$size": "$action_types"},
                "engagement_score": {
                    "$multiply": [
                        {"$size": "$unique_days"},
                        {"$divide": ["$total_actions", days]}
                    ]
                }
            }},
            
            # Sort by engagement score
            {"$sort": {"engagement_score": -1}},
            
            # Group for summary statistics
            {"$facet": {
                "top_users": [
                    {"$limit": 10}
                ],
                "summary": [
                    {"$group": {
                        "_id": None,
                        "total_active_users": {"$sum": 1},
                        "avg_actions_per_user": {"$avg": "$total_actions"},
                        "avg_engagement_score": {"$avg": "$engagement_score"}
                    }}
                ]
            }}
        ]
        
        result = await UserAction.aggregate(pipeline)
        return result[0] if result else {}
```

### Time Series Analysis

```python
class TimeSeriesAnalytics:
    """Time series analytics patterns"""
    
    @staticmethod
    async def daily_metrics(
        model_class,
        date_field: str = "created_at",
        days: int = 30
    ) -> List[Dict]:
        """Generate daily metrics for any model"""
        start_date = datetime.now(UTC) - timedelta(days=days)
        
        pipeline = [
            {"$match": {date_field: {"$gte": start_date}}},
            
            {"$group": {
                "_id": {
                    "year": {"$year": f"${date_field}"},
                    "month": {"$month": f"${date_field}"},
                    "day": {"$dayOfMonth": f"${date_field}"}
                },
                "count": {"$sum": 1}
            }},
            
            {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
            
            {"$project": {
                "date": {
                    "$dateFromParts": {
                        "year": "$_id.year",
                        "month": "$_id.month",
                        "day": "$_id.day"
                    }
                },
                "count": 1,
                "_id": 0
            }}
        ]
        
        return await model_class.aggregate(pipeline)
    
    @staticmethod
    async def moving_average(
        model_class,
        window_days: int = 7,
        total_days: int = 30
    ) -> List[Dict]:
        """Calculate moving average"""
        # First get daily counts
        daily_data = await TimeSeriesAnalytics.daily_metrics(
            model_class, days=total_days
        )
        
        # Calculate moving average (simplified version)
        result = []
        for i in range(len(daily_data)):
            if i >= window_days - 1:
                window_data = daily_data[i-window_days+1:i+1]
                avg = sum(d["count"] for d in window_data) / window_days
                result.append({
                    "date": daily_data[i]["date"],
                    "count": daily_data[i]["count"],
                    "moving_average": avg
                })
        
        return result
```

## Multi-Database Setup

### Multiple Database Configuration

```python
class DatabaseManager:
    """Manage multiple database connections"""
    
    def __init__(self):
        self.databases = {}
    
    async def register_database(self, name: str, config: DatabaseConfig):
        """Register a database configuration"""
        self.databases[name] = config
    
    async def initialize_models(self, database_name: str, models: List):
        """Initialize models with specific database"""
        config = self.databases[database_name]
        
        for model in models:
            await model.__initialize__(db_config=config)

# Setup multiple databases
db_manager = DatabaseManager()

# User database
await db_manager.register_database("users", DatabaseConfig(
    mongo_uri="mongodb://user-cluster/",
    database_name="users_db"
))

# Analytics database
await db_manager.register_database("analytics", DatabaseConfig(
    mongo_uri="mongodb://analytics-cluster/",
    database_name="analytics_db"
))

# Initialize models
await db_manager.initialize_models("users", [User, UserProfile])
await db_manager.initialize_models("analytics", [UserAction, Event])
```

### Cross-Database Operations

```python
class CrossDatabaseService:
    """Service for operations across multiple databases"""
    
    @staticmethod
    async def sync_user_data():
        """Sync user data between databases"""
        # Get users from main database
        users = await User.all()  # From users database
        
        # Create analytics profiles
        for user in users:
            # Check if analytics profile exists
            profile = await AnalyticsProfile.get(user_id=user.id)
            
            if not profile:
                # Create in analytics database
                profile = AnalyticsProfile(
                    user_id=user.id,
                    user_name=user.name,
                    created_at=user.created_at
                )
                await profile.save()
    
    @staticmethod
    async def generate_cross_db_report():
        """Generate report using data from multiple databases"""
        # Get user data
        users = await User.filter(is_active=True)
        user_ids = [u.id for u in users]
        
        # Get analytics data
        analytics = await UserAction.filter(
            user_id={"$in": user_ids}
        )
        
        # Combine data
        report = {}
        for user in users:
            user_analytics = [a for a in analytics if a.user_id == user.id]
            report[user.id] = {
                "name": user.name,
                "email": user.email,
                "action_count": len(user_analytics),
                "last_action": max(
                    (a.created_at for a in user_analytics),
                    default=None
                )
            }
        
        return report
```

## Performance Optimization

### Query Optimization Patterns

```python
class OptimizedQueries:
    """Performance-optimized query patterns"""
    
    @staticmethod
    async def efficient_pagination(
        model_class,
        last_id: Optional[int] = None,
        limit: int = 20
    ):
        """Cursor-based pagination for better performance"""
        query = {}
        if last_id:
            query["id"] = {"$gt": last_id}
        
        return await model_class.filter(
            **query,
            sort_by={"id": 1},
            limit=limit
        )
    
    @staticmethod
    async def batch_load_related(users: List[User]) -> Dict[int, List]:
        """Batch load related data to avoid N+1 queries"""
        user_ids = [u.id for u in users]
        
        # Load all related data in one query
        orders = await Order.filter(user_id={"$in": user_ids})
        
        # Group by user_id
        orders_by_user = {}
        for order in orders:
            if order.user_id not in orders_by_user:
                orders_by_user[order.user_id] = []
            orders_by_user[order.user_id].append(order)
        
        return orders_by_user
    
    @staticmethod
    async def optimized_search(
        search_term: str,
        filters: Dict = None,
        limit: int = 50
    ):
        """Optimized text search with filters"""
        pipeline = []
        
        # Text search stage
        if search_term:
            pipeline.append({
                "$match": {"$text": {"$search": search_term}}
            })
            
            # Add text score for sorting
            pipeline.append({
                "$addFields": {"score": {"$meta": "textScore"}}
            })
        
        # Additional filters
        if filters:
            pipeline.append({"$match": filters})
        
        # Sort by relevance score
        if search_term:
            pipeline.append({"$sort": {"score": {"$meta": "textScore"}}})
        
        # Limit results
        pipeline.append({"$limit": limit})
        
        return await User.aggregate(pipeline)
```

### Caching Strategies

```python
import asyncio
from typing import Optional
import hashlib
import json

class CacheManager:
    """Advanced caching for model operations"""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.ttl = ttl
    
    def _make_key(self, model_class, method: str, *args, **kwargs) -> str:
        """Generate cache key"""
        key_data = {
            "model": model_class.__name__,
            "method": method,
            "args": args,
            "kwargs": kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get_or_set(
        self,
        model_class,
        method: str,
        func,
        *args,
        **kwargs
    ):
        """Get from cache or execute function and cache result"""
        cache_key = self._make_key(model_class, method, *args, **kwargs)
        
        # Check cache
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                return data
        
        # Execute function and cache result
        result = await func(*args, **kwargs)
        self.cache[cache_key] = (result, time.time())
        
        return result
    
    def invalidate(self, model_class, pattern: str = None):
        """Invalidate cache entries"""
        if pattern:
            # Invalidate specific pattern
            keys_to_remove = [
                k for k in self.cache.keys()
                if pattern in k and model_class.__name__ in k
            ]
        else:
            # Invalidate all for model
            keys_to_remove = [
                k for k in self.cache.keys()
                if model_class.__name__ in k
            ]
        
        for key in keys_to_remove:
            del self.cache[key]

# Global cache manager
cache = CacheManager()

class CachedModel(BaseModel):
    """Model with automatic caching"""
    
    @classmethod
    async def get_cached(cls, **kwargs):
        """Get with caching"""
        return await cache.get_or_set(
            cls, "get", cls.get, **kwargs
        )
    
    @classmethod
    async def filter_cached(cls, **kwargs):
        """Filter with caching"""
        return await cache.get_or_set(
            cls, "filter", cls.filter, **kwargs
        )
    
    async def save(self, **kwargs):
        """Save and invalidate cache"""
        result = await super().save(**kwargs)
        cache.invalidate(self.__class__)
        return result
    
    async def delete(self, **kwargs):
        """Delete and invalidate cache"""
        result = await super().delete(**kwargs)
        cache.invalidate(self.__class__)
        return result
```

This advanced usage documentation covers sophisticated patterns and techniques for building complex applications with MongoDB ORM. The examples demonstrate real-world scenarios and performance considerations that are essential for production systems.
