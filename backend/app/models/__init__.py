"""
SQLAlchemy ORM models.

This package contains all SQLAlchemy declarative models
representing the database schema:

- User: Authentication and identity
- Company: Company intelligence
- Job: Normalized job listings
- JobSkill: Skills extracted from jobs
- JobSource: Provider tracking per job
- JobEmbedding: Vector embeddings for jobs
- ResumeVersion: Resume variants
- ResumeSkill: Skills extracted from resumes
- ResumeEmbedding: Vector embeddings for resumes
- Application: Application tracking
- ApplicationStage: Stage transition history
- Bookmark: Saved jobs
- BookmarkTag: Tag associations
- Recruiter: Recruiter contacts
- Notification: Notification history
- Report: Generated report metadata
- AnalyticsSnapshot: Aggregated metrics
- UserPreference: User configuration
- LLMCache: Cached LLM responses
- SearchCheckpoint: Interrupted search state
"""
