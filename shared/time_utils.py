from datetime import datetime, timezone, timedelta;
import time;


LOCAL_TZ = datetime.now().astimezone().tzinfo;

# time functions

def str_to_unix(s, fmt="%Y-%m-%d %H:%M") -> int:
    """
    Local string -> UTC Unix timestamp
    """
    local_dt = datetime.strptime(s, fmt).replace(tzinfo=LOCAL_TZ)
    return int(local_dt.timestamp())

def unix_to_local(unix_ts) -> datetime:
    """
    UTC Unix timestamp -> local datetime
    """
    return datetime.fromtimestamp(unix_ts, LOCAL_TZ);

def unix_to_localstr(unix_ts, fmt="%Y-%m-%d %H:%M") -> str:
    """
    UTC Unix timestamp -> local string
    """
    return datetime.fromtimestamp(unix_ts, LOCAL_TZ).strftime(fmt)

# today

def get_str_today() -> str:
    """
    Returns today's local date as YYYY-MM-DD.
    Example: "2026-07-02"
    """
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")

def get_today() -> int:
    """
    Returns the Unix timestamp for today's local midnight (00:00).
    """
    now = datetime.now(LOCAL_TZ)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(today.timestamp());

def get_str_tomorrow() -> str:
    """
    Returns tomorrow's local date as YYYY-MM-DD.
    Example: "2026-07-03"
    """
    return (datetime.now(LOCAL_TZ) + timedelta(days=1)).strftime("%Y-%m-%d")

def get_current_time():
    return int(time.time())

def get_current_time_str(fmt="%Y-%m-%d %H:%M"):
    return datetime.now().strftime(fmt);

def is_time_in_range(start: tuple, current: tuple, end: tuple):
    # tuples with two elements: (hours, minutes)

    if start <= end:
        inside = start <= current <= end;
    else:
        # диапазон через полночь
        inside = current >= start or current <= end;
    
    return inside;

def get_local_hour_minute():
    now = datetime.now(LOCAL_TZ)
    time = (now.hour, now.minute)
    return time;

def sec_to_hour_min(seconds):
    hours   = seconds // 3600;
    minutes = (seconds - (hours * 3600)) // 60;
    
    return hours, minutes;

