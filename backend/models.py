from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON
from sqlalchemy.sql import func
from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    gem_balance = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    avatar_url = Column(String(500), nullable=True)
    short_description = Column(String(300), nullable=True)
    tags = Column(JSON, nullable=True)
    rating_avg = Column(Float, nullable=False, default=0.0)
    rating_count = Column(Integer, nullable=False, default=0)
    gem_cost_per_message = Column(Integer, nullable=True)
    nsfw_flags = Column(Boolean, nullable=False, default=False)
    last_active = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
