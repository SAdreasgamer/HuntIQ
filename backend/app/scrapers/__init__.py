"""
Job scraping subsystem.

This package contains the Apify HTTP client, provider
abstraction, and all job source provider implementations.

Usage:
    from app.scrapers.apify_client import ApifyClient

    async with ApifyClient() as client:
        run = await client.run_actor("actor-id", {"input": "data"})
        items = await client.get_dataset_items(run["defaultDatasetId"])
"""

from app.scrapers.apify_client import ApifyClient


__all__ = [
    "ApifyClient",
]
