"""
Custom exceptions for MongoDB ORM
"""


class MongoDBORMError(Exception):
    """Base exception class for MongoDB ORM"""
    pass


class ConnectionError(MongoDBORMError):
    """Raised when connection to MongoDB fails"""
    pass


class ModelNotInitializedError(MongoDBORMError):
    """Raised when trying to use a model that hasn't been initialized"""
    pass


class ValidationError(MongoDBORMError):
    """Raised when model validation fails"""
    pass


class DocumentNotFoundError(MongoDBORMError):
    """Raised when a document is not found"""
    pass


class DuplicateDocumentError(MongoDBORMError):
    """Raised when trying to create a duplicate document"""
    pass


class ConfigurationError(MongoDBORMError):
    """Raised when configuration is invalid"""
    pass
