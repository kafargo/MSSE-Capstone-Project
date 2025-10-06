"""Simple Garmin client wrapper used by MCP tools.

This module provides a minimal API to initialize Garmin, handle token storage,
prompt for credentials/MFA, and fetch today's stats using the example logic.
Modeled after the robust authentication flow in example.py.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from garth.exc import GarthException, GarthHTTPError

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("garmin_config.json")


def load_config() -> Dict[str, Any]:
    """Load configuration from garmin_config.json."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            logger.exception("Failed to read config file")
    return {}


def save_config(cfg: Dict[str, Any]) -> None:
    """Save configuration to garmin_config.json."""
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
        logger.info("Saved Garmin credentials to %s (INSECURE - for demo only)", CONFIG_PATH)
    except Exception:
        logger.exception("Failed to save config file")


def init_garmin(mfa_code: Optional[str] = None) -> Optional[Garmin]:
    """Initialize Garmin API with authentication and token management.
    
    Modified for MCP compatibility - no interactive prompts.
    
    Args:
        mfa_code: Optional MFA code if needed for authentication
    
    Returns:
        Garmin instance or raises appropriate exceptions
    
    Behavior:
    - First try to use saved tokens from token_dir
    - If no valid tokens, load email/password from garmin_config.json
    - If credentials missing, raise ValueError("missing_credentials")
    - If MFA required but no code provided, raise ValueError("mfa_required")
    - Save tokens after successful authentication
    """
    cfg = load_config()
    email = cfg.get("email")
    password = cfg.get("password")
    token_dir = cfg.get("token_dir", "~/.garminconnect")
    
    if not email or not password:
        raise ValueError("missing_credentials")
    
    # Configure token storage
    tokenstore_path = Path(token_dir).expanduser()
    
    logger.info("Token storage: %s", tokenstore_path)
    
    # First try to login with stored tokens
    try:
        logger.info("Attempting to use saved authentication tokens...")
        garmin = Garmin()
        garmin.login(str(tokenstore_path))
        logger.info("Successfully logged in using saved tokens!")
        return garmin
    
    except FileNotFoundError:
        logger.info("No token files found. Will login with credentials.")
    except Exception as e:
        # Be more careful about when to fall back to credential login
        logger.warning("Token login failed with %s: %s", type(e).__name__, str(e))
        logger.info("Will attempt credential login as fallback.")
    
    # Login with credentials and handle MFA
    try:
        logger.info("Logging in with credentials...")
        garmin = Garmin(email=email, password=password, is_cn=False, return_on_mfa=True)
        result1, result2 = garmin.login()
        
        if result1 == "needs_mfa":
            logger.info("Multi-factor authentication required")
            
            if not mfa_code:
                raise ValueError("mfa_required")
            
            logger.info("Submitting provided MFA code...")
            
            try:
                garmin.resume_login(result2, mfa_code)
                logger.info("MFA authentication successful!")
                
            except GarthHTTPError as garth_error:
                # Handle specific HTTP errors from MFA
                error_str = str(garth_error)
                if "429" in error_str and "Too Many Requests" in error_str:
                    raise RuntimeError("MFA rate limit exceeded. Please wait 30 minutes.")
                elif "401" in error_str or "403" in error_str:
                    raise RuntimeError("Invalid MFA code. Please verify and try again.")
                else:
                    raise RuntimeError(f"MFA authentication failed: {garth_error}")
                    
            except GarthException as garth_error:
                raise RuntimeError(f"MFA authentication failed: {garth_error}")
        
        # Save tokens for future use
        garmin.garth.dump(str(tokenstore_path))
        logger.info("Authentication tokens saved to: %s", tokenstore_path)
        logger.info("Login successful!")
        return garmin
        
    except GarminConnectAuthenticationError as e:
        raise RuntimeError(f"Authentication failed. Please check credentials in garmin_config.json: {e}")
        
    except (
        FileNotFoundError,
        GarthHTTPError,
        GarminConnectConnectionError,
        requests.exceptions.HTTPError,
    ) as err:
        raise RuntimeError(f"Connection error: {err}")
        
    except KeyboardInterrupt:
        raise RuntimeError("Authentication cancelled by user")



def get_today_stats(garmin: Garmin) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Fetches today's stats and returns (success, data, error_message).
    
    Uses the same pattern as display_daily_stats() from example.py.
    Data shape: {"steps": int, "distance_km": float, "calories": int, "floors": int}
    """
    try:
        today = date.today().isoformat()
        
        # Get user summary (steps, calories, etc.) - matches example.py pattern
        summary = garmin.get_user_summary(today)
        
        if not summary:
            return False, None, "No activity summary available for today"
            
        steps = summary.get("totalSteps", 0)
        distance_m = summary.get("totalDistanceMeters", 0)
        calories = summary.get("totalKilocalories", 0)
        floors = summary.get("floorsClimbed", 0)

        return (
            True,
            {
                "steps": int(steps or 0),
                "distance_km": float(distance_m or 0) / 1000.0,
                "calories": int(calories or 0),
                "floors": int(floors or 0),
                "date": today
            },
            None,
        )

    except Exception as e:
        logger.exception("Failed to fetch today stats")
        return False, None, str(e)
    
def get_last_activity(garmin: Garmin) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Get the most recent activity from Garmin.
    
    Args:
        garmin: Authenticated Garmin client
        
    Returns:
        Tuple of (success: bool, data: dict, error: str)
        
    Example return data:
        {
            "activity_id": 12345678901,
            "activity_name": "Morning Run",
            "activity_type": "running",
            "start_time": "2025-10-06T07:30:00",
            "duration_seconds": 2147,
            "distance_meters": 5000.0,
            "calories": 320,
            "avg_heart_rate": 145
        }
    """
    try:
        # Get activities (limit to 1 for most recent)
        activities = garmin.get_activities(0, 1)  # start=0, limit=1
        
        if not activities or len(activities) == 0:
            return False, None, "No activities found"
            
        activity = activities[0]
        
        # Format the activity data
        formatted_activity = {
            "activity_id": activity.get("activityId"),
            "activity_name": activity.get("activityName"),
            "activity_type": activity.get("activityType", {}).get("typeKey"),
            "start_time": activity.get("startTimeLocal"),
            "duration_seconds": activity.get("duration"),
            "distance_meters": activity.get("distance"),
            "calories": activity.get("calories"),
            "avg_heart_rate": activity.get("averageHR")
        }
        
        logger.info("Successfully fetched last activity: %s", formatted_activity.get("activity_name"))
        return True, formatted_activity, None
        
    except Exception as e:
        error_msg = f"Failed to fetch last activity: {e}"
        logger.exception(error_msg)
        return False, None, error_msg


def get_body_battery(garmin: Garmin, start_date: str, end_date: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Get body battery data for specified date range.
    
    Args:
        garmin: Authenticated Garmin client
        start_date: Start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format (defaults to start_date)
        
    Returns:
        Tuple of (success: bool, data: dict, error: str)
    """
    try:
        if end_date is None:
            end_date = start_date
            
        body_battery_data = garmin.get_body_battery(start_date, end_date)
        
        logger.info("Successfully fetched body battery data for %s to %s", start_date, end_date)
        return True, {"body_battery": body_battery_data, "start_date": start_date, "end_date": end_date}, None
        
    except Exception as e:
        error_msg = f"Failed to fetch body battery data: {e}"
        logger.exception(error_msg)
        return False, None, error_msg


def get_all_day_stress(garmin: Garmin, date_str: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Get all day stress data for specified date.
    
    Args:
        garmin: Authenticated Garmin client
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Tuple of (success: bool, data: dict, error: str)
    """
    try:
        stress_data = garmin.get_all_day_stress(date_str)
        
        logger.info("Successfully fetched stress data for %s", date_str)
        return True, {"stress_data": stress_data, "date": date_str}, None
        
    except Exception as e:
        error_msg = f"Failed to fetch stress data: {e}"
        logger.exception(error_msg)
        return False, None, error_msg


def get_sleep_data(garmin: Garmin, date_str: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Get sleep data for specified date.
    
    Args:
        garmin: Authenticated Garmin client
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Tuple of (success: bool, data: dict, error: str)
    """
    try:
        sleep_data = garmin.get_sleep_data(date_str)
        
        logger.info("Successfully fetched sleep data for %s", date_str)
        return True, {"sleep_data": sleep_data, "date": date_str}, None
        
    except Exception as e:
        error_msg = f"Failed to fetch sleep data: {e}"
        logger.exception(error_msg)
        return False, None, error_msg


def get_hrv_data(garmin: Garmin, date_str: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Get heart rate variability data for specified date.
    
    Args:
        garmin: Authenticated Garmin client
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Tuple of (success: bool, data: dict, error: str)
    """
    try:
        hrv_data = garmin.get_hrv_data(date_str)
        
        logger.info("Successfully fetched HRV data for %s", date_str)
        return True, {"hrv_data": hrv_data, "date": date_str}, None
        
    except Exception as e:
        error_msg = f"Failed to fetch HRV data: {e}"
        logger.exception(error_msg)
        return False, None, error_msg


def get_training_readiness(garmin: Garmin, date_str: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Get training readiness data for specified date.
    
    Args:
        garmin: Authenticated Garmin client
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Tuple of (success: bool, data: dict, error: str)
    """
    try:
        readiness_data = garmin.get_training_readiness(date_str)
        
        logger.info("Successfully fetched training readiness data for %s", date_str)
        return True, {"training_readiness": readiness_data, "date": date_str}, None
        
    except Exception as e:
        error_msg = f"Failed to fetch training readiness data: {e}"
        logger.exception(error_msg)
        return False, None, error_msg


def get_training_status(garmin: Garmin, date_str: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Get training status data for specified date.
    
    Args:
        garmin: Authenticated Garmin client
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Tuple of (success: bool, data: dict, error: str)
    """
    try:
        status_data = garmin.get_training_status(date_str)
        
        logger.info("Successfully fetched training status data for %s", date_str)
        return True, {"training_status": status_data, "date": date_str}, None
        
    except Exception as e:
        error_msg = f"Failed to fetch training status data: {e}"
        logger.exception(error_msg)
        return False, None, error_msg


def get_activities_by_date(garmin: Garmin, start_date: str, end_date: Optional[str] = None, 
                          activity_type: Optional[str] = None, sort_order: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Get activities for specified date range.
    
    Args:
        garmin: Authenticated Garmin client
        start_date: Start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format (defaults to start_date)
        activity_type: Optional activity type filter (cycling, running, swimming, etc.)
        sort_order: Optional sort order ("asc" for oldest to newest)
        
    Returns:
        Tuple of (success: bool, data: dict, error: str)
    """
    try:
        activities = garmin.get_activities_by_date(start_date, end_date, activity_type, sort_order)
        
        logger.info("Successfully fetched %d activities for %s to %s", 
                   len(activities), start_date, end_date or start_date)
        return True, {
            "activities": activities, 
            "start_date": start_date, 
            "end_date": end_date or start_date,
            "activity_type": activity_type,
            "count": len(activities)
        }, None
        
    except Exception as e:
        error_msg = f"Failed to fetch activities: {e}"
        logger.exception(error_msg)
        return False, None, error_msg
