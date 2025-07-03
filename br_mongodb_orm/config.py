"""
Configuration management for MongoDB ORM
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from .exceptions import ConfigurationError


logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration class"""
    mongo_uri: str = field(default_factory=lambda: os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    database_name: str = field(default_factory=lambda: os.environ.get("MONGO_DATABASE", "default_db"))
    max_pool_size: int = field(default_factory=lambda: int(os.environ.get("MONGO_MAX_POOL_SIZE", "100")))
    min_pool_size: int = field(default_factory=lambda: int(os.environ.get("MONGO_MIN_POOL_SIZE", "0")))
    server_selection_timeout_ms: int = field(default_factory=lambda: int(os.environ.get("MONGO_SERVER_SELECTION_TIMEOUT", "5000")))
    connect_timeout_ms: int = field(default_factory=lambda: int(os.environ.get("MONGO_CONNECT_TIMEOUT", "10000")))
    socket_timeout_ms: int = field(default_factory=lambda: int(os.environ.get("MONGO_SOCKET_TIMEOUT", "5000")))
    retry_writes: bool = field(default_factory=lambda: os.environ.get("MONGO_RETRY_WRITES", "true").lower() == "true")

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.mongo_uri:
            raise ConfigurationError("MONGO_URI is required")
        if not self.database_name:
            raise ConfigurationError("Database name is required")
        if self.max_pool_size <= 0:
            raise ConfigurationError("max_pool_size must be positive")
        if self.min_pool_size < 0:
            raise ConfigurationError("min_pool_size cannot be negative")
        if self.server_selection_timeout_ms <= 0:
            raise ConfigurationError("server_selection_timeout_ms must be positive")

    def to_motor_kwargs(self) -> Dict[str, Any]:
        """Convert config to motor client kwargs"""
        return {
            "maxPoolSize": self.max_pool_size,
            "minPoolSize": self.min_pool_size,
            "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
            "connectTimeoutMS": self.connect_timeout_ms,
            "socketTimeoutMS": self.socket_timeout_ms,
            "retryWrites": self.retry_writes,
        }


@dataclass
class ModelConfig:
    """Model-specific configuration"""
    collection_name: Optional[str] = None
    auto_create_indexes: bool = True
    strict_mode: bool = True
    use_auto_id: bool = True
    id_field: str = "id"

    def __post_init__(self):
        """Validate model configuration"""
        if self.id_field and not isinstance(self.id_field, str):
            raise ConfigurationError("id_field must be a string")
