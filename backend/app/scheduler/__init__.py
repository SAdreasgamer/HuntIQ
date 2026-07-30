"""
Task scheduler.

This package configures APScheduler for recurring tasks:

- Job search (configurable frequency)
- Job refresh (daily, check for closed postings)
- Report generation (daily)
- Analytics snapshot (daily)
- Notification dispatch (event-driven)
- Provider health checks (hourly)

The scheduler enqueues tasks into Celery via Redis
for reliable async execution.
"""
