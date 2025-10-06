"""Client package for external service integrations."""

from .garmin_client import init_garmin, get_today_stats, get_last_activity, load_config, save_config

__all__ = [
    "init_garmin",
    "get_today_stats", 
    "get_last_activity",
    "load_config",
    "save_config",
]