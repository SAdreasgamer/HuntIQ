"""
Job scraping subsystem.

This package contains the Apify HTTP client, provider abstraction
layer, provider registry, and all job source provider implementations.

Architecture:
    ApifyClient → JobProvider (ABC) → Concrete Providers
                                    ↓
                              ProviderRegistry

Usage:
    from app.scrapers import ApifyClient
    from app.scrapers.registry import get_provider, get_all_providers

    async with ApifyClient() as client:
        provider = get_provider("linkedin", client)
        result = await provider.search(search_input)
"""

from app.scrapers.apify_client import ApifyClient
from app.scrapers.base_provider import JobProvider
from app.scrapers.registry import (
    get_all_providers,
    get_provider,
    import_all_providers,
    is_registered,
    list_providers,
    register_provider,
)
from app.scrapers.schemas import ProviderResult, RawJobData, SearchInput


__all__ = [
    # Client
    "ApifyClient",
    # Base
    "JobProvider",
    # Registry
    "register_provider",
    "get_provider",
    "get_all_providers",
    "list_providers",
    "is_registered",
    "import_all_providers",
    # Schemas
    "RawJobData",
    "SearchInput",
    "ProviderResult",
]
