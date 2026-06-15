from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Float, Integer
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime, timezone


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    agent_name = Column(String, nullable=True)
    primary_color = Column(String, default="#6366f1")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="business", uselist=False)
    config = relationship("AgentConfig", back_populates="business", uselist=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="user")


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, unique=True)

    agent_name = Column(String, default="Agent")
    persona_prompt = Column(Text, nullable=True)
    tone = Column(String, default="professional")

    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=500)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", back_populates="config")