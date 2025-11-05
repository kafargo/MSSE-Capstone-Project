"""Client package exports."""

from .garmin_client import (
    init_garmin,
    get_today_stats,
    get_last_activity,
    get_body_battery,
    get_all_day_stress,
    get_sleep_data,
    get_hrv_data,
    get_training_readiness,
    get_training_status,
    get_activities_by_date,
    load_config,
    save_config,
)

from .preferences_client import (
    load_workout_preferences,
    save_workout_preferences,
    load_available_equipment,
    save_available_equipment,
)

__all__ = [
    "init_garmin",
    "get_today_stats", 
    "get_last_activity",
    "get_body_battery",
    "get_all_day_stress",
    "get_sleep_data",
    "get_hrv_data",
    "get_training_readiness",
    "get_training_status",
    "get_activities_by_date",
    "load_config",
    "save_config",
    "load_workout_preferences",
    "save_workout_preferences",
    "load_available_equipment",
    "save_available_equipment",
]