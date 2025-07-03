"""
Connection manager for MongoDB ORM
"""
import asyncio
import logging
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import DatabaseConfig
from .exceptions import ConnectionError


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages MongoDB connections with proper cleanup and connection pooling"""

    _instance: Optional['ConnectionManager'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._clients: Dict[str, AsyncIOMotorClient] = {}
        self._databases: Dict[str, AsyncIOMotorDatabase] = {}
        self._is_closed = False

    @classmethod
    async def get_instance(cls) -> 'ConnectionManager':
        """Get singleton instance of connection manager"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def get_client(self, config: DatabaseConfig) -> AsyncIOMotorClient:
        """Get or create a client for the given configuration"""
        if self._is_closed:
            raise ConnectionError("Connection manager is closed")

        client_key = f"{config.mongo_uri}_{config.database_name}"

        if client_key not in self._clients:
            try:
                motor_kwargs = config.to_motor_kwargs()
                client = AsyncIOMotorClient(config.mongo_uri, **motor_kwargs)

                # Test the connection
                await client.admin.command("ping")

                self._clients[client_key] = client
                logger.info(f"Created new client for {client_key}")

            except Exception as e:
                logger.error(f"Failed to create client for {client_key}: {e}")
                raise ConnectionError(f"Failed to connect to MongoDB: {e}")

        return self._clients[client_key]

    async def get_database(self, config: DatabaseConfig) -> AsyncIOMotorDatabase:
        """Get or create a database for the given configuration"""
        db_key = f"{config.mongo_uri}_{config.database_name}"

        if db_key not in self._databases:
            client = await self.get_client(config)
            self._databases[db_key] = client[config.database_name]
            logger.info(f"Created database connection for {config.database_name}")

        return self._databases[db_key]

    async def close_all(self):
        """Close all connections"""
        self._is_closed = True

        for client_key, client in self._clients.items():
            try:
                client.close()
                logger.info(f"Closed client {client_key}")
            except Exception as e:
                logger.error(f"Error closing client {client_key}: {e}")

        self._clients.clear()
        self._databases.clear()

        # Reset singleton
        ConnectionManager._instance = None
        logger.info("Connection manager closed")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_all()

    def __del__(self):
        """Cleanup on deletion"""
        if not self._is_closed and self._clients:
            logger.warning("Connection manager was not properly closed")
