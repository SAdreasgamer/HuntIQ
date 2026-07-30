"""
Notification service.

This package handles notification routing and delivery:

- NotificationChannel interface (ABC)
- Channel implementations (Email, Desktop, Webhook)
- Notification rule engine (threshold, favorites, dedup)
- Delivery tracking and retry

Notifications are sent only when:
- Match score exceeds configured threshold
- Company is in user's favorites
- Job is newly posted (not stale)
- Salary exceeds configured minimum
- The notification has not been sent before (dedup)
"""
