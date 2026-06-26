from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ..resources.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # This will store the AD username (sub from JWT)
    token = Column(String, unique=True, index=True)
    groups = Column(JSON, nullable=True) # Store user groups
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
