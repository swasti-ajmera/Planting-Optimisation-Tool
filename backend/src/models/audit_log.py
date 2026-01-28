"""
Audit Log Model

SQLAlchemy model for tracking security-relevant events and user actions.
Provides an immutable audit trail for compliance, security monitoring, and forensics.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
import datetime


class AuditLog(Base):
    """
    Audit log database model for security and compliance tracking.

    Records important user actions and system events for accountability,
    security monitoring, and regulatory compliance. Audit logs should be
    treated as append-only and never modified or deleted.

    Attributes:
        id: Primary key, unique identifier for the log entry
        user_id: Foreign key to users table - who performed the action
        event_type: Category of event (indexed for fast filtering)
        details: Detailed description of what happened
        timestamp: When the event occurred (UTC, auto-set on creation)
        user: Relationship to User model - the user who triggered the event

    Common Event Types:
        - "user_create": New user account created
        - "user_update": User account modified
        - "user_delete": User account deleted
        - "login": Successful authentication
        - "login_failed": Failed authentication attempt
        - "role_change": User role modified
        - "password_change": User password changed

    Usage Example:
        from src.domains.authentication import log_audit_event

        await log_audit_event(
            db=db,
            user_id=current_user.id,
            event_type="user_create",
            details=f"Created user {new_user.email} with role {new_user.role}"
        )

    Security & Compliance:
        - Provides accountability for user actions
        - Helps detect suspicious activity patterns
        - Required for many security standards (SOC 2, ISO 27001, etc.)
        - Useful for incident response and forensics
        - Should be backed up and protected from tampering

    Database Schema:
        - Table name: audit_logs
        - Indexes on: id, event_type (for fast queries)
        - Foreign key: user_id -> users.id
        - Auto-timestamp on insert

    Best Practices:
        - Never modify or delete audit logs (append-only)
        - Include enough detail to understand what happened
        - Log both successful and failed security-relevant actions
        - Protect audit logs with appropriate access controls
        - Regularly review logs for anomalies
    """

    __tablename__ = "audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action
    user_id = Column(Integer, ForeignKey("users.id"))

    # What type of event occurred (indexed for fast filtering)
    event_type = Column(String, index=True)

    # Detailed description of the event
    details = Column(String)

    # When the event occurred (UTC, auto-set on creation)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship to User model
    user = relationship("User")
