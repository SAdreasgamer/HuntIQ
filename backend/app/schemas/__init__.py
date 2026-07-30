"""
Pydantic schemas for request/response validation.

This package contains Pydantic v2 models used for:

- API request body validation
- API response serialization
- Internal data transfer objects (DTOs)
- Configuration validation

Naming convention:
- *Create: Input schema for creation
- *Update: Input schema for updates
- *Response: Output schema for API responses
- *Filter: Query parameter schemas
- *Internal: Internal DTOs not exposed via API
"""
