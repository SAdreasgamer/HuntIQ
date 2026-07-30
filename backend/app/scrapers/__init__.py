"""
Job scraper layer — provider implementations.

This package contains the job provider plugin system:

- Base provider interface (JobProvider ABC)
- Provider registry (dynamic discovery and instantiation)
- Apify client (HTTP gateway to Apify API)
- Individual provider implementations

Each provider implements the JobProvider interface:
- search_jobs(): Execute search against the job source
- normalize_job(): Convert raw data to structured Job schema
- validate(): Validate provider configuration
- health_check(): Check provider availability

Adding a new provider requires only creating a new module
in the providers/ sub-package.
"""
