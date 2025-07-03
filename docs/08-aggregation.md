# Aggregation

MongoDB ORM provides powerful aggregation capabilities through the `aggregate()` method, allowing you to perform complex data processing and analysis operations.

## Table of Contents

- [Overview](#overview)
- [Basic Aggregation](#basic-aggregation)
- [Pipeline Stages](#pipeline-stages)
- [Common Aggregation Patterns](#common-aggregation-patterns)
- [Performance Considerations](#performance-considerations)
- [Examples](#examples)

## Overview

MongoDB aggregation is a framework for data processing that allows you to:

- **Transform Data**: Reshape documents and fields
- **Group Data**: Group by fields and calculate statistics
- **Filter Data**: Apply complex filtering logic
- **Join Data**: Combine data from multiple collections
- **Calculate**: Perform mathematical operations and analytics

The aggregation framework uses a pipeline approach where data flows through multiple stages.

## Basic Aggregation

### Simple Aggregation

```python
from br_mongodb_orm import BaseModel

class User(BaseModel):
    name: str
    age: int
    city: str
    salary: float

# Basic aggregation pipeline
pipeline = [
    {"$match": {"age": {"$gte": 18}}},
    {"$group": {"_id": "$city", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]

result = await User.aggregate(pipeline)
print(result)
# [{"_id": "New York", "count": 150}, {"_id": "LA", "count": 120}, ...]
```

### Aggregation with Type Safety

```python
from typing import Dict, Any, List

async def get_user_stats_by_city() -> List[Dict[str, Any]]:
    """Get user statistics grouped by city"""
    pipeline = [
        {"$group": {
            "_id": "$city",
            "total_users": {"$sum": 1},
            "avg_age": {"$avg": "$age"},
            "avg_salary": {"$avg": "$salary"}
        }},
        {"$sort": {"total_users": -1}}
    ]
    
    return await User.aggregate(pipeline)

# Usage
city_stats = await get_user_stats_by_city()
```

## Pipeline Stages

### $match - Filtering

```python
# Filter documents (similar to WHERE in SQL)
pipeline = [
    {"$match": {
        "age": {"$gte": 25, "$lte": 40},
        "city": {"$in": ["New York", "San Francisco"]}
    }}
]

adults = await User.aggregate(pipeline)
```

### $group - Grouping and Aggregation

```python
# Group by field and calculate statistics
pipeline = [
    {"$group": {
        "_id": "$department",
        "employee_count": {"$sum": 1},
        "avg_salary": {"$avg": "$salary"},
        "max_salary": {"$max": "$salary"},
        "min_salary": {"$min": "$salary"},
        "total_salary": {"$sum": "$salary"}
    }}
]

dept_stats = await User.aggregate(pipeline)
```

### $project - Field Selection and Transformation

```python
# Select and transform fields
pipeline = [
    {"$project": {
        "name": 1,
        "age": 1,
        "full_name": {"$concat": ["$first_name", " ", "$last_name"]},
        "age_group": {
            "$cond": {
                "if": {"$lt": ["$age", 30]},
                "then": "young",
                "else": "mature"
            }
        }
    }}
]

transformed_users = await User.aggregate(pipeline)
```

### $sort - Sorting

```python
# Sort results
pipeline = [
    {"$group": {"_id": "$city", "population": {"$sum": 1}}},
    {"$sort": {"population": -1}}  # Descending order
]

sorted_cities = await User.aggregate(pipeline)
```

### $limit and $skip - Pagination

```python
# Paginate aggregation results
pipeline = [
    {"$match": {"is_active": True}},
    {"$sort": {"created_at": -1}},
    {"$skip": 20},
    {"$limit": 10}
]

page_3_users = await User.aggregate(pipeline)
```

### $lookup - Joining Collections

```python
class Order(BaseModel):
    user_id: int
    product_id: int
    quantity: int
    amount: float

# Join users with their orders
pipeline = [
    {"$lookup": {
        "from": "orders",  # Collection name
        "localField": "id",
        "foreignField": "user_id",
        "as": "orders"
    }},
    {"$match": {"orders": {"$ne": []}}},  # Only users with orders
    {"$project": {
        "name": 1,
        "email": 1,
        "order_count": {"$size": "$orders"},
        "total_amount": {"$sum": "$orders.amount"}
    }}
]

users_with_orders = await User.aggregate(pipeline)
```

### $unwind - Array Deconstruction

```python
class Post(BaseModel):
    title: str
    author_id: int
    tags: List[str]
    comments: List[Dict[str, Any]]

# Unwind array fields for analysis
pipeline = [
    {"$unwind": "$tags"},
    {"$group": {
        "_id": "$tags",
        "post_count": {"$sum": 1}
    }},
    {"$sort": {"post_count": -1}}
]

tag_popularity = await Post.aggregate(pipeline)
```

## Common Aggregation Patterns

### 1. Data Analytics

```python
# User activity analytics
async def get_user_activity_stats():
    pipeline = [
        {"$match": {"last_login": {"$exists": True}}},
        {"$group": {
            "_id": {
                "year": {"$year": "$last_login"},
                "month": {"$month": "$last_login"}
            },
            "active_users": {"$sum": 1},
            "avg_age": {"$avg": "$age"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    
    return await User.aggregate(pipeline)

# Sales analytics
async def get_monthly_sales():
    pipeline = [
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"}
            },
            "total_sales": {"$sum": "$amount"},
            "order_count": {"$sum": 1},
            "avg_order_value": {"$avg": "$amount"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    
    return await Order.aggregate(pipeline)
```

### 2. Reporting and Dashboards

```python
# Executive dashboard data
async def get_dashboard_metrics():
    # Total users by status
    user_stats = await User.aggregate([
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ])
    
    # Revenue by month
    revenue_stats = await Order.aggregate([
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"}
            },
            "revenue": {"$sum": "$amount"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$limit": 12}  # Last 12 months
    ])
    
    return {
        "users": user_stats,
        "revenue": revenue_stats
    }
```

### 3. Data Enrichment

```python
# Enrich user data with calculated fields
async def get_enriched_users():
    pipeline = [
        {"$lookup": {
            "from": "orders",
            "localField": "id",
            "foreignField": "user_id",
            "as": "orders"
        }},
        {"$addFields": {
            "order_count": {"$size": "$orders"},
            "total_spent": {"$sum": "$orders.amount"},
            "avg_order_value": {"$avg": "$orders.amount"},
            "customer_tier": {
                "$switch": {
                    "branches": [
                        {"case": {"$gte": [{"$sum": "$orders.amount"}, 1000]}, "then": "platinum"},
                        {"case": {"$gte": [{"$sum": "$orders.amount"}, 500]}, "then": "gold"},
                        {"case": {"$gte": [{"$sum": "$orders.amount"}, 100]}, "then": "silver"}
                    ],
                    "default": "bronze"
                }
            }
        }},
        {"$project": {
            "name": 1,
            "email": 1,
            "order_count": 1,
            "total_spent": 1,
            "avg_order_value": 1,
            "customer_tier": 1
        }}
    ]
    
    return await User.aggregate(pipeline)
```

### 4. Text Analysis

```python
# Analyze content engagement
async def analyze_post_engagement():
    pipeline = [
        {"$addFields": {
            "word_count": {"$size": {"$split": ["$content", " "]}},
            "comment_count": {"$size": "$comments"}
        }},
        {"$group": {
            "_id": None,
            "avg_word_count": {"$avg": "$word_count"},
            "avg_comments": {"$avg": "$comment_count"},
            "posts_by_length": {
                "$push": {
                    "$cond": {
                        "if": {"$lt": ["$word_count", 100]},
                        "then": "short",
                        "else": {"$cond": {
                            "if": {"$lt": ["$word_count", 500]},
                            "then": "medium",
                            "else": "long"
                        }}
                    }
                }
            }
        }}
    ]
    
    return await Post.aggregate(pipeline)
```

## Performance Considerations

### 1. Index Usage

Ensure aggregation stages can use indexes:

```python
# Create indexes for aggregation performance
await User.create_index("city")
await User.create_index("age")
await User.create_compound_index({"city": 1, "age": 1})

# Aggregation that uses indexes
pipeline = [
    {"$match": {"city": "New York", "age": {"$gte": 25}}},  # Uses index
    {"$group": {"_id": "$department", "count": {"$sum": 1}}}
]
```

### 2. Early Filtering

Place `$match` stages early in the pipeline:

```python
# Good: Filter early
pipeline = [
    {"$match": {"is_active": True}},  # Reduce documents early
    {"$lookup": {
        "from": "orders",
        "localField": "id", 
        "foreignField": "user_id",
        "as": "orders"
    }},
    {"$group": {"_id": "$city", "count": {"$sum": 1}}}
]

# Bad: Filter late
pipeline = [
    {"$lookup": {
        "from": "orders",
        "localField": "id",
        "foreignField": "user_id", 
        "as": "orders"
    }},
    {"$group": {"_id": "$city", "count": {"$sum": 1}}},
    {"$match": {"count": {"$gte": 10}}}  # Filter after processing
]
```

### 3. Memory Usage

Be aware of memory limits:

```python
# Use $limit to prevent memory issues
pipeline = [
    {"$match": {"status": "active"}},
    {"$sort": {"created_at": -1}},
    {"$limit": 1000},  # Limit results
    {"$group": {"_id": "$city", "count": {"$sum": 1}}}
]
```

## Examples

### E-commerce Analytics

```python
class Product(BaseModel):
    name: str
    category: str
    price: float
    sales_count: int

class Order(BaseModel):
    user_id: int
    product_id: int
    quantity: int
    amount: float

# Top selling products by category
async def top_products_by_category(limit: int = 5):
    pipeline = [
        {"$group": {
            "_id": "$category",
            "products": {
                "$push": {
                    "name": "$name",
                    "sales": "$sales_count",
                    "price": "$price"
                }
            }
        }},
        {"$unwind": "$products"},
        {"$sort": {"products.sales": -1}},
        {"$group": {
            "_id": "$_id",
            "top_products": {"$push": "$products"},
            "total_sales": {"$sum": "$products.sales"}
        }},
        {"$addFields": {
            "top_products": {"$slice": ["$top_products", limit]}
        }},
        {"$sort": {"total_sales": -1}}
    ]
    
    return await Product.aggregate(pipeline)

# Customer purchase patterns
async def customer_purchase_patterns():
    pipeline = [
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "id",
            "as": "user"
        }},
        {"$unwind": "$user"},
        {"$group": {
            "_id": {
                "user_id": "$user_id",
                "age_group": {
                    "$cond": {
                        "if": {"$lt": ["$user.age", 30]},
                        "then": "18-29",
                        "else": {"$cond": {
                            "if": {"$lt": ["$user.age", 50]},
                            "then": "30-49", 
                            "else": "50+"
                        }}
                    }
                }
            },
            "total_spent": {"$sum": "$amount"},
            "order_count": {"$sum": 1},
            "avg_order_value": {"$avg": "$amount"}
        }},
        {"$group": {
            "_id": "$_id.age_group",
            "customer_count": {"$sum": 1},
            "avg_total_spent": {"$avg": "$total_spent"},
            "avg_order_count": {"$avg": "$order_count"},
            "avg_order_value": {"$avg": "$avg_order_value"}
        }},
        {"$sort": {"avg_total_spent": -1}}
    ]
    
    return await Order.aggregate(pipeline)
```

### Content Management Analytics

```python
class Article(BaseModel):
    title: str
    author_id: int
    category: str
    views: int
    likes: int
    reading_time: int  # in minutes

# Content performance analysis
async def content_performance_report():
    pipeline = [
        {"$addFields": {
            "engagement_rate": {
                "$cond": {
                    "if": {"$eq": ["$views", 0]},
                    "then": 0,
                    "else": {"$divide": ["$likes", "$views"]}
                }
            },
            "content_length": {
                "$switch": {
                    "branches": [
                        {"case": {"$lt": ["$reading_time", 3]}, "then": "short"},
                        {"case": {"$lt": ["$reading_time", 10]}, "then": "medium"},
                    ],
                    "default": "long"
                }
            }
        }},
        {"$group": {
            "_id": {
                "category": "$category",
                "length": "$content_length"
            },
            "article_count": {"$sum": 1},
            "avg_views": {"$avg": "$views"},
            "avg_likes": {"$avg": "$likes"},
            "avg_engagement": {"$avg": "$engagement_rate"},
            "total_views": {"$sum": "$views"}
        }},
        {"$sort": {"avg_engagement": -1}}
    ]
    
    return await Article.aggregate(pipeline)

# Author productivity analysis
async def author_productivity():
    pipeline = [
        {"$group": {
            "_id": "$author_id",
            "article_count": {"$sum": 1},
            "total_views": {"$sum": "$views"},
            "total_likes": {"$sum": "$likes"},
            "avg_reading_time": {"$avg": "$reading_time"}
        }},
        {"$addFields": {
            "avg_views_per_article": {"$divide": ["$total_views", "$article_count"]},
            "avg_likes_per_article": {"$divide": ["$total_likes", "$article_count"]}
        }},
        {"$sort": {"avg_views_per_article": -1}},
        {"$limit": 20}
    ]
    
    return await Article.aggregate(pipeline)
```

### Time Series Analysis

```python
# Daily active users trend
async def daily_active_users(days: int = 30):
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    
    pipeline = [
        {"$match": {
            "last_login": {"$gte": start_date}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$last_login"},
                "month": {"$month": "$last_login"},
                "day": {"$dayOfMonth": "$last_login"}
            },
            "active_users": {"$sum": 1},
            "new_users": {
                "$sum": {
                    "$cond": {
                        "if": {"$gte": ["$created_at", start_date]},
                        "then": 1,
                        "else": 0
                    }
                }
            }
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
    ]
    
    return await User.aggregate(pipeline)

# Revenue trend with moving average
async def revenue_trend_with_moving_average():
    pipeline = [
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"},
                "day": {"$dayOfMonth": "$created_at"}
            },
            "daily_revenue": {"$sum": "$amount"},
            "order_count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
        {"$group": {
            "_id": None,
            "daily_data": {
                "$push": {
                    "date": "$_id",
                    "revenue": "$daily_revenue",
                    "orders": "$order_count"
                }
            }
        }},
        {"$addFields": {
            "daily_data": {
                "$map": {
                    "input": "$daily_data",
                    "as": "day",
                    "in": {
                        "date": "$$day.date",
                        "revenue": "$$day.revenue",
                        "orders": "$$day.orders",
                        "moving_avg": {
                            # 7-day moving average calculation would require more complex logic
                            "$avg": "$daily_data.revenue"
                        }
                    }
                }
            }
        }}
    ]
    
    return await Order.aggregate(pipeline)
```
