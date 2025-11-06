"""Database models and schemas for the application."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """Represents a subscribed user."""
    user_id: int
    subscribed_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row):
        """Create a User instance from a database row."""
        user_id, subscribed_at = row
        return cls(user_id=user_id, subscribed_at=subscribed_at)


@dataclass
class BotUser:
    """Represents a bot user."""
    user_id: int
    first_used_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row):
        """Create a BotUser instance from a database row."""
        user_id, first_used_at = row
        return cls(user_id=user_id, first_used_at=first_used_at)
