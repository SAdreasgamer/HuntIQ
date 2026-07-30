"""
HuntIQ — Provider Registry.

Decorator-based registration and discovery of job providers.
Providers self-register on import via @register_provider.
The orchestrator uses get_provider() or get_all_providers()
to discover and instantiate them.

Usage:
    # In a provider module:
    @register_provider
    class LinkedInProvider(JobProvider):
        provider_name = "linkedin"
        ...

    # In the orchestrator:
    from app.scrapers.registry import get_provider, get_all_providers

    provider = get_provider("linkedin", apify_client)
    all_providers = get_all_providers(apify_client)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.scrapers.apify_client import ApifyClient
    from app.scrapers.base_provider import JobProvider

logger = get_logger(__name__)

# Internal registry: provider_name -> provider class
_REGISTRY: dict[str, type[JobProvider]] = {}


def register_provider(cls: type[JobProvider]) -> type[JobProvider]:
    """
    Decorator to register a provider class in the global registry.

    Validates that the provider has required class attributes set
    before registration.

    Args:
        cls: The JobProvider subclass to register.

    Returns:
        The same class (unmodified).

    Raises:
        ConfigurationError: If provider_name or actor_id is not set.
    """
    if not cls.provider_name:
        raise ConfigurationError(
            message=f"Provider {cls.__name__} must set 'provider_name'",
        )
    if not cls.actor_id:
        raise ConfigurationError(
            message=f"Provider {cls.__name__} must set 'actor_id'",
        )

    if cls.provider_name in _REGISTRY:
        logger.warning(
            "provider_overwrite",
            provider=cls.provider_name,
            old_class=_REGISTRY[cls.provider_name].__name__,
            new_class=cls.__name__,
        )

    _REGISTRY[cls.provider_name] = cls
    logger.info(
        "provider_registered",
        provider=cls.provider_name,
        actor_id=cls.actor_id,
        class_name=cls.__name__,
    )
    return cls


def get_provider(name: str, apify_client: ApifyClient) -> JobProvider:
    """
    Get an instantiated provider by name.

    Args:
        name: The provider name (e.g., "linkedin").
        apify_client: An initialized ApifyClient instance.

    Returns:
        An instantiated JobProvider subclass.

    Raises:
        ConfigurationError: If no provider with that name is registered.
    """
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY.keys())) or "(none)"
        raise ConfigurationError(
            message=f"Unknown provider '{name}'. Available: {available}",
        )
    return cls(apify_client)


def get_all_providers(apify_client: ApifyClient) -> list[JobProvider]:
    """
    Get instances of all registered providers.

    Args:
        apify_client: An initialized ApifyClient instance.

    Returns:
        List of all registered JobProvider instances.
    """
    return [cls(apify_client) for cls in _REGISTRY.values()]


def list_providers() -> list[str]:
    """
    Get names of all registered providers.

    Returns:
        Sorted list of registered provider names.
    """
    return sorted(_REGISTRY.keys())


def is_registered(name: str) -> bool:
    """
    Check if a provider is registered.

    Args:
        name: The provider name.

    Returns:
        True if the provider is registered.
    """
    return name in _REGISTRY


def import_all_providers() -> None:
    """
    Import all provider modules to trigger @register_provider decorators.

    This must be called at application startup to ensure all providers
    are discovered and registered.
    """
    # Import each provider module — the @register_provider decorator
    # on each class will automatically register it.
    provider_modules = [
        "app.scrapers.providers.linkedin",
        "app.scrapers.providers.greenhouse",
        "app.scrapers.providers.lever",
        "app.scrapers.providers.ashby",
        "app.scrapers.providers.wellfound",
        "app.scrapers.providers.indeed",
        "app.scrapers.providers.naukri",
        "app.scrapers.providers.company_careers",
    ]

    import importlib

    for module_path in provider_modules:
        try:
            importlib.import_module(module_path)
        except ImportError:
            logger.debug(
                "provider_module_not_found",
                module=module_path,
            )
        except Exception as exc:
            logger.error(
                "provider_import_error",
                module=module_path,
                error=str(exc),
            )

    logger.info(
        "provider_discovery_complete",
        registered_count=len(_REGISTRY),
        providers=list_providers(),
    )
