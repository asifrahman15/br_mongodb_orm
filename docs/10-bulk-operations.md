# Bulk Operations

MongoDB ORM provides efficient bulk operations for handling large datasets with optimal performance.

## Table of Contents

- [Overview](#overview)
- [Bulk Insert Operations](#bulk-insert-operations)
- [Bulk Update Operations](#bulk-update-operations)
- [Bulk Delete Operations](#bulk-delete-operations)
- [Mixed Bulk Operations](#mixed-bulk-operations)
- [Performance Considerations](#performance-considerations)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview

Bulk operations allow you to perform multiple database operations in a single round-trip, significantly improving performance when dealing with large amounts of data.

Benefits of bulk operations:
- **Reduced Network Overhead**: Multiple operations in one request
- **Better Performance**: Optimized database processing
- **Atomic Operations**: Operations grouped together
- **Memory Efficiency**: Streaming large datasets

MongoDB ORM provides both ordered and unordered bulk operations through utility functions.

## Bulk Insert Operations

### Basic Bulk Insert

```python
from py_mongo_orm import BaseModel
from py_mongo_orm.utils import bulk_insert

class User(BaseModel):
    name: str
    email: str
    age: int

# Create multiple users
users_data = [
    {"name": "John Doe", "email": "john@example.com", "age": 30},
    {"name": "Jane Smith", "email": "jane@example.com", "age": 25},
    {"name": "Bob Johnson", "email": "bob@example.com", "age": 35},
]

# Bulk insert
inserted_count = await bulk_insert(User, users_data)
print(f"Inserted {inserted_count} users")
```

### Large Dataset Insertion

```python
async def import_users_from_csv(file_path: str):
    """Import users from CSV file using bulk operations"""
    import csv
    
    users_data = []
    batch_size = 1000
    
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            users_data.append({
                "name": row["name"],
                "email": row["email"],
                "age": int(row["age"])
            })
            
            # Insert in batches
            if len(users_data) >= batch_size:
                count = await bulk_insert(User, users_data)
                print(f"Inserted batch of {count} users")
                users_data = []
        
        # Insert remaining users
        if users_data:
            count = await bulk_insert(User, users_data)
            print(f"Inserted final batch of {count} users")

# Usage
await import_users_from_csv("users.csv")
```

### Bulk Insert with Validation

```python
from typing import List, Dict, Any
from py_mongo_orm.exceptions import ValidationError

async def safe_bulk_insert(model_class, data_list: List[Dict[str, Any]]):
    """Bulk insert with validation and error handling"""
    valid_data = []
    errors = []
    
    # Validate each record
    for i, data in enumerate(data_list):
        try:
            # Create model instance for validation
            instance = model_class(**data)
            valid_data.append(instance.model_dump())
        except ValidationError as e:
            errors.append(f"Row {i}: {e}")
    
    if errors:
        print(f"Validation errors: {errors}")
        
    if valid_data:
        count = await bulk_insert(model_class, valid_data)
        return count, errors
    
    return 0, errors

# Usage
count, errors = await safe_bulk_insert(User, users_data)
```

## Bulk Update Operations

### Basic Bulk Update

```python
from py_mongo_orm.utils import bulk_update

# Update multiple users
updates = [
    {"filter": {"age": {"$lt": 30}}, "update": {"$set": {"status": "young"}}},
    {"filter": {"age": {"$gte": 30}}, "update": {"$set": {"status": "mature"}}},
]

result = await bulk_update(User, updates)
print(f"Updated {result.modified_count} documents")
```

### Conditional Bulk Updates

```python
async def update_user_tiers():
    """Update user tiers based on various criteria"""
    
    updates = [
        # Platinum tier: high spenders
        {
            "filter": {"total_spent": {"$gte": 1000}},
            "update": {"$set": {"tier": "platinum", "discount": 0.15}}
        },
        # Gold tier: medium spenders  
        {
            "filter": {"total_spent": {"$gte": 500, "$lt": 1000}},
            "update": {"$set": {"tier": "gold", "discount": 0.10}}
        },
        # Silver tier: low spenders
        {
            "filter": {"total_spent": {"$gte": 100, "$lt": 500}},
            "update": {"$set": {"tier": "silver", "discount": 0.05}}
        },
        # Bronze tier: minimal spenders
        {
            "filter": {"total_spent": {"$lt": 100}},
            "update": {"$set": {"tier": "bronze", "discount": 0.0}}
        }
    ]
    
    result = await bulk_update(User, updates)
    return result.modified_count

# Update tiers
updated_count = await update_user_tiers()
```

### Bulk Upsert Operations

```python
async def sync_external_data(external_users: List[Dict]):
    """Sync external user data using upserts"""
    
    upserts = []
    for user_data in external_users:
        upserts.append({
            "filter": {"external_id": user_data["id"]},
            "update": {
                "$set": {
                    "name": user_data["name"],
                    "email": user_data["email"],
                    "last_sync": datetime.now(UTC)
                }
            },
            "upsert": True  # Create if doesn't exist
        })
    
    result = await bulk_update(User, upserts)
    print(f"Upserted {result.upserted_count} new documents")
    print(f"Modified {result.modified_count} existing documents")
```

## Bulk Delete Operations

### Basic Bulk Delete

```python
from py_mongo_orm.utils import bulk_delete

# Delete operations
deletes = [
    {"filter": {"is_active": False}},           # Delete inactive users
    {"filter": {"last_login": {"$lt": old_date}}},  # Delete old users
]

result = await bulk_delete(User, deletes)
print(f"Deleted {result.deleted_count} documents")
```

### Conditional Bulk Delete

```python
from datetime import datetime, timedelta

async def cleanup_old_data():
    """Clean up old and inactive data"""
    
    # Define cutoff dates
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    one_year_ago = datetime.now(UTC) - timedelta(days=365)
    
    deletes = [
        # Delete unverified users older than 30 days
        {
            "filter": {
                "is_verified": False,
                "created_at": {"$lt": thirty_days_ago}
            }
        },
        # Delete inactive users older than 1 year
        {
            "filter": {
                "is_active": False,
                "last_login": {"$lt": one_year_ago}
            }
        },
        # Delete soft-deleted users
        {
            "filter": {"status": "deleted"}
        }
    ]
    
    result = await bulk_delete(User, deletes)
    return result.deleted_count

# Cleanup
deleted_count = await cleanup_old_data()
```

## Mixed Bulk Operations

### Combined Operations

```python
from py_mongo_orm.utils import bulk_write

async def process_user_batch(user_updates: List[Dict]):
    """Process a batch of user operations"""
    
    operations = []
    
    for update in user_updates:
        action = update["action"]
        data = update["data"]
        
        if action == "insert":
            operations.append({
                "insert_one": {"document": data}
            })
        elif action == "update":
            operations.append({
                "update_one": {
                    "filter": {"id": data["id"]},
                    "update": {"$set": data},
                    "upsert": False
                }
            })
        elif action == "delete":
            operations.append({
                "delete_one": {"filter": {"id": data["id"]}}
            })
    
    result = await bulk_write(User, operations)
    return {
        "inserted": result.inserted_count,
        "modified": result.modified_count, 
        "deleted": result.deleted_count
    }

# Usage
batch_updates = [
    {"action": "insert", "data": {"name": "New User", "email": "new@example.com"}},
    {"action": "update", "data": {"id": 123, "name": "Updated Name"}},
    {"action": "delete", "data": {"id": 456}},
]

result = await process_user_batch(batch_updates)
```

## Performance Considerations

### Batch Size Optimization

```python
async def optimal_bulk_insert(model_class, data_list: List[Dict], batch_size: int = 1000):
    """Insert data in optimal batch sizes"""
    
    total_inserted = 0
    
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        count = await bulk_insert(model_class, batch)
        total_inserted += count
        
        # Progress reporting
        if i % (batch_size * 10) == 0:
            progress = (i / len(data_list)) * 100
            print(f"Progress: {progress:.1f}% ({total_inserted} inserted)")
    
    return total_inserted

# Usage with optimal batch size
await optimal_bulk_insert(User, large_dataset, batch_size=500)
```

### Memory-Efficient Processing

```python
async def stream_bulk_insert(model_class, data_generator, batch_size: int = 1000):
    """Memory-efficient bulk insert using generators"""
    
    batch = []
    total_inserted = 0
    
    async for data in data_generator:
        batch.append(data)
        
        if len(batch) >= batch_size:
            count = await bulk_insert(model_class, batch)
            total_inserted += count
            batch = []
    
    # Insert remaining data
    if batch:
        count = await bulk_insert(model_class, batch)
        total_inserted += count
    
    return total_inserted

# Usage with async generator
async def user_data_generator():
    """Generate user data asynchronously"""
    for i in range(100000):
        yield {
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "age": 20 + (i % 60)
        }

total = await stream_bulk_insert(User, user_data_generator())
```

### Performance Monitoring

```python
import time
from typing import List, Dict

async def monitored_bulk_insert(model_class, data_list: List[Dict], batch_size: int = 1000):
    """Bulk insert with performance monitoring"""
    
    start_time = time.time()
    total_inserted = 0
    batch_times = []
    
    for i in range(0, len(data_list), batch_size):
        batch_start = time.time()
        batch = data_list[i:i + batch_size]
        
        count = await bulk_insert(model_class, batch)
        total_inserted += count
        
        batch_time = time.time() - batch_start
        batch_times.append(batch_time)
        
        # Performance metrics
        docs_per_second = len(batch) / batch_time
        print(f"Batch {i//batch_size + 1}: {len(batch)} docs in {batch_time:.2f}s ({docs_per_second:.0f} docs/s)")
    
    total_time = time.time() - start_time
    avg_batch_time = sum(batch_times) / len(batch_times)
    overall_rate = total_inserted / total_time
    
    print(f"\nSummary:")
    print(f"Total inserted: {total_inserted}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average batch time: {avg_batch_time:.2f}s")
    print(f"Overall rate: {overall_rate:.0f} docs/s")
    
    return total_inserted
```

## Error Handling

### Partial Failure Handling

```python
from py_mongo_orm.exceptions import BulkWriteError

async def resilient_bulk_insert(model_class, data_list: List[Dict]):
    """Bulk insert with error recovery"""
    
    try:
        count = await bulk_insert(model_class, data_list)
        return count, []
    
    except BulkWriteError as e:
        # Handle partial failures
        successful_count = e.details.get("nInserted", 0)
        errors = e.details.get("writeErrors", [])
        
        print(f"Partial success: {successful_count} inserted")
        print(f"Errors: {len(errors)}")
        
        # Retry failed operations
        failed_data = []
        for error in errors:
            index = error.get("index")
            if index is not None and index < len(data_list):
                failed_data.append(data_list[index])
        
        return successful_count, failed_data

# Usage
count, failures = await resilient_bulk_insert(User, users_data)
if failures:
    print(f"Retrying {len(failures)} failed inserts...")
    # Implement retry logic
```

### Validation Error Handling

```python
async def validated_bulk_operations(model_class, operations: List[Dict]):
    """Bulk operations with comprehensive validation"""
    
    validated_ops = []
    validation_errors = []
    
    for i, op in enumerate(operations):
        try:
            # Validate operation structure
            if "insert_one" in op:
                # Validate document
                model_class(**op["insert_one"]["document"])
            elif "update_one" in op:
                # Validate update operation
                if "$set" in op["update_one"]["update"]:
                    model_class(**op["update_one"]["update"]["$set"])
            
            validated_ops.append(op)
            
        except Exception as e:
            validation_errors.append(f"Operation {i}: {e}")
    
    if validation_errors:
        print(f"Validation errors: {validation_errors}")
    
    if validated_ops:
        result = await bulk_write(model_class, validated_ops)
        return result, validation_errors
    
    return None, validation_errors
```

## Examples

### Data Migration

```python
async def migrate_user_data():
    """Migrate user data from old format to new format"""
    
    # Get all users in old format
    old_users = await OldUser.all()
    
    # Transform to new format
    new_user_data = []
    for old_user in old_users:
        new_user_data.append({
            "name": f"{old_user.first_name} {old_user.last_name}",
            "email": old_user.email_address,
            "age": old_user.age,
            "profile": {
                "bio": old_user.biography,
                "avatar_url": old_user.avatar
            },
            "migrated_from": old_user.id,
            "migrated_at": datetime.now(UTC)
        })
    
    # Bulk insert new users
    count = await bulk_insert(NewUser, new_user_data, batch_size=500)
    print(f"Migrated {count} users")
    
    # Mark old users as migrated
    updates = [{
        "filter": {"id": {"$in": [u.id for u in old_users]}},
        "update": {"$set": {"migrated": True, "migrated_at": datetime.now(UTC)}}
    }]
    
    result = await bulk_update(OldUser, updates)
    print(f"Marked {result.modified_count} old users as migrated")
```

### Data Synchronization

```python
async def sync_with_external_api():
    """Synchronize data with external API"""
    
    # Fetch data from external API
    external_data = await fetch_external_users()
    
    # Prepare upsert operations
    operations = []
    for user_data in external_data:
        operations.append({
            "update_one": {
                "filter": {"external_id": user_data["id"]},
                "update": {
                    "$set": {
                        "name": user_data["name"],
                        "email": user_data["email"],
                        "external_updated_at": user_data["updated_at"],
                        "last_sync": datetime.now(UTC)
                    }
                },
                "upsert": True
            }
        })
    
    result = await bulk_write(User, operations)
    
    print(f"Synchronized {len(external_data)} users:")
    print(f"  - Created: {result.upserted_count}")
    print(f"  - Updated: {result.modified_count}")
```

### Analytics Data Processing

```python
async def process_analytics_events():
    """Process large volumes of analytics events"""
    
    # Read events from queue/file
    events = await read_analytics_events()
    
    # Group events by type for bulk processing
    events_by_type = {}
    for event in events:
        event_type = event["type"]
        if event_type not in events_by_type:
            events_by_type[event_type] = []
        events_by_type[event_type].append(event)
    
    # Process each event type
    for event_type, type_events in events_by_type.items():
        print(f"Processing {len(type_events)} {event_type} events...")
        
        # Bulk insert events
        count = await bulk_insert(AnalyticsEvent, type_events, batch_size=2000)
        print(f"Inserted {count} {event_type} events")
        
        # Update aggregated statistics
        if event_type == "page_view":
            await update_page_view_stats(type_events)
        elif event_type == "user_action":
            await update_user_action_stats(type_events)

async def update_page_view_stats(events: List[Dict]):
    """Update page view statistics using bulk operations"""
    
    # Group by page
    page_views = {}
    for event in events:
        page = event["page"]
        if page not in page_views:
            page_views[page] = 0
        page_views[page] += 1
    
    # Bulk update page statistics
    updates = []
    for page, count in page_views.items():
        updates.append({
            "filter": {"page": page},
            "update": {
                "$inc": {"view_count": count},
                "$set": {"last_updated": datetime.now(UTC)}
            },
            "upsert": True
        })
    
    result = await bulk_update(PageStats, updates)
    print(f"Updated statistics for {result.modified_count + result.upserted_count} pages")
```

### Data Cleanup and Maintenance

```python
async def monthly_data_cleanup():
    """Monthly data cleanup using bulk operations"""
    
    from datetime import datetime, timedelta
    
    # Define cleanup criteria
    one_month_ago = datetime.now(UTC) - timedelta(days=30)
    six_months_ago = datetime.now(UTC) - timedelta(days=180)
    one_year_ago = datetime.now(UTC) - timedelta(days=365)
    
    # Cleanup operations
    cleanup_results = {}
    
    # 1. Delete expired sessions
    session_deletes = [{
        "filter": {"expires_at": {"$lt": datetime.now(UTC)}}
    }]
    result = await bulk_delete(UserSession, session_deletes)
    cleanup_results["expired_sessions"] = result.deleted_count
    
    # 2. Archive old logs
    log_updates = [{
        "filter": {"created_at": {"$lt": six_months_ago}},
        "update": {"$set": {"archived": True, "archived_at": datetime.now(UTC)}}
    }]
    result = await bulk_update(ApplicationLog, log_updates)
    cleanup_results["archived_logs"] = result.modified_count
    
    # 3. Delete old temporary files
    temp_deletes = [{
        "filter": {
            "file_type": "temporary",
            "created_at": {"$lt": one_month_ago}
        }
    }]
    result = await bulk_delete(FileRecord, temp_deletes)
    cleanup_results["temp_files"] = result.deleted_count
    
    # 4. Update user activity flags
    user_updates = [
        {
            "filter": {"last_login": {"$lt": six_months_ago}},
            "update": {"$set": {"status": "inactive"}}
        },
        {
            "filter": {"last_login": {"$lt": one_year_ago}},
            "update": {"$set": {"status": "dormant"}}
        }
    ]
    result = await bulk_update(User, user_updates)
    cleanup_results["user_status_updates"] = result.modified_count
    
    return cleanup_results

# Run monthly cleanup
results = await monthly_data_cleanup()
print(f"Cleanup completed: {results}")
```
