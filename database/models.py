"""Database models and schemas for the application."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """Represents a subscribed user."""

    user_id: int
    subscribed_at: Optional[datetime] = None
    daily_cat_time: Optional[int] = (
        9  # Hour of the day for daily cat image (0-23) in user's local time
    )
    timezone: Optional[str] = (
        "UTC"  # User's timezone (e.g. 'Europe/Moscow', 'America/New_York')
    )

    @classmethod
    def from_row(cls, row):
        """Create a User instance from a database row."""
        if len(row) == 2:
            user_id, subscribed_at = row
            return cls(user_id=user_id, subscribed_at=subscribed_at)
        elif len(row) == 3:
            user_id, subscribed_at, daily_cat_time = row
            return cls(
                user_id=user_id,
                subscribed_at=subscribed_at,
                daily_cat_time=daily_cat_time,
            )
        else:
            raise ValueError(f"Invalid row format: {row}")


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
