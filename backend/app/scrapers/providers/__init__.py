"""
Job source provider implementations.

All provider modules defined in this package self-register
via the @register_provider decorator upon import.
"""

from app.scrapers.providers.ashby import AshbyProvider
from app.scrapers.providers.company_careers import CompanyCareersProvider
from app.scrapers.providers.greenhouse import GreenhouseProvider
from app.scrapers.providers.indeed import IndeedProvider
from app.scrapers.providers.lever import LeverProvider
from app.scrapers.providers.linkedin import LinkedInProvider
from app.scrapers.providers.naukri import NaukriProvider
from app.scrapers.providers.wellfound import WellfoundProvider

__all__ = [
    "LinkedInProvider",
    "GreenhouseProvider",
    "LeverProvider",
    "AshbyProvider",
    "WellfoundProvider",
    "IndeedProvider",
    "NaukriProvider",
    "CompanyCareersProvider",
]
