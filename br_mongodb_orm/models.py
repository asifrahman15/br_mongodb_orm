import os
import logging
import asyncio
from typing import Optional, Dict, Any, List, Union, Type, TypeVar, ClassVar, AsyncIterator
from datetime import datetime, UTC

import pydantic
import pymongo
from motor.motor_asyncio import (
    AsyncIOMotorClient as Client,
    AsyncIOMotorDatabase as Database,
    AsyncIOMotorCollection as Collection
)

from .config import DatabaseConfig, ModelConfig
from .connection import ConnectionManager
from .exceptions import (
    ModelNotInitializedError,
    DocumentNotFoundError,
    ValidationError,
    DuplicateDocumentError
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseModel')


class BaseModel(pydantic.BaseModel):
    """
    Base MongoDB Model class with async operations and proper error handling.

    By inheriting this class you can make your class a MongoDB Model.
    The definition of the Meta class is optional, the following are the default values:
        mongo_uri: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        database_name: str = os.environ.get("MONGO_DATABASE", "default_db")
        collection_name: str = cls.__name__
        auto_create_indexes: bool = True
        strict_mode: bool = True
        use_auto_id: bool = True
        id_field: str = "id"
    """

    # Class-level attributes for MongoDB operations
    _db_config: ClassVar[Optional[DatabaseConfig]] = None
    _model_config: ClassVar[Optional[ModelConfig]] = None
    _collection: ClassVar[Optional[Collection]] = None
    _id_sequences: ClassVar[Optional[Collection]] = None
    _initialized: ClassVar[bool] = False
    _connection_manager: ClassVar[Optional[ConnectionManager]] = None

    # Instance attributes
    id: Optional[int] = pydantic.Field(default=None, description="Auto-generated unique ID")
    created_at: datetime = pydantic.Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = pydantic.Field(default_factory=lambda: datetime.now(UTC))

    model_config = pydantic.ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
        extra='forbid'
    )
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    @classmethod
    async def __initialize__(cls, client: Optional[Client] = None,
                           db_config: Optional[DatabaseConfig] = None) -> None:
        """
        Initialize the model with database configuration and connection.

        Args:
            client: Optional pre-configured AsyncIOMotorClient
            db_config: Optional database configuration

        Raises:
            ModelNotInitializedError: If initialization fails
        """
        if cls._initialized:
            return

        try:
            logger.info(f"Initializing {cls.__name__} Model")

            # Setup configuration
            cls._setup_configuration(db_config)

            # Setup connection
            await cls._setup_connection(client)

            # Setup collections
            await cls._setup_collections()

            # Create indexes if needed
            if cls._model_config.auto_create_indexes:
                await cls._create_default_indexes()

            cls._initialized = True
            logger.info(f"{cls.__name__} Model initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize {cls.__name__}: {e}")
            raise ModelNotInitializedError(f"Failed to initialize {cls.__name__}: {e}")

    @classmethod
    def _setup_configuration(cls, db_config: Optional[DatabaseConfig] = None) -> None:
        """Setup database and model configuration"""
        # Get or create database config
        if db_config:
            cls._db_config = db_config
        else:
            # Try to get from Meta class or use defaults
            meta_class = getattr(cls, "Meta", None)
            if meta_class:
                cls._db_config = DatabaseConfig(
                    mongo_uri=getattr(meta_class, 'mongo_uri', os.environ.get("MONGO_URI", "mongodb://localhost:27017")),
                    database_name=getattr(meta_class, 'database_name', os.environ.get("MONGO_DATABASE", "default_db")),
                    max_pool_size=getattr(meta_class, 'max_pool_size', 100),
                    min_pool_size=getattr(meta_class, 'min_pool_size', 0),
                )
            else:
                cls._db_config = DatabaseConfig()

        # Setup model config with smart defaults
        meta_class = getattr(cls, "Meta", None)

        # Auto-generate collection name from class name (convert CamelCase to snake_case)
        default_collection_name = cls._camel_to_snake(cls.__name__)

        if meta_class:
            cls._model_config = ModelConfig(
                collection_name=getattr(meta_class, 'collection_name', default_collection_name),
                auto_create_indexes=getattr(meta_class, 'auto_create_indexes', True),
                strict_mode=getattr(meta_class, 'strict_mode', True),
                use_auto_id=getattr(meta_class, 'use_auto_id', True),
                id_field=getattr(meta_class, 'id_field', 'id'),
            )
        else:
            # No Meta class defined - use all defaults
            cls._model_config = ModelConfig(
                collection_name=default_collection_name,
                auto_create_indexes=True,
                strict_mode=True,
                use_auto_id=True,
                id_field='id'
            )

    @classmethod
    def _camel_to_snake(cls, name: str) -> str:
        """Convert CamelCase to snake_case for collection names"""
        import re
        # Insert an underscore before any uppercase letter that follows a lowercase letter
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert an underscore before any uppercase letter that follows a lowercase letter or digit
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @classmethod
    async def _setup_connection(cls, client: Optional[Client] = None) -> None:
        """Setup database connection"""
        cls._connection_manager = await ConnectionManager.get_instance()

        if client:
            # Use provided client (for testing or custom setup)
            cls._database = client[cls._db_config.database_name]
        else:
            # Use connection manager
            cls._database = await cls._connection_manager.get_database(cls._db_config)

    @classmethod
    async def _setup_collections(cls) -> None:
        """Setup collections"""
        cls._collection = cls._database[cls._model_config.collection_name]
        cls._id_sequences = cls._database["id_sequences"]

    @classmethod
    async def _create_default_indexes(cls) -> None:
        """Create default indexes for the model"""
        try:
            # Create index on id field if using auto ID
            if cls._model_config.use_auto_id:
                await cls._collection.create_index(cls._model_config.id_field, unique=True)

            # Create indexes on timestamp fields
            await cls._collection.create_index("created_at")
            await cls._collection.create_index("updated_at")

            logger.info(f"Created default indexes for {cls.__name__}")
        except Exception as e:
            logger.warning(f"Failed to create indexes for {cls.__name__}: {e}")

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure the model is initialized before operations"""
        if not cls._initialized:
            raise ModelNotInitializedError(f"{cls.__name__} must be initialized before use. Call __initialize__() first.")

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override to update timestamp on dump"""
        self.updated_at = datetime.now(UTC)
        return super().model_dump(**kwargs)

    def dict(self) -> Dict[str, Any]:
        """Legacy method for compatibility"""
        return self.model_dump()

    def json(self) -> str:
        """Legacy method for compatibility"""
        return self.model_dump_json()

    async def _get_next_id(self) -> int:
        """
        Get the next auto-increment ID for this model.

        Returns:
            Next available ID

        Raises:
            ValidationError: If ID generation fails
        """
        if not self._model_config.use_auto_id:
            raise ValidationError(f"Auto ID is disabled for {self.__class__.__name__}")

        try:
            sequence = await self._id_sequences.find_one_and_update(
                {"_id": self._model_config.collection_name},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=pymongo.ReturnDocument.AFTER
            )
            return sequence["seq"]
        except Exception as e:
            logger.error(f"Failed to generate ID for {self.__class__.__name__}: {e}")
            raise ValidationError(f"Failed to generate ID: {e}")

    async def _prepare_for_save(self) -> Dict[str, Any]:
        """Prepare document data for saving"""
        # Generate ID if needed
        if not getattr(self, self._model_config.id_field) and self._model_config.use_auto_id:
            setattr(self, self._model_config.id_field, await self._get_next_id())

        # Update timestamp
        self.updated_at = datetime.now(UTC)

        return self.model_dump()

    @classmethod
    def params_to_mongo_style(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert filter parameters to MongoDB style.

        Args:
            kwargs: Filter criteria

        Returns:
            Converted filter criteria
        """
        converted = {}
        for key, value in kwargs.items():
            if '__' in key:
                field, operator = key.split('__', 1)
                if field not in converted:
                    converted[field] = {}
                converted[field][f'${operator}'] = value
            else:
                converted[key] = value
        return converted

    @classmethod
    async def get(cls: Type[T], **kwargs) -> Optional[T]:
        """
        Get a single document by filter criteria.

        Args:
            **kwargs: Filter criteria

        Returns:
            Model instance or None if not found

        Raises:
            ModelNotInitializedError: If model is not initialized
        """
        cls._ensure_initialized()

        try:
            kwargs = cls.params_to_mongo_style(kwargs)
            document = await cls._collection.find_one(kwargs)
            if document:
                # Remove MongoDB's _id field before creating instance
                document.pop('_id', None)
                return cls(**document)
            return None
        except Exception as e:
            logger.error(f"Error getting document from {cls.__name__}: {e}")
            raise ValidationError(f"Failed to get document: {e}")

    @classmethod
    async def get_by_id(cls: Type[T], doc_id: int) -> Optional[T]:
        """
        Get a document by its ID.

        Args:
            doc_id: Document ID

        Returns:
            Model instance or None if not found
        """
        return await cls.get(**{cls._model_config.id_field: doc_id})

    @classmethod
    def filter(cls: Type[T],
               sort_by: Optional[Dict[str, int]] = None,
               limit: int = 0,
               skip: int = 0,
               projection: Optional[Dict[str, int]] = None,
               **kwargs) -> 'AsyncModelCursor':
        """
        Filter documents with advanced options. Returns an async cursor for memory-efficient iteration.

        Args:
            sort_by: Sort criteria (default: {id_field: 1})
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            projection: Fields to include/exclude
            **kwargs: Filter criteria

        Returns:
            AsyncModelCursor for iterating over results with async for

        Example:
            # Memory-efficient iteration
            async for user in User.filter(age__gte=18):
                print(user.name)

            # Or convert to list if needed (less memory efficient)
            users = await User.filter(age__gte=18).to_list()
        """
        cls._ensure_initialized()

        try:
            kwargs = cls.params_to_mongo_style(kwargs)

            # Set default sort
            if sort_by is None:
                sort_by = {cls._model_config.id_field: 1}

            # Set default projection to exclude MongoDB's _id
            if projection is None:
                projection = {"_id": 0}
            elif "_id" not in projection:
                projection["_id"] = 0

            cursor = cls._collection.find(
                filter=kwargs,
                projection=projection,
                limit=limit,
                skip=skip
            )

            if sort_by:
                cursor = cursor.sort(list(sort_by.items()))

            # Determine if we should return raw documents or model instances
            use_raw_docs = projection and len(projection) > 1  # More than just _id exclusion

            return AsyncModelCursor(cursor, cls, use_raw_docs=use_raw_docs)

        except Exception as e:
            logger.error(f"Error creating cursor for {cls.__name__}: {e}")
            raise ValidationError(f"Failed to create cursor: {e}")

    @classmethod
    async def count(cls, **kwargs) -> int:
        """
        Count documents matching the filter criteria.

        Args:
            **kwargs: Filter criteria

        Returns:
            Number of matching documents
        """
        cls._ensure_initialized()

        try:
            kwargs = cls.params_to_mongo_style(kwargs)
            return await cls._collection.count_documents(kwargs)
        except Exception as e:
            logger.error(f"Error counting documents in {cls.__name__}: {e}")
            raise ValidationError(f"Failed to count documents: {e}")

    @classmethod
    async def distinct(cls, field: str, **kwargs) -> List[Any]:
        """
        Get distinct values for a field.

        Args:
            field: Field name to get distinct values for
            **kwargs: Filter criteria

        Returns:
            List of distinct values
        """
        cls._ensure_initialized()

        try:
            kwargs = cls.params_to_mongo_style(kwargs)
            return await cls._collection.distinct(field, filter=kwargs)
        except Exception as e:
            logger.error(f"Error getting distinct values from {cls.__name__}: {e}")
            raise ValidationError(f"Failed to get distinct values: {e}")

    @classmethod
    def all(cls: Type[T]) -> 'AsyncModelCursor':
        """
        Get all documents in the collection as an async cursor.

        Returns:
            AsyncModelCursor for iterating over all documents

        Example:
            # Memory-efficient iteration
            async for user in User.all():
                print(user.name)

            # Or convert to list if needed (less memory efficient)
            users = await User.all().to_list()
        """
        return cls.filter()

    @classmethod
    async def create(cls: Type[T], **kwargs) -> T:
        """
        Create and save a new document.

        Args:
            **kwargs: Document data

        Returns:
            Created model instance

        Raises:
            ValidationError: If document creation fails
            DuplicateDocumentError: If document with same ID already exists
        """
        cls._ensure_initialized()

        try:
            instance = cls(**kwargs)
            document_data = await instance._prepare_for_save()

            result = await cls._collection.insert_one(document_data)

            if result.inserted_id:
                # Return the created instance with the generated ID
                return instance
            else:
                raise ValidationError("Failed to insert document")

        except pymongo.errors.DuplicateKeyError as e:
            logger.error(f"Duplicate document in {cls.__name__}: {e}")
            raise DuplicateDocumentError(f"Document with same ID already exists: {e}")
        except Exception as e:
            logger.error(f"Error creating document in {cls.__name__}: {e}")
            raise ValidationError(f"Failed to create document: {e}")

    @classmethod
    async def get_or_create(cls: Type[T], defaults: Optional[Dict[str, Any]] = None,
                          **kwargs) -> tuple[T, bool]:
        """
        Get an existing document or create a new one.

        Args:
            defaults: Default values for creation if document doesn't exist
            **kwargs: Filter criteria for existing document

        Returns:
            Tuple of (instance, created) where created is True if new document was created
        """
        cls._ensure_initialized()

        try:
            # Try to get existing document
            existing = await cls.get(**kwargs)
            if existing:
                return existing, False

            # Create new document
            create_data = {**kwargs}
            if defaults:
                create_data.update(defaults)

            new_instance = await cls.create(**create_data)
            return new_instance, True

        except Exception as e:
            logger.error(f"Error in get_or_create for {cls.__name__}: {e}")
            raise ValidationError(f"Failed to get or create document: {e}")

    async def save(self, only_update: bool = False) -> 'BaseModel':
        """
        Save the current instance to the database.

        Args:
            only_update: If True, only update existing documents (don't create new)

        Returns:
            Self instance

        Raises:
            ValidationError: If save operation fails
            DocumentNotFoundError: If only_update=True and document doesn't exist
        """
        self._ensure_initialized()

        try:
            document_data = await self._prepare_for_save()
            id_field = self._model_config.id_field
            doc_id = getattr(self, id_field)

            if not doc_id:
                if only_update:
                    raise DocumentNotFoundError("Cannot update document without ID")
                else:
                    # This should not happen as _prepare_for_save generates ID
                    raise ValidationError("Document ID is required for save operation")

            result = await self._collection.update_one(
                {id_field: doc_id},
                {"$set": document_data},
                upsert=not only_update
            )

            if only_update and result.matched_count == 0:
                raise DocumentNotFoundError(f"Document with {id_field}={doc_id} not found")

            return self

        except Exception as e:
            logger.error(f"Error saving document in {self.__class__.__name__}: {e}")
            raise ValidationError(f"Failed to save document: {e}")

    async def delete(self) -> bool:
        """
        Delete the current document from the database.

        Returns:
            True if document was deleted, False otherwise

        Raises:
            DocumentNotFoundError: If document doesn't have an ID
            ValidationError: If delete operation fails
        """
        self._ensure_initialized()

        id_field = self._model_config.id_field
        doc_id = getattr(self, id_field)

        if not doc_id:
            raise DocumentNotFoundError("Cannot delete document without ID")

        try:
            result = await self._collection.delete_one({id_field: doc_id})
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting document from {self.__class__.__name__}: {e}")
            raise ValidationError(f"Failed to delete document: {e}")

    @classmethod
    async def delete_many(cls, **kwargs) -> int:
        """
        Delete multiple documents matching the filter criteria.

        Args:
            **kwargs: Filter criteria

        Returns:
            Number of deleted documents

        Raises:
            ValidationError: If delete operation fails
        """
        cls._ensure_initialized()

        try:
            kwargs = cls.params_to_mongo_style(kwargs)
            result = await cls._collection.delete_many(kwargs)
            return result.deleted_count

        except Exception as e:
            logger.error(f"Error deleting documents from {cls.__name__}: {e}")
            raise ValidationError(f"Failed to delete documents: {e}")

    async def refresh_from_db(self) -> Optional['BaseModel']:
        """
        Refresh the current instance with data from the database.

        Returns:
            Self instance if refreshed successfully, None if document not found

        Raises:
            DocumentNotFoundError: If document doesn't have an ID
        """
        self._ensure_initialized()

        id_field = self._model_config.id_field
        doc_id = getattr(self, id_field)

        if not doc_id:
            raise DocumentNotFoundError("Cannot refresh document without ID")

        try:
            fresh_instance = await self.get(**{id_field: doc_id})
            if fresh_instance:
                # Update current instance with fresh data
                for key, value in fresh_instance.model_dump().items():
                    setattr(self, key, value)
                return self
            return None

        except Exception as e:
            logger.error(f"Error refreshing document from {self.__class__.__name__}: {e}")
            raise ValidationError(f"Failed to refresh document: {e}")

    @classmethod
    def aggregate(cls, pipeline: List[Dict[str, Any]]) -> 'AsyncAggregationCursor':
        """
        Perform aggregation query on the collection. Returns an async cursor for memory-efficient iteration.

        Args:
            pipeline: MongoDB aggregation pipeline

        Returns:
            AsyncAggregationCursor for iterating over aggregation results

        Example:
            # Memory-efficient iteration
            async for result in User.aggregate([{"$group": {"_id": "$age", "count": {"$sum": 1}}}]):
                print(f"Age {result['_id']}: {result['count']} users")

            # Or convert to list if needed (less memory efficient)
            results = await User.aggregate(pipeline).to_list()

        Raises:
            ValidationError: If aggregation fails
        """
        cls._ensure_initialized()

        try:
            cursor = cls._collection.aggregate(pipeline)
            return AsyncAggregationCursor(cursor)

        except Exception as e:
            logger.error(f"Error creating aggregation cursor for {cls.__name__}: {e}")
            raise ValidationError(f"Aggregation failed: {e}")

    @classmethod
    async def create_index(cls, field: str, unique: bool = False,
                         direction: int = pymongo.ASCENDING) -> bool:
        """
        Create an index on a field.

        Args:
            field: Field name to index
            unique: Whether the index should enforce uniqueness
            direction: Index direction (ASCENDING or DESCENDING)

        Returns:
            True if index was created, False if it already exists

        Raises:
            ValidationError: If index creation fails
        """
        cls._ensure_initialized()

        try:
            index_name = f"{field}_{direction}"
            existing_indexes = await cls._collection.index_information()

            if index_name in existing_indexes:
                logger.info(f"Index {index_name} already exists for {cls.__name__}")
                return False

            await cls._collection.create_index(
                [(field, direction)],
                unique=unique,
                name=index_name
            )
            logger.info(f"Created index {index_name} for {cls.__name__}")
            return True

        except Exception as e:
            logger.error(f"Error creating index for {cls.__name__}: {e}")
            raise ValidationError(f"Failed to create index: {e}")

    @classmethod
    async def create_compound_index(cls, fields: Dict[str, int], unique: bool = False) -> bool:
        """
        Create a compound index on multiple fields.

        Args:
            fields: Dictionary of field names and directions
            unique: Whether the index should enforce uniqueness

        Returns:
            True if index was created, False if it already exists

        Raises:
            ValidationError: If index creation fails
        """
        cls._ensure_initialized()

        try:
            # Generate index name
            index_parts = []
            for field, direction in fields.items():
                index_parts.append(f"{field}_{direction}")
            index_name = "_".join(index_parts)

            existing_indexes = await cls._collection.index_information()

            if index_name in existing_indexes:
                logger.info(f"Compound index {index_name} already exists for {cls.__name__}")
                return False

            index_list = [(field, direction) for field, direction in fields.items()]
            await cls._collection.create_index(
                index_list,
                unique=unique,
                name=index_name
            )
            logger.info(f"Created compound index {index_name} for {cls.__name__}")
            return True

        except Exception as e:
            logger.error(f"Error creating compound index for {cls.__name__}: {e}")
            raise ValidationError(f"Failed to create compound index: {e}")

    @classmethod
    async def drop_index(cls, index_name: str) -> bool:
        """
        Drop an index from the collection.

        Args:
            index_name: Name of the index to drop

        Returns:
            True if index was dropped successfully

        Raises:
            ValidationError: If index dropping fails
        """
        cls._ensure_initialized()

        try:
            await cls._collection.drop_index(index_name)
            logger.info(f"Dropped index {index_name} for {cls.__name__}")
            return True

        except Exception as e:
            logger.error(f"Error dropping index for {cls.__name__}: {e}")
            raise ValidationError(f"Failed to drop index: {e}")

    @classmethod
    async def list_indexes(cls) -> Dict[str, Any]:
        """
        List all indexes for the collection.

        Returns:
            Dictionary of index information
        """
        cls._ensure_initialized()

        try:
            return await cls._collection.index_information()
        except Exception as e:
            logger.error(f"Error listing indexes for {cls.__name__}: {e}")
            raise ValidationError(f"Failed to list indexes: {e}")

    @classmethod
    async def bulk_create(cls: Type[T], documents: List[Dict[str, Any]],
                         ordered: bool = True) -> List[T]:
        """
        Bulk create multiple documents.

        Args:
            documents: List of document data dictionaries
            ordered: Whether to stop on first error (ordered) or continue (unordered)

        Returns:
            List of created model instances

        Raises:
            ValidationError: If bulk creation fails
        """
        cls._ensure_initialized()

        try:
            instances = []
            insert_docs = []

            for doc_data in documents:
                instance = cls(**doc_data)
                prepared_data = await instance._prepare_for_save()
                instances.append(instance)
                insert_docs.append(prepared_data)

            result = await cls._collection.insert_many(insert_docs, ordered=ordered)

            if len(result.inserted_ids) != len(documents):
                raise ValidationError("Not all documents were inserted")

            return instances

        except Exception as e:
            logger.error(f"Error in bulk create for {cls.__name__}: {e}")
            raise ValidationError(f"Bulk create failed: {e}")

    @classmethod
    async def close_connections(cls) -> None:
        """Close all database connections for this model"""
        if cls._connection_manager:
            await cls._connection_manager.close_all()
            cls._initialized = False
            logger.info(f"Closed connections for {cls.__name__}")

    def __repr__(self) -> str:
        """String representation of the model instance"""
        id_field = self._model_config.id_field if self._model_config else 'id'
        doc_id = getattr(self, id_field, None)
        return f"<{self.__class__.__name__}({id_field}={doc_id})>"

    def __str__(self) -> str:
        """String representation of the model instance"""
        return self.__repr__()


class AsyncModelCursor:
    """
    Async iterator for MongoDB documents that yields model instances one by one.
    This prevents loading all documents into memory at once.
    """

    def __init__(self, cursor, model_class: Type['BaseModel'], use_raw_docs: bool = False):
        """
        Initialize the async cursor.

        Args:
            cursor: MongoDB cursor
            model_class: The model class to instantiate
            use_raw_docs: If True, return raw documents instead of model instances
        """
        self._cursor = cursor
        self._model_class = model_class
        self._use_raw_docs = use_raw_docs

    def __aiter__(self) -> AsyncIterator[Union['BaseModel', Dict[str, Any]]]:
        """Return self as async iterator"""
        return self

    async def __anext__(self) -> Union['BaseModel', Dict[str, Any]]:
        """Get next document from cursor"""
        try:
            doc = await self._cursor.next()
            if doc is None:
                raise StopAsyncIteration

            # Remove MongoDB's _id field
            doc.pop('_id', None)

            if self._use_raw_docs:
                return doc
            else:
                return self._model_class(**doc)

        except StopAsyncIteration:
            raise
        except Exception as e:
            logger.error(f"Error getting next document: {e}")
            raise StopAsyncIteration

    async def to_list(self, length: Optional[int] = None) -> List[Union['BaseModel', Dict[str, Any]]]:
        """
        Convert cursor to list (for backward compatibility).

        Args:
            length: Maximum number of documents to return

        Returns:
            List of model instances or raw documents
        """
        results = []
        count = 0

        async for doc in self:
            results.append(doc)
            count += 1
            if length is not None and count >= length:
                break

        return results

    async def count(self) -> int:
        """Count total documents in cursor"""
        return await self._cursor.count()

    async def skip(self, count: int) -> 'AsyncModelCursor':
        """Skip specified number of documents"""
        self._cursor = self._cursor.skip(count)
        return self

    async def limit(self, count: int) -> 'AsyncModelCursor':
        """Limit number of documents"""
        self._cursor = self._cursor.limit(count)
        return self

    async def sort(self, key_or_list: Union[str, List[tuple]], direction: Optional[int] = None) -> 'AsyncModelCursor':
        """Sort documents"""
        if isinstance(key_or_list, str) and direction is not None:
            self._cursor = self._cursor.sort(key_or_list, direction)
        else:
            self._cursor = self._cursor.sort(key_or_list)
        return self


class AsyncAggregationCursor:
    """
    Async iterator for MongoDB aggregation results.
    This prevents loading all aggregation results into memory at once.
    """

    def __init__(self, cursor):
        """
        Initialize the async aggregation cursor.

        Args:
            cursor: MongoDB aggregation cursor
        """
        self._cursor = cursor

    def __aiter__(self) -> AsyncIterator[Dict[str, Any]]:
        """Return self as async iterator"""
        return self

    async def __anext__(self) -> Dict[str, Any]:
        """Get next document from aggregation cursor"""
        try:
            doc = await self._cursor.next()
            if doc is None:
                raise StopAsyncIteration
            return doc
        except StopAsyncIteration:
            raise
        except Exception as e:
            logger.error(f"Error getting next aggregation result: {e}")
            raise StopAsyncIteration

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Convert aggregation cursor to list (for backward compatibility).

        Args:
            length: Maximum number of documents to return

        Returns:
            List of aggregation results
        """
        results = []
        count = 0

        async for doc in self:
            results.append(doc)
            count += 1
            if length is not None and count >= length:
                break

        return results
