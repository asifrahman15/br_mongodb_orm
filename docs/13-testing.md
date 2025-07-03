# Testing

MongoDB ORM provides comprehensive testing utilities and patterns to help you write robust tests for your applications.

## Table of Contents

- [Overview](#overview)
- [Test Setup](#test-setup)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [Mock Objects](#mock-objects)
- [Test Data Factories](#test-data-factories)
- [Performance Testing](#performance-testing)
- [Testing Best Practices](#testing-best-practices)
- [Examples](#examples)

## Overview

Testing with MongoDB ORM involves several strategies:

- **Unit Tests**: Test individual models and methods
- **Integration Tests**: Test database operations and workflows
- **Mock Testing**: Test without database dependencies
- **Performance Tests**: Validate performance characteristics
- **End-to-End Tests**: Test complete application workflows

The library provides utilities to support all these testing approaches.

## Test Setup

### Basic Test Configuration

```python
import pytest
import asyncio
from br_mongodb_orm import BaseModel, DatabaseConfig
from br_mongodb_orm.utils import TestDatabase

class User(BaseModel):
    name: str
    email: str
    age: int

class TestUserModel:
    """Test class for User model"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_db(self):
        """Set up test database for each test"""
        # Create test database configuration
        self.test_db = TestDatabase("test_br_mongodb_orm")
        await self.test_db.setup()
        
        # Initialize model with test database
        await User.__initialize__(db_config=self.test_db.config)
        
        yield
        
        # Cleanup after test
        await self.test_db.cleanup()
        await User._connection_manager.close()
```

### pytest Configuration

Create `conftest.py`:

```python
import pytest
import asyncio
from br_mongodb_orm import DatabaseConfig
from br_mongodb_orm.utils import TestDatabase

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_database():
    """Session-wide test database"""
    test_db = TestDatabase("test_session_db")
    await test_db.setup()
    yield test_db
    await test_db.cleanup()

@pytest.fixture
async def clean_database(test_database):
    """Clean database before each test"""
    await test_database.clear_all_collections()
    yield test_database

@pytest.fixture
async def sample_users():
    """Create sample users for testing"""
    users = []
    for i in range(5):
        user = User(
            name=f"User {i}",
            email=f"user{i}@example.com",
            age=20 + i
        )
        await user.save()
        users.append(user)
    return users
```

### Test Environment Configuration

```python
import os
from br_mongodb_orm import DatabaseConfig

def get_test_config():
    """Get configuration for testing environment"""
    if os.environ.get("CI"):
        # CI environment
        return DatabaseConfig(
            mongo_uri="mongodb://localhost:27017",
            database_name=f"test_ci_{os.environ.get('BUILD_ID', 'local')}"
        )
    else:
        # Local development
        return DatabaseConfig(
            mongo_uri="mongodb://localhost:27017",
            database_name="test_local_dev"
        )
```

## Unit Testing

### Model Validation Tests

```python
import pytest
from br_mongodb_orm.exceptions import ValidationError

class TestUserValidation:
    """Test user model validation"""
    
    async def test_valid_user_creation(self):
        """Test creating a valid user"""
        user = User(
            name="John Doe",
            email="john@example.com",
            age=30
        )
        
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.age == 30
        assert user.id is None  # Not saved yet
    
    async def test_invalid_email_validation(self):
        """Test invalid email validation"""
        with pytest.raises(ValidationError):
            User(
                name="John Doe",
                email="invalid-email",  # Invalid email
                age=30
            )
    
    async def test_negative_age_validation(self):
        """Test negative age validation"""
        with pytest.raises(ValidationError):
            User(
                name="John Doe",
                email="john@example.com",
                age=-5  # Invalid age
            )
    
    async def test_required_fields(self):
        """Test required field validation"""
        with pytest.raises(ValidationError):
            User(name="John Doe")  # Missing email and age
```

### CRUD Operation Tests

```python
class TestUserCRUD:
    """Test CRUD operations for User model"""
    
    async def test_create_user(self, clean_database):
        """Test user creation"""
        user = User(
            name="John Doe",
            email="john@example.com",
            age=30
        )
        
        # Save user
        saved_user = await user.save()
        
        assert saved_user.id is not None
        assert saved_user.created_at is not None
        assert saved_user.updated_at is not None
    
    async def test_get_user_by_id(self, clean_database):
        """Test getting user by ID"""
        # Create user
        user = User(name="Jane Doe", email="jane@example.com", age=25)
        await user.save()
        
        # Retrieve user
        found_user = await User.get_by_id(user.id)
        
        assert found_user is not None
        assert found_user.name == "Jane Doe"
        assert found_user.email == "jane@example.com"
    
    async def test_update_user(self, clean_database):
        """Test user update"""
        # Create user
        user = User(name="Bob Smith", email="bob@example.com", age=35)
        await user.save()
        original_updated_at = user.updated_at
        
        # Update user
        user.name = "Robert Smith"
        updated_user = await user.save()
        
        assert updated_user.name == "Robert Smith"
        assert updated_user.updated_at > original_updated_at
    
    async def test_delete_user(self, clean_database):
        """Test user deletion"""
        # Create user
        user = User(name="Test User", email="test@example.com", age=30)
        await user.save()
        user_id = user.id
        
        # Delete user
        deleted = await user.delete()
        assert deleted is True
        
        # Verify deletion
        found_user = await User.get_by_id(user_id)
        assert found_user is None
```

### Query Tests

```python
class TestUserQueries:
    """Test user query methods"""
    
    async def test_filter_by_age(self, clean_database, sample_users):
        """Test filtering users by age"""
        young_users = await User.filter(age={"$lt": 23})
        
        assert len(young_users) == 3  # Users 0, 1, 2 (ages 20, 21, 22)
        for user in young_users:
            assert user.age < 23
    
    async def test_sort_by_name(self, clean_database, sample_users):
        """Test sorting users by name"""
        sorted_users = await User.filter(sort_by={"name": 1})
        
        assert len(sorted_users) == 5
        # Verify sorting
        names = [user.name for user in sorted_users]
        assert names == sorted(names)
    
    async def test_pagination(self, clean_database, sample_users):
        """Test query pagination"""
        page1 = await User.filter(limit=2, skip=0, sort_by={"age": 1})
        page2 = await User.filter(limit=2, skip=2, sort_by={"age": 1})
        
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].age < page2[0].age
    
    async def test_count(self, clean_database, sample_users):
        """Test counting documents"""
        total_count = await User.count()
        active_count = await User.count(age={"$gte": 22})
        
        assert total_count == 5
        assert active_count == 3  # Users 2, 3, 4 (ages 22, 23, 24)
```

## Integration Testing

### Database Connection Tests

```python
class TestDatabaseIntegration:
    """Test database integration"""
    
    async def test_connection_initialization(self):
        """Test database connection setup"""
        # Test with custom configuration
        config = DatabaseConfig(
            mongo_uri="mongodb://localhost:27017",
            database_name="test_integration"
        )
        
        await User.__initialize__(db_config=config)
        
        assert User._initialized is True
        assert User._collection is not None
        assert User._connection_manager is not None
    
    async def test_connection_retry(self):
        """Test connection retry on failure"""
        # Test with invalid URI
        config = DatabaseConfig(
            mongo_uri="mongodb://invalid-host:27017",
            database_name="test_db"
        )
        
        with pytest.raises(ConnectionError):
            await User.__initialize__(db_config=config)
    
    async def test_concurrent_operations(self, clean_database):
        """Test concurrent database operations"""
        import asyncio
        
        async def create_user(index):
            user = User(
                name=f"Concurrent User {index}",
                email=f"user{index}@concurrent.com",
                age=20 + index
            )
            return await user.save()
        
        # Create users concurrently
        tasks = [create_user(i) for i in range(10)]
        users = await asyncio.gather(*tasks)
        
        assert len(users) == 10
        assert all(user.id is not None for user in users)
        
        # Verify all users are in database
        total_count = await User.count()
        assert total_count == 10
```

### Transaction Tests

```python
class TestTransactions:
    """Test transaction handling"""
    
    async def test_transaction_success(self, clean_database):
        """Test successful transaction"""
        # Note: This is a conceptual example
        # Actual transaction implementation would depend on your needs
        
        users_data = [
            {"name": "User 1", "email": "user1@tx.com", "age": 25},
            {"name": "User 2", "email": "user2@tx.com", "age": 30},
        ]
        
        try:
            # Simulate transaction
            created_users = []
            for data in users_data:
                user = User(**data)
                await user.save()
                created_users.append(user)
            
            # Verify all users created
            assert len(created_users) == 2
            total_count = await User.count()
            assert total_count == 2
            
        except Exception:
            # In real implementation, rollback would happen here
            raise
    
    async def test_transaction_rollback(self, clean_database):
        """Test transaction rollback on error"""
        # This is a conceptual example
        users_data = [
            {"name": "User 1", "email": "user1@tx.com", "age": 25},
            {"name": "User 2", "email": "invalid", "age": 30},  # Invalid email
        ]
        
        created_users = []
        try:
            for data in users_data:
                user = User(**data)
                await user.save()
                created_users.append(user)
        except ValidationError:
            # Clean up created users (simulate rollback)
            for user in created_users:
                await user.delete()
        
        # Verify no users remain
        total_count = await User.count()
        assert total_count == 0
```

## Mock Objects

### Model Mocking

```python
from unittest.mock import AsyncMock, MagicMock
import pytest

class TestUserMocking:
    """Test using mocks for User model"""
    
    async def test_mocked_user_save(self):
        """Test user save with mocking"""
        # Create mock user
        user = User(name="Mock User", email="mock@example.com", age=30)
        
        # Mock the save method
        user.save = AsyncMock(return_value=user)
        user.id = 123
        
        # Test the mocked save
        result = await user.save()
        
        assert result == user
        assert result.id == 123
        user.save.assert_called_once()
    
    async def test_mocked_user_queries(self):
        """Test user queries with mocking"""
        # Mock the filter method
        mock_users = [
            User(id=1, name="User 1", email="user1@example.com", age=25),
            User(id=2, name="User 2", email="user2@example.com", age=30),
        ]
        
        User.filter = AsyncMock(return_value=mock_users)
        
        # Test the mocked filter
        result = await User.filter(age={"$gte": 25})
        
        assert len(result) == 2
        assert result[0].name == "User 1"
        User.filter.assert_called_once_with(age={"$gte": 25})
```

### Database Mocking

```python
class MockDatabase:
    """Mock database for testing without MongoDB"""
    
    def __init__(self):
        self.collections = {}
        self.next_id = 1
    
    def get_collection(self, name):
        if name not in self.collections:
            self.collections[name] = []
        return MockCollection(self.collections[name], self)
    
    def generate_id(self):
        current_id = self.next_id
        self.next_id += 1
        return current_id

class MockCollection:
    """Mock collection for testing"""
    
    def __init__(self, data, database):
        self.data = data
        self.database = database
    
    async def insert_one(self, document):
        document["id"] = self.database.generate_id()
        self.data.append(document)
        return MagicMock(inserted_id=document["id"])
    
    async def find_one(self, filter_dict):
        for doc in self.data:
            if self._matches_filter(doc, filter_dict):
                return doc
        return None
    
    async def find(self, filter_dict=None):
        if filter_dict is None:
            return list(self.data)
        return [doc for doc in self.data if self._matches_filter(doc, filter_dict)]
    
    def _matches_filter(self, document, filter_dict):
        for key, value in filter_dict.items():
            if key not in document or document[key] != value:
                return False
        return True

# Usage in tests
@pytest.fixture
def mock_database():
    return MockDatabase()

async def test_with_mock_database(mock_database):
    """Test using mock database"""
    # Replace real database with mock
    User._collection = mock_database.get_collection("users")
    
    # Test operations
    user = User(name="Test User", email="test@example.com", age=30)
    await user.save()
    
    assert user.id is not None
    
    found_user = await User.get_by_id(user.id)
    assert found_user is not None
    assert found_user.name == "Test User"
```

## Test Data Factories

### User Factory

```python
import random
from faker import Faker

fake = Faker()

class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def build(**kwargs):
        """Build user data without saving"""
        data = {
            "name": fake.name(),
            "email": fake.email(),
            "age": random.randint(18, 80)
        }
        data.update(kwargs)
        return User(**data)
    
    @staticmethod
    async def create(**kwargs):
        """Create and save user"""
        user = UserFactory.build(**kwargs)
        await user.save()
        return user
    
    @staticmethod
    async def create_batch(count: int, **kwargs):
        """Create multiple users"""
        users = []
        for _ in range(count):
            user = await UserFactory.create(**kwargs)
            users.append(user)
        return users
    
    @staticmethod
    def admin_user(**kwargs):
        """Create admin user"""
        data = {
            "name": "Admin User",
            "email": "admin@example.com",
            "role": "admin",
            "is_active": True
        }
        data.update(kwargs)
        return UserFactory.build(**data)

# Usage in tests
async def test_user_factory(clean_database):
    """Test using user factory"""
    # Create single user
    user = await UserFactory.create(name="Specific Name")
    assert user.name == "Specific Name"
    assert user.id is not None
    
    # Create multiple users
    users = await UserFactory.create_batch(5, age=25)
    assert len(users) == 5
    assert all(user.age == 25 for user in users)
    
    # Create admin user
    admin = UserFactory.admin_user()
    assert admin.role == "admin"
```

### Scenario-Based Factories

```python
class TestScenarios:
    """Test scenarios using factories"""
    
    async def setup_e_commerce_scenario(self):
        """Set up e-commerce test scenario"""
        # Create admin user
        self.admin = await UserFactory.create(
            name="Admin User",
            email="admin@store.com",
            role="admin"
        )
        
        # Create regular customers
        self.customers = await UserFactory.create_batch(
            10,
            role="customer",
            is_active=True
        )
        
        # Create inactive users
        self.inactive_users = await UserFactory.create_batch(
            3,
            is_active=False
        )
    
    async def test_user_management_workflow(self, clean_database):
        """Test complete user management workflow"""
        await self.setup_e_commerce_scenario()
        
        # Test admin can see all users
        all_users = await User.all()
        assert len(all_users) == 14  # 1 admin + 10 customers + 3 inactive
        
        # Test active user filtering
        active_users = await User.filter(is_active=True)
        assert len(active_users) == 11  # 1 admin + 10 customers
        
        # Test role-based filtering
        customers = await User.filter(role="customer")
        assert len(customers) == 10
```

## Performance Testing

### Load Testing

```python
import asyncio
import time
from statistics import mean, median

class TestUserPerformance:
    """Performance tests for User model"""
    
    async def test_bulk_insert_performance(self, clean_database):
        """Test bulk insert performance"""
        users_data = [
            {
                "name": f"User {i}",
                "email": f"user{i}@perf.com",
                "age": 20 + (i % 50)
            }
            for i in range(1000)
        ]
        
        start_time = time.time()
        
        # Insert users
        for data in users_data:
            user = User(**data)
            await user.save()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Inserted 1000 users in {duration:.2f}s")
        print(f"Rate: {1000/duration:.0f} users/second")
        
        # Verify all users were created
        count = await User.count()
        assert count == 1000
        
        # Performance assertion
        assert duration < 30.0  # Should complete within 30 seconds
    
    async def test_query_performance(self, clean_database):
        """Test query performance"""
        # Create test data
        await UserFactory.create_batch(1000)
        
        # Test various query patterns
        query_times = []
        
        # Simple queries
        for _ in range(10):
            start = time.time()
            users = await User.filter(is_active=True, limit=50)
            duration = time.time() - start
            query_times.append(duration)
        
        avg_time = mean(query_times)
        median_time = median(query_times)
        
        print(f"Average query time: {avg_time:.3f}s")
        print(f"Median query time: {median_time:.3f}s")
        
        # Performance assertions
        assert avg_time < 0.1  # Average should be under 100ms
        assert median_time < 0.05  # Median should be under 50ms
    
    async def test_concurrent_access(self, clean_database):
        """Test concurrent access performance"""
        async def worker(worker_id):
            """Worker function for concurrent testing"""
            users = []
            for i in range(10):
                user = await UserFactory.create(
                    name=f"Worker {worker_id} User {i}"
                )
                users.append(user)
            return users
        
        start_time = time.time()
        
        # Run 10 concurrent workers
        tasks = [worker(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify results
        total_users = sum(len(worker_users) for worker_users in results)
        assert total_users == 100
        
        db_count = await User.count()
        assert db_count == 100
        
        print(f"Concurrent creation of 100 users took {duration:.2f}s")
        assert duration < 10.0  # Should complete within 10 seconds
```

### Memory Usage Testing

```python
import psutil
import os

class TestMemoryUsage:
    """Test memory usage patterns"""
    
    def get_memory_usage(self):
        """Get current memory usage"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    async def test_memory_usage_bulk_operations(self, clean_database):
        """Test memory usage during bulk operations"""
        initial_memory = self.get_memory_usage()
        
        # Create large dataset
        users_data = [
            UserFactory.build(name=f"User {i}")
            for i in range(10000)
        ]
        
        after_creation_memory = self.get_memory_usage()
        
        # Save all users
        for user in users_data:
            await user.save()
        
        after_save_memory = self.get_memory_usage()
        
        # Clear references
        del users_data
        
        final_memory = self.get_memory_usage()
        
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"After creation: {after_creation_memory:.1f} MB")
        print(f"After save: {after_save_memory:.1f} MB")
        print(f"Final memory: {final_memory:.1f} MB")
        
        # Memory usage assertions
        creation_increase = after_creation_memory - initial_memory
        save_increase = after_save_memory - after_creation_memory
        
        assert creation_increase < 100  # Should not use more than 100MB for object creation
        assert save_increase < 50      # Should not use more than 50MB additional for saving
```

## Testing Best Practices

### 1. Test Organization

```python
# tests/conftest.py - Shared fixtures
# tests/unit/ - Unit tests
# tests/integration/ - Integration tests  
# tests/performance/ - Performance tests
# tests/factories/ - Test data factories

# Example structure:
# tests/
#   ├── conftest.py
#   ├── unit/
#   │   ├── test_user_model.py
#   │   ├── test_validation.py
#   │   └── test_queries.py
#   ├── integration/
#   │   ├── test_database.py
#   │   └── test_workflows.py
#   └── factories/
#       └── user_factory.py
```

### 2. Test Isolation

```python
class TestIsolation:
    """Ensure test isolation"""
    
    @pytest.fixture(autouse=True)
    async def isolate_tests(self, clean_database):
        """Ensure each test starts with clean state"""
        # This fixture runs before each test
        yield
        # Cleanup after each test
        await User.delete_many()  # Clear all users
    
    async def test_user_creation_isolated(self):
        """Test runs in isolation"""
        user = await UserFactory.create()
        count = await User.count()
        assert count == 1
    
    async def test_another_isolated_test(self):
        """This test also starts with clean database"""
        count = await User.count()
        assert count == 0  # Starts clean due to isolation
```

### 3. Test Data Management

```python
class TestDataManagement:
    """Best practices for test data management"""
    
    @pytest.fixture
    async def small_dataset(self):
        """Small dataset for quick tests"""
        return await UserFactory.create_batch(5)
    
    @pytest.fixture
    async def large_dataset(self):
        """Large dataset for performance tests"""
        return await UserFactory.create_batch(1000)
    
    @pytest.fixture
    async def specific_users(self):
        """Specific users for edge case testing"""
        return {
            "admin": await UserFactory.create(role="admin"),
            "regular": await UserFactory.create(role="user"),
            "inactive": await UserFactory.create(is_active=False),
            "old": await UserFactory.create(age=90),
            "young": await UserFactory.create(age=18),
        }
    
    async def test_with_specific_data(self, specific_users):
        """Test using specific test data"""
        admin = specific_users["admin"]
        assert admin.role == "admin"
        
        young = specific_users["young"]
        assert young.age == 18
```

## Examples

### Complete Test Suite Example

```python
# tests/test_user_complete.py
import pytest
from br_mongodb_orm.exceptions import ValidationError, DocumentNotFoundError

class TestUserComplete:
    """Complete test suite for User model"""
    
    # Test fixtures and setup
    @pytest.fixture(autouse=True)
    async def setup(self, clean_database):
        """Set up for each test"""
        self.test_data = {
            "valid_user": {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30
            },
            "invalid_user": {
                "name": "",
                "email": "invalid-email",
                "age": -1
            }
        }
    
    # Validation tests
    async def test_valid_user_creation(self):
        user = User(**self.test_data["valid_user"])
        assert user.name == "John Doe"
    
    async def test_invalid_user_validation(self):
        with pytest.raises(ValidationError):
            User(**self.test_data["invalid_user"])
    
    # CRUD tests
    async def test_create_read_update_delete(self):
        # Create
        user = User(**self.test_data["valid_user"])
        await user.save()
        assert user.id is not None
        
        # Read
        found = await User.get_by_id(user.id)
        assert found.name == "John Doe"
        
        # Update
        found.name = "Jane Doe"
        await found.save()
        updated = await User.get_by_id(user.id)
        assert updated.name == "Jane Doe"
        
        # Delete
        await updated.delete()
        deleted = await User.get_by_id(user.id)
        assert deleted is None
    
    # Query tests
    async def test_complex_queries(self):
        # Create test data
        users = await UserFactory.create_batch(10)
        
        # Test filtering
        young_users = await User.filter(age={"$lt": 25})
        assert len(young_users) >= 0
        
        # Test sorting
        sorted_users = await User.filter(sort_by={"name": 1})
        names = [u.name for u in sorted_users]
        assert names == sorted(names)
        
        # Test pagination
        page1 = await User.filter(limit=5, skip=0)
        page2 = await User.filter(limit=5, skip=5)
        assert len(page1) <= 5
        assert len(page2) <= 5
    
    # Error handling tests
    async def test_error_handling(self):
        # Test not found
        user = await User.get_by_id(999999)
        assert user is None
        
        # Test duplicate handling would go here
        # (depends on your unique constraints)
    
    # Performance tests
    async def test_bulk_operations(self):
        start_time = time.time()
        
        # Create many users
        users = []
        for i in range(100):
            user = User(
                name=f"Bulk User {i}",
                email=f"bulk{i}@example.com",
                age=20 + (i % 50)
            )
            await user.save()
            users.append(user)
        
        duration = time.time() - start_time
        
        # Verify creation
        count = await User.count()
        assert count >= 100
        
        # Performance check
        print(f"Created 100 users in {duration:.2f}s")
        # assert duration < 10.0  # Uncomment for strict timing
```

This comprehensive testing documentation provides everything needed to thoroughly test MongoDB ORM applications, from unit tests to performance testing, with practical examples and best practices.
