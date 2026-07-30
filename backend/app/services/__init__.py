"""
Service layer — business logic.

This package contains service classes that implement
all business logic. Services are the primary consumers
of repositories and external providers.

Each service:
- Receives repositories and providers via dependency injection
- Implements business rules and workflows
- Orchestrates cross-cutting operations
- Never accesses the database directly (uses repositories)
- Never handles HTTP concerns (that's the API layer's job)
"""
