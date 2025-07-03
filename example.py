# Example usage of the MongoDB ORM

import asyncio
import os
from typing import Optional, List
from datetime import datetime

# Set environment variables for this example
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DATABASE"] = "example_db"

from br_mongodb_orm import (
    BaseModel, 
    register_all_models,
    close_all_connections,
    setup_logging
)


# Simple models without Meta class - everything is automatic!
class User(BaseModel):
    """User model - collection will be 'user' automatically"""
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
    # created_at and updated_at are automatically added by BaseModel


class BlogPost(BaseModel):
    """BlogPost model - collection will be 'blog_post' automatically"""
    title: str
    content: str
    author_id: int
    tags: List[str] = []
    published: bool = False
    view_count: int = 0


class UserProfile(BaseModel):
    """UserProfile model - collection will be 'user_profile' automatically"""
    user_id: int
    bio: str
    website: Optional[str] = None
    social_links: dict = {}


# Example with custom Meta class (if you need to override defaults)
class CustomCollection(BaseModel):
    """Example with custom configuration"""
    name: str
    value: int

    class Meta:
        collection_name = "my_custom_collection"  # Override default
        auto_create_indexes = False  # Disable auto-indexing
        use_auto_id = False  # Use MongoDB's _id instead


async def demonstrate_automatic_collections():
    """Demonstrate automatic collection naming"""
    print("\n=== Automatic Collection Naming Demo ===")

    # All these models will automatically get collection names:
    # User -> 'user'
    # BlogPost -> 'blog_post' 
    # UserProfile -> 'user_profile'

    # Create some data
    user = await User.create(
        name="John Smith",
        email="john@example.com",
        age=25
    )
    print(f"Created user in collection: user")
    print(f"User: {user}")

    profile = await UserProfile.create(
        user_id=user.id,
        bio="Software developer passionate about Python",
        website="https://johnsmith.dev",
        social_links={"twitter": "@johnsmith", "github": "johnsmith"}
    )
    print(f"Created profile in collection: user_profile")
    print(f"Profile: {profile}")

    post = await BlogPost.create(
        title="My First Blog Post",
        content="This is my first post about MongoDB ORM",
        author_id=user.id,
        tags=["mongodb", "python", "orm"],
        published=True,
        view_count=0
    )
    print(f"Created post in collection: blog_post")
    print(f"Post: {post}")

    return user, profile, post


async def demonstrate_minimal_setup():
    """Show how minimal the setup can be"""
    print("\n=== Minimal Setup Demo ===")

    # This is all you need for a simple model!
    class Product(BaseModel):
        name: str
        price: float
        in_stock: bool = True

    # Register the model
    await Product.__initialize__()

    # Use it immediately
    product = await Product.create(
        name="Laptop",
        price=999.99,
        in_stock=True
    )
    print(f"Created product: {product}")
    print(f"Collection name automatically set to: 'product'")

    # Query it
    all_products = await Product.all()
    print(f"Found {len(all_products)} products")

    # Clean up
    await Product.delete_many()
    print("Cleaned up products")


async def demonstrate_smart_naming():
    """Demonstrate smart collection naming conversion"""
    print("\n=== Smart Collection Naming Demo ===")

    class ShoppingCart(BaseModel):
        items: List[dict] = []
        total_price: float = 0.0

    class APIKey(BaseModel):
        key: str
        user_id: int
        is_active: bool = True

    class XMLDocument(BaseModel):
        content: str
        format: str = "xml"

    # Initialize models
    await ShoppingCart.__initialize__()
    await APIKey.__initialize__()
    await XMLDocument.__initialize__()

    # Show the automatically generated collection names
    print(f"ShoppingCart -> collection: 'shopping_cart'")
    print(f"APIKey -> collection: 'api_key'")
    print(f"XMLDocument -> collection: 'xml_document'")

    # Create some test data
    cart = await ShoppingCart.create(
        items=[{"name": "Book", "price": 19.99}],
        total_price=19.99
    )
    print(f"Created cart: {cart}")

    # Clean up
    await ShoppingCart.delete_many()
    await APIKey.delete_many()
    await XMLDocument.delete_many()


async def demonstrate_basic_operations():
    """Demonstrate basic CRUD operations"""
    print("\n=== Basic Operations Demo ===")

    # Create a user (indexes are created automatically)
    user = await User.create(
        name="Alice Johnson",
        email="alice@example.com",
        age=28
    )
    print(f"Created user: {user}")

    # Get user by ID
    found_user = await User.get_by_id(user.id)
    print(f"Found user by ID: {found_user}")

    # Update user
    found_user.age = 29
    await found_user.save()
    print(f"Updated user age: {found_user.age}")

    # Create multiple posts
    posts_data = [
        {
            "title": "Getting Started with MongoDB",
            "content": "This is a guide for beginners...",
            "author_id": user.id,
            "tags": ["mongodb", "tutorial", "database"],
            "published": True
        },
        {
            "title": "Advanced MongoDB Queries", 
            "content": "Let's explore complex queries...",
            "author_id": user.id,
            "tags": ["mongodb", "advanced", "queries"],
            "published": False
        }
    ]

    posts = await BlogPost.bulk_create(posts_data)
    print(f"Created {len(posts)} posts")

    # Query posts
    user_posts = await BlogPost.filter(author_id=user.id)
    print(f"User has {len(user_posts)} posts")

    published_posts = await BlogPost.filter(published=True)
    print(f"Found {len(published_posts)} published posts")

    return user, posts


async def cleanup_demo_data():
    """Clean up demo data"""
    print("\n=== Cleanup ===")

    # Delete all demo data
    deleted_posts = await BlogPost.delete_many()
    deleted_profiles = await UserProfile.delete_many()
    deleted_users = await User.delete_many()

    print(f"Deleted {deleted_posts} posts")
    print(f"Deleted {deleted_profiles} profiles")
    print(f"Deleted {deleted_users} users")


async def main():
    """Main demo function"""
    # Setup logging
    setup_logging(level="INFO")

    try:
        # Initialize models - this is all you need!
        print("Initializing models...")
        await register_all_models(__name__)
        print("Models initialized successfully!")
        print("✅ No Meta class required!")
        print("✅ Collection names auto-generated!")
        print("✅ Indexes created automatically!")

        # Run demonstrations
        await demonstrate_automatic_collections()
        await demonstrate_minimal_setup()
        await demonstrate_smart_naming()
        user, posts = await demonstrate_basic_operations()

        # Show advanced features with the created data
        await demonstrate_advanced_queries()
        await demonstrate_indexing()
        await demonstrate_error_handling()

        # Clean up
        await cleanup_demo_data()

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close all connections
        print("\nClosing database connections...")
        await close_all_connections()
        print("Demo completed!")


if __name__ == "__main__":
    # Run the demo
    print("MongoDB ORM Demo - Simplified!")
    print("==============================")
    print("This demo shows how simple the ORM can be:")
    print("• Just define your model fields")
    print("• Set MONGO_URI and MONGO_DATABASE environment variables")
    print("• Collection names are auto-generated from class names")
    print("• Indexes are created automatically")
    print("• No Meta class required for basic usage!")
    print()
    print("Make sure MongoDB is running on localhost:27017")

    # Run async main
    asyncio.run(main())


async def demonstrate_advanced_queries():
    """Demonstrate advanced query operations"""
    print("\n=== Advanced Queries Demo ===")

    # Count documents
    total_users = await User.count()
    active_users = await User.count(is_active=True)
    print(f"Total users: {total_users}, Active users: {active_users}")

    # Get distinct values
    unique_tags = await BlogPost.distinct("tags")
    print(f"Unique tags: {unique_tags}")

    # Aggregation example
    pipeline = [
        {"$match": {"published": True}},
        {"$group": {
            "_id": "$author_id",
            "post_count": {"$sum": 1},
            "total_views": {"$sum": "$view_count"},
            "avg_views": {"$avg": "$view_count"}
        }},
        {"$sort": {"post_count": -1}}
    ]

    author_stats = await BlogPost.aggregate(pipeline)
    print(f"Author statistics: {author_stats}")


async def demonstrate_indexing():
    """Demonstrate index management"""
    print("\n=== Indexing Demo ===")

    # Create single field index
    await User.create_index("email", unique=True)
    print("Created unique index on email field")

    # Create compound index
    await BlogPost.create_compound_index({
        "author_id": 1,
        "published": 1,
        "created_at": -1
    })
    print("Created compound index on blog posts")

    # List indexes
    user_indexes = await User.list_indexes()
    print(f"User indexes: {list(user_indexes.keys())}")


async def demonstrate_error_handling():
    """Demonstrate error handling"""
    print("\n=== Error Handling Demo ===")

    from br_mongodb_orm import ValidationError, DocumentNotFoundError

    try:
        # Try to create user with invalid data
        invalid_user = await User.create(name="", email="invalid-email")
    except ValidationError as e:
        print(f"✅ Validation error caught: {e}")

    try:
        # Try to find non-existent user
        missing_user = await User.get_by_id(999999)
        if not missing_user:
            print("✅ User not found (returned None)")
    except DocumentNotFoundError as e:
        print(f"Document not found error: {e}")


async def cleanup_demo_data():
    """Clean up demo data"""
    print("\n=== Cleanup ===")

    # Delete all demo data
    deleted_posts = await BlogPost.delete_many()
    deleted_profiles = await UserProfile.delete_many()
    deleted_users = await User.delete_many()

    print(f"Deleted {deleted_posts} posts")
    print(f"Deleted {deleted_profiles} profiles")
    print(f"Deleted {deleted_users} users")


async def main():
    """Main demo function"""
    # Setup logging
    setup_logging(level="INFO")

    try:
        # Initialize models
        print("Initializing models...")
        await register_all_models(__name__)
        print("Models initialized successfully!")

        # Run demonstrations
        user, posts = await demonstrate_basic_operations()
        await demonstrate_advanced_queries()
        await demonstrate_indexing()
        await demonstrate_error_handling()

        # Clean up
        await cleanup_demo_data()

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close all connections
        print("\nClosing database connections...")
        await close_all_connections()
        print("Demo completed!")


if __name__ == "__main__":
    # Run the demo
    print("MongoDB ORM Demo")
    print("================")
    print("Make sure MongoDB is running on localhost:27017")
    print("This demo will create and delete test data")

    # Run async main
    asyncio.run(main())
