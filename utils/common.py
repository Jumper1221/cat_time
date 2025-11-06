import pytz
from datetime import datetime, timezone, time

def get_current_utc_time():
    """Get current time in UTC."""
    return datetime.now(timezone.utc)

def convert_local_time_to_utc_hour(local_hour, local_tz_name='Europe/Moscow'):
    """Convert a local hour to the corresponding UTC hour for scheduling."""
    local_tz = pytz.timezone(local_tz_name)
    # Create a datetime object with the local hour today
    now = datetime.now()
    local_time = datetime.combine(now.date(), time(local_hour))
    # Localize to user's timezone
    local_time = local_tz.localize(local_time)
    # Convert to UTC
    utc_time = local_time.astimezone(timezone.utc)
    return utc_time.hour

def convert_utc_to_local_hour(utc_hour, local_tz_name='Europe/Moscow'):
    """Convert a UTC hour to the corresponding local hour."""
    local_tz = pytz.timezone(local_tz_name)
    # Create a datetime object with the UTC hour today
    now = datetime.now()
    utc_time = datetime.combine(now.date(), time(utc_hour, 0, 0, tzinfo=timezone.utc))
    # Convert to local timezone
    local_time = utc_time.astimezone(local_tz)
    return local_time.hour

def convert_utc_to_local(utc_time, local_tz_name='Europe/Moscow'):
    """Convert UTC time to local timezone."""
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    local_tz = pytz.timezone(local_tz_name)
    return utc_time.astimezone(local_tz)

def convert_local_to_utc(local_time, local_tz_name='Europe/Moscow'):
    """Convert local time to UTC."""
    local_tz = pytz.timezone(local_tz_name)
    if local_time.tzinfo is None:
        local_time = local_tz.localize(local_time)
    return local_time.astimezone(timezone.utc)
