"""
MongoDB ORM - A modern, async MongoDB Object-Relational Mapping library for Python.

This package provides a simple yet powerful way to work with MongoDB using async/await
patterns, built on top of Motor and Pydantic for robust data validation.
"""

from .__version__ import __version__
__author__ = 'Aasif Rahman M'
__email__ = 'asifrahman15@gmail.com'

# Core imports
from .models import BaseModel
from .config import DatabaseConfig, ModelConfig
from .connection import ConnectionManager
from .exceptions import (
    MongoDBORMError,
    ConnectionError,
    ModelNotInitializedError,
    ValidationError,
    DocumentNotFoundError,
    DuplicateDocumentError,
    ConfigurationError
)
from .utils import (
    register_model,
    register_models,
    register_all_models,
    close_all_connections,
    current_datetime,
    health_check,
    setup_logging,
    create_test_data
)

# Public API
__all__ = [
    # Core classes
    'BaseModel',
    'DatabaseConfig',
    'ModelConfig',
    'ConnectionManager',

    # Exceptions
    'MongoDBORMError',
    'ConnectionError',
    'ModelNotInitializedError',
    'ValidationError',
    'DocumentNotFoundError',
    'DuplicateDocumentError',
    'ConfigurationError',

    # Utility functions
    'register_model',
    'register_models',
    'register_all_models',
    'close_all_connections',
    'current_datetime',
    'health_check',
    'setup_logging',
    'create_test_data',

    # Version info
    '__version__',
    '__author__',
    '__email__'
]
