import inspect
import logging
import asyncio
from typing import List, Optional, Type, Any
from datetime import datetime, UTC
from motor.motor_asyncio import AsyncIOMotorClient

from .config import DatabaseConfig
from .exceptions import ModelNotInitializedError

logger = logging.getLogger(__name__)


def get_classes_from_module(module_name: str) -> List[Type]:
    """
    Get all classes defined in a module.

    Args:
        module_name: Name of the module to inspect

    Returns:
        List of class objects defined in the module

    Raises:
        ImportError: If module cannot be imported
    """
    try:
        # Dynamically import the module
        module = __import__(module_name, fromlist=[''])

        # Get all classes defined in the module
        classes = [
            member for name, member in inspect.getmembers(module, inspect.isclass)
            if member.__module__ == module.__name__
        ]

        return classes

    except ImportError as e:
        logger.error(f"Failed to import module {module_name}: {e}")
        raise


async def register_model(cls: Type, client: Optional[AsyncIOMotorClient] = None,
                        db_config: Optional[DatabaseConfig] = None) -> bool:
    """
    Register a single model with the database.

    Args:
        cls: Model class to register
        client: Optional pre-configured AsyncIOMotorClient
        db_config: Optional database configuration

    Returns:
        True if registration successful, False otherwise

    Raises:
        ModelNotInitializedError: If model initialization fails
    """
    try:
        await cls.__initialize__(client, db_config)
        logger.info(f"{cls.__name__} model registered successfully")
        return True

    except Exception as e:
        logger.error(f"{cls.__name__} model registration failed: {e}")
        raise ModelNotInitializedError(f"Failed to register {cls.__name__}: {e}")


async def register_models(classes: List[Type], client: Optional[AsyncIOMotorClient] = None,
                         db_config: Optional[DatabaseConfig] = None) -> List[bool]:
    """
    Register multiple models with the database.

    Args:
        classes: List of model classes to register
        client: Optional pre-configured AsyncIOMotorClient
        db_config: Optional database configuration

    Returns:
        List of boolean results for each model registration
    """
    results = []

    for cls in classes:
        try:
            result = await register_model(cls, client, db_config)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to register {cls.__name__}: {e}")
            results.append(False)

    return results


async def register_all_models(module_name: str, client: Optional[AsyncIOMotorClient] = None,
                             db_config: Optional[DatabaseConfig] = None) -> List[bool]:
    """
    Register all models defined in a module.

    This will register all the classes defined in the page with the given module name.
    Call this function once at the end of the module where the classes are defined.

    Args:
        module_name: __name__ of the module where the classes are defined
        client: Optional pre-configured AsyncIOMotorClient
        db_config: Optional database configuration

    Returns:
        List of boolean results for each model registration

    Raises:
        ImportError: If module cannot be imported
        ModelNotInitializedError: If any model fails to initialize
    """
    try:
        # Get all classes defined in the current module
        all_classes = get_classes_from_module(module_name)

        # Filter only BaseModel subclasses
        from .models import BaseModel
        model_classes = [cls for cls in all_classes if issubclass(cls, BaseModel) and cls != BaseModel]

        logger.info(f"Found {len(model_classes)} model classes in {module_name}")

        return await register_models(model_classes, client, db_config)

    except Exception as e:
        logger.error(f"Failed to register models from {module_name}: {e}")
        raise


async def close_all_connections() -> None:
    """
    Close all database connections for all models.

    This should be called when shutting down the application.
    """
    try:
        from .connection import ConnectionManager
        manager = await ConnectionManager.get_instance()
        await manager.close_all()
        logger.info("All database connections closed")

    except Exception as e:
        logger.error(f"Error closing connections: {e}")


def current_datetime() -> datetime:
    """
    Get current UTC datetime.

    Returns:
        Current datetime in UTC timezone
    """
    return datetime.now(UTC)


async def health_check(client: Optional[AsyncIOMotorClient] = None,
                      db_config: Optional[DatabaseConfig] = None) -> bool:
    """
    Perform a health check on the database connection.

    Args:
        client: Optional pre-configured client
        db_config: Optional database configuration

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        if client:
            await client.admin.command("ping")
        else:
            from .connection import ConnectionManager
            manager = await ConnectionManager.get_instance()

            if not db_config:
                db_config = DatabaseConfig()

            db_client = await manager.get_client(db_config)
            await db_client.admin.command("ping")

        logger.info("Database health check passed")
        return True

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def setup_logging(level: str = "INFO") -> None:
    """
    Setup logging configuration for the MongoDB ORM.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Set specific logger level for this package
    logger.setLevel(getattr(logging, level.upper()))
    logger.info(f"Logging configured with level: {level}")


async def create_test_data(model_class: Type, count: int = 10,
                          data_factory: Optional[callable] = None) -> List[Any]:
    """
    Create test data for a model.

    Args:
        model_class: Model class to create test data for
        count: Number of test documents to create
        data_factory: Optional function to generate test data

    Returns:
        List of created model instances

    Raises:
        ModelNotInitializedError: If model is not initialized
    """
    if not model_class._initialized:
        raise ModelNotInitializedError(f"{model_class.__name__} must be initialized before creating test data")

    test_instances = []

    for i in range(count):
        if data_factory:
            data = data_factory(i)
        else:
            # Default test data
            data = {
                "name": f"Test Item {i}",
                "value": i * 10,
                "description": f"This is test item number {i}"
            }

        try:
            instance = await model_class.create(**data)
            test_instances.append(instance)

        except Exception as e:
            logger.error(f"Failed to create test data item {i}: {e}")

    logger.info(f"Created {len(test_instances)} test instances for {model_class.__name__}")
    return test_instances
