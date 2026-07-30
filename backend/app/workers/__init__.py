"""
Celery background workers.

This package contains Celery task definitions for
long-running background operations:

- search_tasks: Job search execution
- match_tasks: Matching pipeline execution
- llm_tasks: LLM analysis tasks
- report_tasks: Report generation
- notification_tasks: Notification delivery
- maintenance_tasks: Cleanup and refresh operations

Workers are configured with:
- Retry policies (exponential backoff)
- Rate limiting per task type
- Priority queues
- Dead-letter logging
"""
