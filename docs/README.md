# MongoDB ORM Documentation

Welcome to the complete documentation for MongoDB ORM - a modern, async MongoDB Object-Relational Mapping library for Python.

## Table of Contents

1. [Quick Start Guide](01-quick-start.md) - Get up and running in minutes
2. [Installation & Setup](02-installation.md) - Detailed installation instructions
3. [Model Definition](03-model-definition.md) - Define your data models
4. [Configuration](04-configuration.md) - Configure your database connection
5. [Connection Management](05-connection-management.md) - Manage database connections
6. [CRUD Operations](06-crud-operations.md) - Create, read, update, delete operations
7. [Query Methods](07-query-methods.md) - Advanced querying capabilities
8. [Aggregation](08-aggregation.md) - MongoDB aggregation pipelines
9. [Index Management](09-index-management.md) - Create and manage indexes
10. [Bulk Operations](10-bulk-operations.md) - Efficient bulk operations
11. [Error Handling](11-error-handling.md) - Comprehensive error handling
12. [Utilities & Helpers](12-utilities.md) - Utility functions and helpers
13. [Testing](13-testing.md) - Testing your MongoDB ORM applications
14. [Advanced Usage](14-advanced-usage.md) - Advanced patterns and techniques
15. [Migration Guide](15-migration-guide.md) - Migrate from other ODMs
16. [**API Reference**](16-api-reference.md) - **Complete API documentation**
17. [**Real-World Examples**](17-examples.md) - **Comprehensive application examples**
18. [Best Practices](18-best-practices.md) - Production-ready best practices
19. [Performance Tips](19-performance.md) - Optimization and performance tuning
20. [Troubleshooting](20-troubleshooting.md) - Common issues and solutions

## Overview

MongoDB ORM is a powerful, type-safe, and fully async Object-Relational Mapping library for MongoDB. Built on top of Motor (async MongoDB driver) and Pydantic (data validation), it provides a modern Python interface for MongoDB operations.

### Key Features

- ✨ **Fully Async**: Built from the ground up with async/await support
- 🔒 **Type Safe**: Leverages Pydantic v2 for robust data validation and type hints
- 🚀 **High Performance**: Uses Motor for efficient async MongoDB operations
- 🛡️ **Error Handling**: Comprehensive exception handling with custom exception types
- 🔧 **Flexible Configuration**: Environment-based configuration with sensible defaults
- 📊 **Connection Management**: Automatic connection pooling and cleanup
- 🗃️ **Rich Query API**: Intuitive methods for CRUD operations and aggregations
- 📈 **Indexing Support**: Easy index creation and management
- 🧪 **Testing Utilities**: Built-in utilities for testing and development
- ⚡ **Auto Timestamps**: Automatic `created_at` and `updated_at` fields
- 🏗️ **Convention over Configuration**: Sensible defaults with customization options

### Philosophy

This library follows the principle of **"Convention over Configuration"** while still providing flexibility when needed. It aims to make MongoDB operations as simple as possible while maintaining the power and flexibility of MongoDB.

### Requirements

- Python 3.8+
- MongoDB 4.0+
- Motor (async MongoDB driver)
- Pydantic v2 (data validation)

## Quick Example

```python
import asyncio
from datetime import datetime
from typing import Optional, List
from br_mongodb_orm import Document, configure_database
from pydantic import Field

# Define your model
class User(Document):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    age: Optional[int] = Field(None, ge=0, le=150)
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        collection_name = "users"  # Optional, defaults to "user"
        indexes = [
            ("email", 1),  # Simple index
            [("name", 1), ("age", -1)],  # Compound index
        ]

async def main():
    # Configure database
    await configure_database(
        database_url="mongodb://localhost:27017",
        database_name="myapp"
    )
    
    # Create indexes
    await User.create_indexes()
    
    # Create a user
    user = User(
        name="John Doe",
        email="john@example.com",
        age=30,
        tags=["developer", "python"]
    )
    saved_user = await user.save()
    print(f"Created user: {saved_user.id}")
    
    # Query users
    users = await User.find({"age": {"$gte": 18}})
    print(f"Found {len(users)} adult users")
    
    # Update user
    saved_user.age = 31
    await saved_user.save()
    
    # Advanced query with pagination
    recent_users = await User.find(
        filter_dict={"created_at": {"$gte": datetime(2024, 1, 1)}},
        sort=[("created_at", -1)],
        limit=10
    )

asyncio.run(main())
```

## What Makes This Documentation Special

### 📚 Complete Coverage
Every method, parameter, return type, and exception is documented with examples.

### 🏗️ Real-World Examples
The [Examples section](17-examples.md) includes complete, production-ready applications:
- **Blog Platform**: User management, posts, comments, categories, tags
- **E-commerce System**: Products, orders, cart, reviews, inventory
- **Task Management**: Projects, tasks, assignments, notifications
- **Social Media**: Users, posts, likes, follows, messaging
- **Analytics Dashboard**: Data aggregation, reporting, metrics

### 🔧 Practical API Reference
The [API Reference](16-api-reference.md) provides:
- Complete method signatures with all parameters
- Return type specifications
- Exception documentation
- Usage examples for every feature
- Type definitions and constants

### 🚀 Performance Guidance
Detailed performance optimization covering:
- Connection pooling strategies
- Query optimization techniques
- Indexing best practices
- Memory management
- Production deployment considerations

### 🛠️ Troubleshooting Support
Comprehensive troubleshooting guide with:
- Common error messages and solutions
- Debugging techniques
- Performance issue resolution
- Configuration problems
- Development workflow tips

## Getting Started

1. **Start with the [Quick Start Guide](01-quick-start.md)** for immediate results
2. **Review [Installation](02-installation.md)** for detailed setup
3. **Explore [Model Definition](03-model-definition.md)** to understand the core concepts
4. **Check [Real-World Examples](17-examples.md)** for complete application patterns
5. **Reference the [API Documentation](16-api-reference.md)** for detailed method information

## Learning Path

### Beginner
- Quick Start Guide
- Installation & Setup
- Model Definition
- Basic CRUD Operations

### Intermediate  
- Advanced Queries
- Aggregation Pipelines
- Index Management
- Error Handling

### Advanced
- Performance Optimization
- Real-World Examples
- Custom Utilities
- Production Deployment

## Community and Support

- **Documentation Issues**: Report inaccuracies or request clarifications
- **Feature Requests**: Suggest new functionality
- **Examples**: Contribute real-world usage examples
- **Performance**: Share optimization techniques

## Contributing to Documentation

This documentation is designed to be a complete reference that grows with the community. Contributions are welcome for:

- Additional real-world examples
- Performance optimization case studies
- Advanced usage patterns
- Tutorial improvements
- Error handling scenarios

---

*This documentation covers every aspect of MongoDB ORM, from basic usage to advanced production deployment. Whether you're building a simple application or a complex system, you'll find the guidance you need here.*
- MongoDB 4.0+
- motor>=3.5.1
- pydantic>=2.8.2
- pymongo>=4.0.0

### License

MIT License - see [LICENSE](../LICENSE) file for details.

---

**Next:** [Quick Start Guide](01-quick-start.md)
