# Migration Guide

This guide helps you migrate from other MongoDB libraries or upgrade between versions of MongoDB ORM.

## Table of Contents

- [Overview](#overview)
- [Migrating from PyMongo](#migrating-from-pymongo)
- [Migrating from MongoEngine](#migrating-from-mongoengine)
- [Migrating from Motor](#migrating-from-motor)
- [Version Upgrade Guide](#version-upgrade-guide)
- [Schema Migration](#schema-migration)
- [Data Migration](#data-migration)
- [Best Practices](#best-practices)
- [Common Issues](#common-issues)

## Overview

MongoDB ORM provides migration utilities and patterns to help you:

- **Migrate from other libraries**: PyMongo, MongoEngine, Motor, etc.
- **Upgrade between versions**: Handle breaking changes
- **Schema migrations**: Evolve your data structure
- **Data migrations**: Transform existing data
- **Rollback capabilities**: Safely revert changes

## Migrating from PyMongo

### Before (PyMongo)

```python
import pymongo
from datetime import datetime

# Connection setup
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client.my_database
users_collection = db.users

# Create user
user_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": datetime.now()
}
result = users_collection.insert_one(user_data)
user_id = result.inserted_id

# Find user
user = users_collection.find_one({"_id": user_id})

# Update user
users_collection.update_one(
    {"_id": user_id},
    {"$set": {"name": "Jane Doe"}}
)

# Delete user
users_collection.delete_one({"_id": user_id})
```

### After (MongoDB ORM)

```python
from py_mongo_orm import BaseModel
from datetime import datetime

# Model definition
class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        collection_name = "users"

# Initialize
await User.__initialize__()

# Create user
user = User(name="John Doe", email="john@example.com")
await user.save()

# Find user
user = await User.get_by_id(user.id)

# Update user
user.name = "Jane Doe"
await user.save()

# Delete user
await user.delete()
```

### Migration Script for PyMongo

```python
async def migrate_from_pymongo():
    """Migrate existing PyMongo code to MongoDB ORM"""
    
    # 1. Define models for existing collections
    class User(BaseModel):
        name: str
        email: str
        # Map existing fields as needed
        
        class Meta:
            collection_name = "users"  # Use existing collection name
    
    # 2. Initialize models
    await User.__initialize__()
    
    # 3. Verify data integrity
    pymongo_count = users_collection.count_documents({})
    orm_count = await User.count()
    
    print(f"PyMongo count: {pymongo_count}")
    print(f"ORM count: {orm_count}")
    
    if pymongo_count != orm_count:
        print("WARNING: Data counts don't match!")
    
    # 4. Test basic operations
    test_user = await User.get(email="test@example.com")
    if test_user:
        print(f"Successfully loaded user: {test_user.name}")
    
    return True
```

## Migrating from MongoEngine

### Before (MongoEngine)

```python
from mongoengine import Document, StringField, EmailField, DateTimeField, connect
from datetime import datetime

# Connection
connect('my_database')

# Model definition
class User(Document):
    name = StringField(required=True, max_length=100)
    email = EmailField(required=True, unique=True)
    created_at = DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'users',
        'indexes': ['email']
    }

# Usage
user = User(name="John Doe", email="john@example.com")
user.save()

# Query
users = User.objects(name__icontains="john")
user = User.objects(email="john@example.com").first()
```

### After (MongoDB ORM)

```python
from py_mongo_orm import BaseModel
from typing import Optional

class User(BaseModel):
    name: str
    email: str
    
    class Meta:
        collection_name = "users"
        auto_create_indexes = True

# Initialize
await User.__initialize__()
await User.create_index("email", unique=True)

# Usage
user = User(name="John Doe", email="john@example.com")
await user.save()

# Query
users = await User.filter(name={"$regex": "john", "$options": "i"})
user = await User.get(email="john@example.com")
```

### MongoEngine Migration Script

```python
async def migrate_from_mongoengine():
    """Migrate from MongoEngine to MongoDB ORM"""
    
    # 1. Map MongoEngine models to MongoDB ORM models
    model_mapping = {
        'User': User,
        'Product': Product,
        # Add other models
    }
    
    # 2. Initialize MongoDB ORM models
    for orm_model in model_mapping.values():
        await orm_model.__initialize__()
    
    # 3. Migrate indexes
    # MongoEngine indexes are defined in meta, recreate them
    await User.create_index("email", unique=True)
    await Product.create_index("category")
    
    # 4. Validate data
    for model_name, orm_model in model_mapping.items():
        # Get MongoEngine collection
        mongoengine_collection = eval(model_name)._get_collection()
        mongoengine_count = mongoengine_collection.count_documents({})
        
        # Get ORM count
        orm_count = await orm_model.count()
        
        print(f"{model_name}: MongoEngine={mongoengine_count}, ORM={orm_count}")
        
        if mongoengine_count != orm_count:
            print(f"WARNING: {model_name} counts don't match!")
    
    return True
```

## Migrating from Motor

### Before (Motor)

```python
import motor.motor_asyncio
from datetime import datetime

# Connection
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client.my_database
users_collection = db.users

# Create user
async def create_user():
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "created_at": datetime.now()
    }
    result = await users_collection.insert_one(user_data)
    return result.inserted_id

# Find user
async def find_user(email):
    return await users_collection.find_one({"email": email})

# Update user
async def update_user(user_id, updates):
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": updates}
    )
```

### After (MongoDB ORM)

```python
from py_mongo_orm import BaseModel

class User(BaseModel):
    name: str
    email: str

# Initialize
await User.__initialize__()

# Create user
async def create_user():
    user = User(name="John Doe", email="john@example.com")
    await user.save()
    return user.id

# Find user
async def find_user(email):
    return await User.get(email=email)

# Update user
async def update_user(user_id, updates):
    user = await User.get_by_id(user_id)
    if user:
        for key, value in updates.items():
            setattr(user, key, value)
        await user.save()
```

### Motor Migration Script

```python
async def migrate_from_motor():
    """Migrate from Motor to MongoDB ORM"""
    
    # 1. Use existing Motor client with MongoDB ORM
    motor_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    
    # Initialize models with existing client
    await User.__initialize__(client=motor_client)
    
    # 2. Test compatibility
    # Motor and MongoDB ORM can coexist
    motor_collection = motor_client.my_database.users
    
    # Insert via Motor
    motor_result = await motor_collection.insert_one({
        "name": "Motor User",
        "email": "motor@example.com"
    })
    
    # Read via ORM
    orm_user = await User.get(email="motor@example.com")
    print(f"Found user via ORM: {orm_user.name}")
    
    # Insert via ORM
    orm_user = User(name="ORM User", email="orm@example.com")
    await orm_user.save()
    
    # Read via Motor
    motor_user = await motor_collection.find_one({"email": "orm@example.com"})
    print(f"Found user via Motor: {motor_user['name']}")
    
    return True
```

## Version Upgrade Guide

### Upgrading from v1.0 to v2.0

```python
# Version 1.0 (deprecated)
class User(BaseModel):
    name: str
    email: str
    
    class Config:  # Old configuration
        collection = "users"
        auto_id = True

# Version 2.0 (current)
class User(BaseModel):
    name: str
    email: str
    
    class Meta:  # New configuration
        collection_name = "users"
        use_auto_id = True
        auto_create_indexes = True
```

### Migration Script for Version Upgrade

```python
async def upgrade_v1_to_v2():
    """Upgrade from v1.0 to v2.0"""
    
    # 1. Update model definitions
    # Replace Config with Meta class
    # Update configuration attribute names
    
    # 2. Handle breaking changes
    # Old: created_date -> New: created_at
    # Old: modified_date -> New: updated_at
    
    migration_queries = [
        # Rename fields
        {
            "collection": "users",
            "update": {
                "$rename": {
                    "created_date": "created_at",
                    "modified_date": "updated_at"
                }
            }
        },
        
        # Add new required fields with default values
        {
            "collection": "users", 
            "update": {
                "$set": {
                    "is_active": True  # New field with default
                }
            },
            "filter": {"is_active": {"$exists": False}}
        }
    ]
    
    # Apply migrations
    for migration in migration_queries:
        collection = User._collection
        if migration.get("filter"):
            await collection.update_many(
                migration["filter"],
                migration["update"]
            )
        else:
            await collection.update_many(
                {},
                migration["update"]
            )
    
    print("Migration completed successfully")
    return True
```

## Schema Migration

### Schema Migration Framework

```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any

class Migration(ABC):
    """Base class for schema migrations"""
    
    def __init__(self):
        self.version: str = "0.0.0"
        self.description: str = ""
        self.dependencies: List[str] = []
    
    @abstractmethod
    async def up(self):
        """Apply migration"""
        pass
    
    @abstractmethod
    async def down(self):
        """Rollback migration"""
        pass

class MigrationRunner:
    """Migration runner to manage schema changes"""
    
    def __init__(self):
        self.migrations: List[Migration] = []
        self.applied_migrations: List[str] = []
    
    def register_migration(self, migration: Migration):
        """Register a migration"""
        self.migrations.append(migration)
    
    async def run_migrations(self):
        """Run all pending migrations"""
        # Load applied migrations from database
        await self._load_applied_migrations()
        
        # Sort migrations by version
        self.migrations.sort(key=lambda m: m.version)
        
        # Run pending migrations
        for migration in self.migrations:
            if migration.version not in self.applied_migrations:
                print(f"Running migration {migration.version}: {migration.description}")
                
                try:
                    await migration.up()
                    await self._mark_migration_applied(migration)
                    print(f"Migration {migration.version} completed")
                except Exception as e:
                    print(f"Migration {migration.version} failed: {e}")
                    raise
    
    async def rollback_migration(self, version: str):
        """Rollback a specific migration"""
        migration = next(
            (m for m in self.migrations if m.version == version),
            None
        )
        
        if not migration:
            raise ValueError(f"Migration {version} not found")
        
        if version in self.applied_migrations:
            print(f"Rolling back migration {version}")
            await migration.down()
            await self._mark_migration_unapplied(migration)
            print(f"Migration {version} rolled back")
    
    async def _load_applied_migrations(self):
        """Load applied migrations from database"""
        # Implementation would load from a migrations collection
        pass
    
    async def _mark_migration_applied(self, migration: Migration):
        """Mark migration as applied"""
        # Implementation would save to migrations collection
        pass
    
    async def _mark_migration_unapplied(self, migration: Migration):
        """Mark migration as unapplied"""
        # Implementation would remove from migrations collection
        pass
```

### Example Schema Migrations

```python
class AddUserStatusMigration(Migration):
    """Add status field to users"""
    
    def __init__(self):
        super().__init__()
        self.version = "2023.01.001"
        self.description = "Add status field to users with default value"
    
    async def up(self):
        """Add status field"""
        # Add status field with default value
        await User._collection.update_many(
            {"status": {"$exists": False}},
            {"$set": {"status": "active"}}
        )
        
        # Create index on status
        await User.create_index("status")
    
    async def down(self):
        """Remove status field"""
        await User._collection.update_many(
            {},
            {"$unset": {"status": ""}}
        )

class NormalizeEmailsMigration(Migration):
    """Normalize email addresses to lowercase"""
    
    def __init__(self):
        super().__init__()
        self.version = "2023.01.002"
        self.description = "Normalize email addresses to lowercase"
    
    async def up(self):
        """Normalize emails"""
        # Get all users with uppercase emails
        cursor = User._collection.find(
            {"email": {"$regex": "[A-Z]"}}
        )
        
        async for doc in cursor:
            normalized_email = doc["email"].lower()
            await User._collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"email": normalized_email}}
            )
    
    async def down(self):
        """Cannot rollback email normalization"""
        print("WARNING: Email normalization cannot be rolled back")

class SplitNameFieldMigration(Migration):
    """Split name field into first_name and last_name"""
    
    def __init__(self):
        super().__init__()
        self.version = "2023.01.003"
        self.description = "Split name field into first_name and last_name"
    
    async def up(self):
        """Split name field"""
        cursor = User._collection.find({"name": {"$exists": True}})
        
        async for doc in cursor:
            name_parts = doc["name"].split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            await User._collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "first_name": first_name,
                        "last_name": last_name
                    },
                    "$unset": {"name": ""}
                }
            )
    
    async def down(self):
        """Combine first_name and last_name back to name"""
        cursor = User._collection.find({
            "first_name": {"$exists": True},
            "last_name": {"$exists": True}
        })
        
        async for doc in cursor:
            full_name = f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip()
            
            await User._collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {"name": full_name},
                    "$unset": {"first_name": "", "last_name": ""}
                }
            )
```

## Data Migration

### Data Migration Patterns

```python
class DataMigrator:
    """Utility for data migrations"""
    
    @staticmethod
    async def migrate_collection_data(
        source_collection: str,
        target_collection: str,
        transform_func: callable,
        batch_size: int = 1000
    ):
        """Migrate data between collections with transformation"""
        
        # Get source collection
        source = User._connection_manager._database[source_collection]
        target = User._connection_manager._database[target_collection]
        
        # Process in batches
        cursor = source.find({})
        batch = []
        
        async for doc in cursor:
            # Transform document
            transformed_doc = await transform_func(doc)
            if transformed_doc:
                batch.append(transformed_doc)
            
            # Insert batch when full
            if len(batch) >= batch_size:
                await target.insert_many(batch)
                batch = []
                print(f"Migrated {batch_size} documents")
        
        # Insert remaining documents
        if batch:
            await target.insert_many(batch)
            print(f"Migrated final {len(batch)} documents")
    
    @staticmethod
    async def transform_user_data(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform user document format"""
        # Example transformation
        return {
            "id": doc.get("_id"),
            "name": doc.get("name"),
            "email": doc.get("email", "").lower(),
            "created_at": doc.get("created_date", datetime.now()),
            "updated_at": doc.get("modified_date", datetime.now()),
            "is_active": doc.get("active", True),
            "metadata": {
                "migrated_from": "old_users",
                "migration_date": datetime.now()
            }
        }
    
    @staticmethod
    async def migrate_user_data():
        """Migrate user data from old format"""
        await DataMigrator.migrate_collection_data(
            "old_users",
            "users",
            DataMigrator.transform_user_data
        )
```

### Batch Processing for Large Datasets

```python
async def migrate_large_dataset():
    """Migrate large dataset efficiently"""
    
    batch_size = 5000
    processed = 0
    
    # Get total count for progress tracking
    total = await User._collection.count_documents({})
    
    # Process in batches
    while processed < total:
        # Get batch of documents
        cursor = User._collection.find({}).skip(processed).limit(batch_size)
        batch = await cursor.to_list(length=batch_size)
        
        if not batch:
            break
        
        # Transform batch
        transformed_batch = []
        for doc in batch:
            # Apply transformations
            doc["migrated"] = True
            doc["migration_date"] = datetime.now()
            transformed_batch.append(doc)
        
        # Update documents
        for doc in transformed_batch:
            await User._collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "migrated": doc["migrated"],
                    "migration_date": doc["migration_date"]
                }}
            )
        
        processed += len(batch)
        progress = (processed / total) * 100
        print(f"Migration progress: {progress:.1f}% ({processed}/{total})")
        
        # Add delay to avoid overwhelming the database
        await asyncio.sleep(0.1)
    
    print("Migration completed successfully")
```

## Best Practices

### 1. Migration Planning

```python
class MigrationPlanner:
    """Plan and validate migrations before execution"""
    
    @staticmethod
    async def validate_migration(migration: Migration):
        """Validate migration before running"""
        checks = []
        
        # Check 1: Backup exists
        checks.append(await MigrationPlanner._check_backup_exists())
        
        # Check 2: Database connectivity
        checks.append(await MigrationPlanner._check_connectivity())
        
        # Check 3: Sufficient disk space
        checks.append(await MigrationPlanner._check_disk_space())
        
        # Check 4: Migration dependencies
        checks.append(await MigrationPlanner._check_dependencies(migration))
        
        return all(checks)
    
    @staticmethod
    async def _check_backup_exists() -> bool:
        """Check if backup exists"""
        # Implementation would check for backup
        return True
    
    @staticmethod
    async def _check_connectivity() -> bool:
        """Check database connectivity"""
        try:
            await User.count()
            return True
        except Exception:
            return False
    
    @staticmethod
    async def _check_disk_space() -> bool:
        """Check available disk space"""
        # Implementation would check disk space
        return True
    
    @staticmethod
    async def _check_dependencies(migration: Migration) -> bool:
        """Check migration dependencies"""
        # Implementation would verify dependencies
        return True
```

### 2. Safe Migration Execution

```python
async def safe_migration_execution():
    """Execute migrations safely with rollback capability"""
    
    migration_runner = MigrationRunner()
    
    try:
        # 1. Create backup
        print("Creating backup...")
        await create_backup()
        
        # 2. Validate migration
        print("Validating migration...")
        for migration in migration_runner.migrations:
            is_valid = await MigrationPlanner.validate_migration(migration)
            if not is_valid:
                raise Exception(f"Migration {migration.version} validation failed")
        
        # 3. Run migration in transaction (if supported)
        print("Running migrations...")
        await migration_runner.run_migrations()
        
        # 4. Validate results
        print("Validating results...")
        await validate_migration_results()
        
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        
        # Rollback
        print("Rolling back migration...")
        await rollback_migration()
        
        # Restore from backup if needed
        print("Restoring from backup...")
        await restore_from_backup()
        
        raise

async def create_backup():
    """Create database backup"""
    # Implementation would create backup
    pass

async def validate_migration_results():
    """Validate migration results"""
    # Implementation would validate results
    pass

async def rollback_migration():
    """Rollback migration"""
    # Implementation would rollback
    pass

async def restore_from_backup():
    """Restore from backup"""
    # Implementation would restore
    pass
```

### 3. Testing Migrations

```python
import pytest

class TestMigrations:
    """Test migration scripts"""
    
    @pytest.fixture
    async def test_database(self):
        """Set up test database"""
        test_config = DatabaseConfig(
            mongo_uri="mongodb://localhost:27017",
            database_name="test_migration_db"
        )
        
        await User.__initialize__(db_config=test_config)
        yield
        
        # Cleanup
        await User._connection_manager._database.drop_collection("users")
    
    async def test_add_status_migration(self, test_database):
        """Test adding status field migration"""
        # Create test data without status field
        await User._collection.insert_many([
            {"name": "User 1", "email": "user1@example.com"},
            {"name": "User 2", "email": "user2@example.com"},
        ])
        
        # Run migration
        migration = AddUserStatusMigration()
        await migration.up()
        
        # Verify results
        users = await User._collection.find({}).to_list(length=10)
        assert all(user.get("status") == "active" for user in users)
        
        # Test rollback
        await migration.down()
        users = await User._collection.find({}).to_list(length=10)
        assert all("status" not in user for user in users)
    
    async def test_email_normalization_migration(self, test_database):
        """Test email normalization migration"""
        # Create test data with mixed case emails
        await User._collection.insert_many([
            {"name": "User 1", "email": "User1@EXAMPLE.com"},
            {"name": "User 2", "email": "USER2@example.COM"},
        ])
        
        # Run migration
        migration = NormalizeEmailsMigration()
        await migration.up()
        
        # Verify results
        users = await User._collection.find({}).to_list(length=10)
        for user in users:
            assert user["email"] == user["email"].lower()
```

## Common Issues

### 1. Data Type Conflicts

```python
async def handle_data_type_conflicts():
    """Handle data type conflicts during migration"""
    
    # Issue: Field stored as string but model expects int
    problematic_docs = await User._collection.find({
        "age": {"$type": "string"}
    }).to_list(length=1000)
    
    for doc in problematic_docs:
        try:
            # Convert string to int
            age_int = int(doc["age"])
            await User._collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"age": age_int}}
            )
        except (ValueError, TypeError):
            # Handle invalid values
            await User._collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"age": 0}}  # Default value
            )
```

### 2. Index Conflicts

```python
async def handle_index_conflicts():
    """Handle index conflicts during migration"""
    
    try:
        # Try to create unique index
        await User.create_index("email", unique=True)
    except Exception as e:
        if "duplicate key" in str(e).lower():
            print("Duplicate emails found, cleaning up...")
            
            # Find and handle duplicates
            pipeline = [
                {"$group": {
                    "_id": "$email",
                    "count": {"$sum": 1},
                    "docs": {"$push": "$_id"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await User._collection.aggregate(pipeline).to_list(length=1000)
            
            for dup in duplicates:
                # Keep first document, remove others
                docs_to_remove = dup["docs"][1:]
                await User._collection.delete_many({
                    "_id": {"$in": docs_to_remove}
                })
            
            # Retry index creation
            await User.create_index("email", unique=True)
```

### 3. Performance Issues

```python
async def optimize_migration_performance():
    """Optimize migration performance for large datasets"""
    
    # Use bulk operations instead of individual updates
    bulk_ops = []
    
    cursor = User._collection.find({})
    async for doc in cursor:
        # Prepare bulk operation
        bulk_ops.append({
            "update_one": {
                "filter": {"_id": doc["_id"]},
                "update": {"$set": {"migrated": True}}
            }
        })
        
        # Execute in batches
        if len(bulk_ops) >= 1000:
            await User._collection.bulk_write(bulk_ops)
            bulk_ops = []
    
    # Execute remaining operations
    if bulk_ops:
        await User._collection.bulk_write(bulk_ops)
```

This migration guide provides comprehensive strategies for migrating to MongoDB ORM from other libraries and handling version upgrades, schema changes, and data transformations safely and efficiently.
