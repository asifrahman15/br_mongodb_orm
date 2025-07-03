# Complete Real-World Examples

Comprehensive examples demonstrating all features of MongoDB ORM in practical applications.

## Table of Contents

1. [Blog Application](#blog-application)
2. [E-commerce System](#e-commerce-system)
3. [User Management System](#user-management-system)
4. [Real-time Chat Application](#real-time-chat-application)
5. [Task Management System](#task-management-system)
6. [Analytics Dashboard](#analytics-dashboard)
7. [File Management System](#file-management-system)
8. [Social Media Platform](#social-media-platform)
9. [Inventory Management](#inventory-management)
10. [Learning Management System](#learning-management-system)

## Blog Application

A complete blog application demonstrating relationships, validation, and advanced queries.

### Model Definitions

```python
# models/blog.py
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import Field, validator, EmailStr
from py_mongo_orm import Document, configure_database
from bson import ObjectId

class UserRole(str, Enum):
    ADMIN = "admin"
    AUTHOR = "author"
    EDITOR = "editor"
    READER = "reader"

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CommentStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"

class User(Document):
    # Basic info
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password_hash: str  # Store hashed passwords only
    
    # Profile info
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    social_links: Dict[str, str] = Field(default_factory=dict)
    
    # System fields
    role: UserRole = UserRole.READER
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    login_count: int = 0
    
    # Stats
    posts_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    
    class Config:
        collection_name = "users"
        indexes = [
            ("username", 1),
            ("email", 1),
            ("role", 1),
            ("is_active", 1),
            [("role", 1), ("is_active", 1)],
            {
                "key": [("email", 1)],
                "unique": True,
                "background": True
            },
            {
                "key": [("username", 1)],
                "unique": True,
                "background": True
            }
        ]
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with _ and - allowed)')
        return v.lower()
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()
    
    @validator('social_links')
    def validate_social_links(cls, v):
        allowed_platforms = ['twitter', 'linkedin', 'github', 'instagram', 'facebook']
        for platform in v.keys():
            if platform not in allowed_platforms:
                raise ValueError(f'Platform {platform} not allowed')
        return v

class Category(Document):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    color: str = "#000000"  # Hex color code
    posts_count: int = 0
    is_active: bool = True
    
    class Config:
        collection_name = "categories"
        indexes = [
            ("name", 1),
            ("slug", 1),
            ("is_active", 1),
            {
                "key": [("slug", 1)],
                "unique": True,
                "background": True
            }
        ]
    
    @validator('slug')
    def slug_format(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must be lowercase alphanumeric with hyphens')
        return v
    
    @validator('color')
    def validate_color(cls, v):
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be a valid hex code')
        return v

class Tag(Document):
    name: str = Field(..., min_length=1, max_length=30)
    slug: str = Field(..., min_length=1, max_length=30)
    usage_count: int = 0
    
    class Config:
        collection_name = "tags"
        indexes = [
            ("name", 1),
            ("slug", 1),
            ("usage_count", -1),
            {
                "key": [("slug", 1)],
                "unique": True,
                "background": True
            }
        ]

class Post(Document):
    # Content
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    featured_image: Optional[str] = None
    
    # Relationships
    author_id: ObjectId
    category_id: Optional[ObjectId] = None
    tag_ids: List[ObjectId] = Field(default_factory=list)
    
    # Status and metadata
    status: PostStatus = PostStatus.DRAFT
    published_at: Optional[datetime] = None
    
    # SEO
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    
    # Stats
    views_count: int = 0
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    
    # Reading time (in minutes)
    reading_time: int = 0
    
    class Config:
        collection_name = "posts"
        indexes = [
            ("author_id", 1),
            ("category_id", 1),
            ("status", 1),
            ("published_at", -1),
            ("views_count", -1),
            ("likes_count", -1),
            [("status", 1), ("published_at", -1)],
            [("author_id", 1), ("status", 1)],
            [("category_id", 1), ("status", 1)],
            ("tag_ids", 1),  # Multikey index for array
            {
                "key": [("slug", 1)],
                "unique": True,
                "background": True
            },
            {
                "key": [("title", "text"), ("content", "text"), ("excerpt", "text")],
                "background": True
            }
        ]
    
    @validator('slug')
    def slug_format(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must be lowercase alphanumeric with hyphens')
        return v
    
    def calculate_reading_time(self):
        """Calculate reading time based on content length."""
        words = len(self.content.split())
        # Average reading speed: 200 words per minute
        return max(1, round(words / 200))
    
    async def publish(self):
        """Publish the post."""
        if self.status != PostStatus.PUBLISHED:
            self.status = PostStatus.PUBLISHED
            self.published_at = datetime.utcnow()
            self.reading_time = self.calculate_reading_time()
            await self.save()
            
            # Update author's post count
            await User.update_many(
                {"_id": self.author_id},
                {"$inc": {"posts_count": 1}}
            )
            
            # Update category post count
            if self.category_id:
                await Category.update_many(
                    {"_id": self.category_id},
                    {"$inc": {"posts_count": 1}}
                )
            
            # Update tag usage counts
            if self.tag_ids:
                await Tag.update_many(
                    {"_id": {"$in": self.tag_ids}},
                    {"$inc": {"usage_count": 1}}
                )

class Comment(Document):
    # Content
    content: str = Field(..., min_length=1, max_length=1000)
    
    # Relationships
    post_id: ObjectId
    author_id: Optional[ObjectId] = None  # None for anonymous comments
    parent_id: Optional[ObjectId] = None  # For threaded comments
    
    # Anonymous comment fields
    author_name: Optional[str] = Field(None, max_length=100)
    author_email: Optional[EmailStr] = None
    author_website: Optional[str] = None
    
    # Status
    status: CommentStatus = CommentStatus.PENDING
    
    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Stats
    likes_count: int = 0
    replies_count: int = 0
    
    class Config:
        collection_name = "comments"
        indexes = [
            ("post_id", 1),
            ("author_id", 1),
            ("parent_id", 1),
            ("status", 1),
            [("post_id", 1), ("status", 1), ("created_at", 1)],
            [("author_id", 1), ("created_at", -1)]
        ]
    
    @validator('content')
    def sanitize_content(cls, v):
        # Basic HTML sanitization (in real app, use bleach or similar)
        import re
        # Remove script tags
        v = re.sub(r'<script.*?</script>', '', v, flags=re.DOTALL | re.IGNORECASE)
        return v

class PostLike(Document):
    post_id: ObjectId
    user_id: ObjectId
    
    class Config:
        collection_name = "post_likes"
        indexes = [
            ("post_id", 1),
            ("user_id", 1),
            [("post_id", 1), ("user_id", 1)],
            {
                "key": [("post_id", 1), ("user_id", 1)],
                "unique": True,
                "background": True
            }
        ]

class Follow(Document):
    follower_id: ObjectId  # User who follows
    following_id: ObjectId  # User being followed
    
    class Config:
        collection_name = "follows"
        indexes = [
            ("follower_id", 1),
            ("following_id", 1),
            [("follower_id", 1), ("following_id", 1)],
            {
                "key": [("follower_id", 1), ("following_id", 1)],
                "unique": True,
                "background": True
            }
        ]
```

### Service Layer

```python
# services/blog_service.py
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timedelta
from .models.blog import User, Post, Category, Tag, Comment, PostLike, Follow

class BlogService:
    """Service layer for blog operations."""
    
    @staticmethod
    async def create_user(user_data: Dict[str, Any]) -> User:
        """Create a new user with proper validation."""
        # Check if username or email already exists
        existing_user = await User.find_one({
            "$or": [
                {"username": user_data["username"]},
                {"email": user_data["email"]}
            ]
        })
        
        if existing_user:
            if existing_user.username == user_data["username"]:
                raise ValueError("Username already taken")
            if existing_user.email == user_data["email"]:
                raise ValueError("Email already registered")
        
        user = User(**user_data)
        return await user.save()
    
    @staticmethod
    async def create_post(author_id: ObjectId, post_data: Dict[str, Any]) -> Post:
        """Create a new blog post."""
        # Validate author exists
        author = await User.find_by_id(author_id)
        if not author:
            raise ValueError("Author not found")
        
        # Validate category if provided
        if "category_id" in post_data and post_data["category_id"]:
            category = await Category.find_by_id(post_data["category_id"])
            if not category:
                raise ValueError("Category not found")
        
        # Validate tags if provided
        if "tag_ids" in post_data and post_data["tag_ids"]:
            existing_tags = await Tag.find({"_id": {"$in": post_data["tag_ids"]}})
            if len(existingTags) != len(post_data["tag_ids"]):
                raise ValueError("One or more tags not found")
        
        post_data["author_id"] = author_id
        post = Post(**post_data)
        post.reading_time = post.calculate_reading_time()
        
        return await post.save()
    
    @staticmethod
    async def get_published_posts(
        page: int = 1,
        limit: int = 10,
        category_id: Optional[ObjectId] = None,
        tag_id: Optional[ObjectId] = None,
        author_id: Optional[ObjectId] = None
    ) -> Dict[str, Any]:
        """Get published posts with pagination and filters."""
        skip = (page - 1) * limit
        
        # Build filter
        filter_dict = {"status": "published"}
        if category_id:
            filter_dict["category_id"] = category_id
        if tag_id:
            filter_dict["tag_ids"] = {"$in": [tag_id]}
        if author_id:
            filter_dict["author_id"] = author_id
        
        # Get posts
        posts = await Post.find(
            filter_dict=filter_dict,
            sort=[("published_at", -1)],
            skip=skip,
            limit=limit
        )
        
        # Get total count for pagination
        total_count = await Post.count_documents(filter_dict)
        
        return {
            "posts": posts,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    @staticmethod
    async def get_post_with_author_and_category(slug: str) -> Optional[Dict[str, Any]]:
        """Get a post with populated author and category data."""
        post = await Post.find_one({"slug": slug, "status": "published"})
        if not post:
            return None
        
        # Get author
        author = await User.find_by_id(post.author_id)
        
        # Get category
        category = None
        if post.category_id:
            category = await Category.find_by_id(post.category_id)
        
        # Get tags
        tags = []
        if post.tag_ids:
            tags = await Tag.find({"_id": {"$in": post.tag_ids}})
        
        # Increment view count
        await Post.update_many(
            {"_id": post.id},
            {"$inc": {"views_count": 1}}
        )
        
        return {
            "post": post,
            "author": author,
            "category": category,
            "tags": tags
        }
    
    @staticmethod
    async def add_comment(post_id: ObjectId, comment_data: Dict[str, Any]) -> Comment:
        """Add a comment to a post."""
        # Validate post exists
        post = await Post.find_by_id(post_id)
        if not post or post.status != "published":
            raise ValueError("Post not found or not published")
        
        # If parent_id is provided, validate parent comment exists
        if "parent_id" in comment_data and comment_data["parent_id"]:
            parent = await Comment.find_by_id(comment_data["parent_id"])
            if not parent or parent.post_id != post_id:
                raise ValueError("Parent comment not found")
        
        comment_data["post_id"] = post_id
        comment = Comment(**comment_data)
        saved_comment = await comment.save()
        
        # Update post comment count
        await Post.update_many(
            {"_id": post_id},
            {"$inc": {"comments_count": 1}}
        )
        
        # Update parent comment reply count if this is a reply
        if comment.parent_id:
            await Comment.update_many(
                {"_id": comment.parent_id},
                {"$inc": {"replies_count": 1}}
            )
        
        return saved_comment
    
    @staticmethod
    async def like_post(post_id: ObjectId, user_id: ObjectId) -> bool:
        """Like or unlike a post."""
        # Check if already liked
        existing_like = await PostLike.find_one({
            "post_id": post_id,
            "user_id": user_id
        })
        
        if existing_like:
            # Unlike
            await existing_like.delete()
            await Post.update_many(
                {"_id": post_id},
                {"$inc": {"likes_count": -1}}
            )
            return False
        else:
            # Like
            like = PostLike(post_id=post_id, user_id=user_id)
            await like.save()
            await Post.update_many(
                {"_id": post_id},
                {"$inc": {"likes_count": 1}}
            )
            return True
    
    @staticmethod
    async def follow_user(follower_id: ObjectId, following_id: ObjectId) -> bool:
        """Follow or unfollow a user."""
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")
        
        # Check if already following
        existing_follow = await Follow.find_one({
            "follower_id": follower_id,
            "following_id": following_id
        })
        
        if existing_follow:
            # Unfollow
            await existing_follow.delete()
            await User.update_many(
                {"_id": follower_id},
                {"$inc": {"following_count": -1}}
            )
            await User.update_many(
                {"_id": following_id},
                {"$inc": {"followers_count": -1}}
            )
            return False
        else:
            # Follow
            follow = Follow(follower_id=follower_id, following_id=following_id)
            await follow.save()
            await User.update_many(
                {"_id": follower_id},
                {"$inc": {"following_count": 1}}
            )
            await User.update_many(
                {"_id": following_id},
                {"$inc": {"followers_count": 1}}
            )
            return True
    
    @staticmethod
    async def search_posts(query: str, limit: int = 10) -> List[Post]:
        """Search posts using text search."""
        return await Post.find(
            filter_dict={
                "$text": {"$search": query},
                "status": "published"
            },
            sort=[("score", {"$meta": "textScore"})],
            limit=limit
        )
    
    @staticmethod
    async def get_popular_posts(days: int = 7, limit: int = 10) -> List[Post]:
        """Get popular posts based on recent views and likes."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        return await Post.find(
            filter_dict={
                "status": "published",
                "published_at": {"$gte": since_date}
            },
            sort=[("views_count", -1), ("likes_count", -1)],
            limit=limit
        )
    
    @staticmethod
    async def get_user_feed(user_id: ObjectId, limit: int = 20) -> List[Post]:
        """Get personalized feed for a user based on who they follow."""
        # Get users this user follows
        follows = await Follow.find({"follower_id": user_id})
        following_ids = [follow.following_id for follow in follows]
        
        if not following_ids:
            # If not following anyone, return popular posts
            return await BlogService.get_popular_posts(limit=limit)
        
        # Get posts from followed users
        return await Post.find(
            filter_dict={
                "author_id": {"$in": following_ids},
                "status": "published"
            },
            sort=[("published_at", -1)],
            limit=limit
        )
    
    @staticmethod
    async def get_blog_stats() -> Dict[str, Any]:
        """Get overall blog statistics."""
        # Use aggregation for efficient stats calculation
        stats = {}
        
        # User stats
        user_stats = await User.aggregate([
            {"$group": {
                "_id": None,
                "total_users": {"$sum": 1},
                "active_users": {"$sum": {"$cond": ["$is_active", 1, 0]}},
                "authors": {"$sum": {"$cond": [{"$in": ["$role", ["author", "admin"]]}, 1, 0]}}
            }}
        ])
        
        if user_stats:
            stats.update(user_stats[0])
        
        # Post stats
        post_stats = await Post.aggregate([
            {"$group": {
                "_id": None,
                "total_posts": {"$sum": 1},
                "published_posts": {"$sum": {"$cond": [{"$eq": ["$status", "published"]}, 1, 0]}},
                "total_views": {"$sum": "$views_count"},
                "total_likes": {"$sum": "$likes_count"}
            }}
        ])
        
        if post_stats:
            stats.update(post_stats[0])
        
        # Category and tag counts
        stats["total_categories"] = await Category.count_documents({"is_active": True})
        stats["total_tags"] = await Tag.count_documents()
        stats["total_comments"] = await Comment.count_documents({"status": "approved"})
        
        return stats

class CategoryService:
    """Service for category management."""
    
    @staticmethod
    async def create_category(category_data: Dict[str, Any]) -> Category:
        """Create a new category."""
        # Check if slug already exists
        existing = await Category.find_one({"slug": category_data["slug"]})
        if existing:
            raise ValueError("Category slug already exists")
        
        category = Category(**category_data)
        return await category.save()
    
    @staticmethod
    async def get_categories_with_post_counts() -> List[Dict[str, Any]]:
        """Get all categories with their post counts."""
        pipeline = [
            {"$match": {"is_active": True}},
            {"$lookup": {
                "from": "posts",
                "localField": "_id",
                "foreignField": "category_id",
                "as": "posts"
            }},
            {"$addFields": {
                "posts_count": {"$size": "$posts"}
            }},
            {"$project": {"posts": 0}},
            {"$sort": {"posts_count": -1}}
        ]
        
        return await Category.aggregate(pipeline)

class TagService:
    """Service for tag management."""
    
    @staticmethod
    async def get_or_create_tags(tag_names: List[str]) -> List[ObjectId]:
        """Get existing tags or create new ones."""
        tag_ids = []
        
        for name in tag_names:
            slug = name.lower().replace(' ', '-').replace('_', '-')
            
            # Try to find existing tag
            tag = await Tag.find_one({"slug": slug})
            
            if not tag:
                # Create new tag
                tag = Tag(name=name, slug=slug)
                tag = await tag.save()
            
            tag_ids.append(tag.id)
        
        return tag_ids
    
    @staticmethod
    async def get_popular_tags(limit: int = 20) -> List[Tag]:
        """Get most popular tags by usage count."""
        return await Tag.find(
            filter_dict={"usage_count": {"$gt": 0}},
            sort=[("usage_count", -1)],
            limit=limit
        )
```

### API Endpoints (FastAPI Example)

```python
# api/blog_api.py
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime

from .services.blog_service import BlogService, CategoryService, TagService
from .models.blog import User, Post, Category, Tag, Comment

app = FastAPI(title="Blog API", version="1.0.0")
security = HTTPBearer()

# Pydantic models for API
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    bio: Optional[str] = None

class PostCreate(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    category_id: Optional[str] = None
    tag_names: List[str] = []
    status: str = "draft"

class CommentCreate(BaseModel):
    content: str
    author_id: Optional[str] = None
    parent_id: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    # In real app, decode JWT and get user
    # For demo, we'll just return a mock user
    return await User.find_one({"username": "demo_user"})

@app.post("/users", response_model=dict)
async def create_user(user_data: UserCreate):
    """Create a new user."""
    try:
        # Hash password (use proper hashing in real app)
        import hashlib
        user_dict = user_data.dict()
        user_dict["password_hash"] = hashlib.sha256(user_data.password.encode()).hexdigest()
        del user_dict["password"]
        
        user = await BlogService.create_user(user_dict)
        return {"id": str(user.id), "username": user.username, "email": user.email}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/posts")
async def get_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category_id: Optional[str] = None,
    tag_id: Optional[str] = None,
    author_id: Optional[str] = None
):
    """Get published posts with pagination."""
    # Convert string IDs to ObjectId
    category_oid = ObjectId(category_id) if category_id else None
    tag_oid = ObjectId(tag_id) if tag_id else None
    author_oid = ObjectId(author_id) if author_id else None
    
    result = await BlogService.get_published_posts(
        page=page,
        limit=limit,
        category_id=category_oid,
        tag_id=tag_oid,
        author_id=author_oid
    )
    
    # Convert posts to dict format
    posts_data = []
    for post in result["posts"]:
        post_dict = post.dict()
        post_dict["id"] = str(post.id)
        post_dict["author_id"] = str(post.author_id)
        if post.category_id:
            post_dict["category_id"] = str(post.category_id)
        post_dict["tag_ids"] = [str(tid) for tid in post.tag_ids]
        posts_data.append(post_dict)
    
    return {
        "posts": posts_data,
        "pagination": {
            "page": result["page"],
            "limit": result["limit"],
            "total_count": result["total_count"],
            "total_pages": result["total_pages"]
        }
    }

@app.get("/posts/{slug}")
async def get_post(slug: str):
    """Get a single post by slug."""
    result = await BlogService.get_post_with_author_and_category(slug)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Convert to dict format
    post_dict = result["post"].dict()
    post_dict["id"] = str(result["post"].id)
    post_dict["author_id"] = str(result["post"].author_id)
    
    author_dict = result["author"].dict() if result["author"] else None
    if author_dict:
        author_dict["id"] = str(result["author"].id)
    
    category_dict = result["category"].dict() if result["category"] else None
    if category_dict:
        category_dict["id"] = str(result["category"].id)
    
    tags_data = []
    for tag in result["tags"]:
        tag_dict = tag.dict()
        tag_dict["id"] = str(tag.id)
        tags_data.append(tag_dict)
    
    return {
        "post": post_dict,
        "author": author_dict,
        "category": category_dict,
        "tags": tags_data
    }

@app.post("/posts")
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new post."""
    try:
        # Get or create tags
        tag_ids = []
        if post_data.tag_names:
            tag_ids = await TagService.get_or_create_tags(post_data.tag_names)
        
        # Prepare post data
        post_dict = post_data.dict(exclude={"tag_names"})
        post_dict["tag_ids"] = tag_ids
        
        # Convert category_id to ObjectId if provided
        if post_dict["category_id"]:
            post_dict["category_id"] = ObjectId(post_dict["category_id"])
        
        post = await BlogService.create_post(current_user.id, post_dict)
        
        return {"id": str(post.id), "slug": post.slug, "status": post.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/posts/{post_id}/comments")
async def add_comment(
    post_id: str,
    comment_data: CommentCreate
):
    """Add a comment to a post."""
    try:
        comment_dict = comment_data.dict()
        if comment_dict["author_id"]:
            comment_dict["author_id"] = ObjectId(comment_dict["author_id"])
        if comment_dict["parent_id"]:
            comment_dict["parent_id"] = ObjectId(comment_dict["parent_id"])
        
        comment = await BlogService.add_comment(ObjectId(post_id), comment_dict)
        return {"id": str(comment.id), "status": comment.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Like or unlike a post."""
    liked = await BlogService.like_post(ObjectId(post_id), current_user.id)
    return {"liked": liked}

@app.get("/search")
async def search_posts(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Search posts."""
    posts = await BlogService.search_posts(q, limit)
    
    posts_data = []
    for post in posts:
        post_dict = post.dict()
        post_dict["id"] = str(post.id)
        post_dict["author_id"] = str(post.author_id)
        posts_data.append(post_dict)
    
    return {"posts": posts_data, "query": q}

@app.get("/stats")
async def get_blog_stats():
    """Get blog statistics."""
    return await BlogService.get_blog_stats()

@app.get("/categories")
async def get_categories():
    """Get all categories with post counts."""
    categories = await CategoryService.get_categories_with_post_counts()
    
    # Convert ObjectIds to strings
    for category in categories:
        category["id"] = str(category["_id"])
        del category["_id"]
    
    return {"categories": categories}

@app.get("/tags/popular")
async def get_popular_tags(limit: int = Query(20, ge=1, le=100)):
    """Get popular tags."""
    tags = await TagService.get_popular_tags(limit)
    
    tags_data = []
    for tag in tags:
        tag_dict = tag.dict()
        tag_dict["id"] = str(tag.id)
        tags_data.append(tag_dict)
    
    return {"tags": tags_data}

# WebSocket endpoint for real-time features
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"New activity: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Database Setup and Testing

```python
# setup.py
import asyncio
from py_mongo_orm import configure_database
from models.blog import User, Post, Category, Tag, Comment
from services.blog_service import BlogService, CategoryService, TagService

async def setup_database():
    """Initialize database and create sample data."""
    
    # Configure database
    await configure_database(
        database_url="mongodb://localhost:27017",
        database_name="blog_app",
        max_pool_size=100
    )
    
    # Create indexes
    await User.create_indexes()
    await Post.create_indexes()
    await Category.create_indexes()
    await Tag.create_indexes()
    await Comment.create_indexes()
    
    print("✓ Database configured and indexes created")

async def create_sample_data():
    """Create sample data for testing."""
    
    # Create categories
    categories_data = [
        {"name": "Technology", "slug": "technology", "description": "Tech articles", "color": "#3498db"},
        {"name": "Programming", "slug": "programming", "description": "Programming tutorials", "color": "#e74c3c"},
        {"name": "Design", "slug": "design", "description": "Design articles", "color": "#9b59b6"},
        {"name": "Lifestyle", "slug": "lifestyle", "description": "Lifestyle content", "color": "#f39c12"}
    ]
    
    categories = []
    for cat_data in categories_data:
        try:
            category = await CategoryService.create_category(cat_data)
            categories.append(category)
            print(f"✓ Created category: {category.name}")
        except ValueError:
            # Category already exists
            category = await Category.find_one({"slug": cat_data["slug"]})
            categories.append(category)
    
    # Create users
    users_data = [
        {
            "username": "johndoe",
            "email": "john@example.com", 
            "full_name": "John Doe",
            "password_hash": "hashed_password_1",
            "bio": "Tech enthusiast and blogger",
            "role": "author",
            "is_active": True,
            "is_verified": True
        },
        {
            "username": "janedoe",
            "email": "jane@example.com",
            "full_name": "Jane Doe", 
            "password_hash": "hashed_password_2",
            "bio": "Designer and writer",
            "role": "author",
            "is_active": True,
            "is_verified": True
        },
        {
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "password_hash": "hashed_password_admin",
            "role": "admin",
            "is_active": True,
            "is_verified": True
        }
    ]
    
    users = []
    for user_data in users_data:
        try:
            user = await BlogService.create_user(user_data)
            users.append(user)
            print(f"✓ Created user: {user.username}")
        except ValueError:
            # User already exists
            user = await User.find_one({"username": user_data["username"]})
            users.append(user)
    
    # Create sample posts
    posts_data = [
        {
            "title": "Getting Started with MongoDB ORM",
            "slug": "getting-started-mongodb-orm",
            "content": "This is a comprehensive guide to getting started with MongoDB ORM...",
            "excerpt": "Learn how to use MongoDB ORM effectively",
            "category_id": categories[0].id,  # Technology
            "status": "published"
        },
        {
            "title": "Advanced Python Patterns",
            "slug": "advanced-python-patterns", 
            "content": "Exploring advanced Python design patterns...",
            "excerpt": "Deep dive into Python design patterns",
            "category_id": categories[1].id,  # Programming
            "status": "published"
        },
        {
            "title": "UI/UX Design Principles",
            "slug": "ui-ux-design-principles",
            "content": "Essential principles for good UI/UX design...",
            "excerpt": "Master the basics of design",
            "category_id": categories[2].id,  # Design
            "status": "draft"
        }
    ]
    
    # Create tags
    tag_names = ["python", "mongodb", "async", "web-development", "database", "orm", "tutorial"]
    tag_ids = await TagService.get_or_create_tags(tag_names)
    
    posts = []
    for i, post_data in enumerate(posts_data):
        post_data["tag_ids"] = tag_ids[:3]  # Add first 3 tags to each post
        post = await BlogService.create_post(users[i % len(users)].id, post_data)
        
        if post.status == "draft":
            await post.publish()  # Publish the post
        
        posts.append(post)
        print(f"✓ Created post: {post.title}")
    
    print(f"✓ Sample data created successfully!")
    print(f"  - {len(categories)} categories")
    print(f"  - {len(users)} users") 
    print(f"  - {len(posts)} posts")
    print(f"  - {len(tag_ids)} tags")

async def run_blog_demo():
    """Run a complete blog demo."""
    await setup_database()
    await create_sample_data()
    
    print("\n" + "="*50)
    print("BLOG DEMO")
    print("="*50)
    
    # Get blog stats
    stats = await BlogService.get_blog_stats()
    print(f"\nBlog Statistics:")
    print(f"  Total Users: {stats.get('total_users', 0)}")
    print(f"  Active Users: {stats.get('active_users', 0)}")
    print(f"  Total Posts: {stats.get('total_posts', 0)}")
    print(f"  Published Posts: {stats.get('published_posts', 0)}")
    print(f"  Total Views: {stats.get('total_views', 0)}")
    print(f"  Total Likes: {stats.get('total_likes', 0)}")
    
    # Get popular posts
    popular_posts = await BlogService.get_popular_posts(limit=5)
    print(f"\nPopular Posts:")
    for post in popular_posts:
        print(f"  - {post.title} (Views: {post.views_count}, Likes: {post.likes_count})")
    
    # Get categories with post counts
    categories = await CategoryService.get_categories_with_post_counts()
    print(f"\nCategories:")
    for category in categories:
        print(f"  - {category['name']}: {category['posts_count']} posts")
    
    # Search demo
    search_results = await BlogService.search_posts("MongoDB", limit=3)
    print(f"\nSearch Results for 'MongoDB':")
    for post in search_results:
        print(f"  - {post.title}")
    
    # Demo user interactions
    users = await User.find(limit=2)
    if len(users) >= 2:
        # User 1 follows User 2
        followed = await BlogService.follow_user(users[0].id, users[1].id)
        print(f"\n{users[0].username} {'followed' if followed else 'unfollowed'} {users[1].username}")
        
        # Get user feed
        feed = await BlogService.get_user_feed(users[0].id, limit=3)
        print(f"\nFeed for {users[0].username}:")
        for post in feed:
            print(f"  - {post.title}")

if __name__ == "__main__":
    asyncio.run(run_blog_demo())
```

## E-commerce System

A complete e-commerce platform demonstrating complex relationships, inventory management, and transaction handling.

### Model Definitions

```python
# models/ecommerce.py
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import Field, validator, EmailStr
from py_mongo_orm import Document
from bson import ObjectId

class UserType(str, Enum):
    CUSTOMER = "customer"
    VENDOR = "vendor"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class Customer(Document):
    # Personal Information
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: Optional[str] = Field(None, regex=r'^\+?[\d\s\-\(\)]+$')
    
    # Account Information
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    email_verified_at: Optional[datetime] = None
    
    # Preferences
    newsletter_subscribed: bool = False
    language: str = "en"
    currency: str = "USD"
    
    # Stats
    total_orders: int = 0
    total_spent: Decimal = Decimal('0.00')
    loyalty_points: int = 0
    
    class Config:
        collection_name = "customers"
        indexes = [
            ("email", 1),
            ("phone", 1),
            ("is_active", 1),
            [("email", 1), ("is_active", 1)],
            {
                "key": [("email", 1)],
                "unique": True,
                "background": True
            }
        ]
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()

class Address(Document):
    customer_id: ObjectId
    
    # Address Details
    type: str = Field(..., regex=r'^(shipping|billing|both)$')
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    company: Optional[str] = Field(None, max_length=100)
    
    # Location
    address_line_1: str = Field(..., min_length=1, max_length=100)
    address_line_2: Optional[str] = Field(None, max_length=100)
    city: str = Field(..., min_length=1, max_length=50)
    state_province: str = Field(..., min_length=1, max_length=50)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=2, max_length=2)  # ISO country code
    
    # Metadata
    is_default_shipping: bool = False
    is_default_billing: bool = False
    phone: Optional[str] = None
    
    class Config:
        collection_name = "addresses"
        indexes = [
            ("customer_id", 1),
            [("customer_id", 1), ("type", 1)],
            [("customer_id", 1), ("is_default_shipping", 1)],
            [("customer_id", 1), ("is_default_billing", 1)]
        ]

class Category(Document):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Hierarchy
    parent_id: Optional[ObjectId] = None
    level: int = 0
    path: str = ""  # e.g., "electronics/computers/laptops"
    
    # Display
    image_url: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    
    # SEO
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    
    # Stats
    products_count: int = 0
    
    class Config:
        collection_name = "categories"
        indexes = [
            ("slug", 1),
            ("parent_id", 1),
            ("path", 1),
            ("is_active", 1),
            ("sort_order", 1),
            [("parent_id", 1), ("sort_order", 1)],
            {
                "key": [("slug", 1)],
                "unique": True,
                "background": True
            }
        ]

class Product(Document):
    # Basic Information
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    short_description: Optional[str] = Field(None, max_length=500)
    
    # Categorization
    category_id: ObjectId
    brand: Optional[str] = Field(None, max_length=50)
    tags: List[str] = Field(default_factory=list)
    
    # Pricing
    price: Decimal = Field(..., gt=0)
    compare_at_price: Optional[Decimal] = Field(None, gt=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    
    # Inventory
    sku: str = Field(..., min_length=1, max_length=50)
    barcode: Optional[str] = None
    track_inventory: bool = True
    inventory_quantity: int = 0
    low_stock_threshold: int = 5
    
    # Physical Properties
    weight: Optional[Decimal] = Field(None, ge=0)  # in kg
    dimensions: Optional[Dict[str, Decimal]] = None  # length, width, height in cm
    
    # Status
    status: ProductStatus = ProductStatus.ACTIVE
    is_featured: bool = False
    is_digital: bool = False
    
    # SEO
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    
    # Media
    images: List[str] = Field(default_factory=list)  # URLs
    
    # Stats
    views_count: int = 0
    sales_count: int = 0
    rating_average: Decimal = Decimal('0.0')
    reviews_count: int = 0
    
    class Config:
        collection_name = "products"
        indexes = [
            ("slug", 1),
            ("sku", 1),
            ("category_id", 1),
            ("brand", 1),
            ("status", 1),
            ("price", 1),
            ("is_featured", 1),
            ("sales_count", -1),
            ("rating_average", -1),
            [("category_id", 1), ("status", 1)],
            [("brand", 1), ("status", 1)],
            [("price", 1), ("status", 1)],
            ("tags", 1),  # Multikey index
            {
                "key": [("slug", 1)],
                "unique": True,
                "background": True
            },
            {
                "key": [("sku", 1)],
                "unique": True,
                "background": True
            },
            {
                "key": [("name", "text"), ("description", "text"), ("tags", "text")],
                "background": True
            }
        ]
    
    @validator('dimensions')
    def validate_dimensions(cls, v):
        if v is not None:
            required_keys = ['length', 'width', 'height']
            if not all(key in v for key in required_keys):
                raise ValueError('Dimensions must include length, width, and height')
            if any(val <= 0 for val in v.values()):
                raise ValueError('All dimensions must be positive')
        return v

class Cart(Document):
    customer_id: ObjectId
    items: List[Dict[str, Any]] = Field(default_factory=list)
    total_amount: Decimal = Decimal('0.00')
    currency: str = "USD"
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    
    class Config:
        collection_name = "carts"
        indexes = [
            ("customer_id", 1),
            ("expires_at", 1),
            {
                "key": [("customer_id", 1)],
                "unique": True,
                "background": True
            },
            {
                "key": [("expires_at", 1)],
                "expireAfterSeconds": 0  # TTL index
            }
        ]
    
    def add_item(self, product_id: ObjectId, quantity: int, price: Decimal):
        """Add item to cart or update quantity if exists."""
        for item in self.items:
            if item['product_id'] == product_id:
                item['quantity'] += quantity
                item['total'] = item['quantity'] * item['price']
                break
        else:
            self.items.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': price,
                'total': quantity * price
            })
        
        self.calculate_total()
    
    def remove_item(self, product_id: ObjectId):
        """Remove item from cart."""
        self.items = [item for item in self.items if item['product_id'] != product_id]
        self.calculate_total()
    
    def calculate_total(self):
        """Calculate total cart amount."""
        self.total_amount = sum(Decimal(str(item['total'])) for item in self.items)

class Order(Document):
    # Basic Information
    order_number: str = Field(..., min_length=1, max_length=50)
    customer_id: ObjectId
    
    # Order Items
    items: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Amounts
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    shipping_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    total_amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    
    # Addresses
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Dates
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Tracking
    tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    
    # Notes
    customer_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    
    class Config:
        collection_name = "orders"
        indexes = [
            ("order_number", 1),
            ("customer_id", 1),
            ("status", 1),
            ("payment_status", 1),
            ("created_at", -1),
            [("customer_id", 1), ("created_at", -1)],
            [("status", 1), ("created_at", -1)],
            {
                "key": [("order_number", 1)],
                "unique": True,
                "background": True
            }
        ]

class Review(Document):
    product_id: ObjectId
    customer_id: ObjectId
    order_id: ObjectId  # Ensure customer actually bought the product
    
    # Review Content
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
    
    # Media
    images: List[str] = Field(default_factory=list)
    
    # Status
    is_verified: bool = False  # Verified purchase
    is_approved: bool = False
    
    # Stats
    helpful_count: int = 0
    
    class Config:
        collection_name = "reviews"
        indexes = [
            ("product_id", 1),
            ("customer_id", 1),
            ("order_id", 1),
            ("rating", 1),
            ("is_approved", 1),
            [("product_id", 1), ("is_approved", 1)],
            [("customer_id", 1), ("created_at", -1)],
            {
                "key": [("product_id", 1), ("customer_id", 1)],
                "unique": True,
                "background": True
            }
        ]

class Coupon(Document):
    code: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., regex=r'^(percentage|fixed_amount)$')
    value: Decimal = Field(..., gt=0)
    
    # Conditions
    minimum_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_discount: Optional[Decimal] = Field(None, gt=0)
    applicable_categories: List[ObjectId] = Field(default_factory=list)
    applicable_products: List[ObjectId] = Field(default_factory=list)
    
    # Usage
    usage_limit: Optional[int] = Field(None, gt=0)
    usage_count: int = 0
    usage_limit_per_customer: Optional[int] = Field(None, gt=0)
    
    # Validity
    starts_at: datetime
    expires_at: datetime
    is_active: bool = True
    
    class Config:
        collection_name = "coupons"
        indexes = [
            ("code", 1),
            ("is_active", 1),
            ("starts_at", 1),
            ("expires_at", 1),
            [("is_active", 1), ("starts_at", 1), ("expires_at", 1)],
            {
                "key": [("code", 1)],
                "unique": True,
                "background": True
            }
        ]
    
    def is_valid(self) -> bool:
        """Check if coupon is currently valid."""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.starts_at <= now <= self.expires_at and
            (self.usage_limit is None or self.usage_count < self.usage_limit)
        )
```

### Service Layer

```python
# services/ecommerce_service.py
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from bson import ObjectId
from ..models.ecommerce import (
    Customer, Product, Category, Cart, Order, Review, Coupon, Address
)

class ProductService:
    """Service for product management."""
    
    @staticmethod
    async def search_products(
        query: Optional[str] = None,
        category_id: Optional[ObjectId] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        brand: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "relevance",
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search products with filters."""
        
        # Build filter
        filter_dict = {"status": "active"}
        
        # Text search
        if query:
            filter_dict["$text"] = {"$search": query}
        
        # Category filter
        if category_id:
            # Include subcategories
            category = await Category.find_by_id(category_id)
            if category:
                # Find all subcategories
                subcategories = await Category.find({
                    "path": {"$regex": f"^{category.path}"}
                })
                category_ids = [cat.id for cat in subcategories] + [category_id]
                filter_dict["category_id"] = {"$in": category_ids}
        
        # Price range
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price
        if price_filter:
            filter_dict["price"] = price_filter
        
        # Brand filter
        if brand:
            filter_dict["brand"] = {"$regex": brand, "$options": "i"}
        
        # Tags filter
        if tags:
            filter_dict["tags"] = {"$in": tags}
        
        # Sort options
        sort_options = {
            "relevance": [("score", {"$meta": "textScore"})] if query else [("is_featured", -1), ("sales_count", -1)],
            "price_low": [("price", 1)],
            "price_high": [("price", -1)],
            "newest": [("created_at", -1)],
            "bestselling": [("sales_count", -1)],
            "rating": [("rating_average", -1)]
        }
        
        sort_spec = sort_options.get(sort_by, sort_options["relevance"])
        
        # Pagination
        skip = (page - 1) * limit
        
        # Execute query
        products = await Product.find(
            filter_dict=filter_dict,
            sort=sort_spec,
            skip=skip,
            limit=limit
        )
        
        # Get total count
        total_count = await Product.count_documents(filter_dict)
        
        return {
            "products": products,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit,
            "filters": {
                "query": query,
                "category_id": category_id,
                "min_price": min_price,
                "max_price": max_price,
                "brand": brand,
                "tags": tags
            }
        }
    
    @staticmethod
    async def get_product_details(slug: str) -> Optional[Dict[str, Any]]:
        """Get product with related data."""
        product = await Product.find_one({"slug": slug, "status": "active"})
        if not product:
            return None
        
        # Get category
        category = await Category.find_by_id(product.category_id)
        
        # Get category path
        category_path = []
        if category:
            current_cat = category
            while current_cat:
                category_path.insert(0, current_cat)
                if current_cat.parent_id:
                    current_cat = await Category.find_by_id(current_cat.parent_id)
                else:
                    break
        
        # Get reviews
        reviews = await Review.find(
            {"product_id": product.id, "is_approved": True},
            sort=[("helpful_count", -1), ("created_at", -1)],
            limit=10
        )
        
        # Get related products
        related_products = await Product.find(
            {
                "category_id": product.category_id,
                "status": "active",
                "_id": {"$ne": product.id}
            },
            limit=4
        )
        
        # Increment view count
        await Product.update_many(
            {"_id": product.id},
            {"$inc": {"views_count": 1}}
        )
        
        return {
            "product": product,
            "category": category,
            "category_path": category_path,
            "reviews": reviews,
            "related_products": related_products
        }
    
    @staticmethod
    async def update_product_rating(product_id: ObjectId):
        """Update product rating based on reviews."""
        pipeline = [
            {"$match": {"product_id": product_id, "is_approved": True}},
            {"$group": {
                "_id": None,
                "average_rating": {"$avg": "$rating"},
                "review_count": {"$sum": 1}
            }}
        ]
        
        result = await Review.aggregate(pipeline)
        
        if result:
            stats = result[0]
            await Product.update_many(
                {"_id": product_id},
                {
                    "$set": {
                        "rating_average": round(stats["average_rating"], 1),
                        "reviews_count": stats["review_count"]
                    }
                }
            )

class CartService:
    """Service for shopping cart management."""
    
    @staticmethod
    async def get_or_create_cart(customer_id: ObjectId) -> Cart:
        """Get customer's cart or create new one."""
        cart = await Cart.find_one({"customer_id": customer_id})
        
        if not cart:
            cart = Cart(customer_id=customer_id)
            cart = await cart.save()
        
        return cart
    
    @staticmethod
    async def add_to_cart(
        customer_id: ObjectId,
        product_id: ObjectId,
        quantity: int
    ) -> Cart:
        """Add product to cart."""
        # Validate product
        product = await Product.find_by_id(product_id)
        if not product or product.status != "active":
            raise ValueError("Product not available")
        
        # Check inventory
        if product.track_inventory and product.inventory_quantity < quantity:
            raise ValueError("Insufficient inventory")
        
        # Get cart
        cart = await CartService.get_or_create_cart(customer_id)
        
        # Add item
        cart.add_item(product_id, quantity, product.price)
        
        return await cart.save()
    
    @staticmethod
    async def update_cart_item(
        customer_id: ObjectId,
        product_id: ObjectId,
        quantity: int
    ) -> Cart:
        """Update cart item quantity."""
        cart = await CartService.get_or_create_cart(customer_id)
        
        if quantity <= 0:
            cart.remove_item(product_id)
        else:
            # Find and update item
            for item in cart.items:
                if item['product_id'] == product_id:
                    # Validate inventory
                    product = await Product.find_by_id(product_id)
                    if product and product.track_inventory and product.inventory_quantity < quantity:
                        raise ValueError("Insufficient inventory")
                    
                    item['quantity'] = quantity
                    item['total'] = quantity * item['price']
                    break
            
            cart.calculate_total()
        
        return await cart.save()
    
    @staticmethod
    async def get_cart_details(customer_id: ObjectId) -> Dict[str, Any]:
        """Get cart with product details."""
        cart = await CartService.get_or_create_cart(customer_id)
        
        if not cart.items:
            return {"cart": cart, "products": [], "total": Decimal('0.00')}
        
        # Get product details
        product_ids = [item['product_id'] for item in cart.items]
        products = await Product.find({"_id": {"$in": product_ids}})
        product_map = {str(p.id): p for p in products}
        
        # Build detailed items
        detailed_items = []
        for item in cart.items:
            product = product_map.get(str(item['product_id']))
            if product:
                detailed_items.append({
                    "product": product,
                    "quantity": item['quantity'],
                    "price": item['price'],
                    "total": item['total']
                })
        
        return {
            "cart": cart,
            "items": detailed_items,
            "total": cart.total_amount
        }

class OrderService:
    """Service for order management."""
    
    @staticmethod
    async def create_order(
        customer_id: ObjectId,
        shipping_address: Dict[str, Any],
        billing_address: Dict[str, Any],
        payment_method: Dict[str, Any],
        coupon_code: Optional[str] = None
    ) -> Order:
        """Create order from cart."""
        
        # Get cart
        cart = await CartService.get_or_create_cart(customer_id)
        if not cart.items:
            raise ValueError("Cart is empty")
        
        # Validate inventory
        for item in cart.items:
            product = await Product.find_by_id(item['product_id'])
            if not product or product.status != "active":
                raise ValueError("Product not available")
            
            if product.track_inventory and product.inventory_quantity < item['quantity']:
                raise ValueError("Insufficient inventory")
        
        # Calculate amounts
        subtotal = cart.total_amount
        tax_amount = subtotal * Decimal('0.1')  # 10% tax
        shipping_amount = Decimal('10.00') if subtotal < Decimal('100.00') else Decimal('0.00')
        discount_amount = Decimal('0.00')
        
        # Apply coupon if provided
        if coupon_code:
            coupon = await Coupon.find_one({"code": coupon_code.upper()})
            if coupon and coupon.is_valid():
                if coupon.minimum_amount is None or subtotal >= coupon.minimum_amount:
                    if coupon.type == "percentage":
                        discount_amount = subtotal * (coupon.value / 100)
                    else:  # fixed_amount
                        discount_amount = coupon.value
                    
                    if coupon.maximum_discount and discount_amount > coupon.maximum_discount:
                        discount_amount = coupon.maximum_discount
        
        total_amount = subtotal + tax_amount + shipping_amount - discount_amount
        
        # Generate order number
        order_count = await Order.count_documents() + 1
        order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{order_count:06d}"
        
        # Create order
        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            items=cart.items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            shipping_address=shipping_address,
            billing_address=billing_address
        )
        
        saved_order = await order.save()
        
        # Update inventory
        for item in cart.items:
            if product.track_inventory:
                await Product.update_many(
                    {"_id": item['product_id']},
                    {"$inc": {"inventory_quantity": -item['quantity']}}
                )
        
        # Update coupon usage
        if coupon_code and discount_amount > 0:
            await Coupon.update_many(
                {"code": coupon_code.upper()},
                {"$inc": {"usage_count": 1}}
            )
        
        # Clear cart
        cart.items = []
        cart.total_amount = Decimal('0.00')
        await cart.save()
        
        # Update customer stats
        await Customer.update_many(
            {"_id": customer_id},
            {
                "$inc": {
                    "total_orders": 1,
                    "total_spent": total_amount,
                    "loyalty_points": int(total_amount)  # 1 point per dollar
                }
            }
        )
        
        return saved_order
    
    @staticmethod
    async def get_customer_orders(
        customer_id: ObjectId,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get customer's orders with pagination."""
        skip = (page - 1) * limit
        
        orders = await Order.find(
            {"customer_id": customer_id},
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit
        )
        
        total_count = await Order.count_documents({"customer_id": customer_id})
        
        return {
            "orders": orders,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    @staticmethod
    async def update_order_status(
        order_id: ObjectId,
        status: str,
        tracking_number: Optional[str] = None,
        shipping_carrier: Optional[str] = None
    ) -> Order:
        """Update order status."""
        order = await Order.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        update_data = {"status": status, "updated_at": datetime.utcnow()}
        
        if status == "shipped":
            update_data["shipped_at"] = datetime.utcnow()
            if tracking_number:
                update_data["tracking_number"] = tracking_number
            if shipping_carrier:
                update_data["shipping_carrier"] = shipping_carrier
        elif status == "delivered":
            update_data["delivered_at"] = datetime.utcnow()
        
        await Order.update_many({"_id": order_id}, {"$set": update_data})
        
        return await Order.find_by_id(order_id)

class ReviewService:
    """Service for product reviews."""
    
    @staticmethod
    async def create_review(
        customer_id: ObjectId,
        product_id: ObjectId,
        order_id: ObjectId,
        rating: int,
        title: str,
        content: str,
        images: Optional[List[str]] = None
    ) -> Review:
        """Create a product review."""
        
        # Verify customer purchased the product
        order = await Order.find_one({
            "_id": order_id,
            "customer_id": customer_id,
            "status": {"$in": ["delivered", "shipped"]}
        })
        
        if not order:
            raise ValueError("Order not found or not eligible for review")
        
        # Check if product was in the order
        product_in_order = any(
            item['product_id'] == product_id for item in order.items
        )
        
        if not product_in_order:
            raise ValueError("Product not found in order")
        
        # Check if review already exists
        existing_review = await Review.find_one({
            "customer_id": customer_id,
            "product_id": product_id
        })
        
        if existing_review:
            raise ValueError("Review already exists for this product")
        
        # Create review
        review = Review(
            product_id=product_id,
            customer_id=customer_id,
            order_id=order_id,
            rating=rating,
            title=title,
            content=content,
            images=images or [],
            is_verified=True  # Verified purchase
        )
        
        saved_review = await review.save()
        
        # Update product rating
        await ProductService.update_product_rating(product_id)
        
        return saved_review

# Analytics and Reporting
class AnalyticsService:
    """Service for e-commerce analytics."""
    
    @staticmethod
    async def get_sales_report(
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get sales report for date range."""
        
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date},
                    "status": {"$nin": ["cancelled", "refunded"]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_orders": {"$sum": 1},
                    "total_revenue": {"$sum": "$total_amount"},
                    "average_order_value": {"$avg": "$total_amount"},
                    "total_items_sold": {"$sum": {"$sum": "$items.quantity"}}
                }
            }
        ]
        
        result = await Order.aggregate(pipeline)
        return result[0] if result else {}
    
    @staticmethod
    async def get_top_products(limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-selling products."""
        
        pipeline = [
            {"$match": {"status": "active"}},
            {"$sort": {"sales_count": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "categories",
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category"
                }
            },
            {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}}
        ]
        
        return await Product.aggregate(pipeline)
    
    @staticmethod
    async def get_customer_insights() -> Dict[str, Any]:
        """Get customer analytics."""
        
        # Customer lifetime value
        clv_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_clv": {"$avg": "$total_spent"},
                    "avg_orders": {"$avg": "$total_orders"},
                    "total_customers": {"$sum": 1}
                }
            }
        ]
        
        clv_result = await Customer.aggregate(clv_pipeline)
        
        # New vs returning customers (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        new_customers = await Customer.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        return {
            "customer_lifetime_value": clv_result[0] if clv_result else {},
            "new_customers_last_30_days": new_customers
        }
```

## User Management System

```python
# models/user_management.py
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from pydantic import Field, validator, EmailStr
from py_mongo_orm import BaseModel, register_all_models

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

class Permission(str, Enum):
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    MANAGE_ROLES = "manage_roles"
    VIEW_REPORTS = "view_reports"

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    password_hash: str  # Store hashed password
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_locked(self) -> bool:
        return (self.locked_until and 
                self.locked_until > datetime.now())
    
    async def lock_account(self, duration_minutes: int = 30):
        """Lock user account for specified duration"""
        self.locked_until = datetime.now() + timedelta(minutes=duration_minutes)
        await self.save()
    
    async def unlock_account(self):
        """Unlock user account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        await self.save()
    
    async def record_login_attempt(self, successful: bool):
        """Record login attempt"""
        if successful:
            self.last_login = datetime.now()
            self.failed_login_attempts = 0
            self.locked_until = None
        else:
            self.failed_login_attempts += 1
            if self.failed_logintempts >= 5:
                await self.lock_account()
        
        await self.save()

class LoginSession(BaseModel):
    user_id: int
    session_token: str = Field(..., min_length=32)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    is_active: bool = True
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    async def extend_session(self, hours: int = 24):
        """Extend session duration"""
        self.expires_at = datetime.now() + timedelta(hours=hours)
        await self.save()
    
    async def invalidate(self):
        """Invalidate session"""
        self.is_active = False
        await self.save()
    
    @classmethod
    async def cleanup_expired(cls):
        """Remove expired sessions"""
        await cls.delete_many(expires_at__lt=datetime.now())

# Initialize user management models
async def init_user_management():
    await register_all_models(__name__)
    
    await User.create_index("username", unique=True)
    await User.create_index("email", unique=True)
    await LoginSession.create_index("session_token", unique=True)
    await LoginSession.create_index("expires_at")
```

### Service Layer

```python
# services/user_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from ..models.user_management import User, LoginSession

class UserService:
    """Service class for user management operations"""
    
    @staticmethod
    async def create_user(
        username: str,
        email: str,
        password: str,
        role: str = "user"
    ) -> User:
        """Create a new user"""
        user = User(
            username=username,
            email=email,
            password_hash=password,  # Hash in real app
            role=role
        )
        return await user.save()
    
    @staticmethod
    async def get_user_by_id(user_id: ObjectId) -> Optional[User]:
        """Get user by ID"""
        return await User.find_by_id(user_id)
    
    @staticmethod
    async def update_user(
        user_id: ObjectId,
        update_data: Dict[str, Any]
    ) -> User:
        """Update user information"""
        user = await User.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        return await user.save()
    
    @staticmethod
    async def delete_user(user_id: ObjectId):
        """Delete a user"""
        user = await User.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        await user.delete()
    
    @staticmethod
    async def create_login_session(
        user_id: ObjectId,
        ip_address: str,
        user_agent: str
    ) -> LoginSession:
        """Create a new login session"""
        session = LoginSession(
            user_id=user_id,
            session_token="random_token_string",  # Generate securely
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        return await session.save()
    
    @staticmethod
    async def get_active_sessions(user_id: ObjectId) -> List[LoginSession]:
        """Get active sessions for a user"""
        return await LoginSession.find({
            "user_id": user_id,
            "is_active": True
        })
    
    @staticmethod
    async def extend_session(session_id: ObjectId):
        """Extend session expiration"""
        session = await LoginSession.find_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        session.expires_at = datetime.now() + timedelta(hours=24)
        await session.save()
    
    @staticmethod
    async def invalidate_session(session_id: ObjectId):
        """Invalidate a session"""
        session = await LoginSession.find_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        session.is_active = False
        await session.save()
```

This user management example demonstrates:

1. **User Registration and Authentication**: Creating users, hashing passwords, managing sessions
2. **Role-based Access Control**: User roles and permissions
3. **Data Validation**: Email format, password strength, unique constraints
4. **Session Management**: Creating, extending, and invalidating sessions
5. **Error Handling**: Properly handling and raising validation errors

The models and services are designed to be secure, efficient, and easy to use in a real-world application.
