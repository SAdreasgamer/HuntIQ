"""
API layer — FastAPI route definitions and endpoint handlers.

This package contains all REST API routes organized by domain.
Each sub-module defines a FastAPI APIRouter with endpoints
for a specific domain (jobs, applications, resumes, etc.).

The routers are assembled in the main FastAPI application
via the `api.router` aggregator.
"""
