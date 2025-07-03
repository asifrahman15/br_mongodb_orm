# Utilities & Helpers

MongoDB ORM provides a comprehensive set of utility functions and helper classes to streamline common operations and enhance productivity.

## Table of Contents

- [Overview](#overview)
- [Data Utilities](#data-utilities)
- [Query Helpers](#query-helpers)
- [Validation Utilities](#validation-utilities)
- [Bulk Operation Helpers](#bulk-operation-helpers)
- [Testing Utilities](#testing-utilities)
- [Performance Helpers](#performance-helpers)
- [Migration Tools](#migration-tools)
- [Examples](#examples)

## Overview

The utilities module (`mongodb_orm.utils`) provides:

- **Data Transformation**: Convert between formats and structures
- **Query Building**: Simplified query construction
- **Validation**: Data validation and sanitization
- **Bulk Operations**: Efficient bulk data processing
- **Testing**: Mock objects and test data generation
- **Performance**: Profiling and optimization tools
- **Migration**: Schema and data migration utilities

## Data Utilities

### Object ID Utilities

```python
from mongodb_orm.utils import ObjectIdUtils
from bson import ObjectId

# Generate new ObjectId
new_id = ObjectIdUtils.generate()

# Validate ObjectId
is_valid = ObjectIdUtils.is_valid("507f1f77bcf86cd799439011")

# Convert string to ObjectId
object_id = ObjectIdUtils.from_string("507f1f77bcf86cd799439011")

# Convert ObjectId to string
id_string = ObjectIdUtils.to_string(object_id)

# Get timestamp from ObjectId
timestamp = ObjectIdUtils.get_timestamp(object_id)
```

### Data Conversion

```python
from mongodb_orm.utils import DataConverter
from datetime import datetime

# Convert dictionary to model
user_dict = {"name": "John", "email": "john@example.com", "age": 30}
user = DataConverter.dict_to_model(User, user_dict)

# Convert model to dictionary
user_dict = DataConverter.model_to_dict(user)

# Convert datetime formats
iso_string = DataConverter.datetime_to_iso(datetime.now())
dt_object = DataConverter.iso_to_datetime(iso_string)

# Sanitize data
clean_data = DataConverter.sanitize_dict({
    "name": "  John Doe  ",
    "email": "JOHN@EXAMPLE.COM",
    "age": "30"
})
# Result: {"name": "John Doe", "email": "john@example.com", "age": 30}
```

### Field Utilities

```python
from mongodb_orm.utils import FieldUtils

# Extract field names from model
field_names = FieldUtils.get_field_names(User)
# ['id', 'name', 'email', 'created_at', 'updated_at']

# Get field types
field_types = FieldUtils.get_field_types(User)
# {'id': int, 'name': str, 'email': str, 'created_at': datetime, 'updated_at': datetime}

# Check if field exists
has_field = FieldUtils.has_field(User, "email")

# Get required fields
required_fields = FieldUtils.get_required_fields(User)

# Get optional fields
optional_fields = FieldUtils.get_optional_fields(User)
```

## Query Helpers

### Query Builder

```python
from mongodb_orm.utils import QueryBuilder

# Build complex queries
query = QueryBuilder() \
    .where("age", {"$gte": 18, "$lte": 65}) \
    .where("city", {"$in": ["New York", "San Francisco"]}) \
    .where("is_active", True) \
    .sort("created_at", -1) \
    .limit(50) \
    .build()

# Use with models
users = await User.filter(**query)

# Build aggregation pipelines
pipeline = QueryBuilder.aggregation() \
    .match({"status": "active"}) \
    .group({"_id": "$city", "count": {"$sum": 1}}) \
    .sort({"count": -1}) \
    .build()

results = await User.aggregate(pipeline)
```

### Date Range Helpers

```python
from mongodb_orm.utils import DateRangeHelper
from datetime import datetime, timedelta

# Common date ranges
today = DateRangeHelper.today()
yesterday = DateRangeHelper.yesterday()
this_week = DateRangeHelper.this_week()
this_month = DateRangeHelper.this_month()
last_30_days = DateRangeHelper.last_n_days(30)

# Custom range
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 31)
custom_range = DateRangeHelper.custom_range(start_date, end_date)

# Use in queries
recent_users = await User.filter(
    created_at=last_30_days,
    sort_by={"created_at": -1}
)
```

### Filter Helpers

```python
from mongodb_orm.utils import FilterHelper

# Text search filters
text_filter = FilterHelper.text_search("python mongodb")
# {"$text": {"$search": "python mongodb"}}

# Range filters
age_filter = FilterHelper.range_filter("age", 18, 65)
# {"age": {"$gte": 18, "$lte": 65}}

# Array filters
tags_filter = FilterHelper.array_contains("tags", ["python", "database"])
# {"tags": {"$in": ["python", "database"]}}

# Combine filters
combined = FilterHelper.and_filters([
    {"status": "active"},
    age_filter,
    tags_filter
])
```

## Validation Utilities

### Data Validators

```python
from mongodb_orm.utils import Validators

# Email validation
is_valid_email = Validators.email("user@example.com")

# URL validation
is_valid_url = Validators.url("https://example.com")

# Phone number validation
is_valid_phone = Validators.phone("+1-555-0123")

# Custom validators
def validate_username(username: str) -> bool:
    """Validate username format"""
    return Validators.regex(username, r"^[a-zA-Z0-9_]{3,20}$")

# Password strength
is_strong = Validators.password_strength("MyP@ssw0rd123", min_length=8)
```

### Schema Validators

```python
from mongodb_orm.utils import SchemaValidator

# Validate model data
validator = SchemaValidator(User)

# Check required fields
missing_fields = validator.check_required_fields({"name": "John"})
# ['email']

# Validate field types
type_errors = validator.validate_types({
    "name": "John",
    "age": "not_a_number"  # Should be int
})

# Full validation
is_valid, errors = validator.validate({
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
})
```

## Bulk Operation Helpers

### Bulk Insert Helper

```python
from mongodb_orm.utils import bulk_insert, batch_processor

# Simple bulk insert
data = [
    {"name": "User 1", "email": "user1@example.com"},
    {"name": "User 2", "email": "user2@example.com"},
]
count = await bulk_insert(User, data)

# Batch processing with callback
async def process_batch(batch_data, batch_number):
    count = await bulk_insert(User, batch_data)
    print(f"Processed batch {batch_number}: {count} records")
    return count

total = await batch_processor(
    data=large_dataset,
    batch_size=1000,
    processor_func=process_batch
)
```

### Bulk Update Helper

```python
from mongodb_orm.utils import bulk_update

# Multiple update operations
updates = [
    {
        "filter": {"age": {"$lt": 30}},
        "update": {"$set": {"category": "young"}}
    },
    {
        "filter": {"age": {"$gte": 30}},
        "update": {"$set": {"category": "mature"}}
    }
]

result = await bulk_update(User, updates)
print(f"Modified {result.modified_count} documents")
```

## Testing Utilities

### Mock Data Generation

```python
from mongodb_orm.utils import MockDataGenerator
import random

# Generate mock users
mock_users = MockDataGenerator.generate_users(count=100)

# Generate with custom parameters
mock_products = MockDataGenerator.generate_products(
    count=50,
    categories=["electronics", "books", "clothing"],
    price_range=(10, 1000)
)

# Custom mock data
def generate_custom_user():
    return {
        "name": MockDataGenerator.random_name(),
        "email": MockDataGenerator.random_email(),
        "age": random.randint(18, 80),
        "city": MockDataGenerator.random_city()
    }

custom_users = [generate_custom_user() for _ in range(10)]
```

### Test Database Utilities

```python
from mongodb_orm.utils import TestDatabase

class TestUserModel:
    async def setup_method(self):
        """Set up test database"""
        self.test_db = TestDatabase("test_users")
        await self.test_db.setup()
        
        # Initialize models with test database
        await User.__initialize__(db_config=self.test_db.config)
    
    async def teardown_method(self):
        """Clean up test database"""
        await self.test_db.cleanup()
    
    async def test_user_creation(self):
        """Test user creation"""
        user = User(name="Test User", email="test@example.com")
        await user.save()
        
        assert user.id is not None
        assert user.name == "Test User"
        
        # Verify in database
        found_user = await User.get_by_id(user.id)
        assert found_user is not None
        assert found_user.email == "test@example.com"
```

### Factory Pattern

```python
from mongodb_orm.utils import ModelFactory

class UserFactory(ModelFactory):
    model = User
    
    @classmethod
    def default_data(cls):
        return {
            "name": cls.fake.name(),
            "email": cls.fake.email(),
            "age": cls.fake.random_int(18, 80)
        }
    
    @classmethod
    def admin_user(cls):
        data = cls.default_data()
        data.update({
            "role": "admin",
            "is_active": True
        })
        return cls.create(**data)

# Usage in tests
async def test_user_permissions():
    admin = await UserFactory.admin_user()
    regular_user = await UserFactory.create()
    
    assert admin.role == "admin"
    assert regular_user.role != "admin"
```

## Performance Helpers

### Query Performance Monitor

```python
from mongodb_orm.utils import QueryMonitor
import time

# Monitor query performance
monitor = QueryMonitor()

@monitor.track("user_queries")
async def get_users_by_city(city: str):
    return await User.filter(city=city)

# Get performance statistics
stats = monitor.get_stats("user_queries")
print(f"Average query time: {stats['avg_time']:.3f}s")
print(f"Total queries: {stats['count']}")
```

### Memory Usage Tracker

```python
from mongodb_orm.utils import MemoryTracker

# Track memory usage during operations
tracker = MemoryTracker()

async def memory_intensive_operation():
    with tracker.track("bulk_insert"):
        # Perform memory-intensive operation
        large_data = [{"name": f"User {i}"} for i in range(100000)]
        await bulk_insert(User, large_data)
    
    # Check memory usage
    usage = tracker.get_usage("bulk_insert")
    print(f"Peak memory: {usage['peak_mb']:.2f} MB")
    print(f"Memory difference: {usage['diff_mb']:.2f} MB")
```

### Connection Pool Monitor

```python
from mongodb_orm.utils import ConnectionPoolMonitor

# Monitor connection pool health
pool_monitor = ConnectionPoolMonitor()

async def check_pool_health():
    health = await pool_monitor.get_pool_status(User._connection_manager)
    
    print(f"Active connections: {health['active']}")
    print(f"Available connections: {health['available']}")
    print(f"Pool utilization: {health['utilization']:.1%}")
    
    if health['utilization'] > 0.8:
        print("WARNING: High pool utilization")
```

## Migration Tools

### Schema Migration

```python
from mongodb_orm.utils import SchemaMigration

class AddUserStatusMigration(SchemaMigration):
    version = "1.0.1"
    description = "Add status field to users"
    
    async def up(self):
        """Apply migration"""
        # Add status field to existing users
        await self.bulk_update(
            User,
            filter={},
            update={"$set": {"status": "active"}}
        )
        
        # Create index on new field
        await User.create_index("status")
    
    async def down(self):
        """Rollback migration"""
        # Remove status field
        await self.bulk_update(
            User,
            filter={},
            update={"$unset": {"status": ""}}
        )

# Run migration
migration = AddUserStatusMigration()
await migration.run()
```

### Data Migration

```python
from mongodb_orm.utils import DataMigration

class UserEmailNormalizationMigration(DataMigration):
    version = "1.0.2"
    description = "Normalize user email addresses"
    
    async def migrate(self):
        """Migrate user email data"""
        users = await User.all()
        
        updates = []
        for user in users:
            normalized_email = user.email.lower().strip()
            if normalized_email != user.email:
                updates.append({
                    "filter": {"id": user.id},
                    "update": {"$set": {"email": normalized_email}}
                })
        
        if updates:
            result = await self.bulk_update(User, updates)
            print(f"Normalized {result.modified_count} email addresses")

# Run migration
migration = UserEmailNormalizationMigration()
await migration.run()
```

## Examples

### Data Import Utility

```python
async def import_data_from_json(file_path: str, model_class):
    """Import data from JSON file with validation and error handling"""
    import json
    from mongodb_orm.utils import batch_processor, Validators
    
    # Load data
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Validation and processing
    valid_data = []
    errors = []
    
    for i, record in enumerate(data):
        try:
            # Validate record
            if model_class == User:
                if not Validators.email(record.get('email', '')):
                    raise ValueError(f"Invalid email: {record.get('email')}")
            
            # Create model instance for validation
            model_instance = model_class(**record)
            valid_data.append(model_instance.model_dump())
            
        except Exception as e:
            errors.append(f"Record {i}: {e}")
    
    # Report validation results
    print(f"Valid records: {len(valid_data)}")
    print(f"Invalid records: {len(errors)}")
    
    if errors:
        print("Errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  {error}")
    
    # Import valid data in batches
    if valid_data:
        total = await batch_processor(
            data=valid_data,
            batch_size=1000,
            processor_func=lambda batch, num: bulk_insert(model_class, batch)
        )
        print(f"Successfully imported {total} records")
    
    return len(valid_data), errors

# Usage
imported_count, import_errors = await import_data_from_json("users.json", User)
```

### Advanced Query Builder

```python
class AdvancedQueryBuilder:
    """Advanced query builder with method chaining"""
    
    def __init__(self):
        self.query = {}
        self.sort_criteria = {}
        self.pagination = {}
    
    def where(self, field: str, value):
        """Add where condition"""
        if isinstance(value, dict):
            # MongoDB operator
            self.query[field] = value
        else:
            # Simple equality
            self.query[field] = value
        return self
    
    def where_in(self, field: str, values: list):
        """Add where in condition"""
        self.query[field] = {"$in": values}
        return self
    
    def where_range(self, field: str, min_val=None, max_val=None):
        """Add range condition"""
        range_query = {}
        if min_val is not None:
            range_query["$gte"] = min_val
        if max_val is not None:
            range_query["$lte"] = max_val
        self.query[field] = range_query
        return self
    
    def where_text(self, search_term: str):
        """Add text search"""
        self.query["$text"] = {"$search": search_term}
        return self
    
    def sort(self, field: str, direction: int = 1):
        """Add sort criteria"""
        self.sort_criteria[field] = direction
        return self
    
    def limit(self, count: int):
        """Set limit"""
        self.pagination["limit"] = count
        return self
    
    def skip(self, count: int):
        """Set skip"""
        self.pagination["skip"] = count
        return self
    
    def page(self, page_num: int, page_size: int = 20):
        """Set pagination by page number"""
        self.pagination["limit"] = page_size
        self.pagination["skip"] = (page_num - 1) * page_size
        return self
    
    def build(self):
        """Build final query"""
        query = dict(self.query)
        if self.sort_criteria:
            query["sort_by"] = self.sort_criteria
        query.update(self.pagination)
        return query

# Usage
query = AdvancedQueryBuilder() \
    .where("status", "active") \
    .where_range("age", 18, 65) \
    .where_in("city", ["New York", "San Francisco"]) \
    .sort("created_at", -1) \
    .page(1, 20) \
    .build()

users = await User.filter(**query)
```

### Data Export Utility

```python
async def export_data_to_csv(model_class, filename: str, filters=None):
    """Export model data to CSV file"""
    import csv
    from mongodb_orm.utils import FieldUtils
    
    # Get field names
    field_names = FieldUtils.get_field_names(model_class)
    
    # Query data
    if filters:
        data = await model_class.filter(**filters)
    else:
        data = await model_class.all()
    
    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        
        for item in data:
            row = {}
            for field in field_names:
                value = getattr(item, field)
                # Handle datetime objects
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row[field] = value
            writer.writerow(row)
    
    print(f"Exported {len(data)} records to {filename}")
    return len(data)

# Usage
count = await export_data_to_csv(
    User, 
    "active_users.csv", 
    filters={"status": "active"}
)
```

### Health Check Utility

```python
from mongodb_orm.utils import HealthChecker

async def comprehensive_health_check():
    """Comprehensive system health check"""
    checker = HealthChecker()
    
    health_report = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Database connectivity
    health_report["checks"]["database"] = await checker.check_database_connection(User)
    
    # Model functionality
    health_report["checks"]["user_model"] = await checker.check_model_operations(User)
    
    # Performance benchmarks
    health_report["checks"]["performance"] = await checker.check_performance(User)
    
    # Data integrity
    health_report["checks"]["data_integrity"] = await checker.check_data_integrity(User)
    
    # Overall status
    all_healthy = all(
        check["status"] == "healthy" 
        for check in health_report["checks"].values()
    )
    health_report["overall_status"] = "healthy" if all_healthy else "unhealthy"
    
    return health_report

# Run health check
health = await comprehensive_health_check()
print(f"System status: {health['overall_status']}")
```
