"""
Configuration management.

This package contains Pydantic Settings classes that load
and validate all application configuration from environment
variables and .env files.

All configuration is centralized here. No other module
should read environment variables directly.

Settings hierarchy:
- Settings (root)
  ├── DatabaseSettings
  ├── RedisSettings
  ├── ApifySettings
  ├── LLMSettings
  ├── SearchSettings
  ├── NotificationSettings
  ├── SecuritySettings
  └── AppSettings
"""
