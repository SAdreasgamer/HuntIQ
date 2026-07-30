"""
Repository layer — data access abstraction.

This package contains repository classes that encapsulate
all database operations. Repositories provide a clean
interface between the service layer and the database.

Each repository:
- Accepts an async SQLAlchemy session
- Provides CRUD operations for its domain
- Returns ORM model instances
- Never contains business logic

Pattern: Repository per aggregate root.
"""
