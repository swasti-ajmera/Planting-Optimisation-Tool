from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
import datetime


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String, index=True)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
