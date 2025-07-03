"""
Type definitions for MongoDB ORM
"""
from typing import TypeVar, Dict, Any, List, Union, Optional
from datetime import datetime

# Type variables for generic model operations
ModelType = TypeVar('ModelType', bound='BaseModel')
DocumentType = Dict[str, Any]
FilterType = Dict[str, Any]
ProjectionType = Dict[str, int]
SortType = Dict[str, int]
PipelineType = List[Dict[str, Any]]

# Common field types
IndexDirection = int  # pymongo.ASCENDING or pymongo.DESCENDING
ObjectId = Any  # MongoDB ObjectId type
Timestamp = datetime

# Result types
QueryResult = Union[ModelType, None]
QueryResults = List[ModelType]
AggregationResult = List[DocumentType]
BulkResult = List[ModelType]
CountResult = int
DistinctResult = List[Any]

# Configuration types
ConfigDict = Dict[str, Any]
ConnectionParams = Dict[str, Any]
