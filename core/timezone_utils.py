from datetime import datetime
from zoneinfo import ZoneInfo

SA_TIMEZONE = ZoneInfo("Africa/Johannesburg")


def now_sa() -> datetime:
    """Current time in South African Standard Time, regardless of server location"""
    return datetime.now(SA_TIMEZONE)