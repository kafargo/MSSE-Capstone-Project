"""MCP Server for Garmin Data Integration.

This module provides MCP tools for accessing Garmin Connect data,
user preferences, and workout equipment information.
"""
import logging
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP
from msse_capstone.clients.garmin_client import (
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
    save_config
)
from msse_capstone.clients.preferences_client import (
    load_workout_preferences,
    save_workout_preferences,
    load_available_equipment,
    save_available_equipment,
)

# Constants
AUTH_ERROR_KEYWORDS = ['credential', 'auth', 'login', 'unauthorized', 'forbidden']
STEPS_TO_MILES_RATIO = 2000.0

# Error messages
ERROR_AUTH_FAILED = "auth_failed"
ERROR_FETCH_FAILED = "fetch_failed"
ERROR_SAVE_FAILED = "save_failed"
ERROR_LOAD_FAILED = "load_failed"

# Status messages
STATUS_NOT_FOUND = "not_found"
STATUS_SAVED = "saved"
STATUS_FOUND = "found"

# Create an MCP server
mcp = FastMCP("MSSE-Capstone-Garmin")


def _is_auth_error(error_message: Optional[str]) -> bool:
    """Check if an error message indicates an authentication failure.
    
    Args:
        error_message: Error message to check
        
    Returns:
        True if the error is authentication-related, False otherwise
    """
    if not error_message:
        return False
    return any(keyword in error_message.lower() for keyword in AUTH_ERROR_KEYWORDS)


def _handle_garmin_auth(mfa_code: Optional[str] = None) -> tuple[object, Optional[dict]]:
    """Handle Garmin authentication with MFA support.
    
    Args:
        mfa_code: Optional MFA code for authentication
        
    Returns:
        Tuple of (garmin_client, error_response)
        If successful: (garmin_client, None)
        If error: (None, error_dict)
    """
    logger = logging.getLogger(__name__)
    logger.info("Attempting Garmin authentication with mfa_code=%s", "***" if mfa_code else None)
    
    try:
        garmin = init_garmin(mfa_code)
        return garmin, None
        
    except ValueError as e:
        error_msg = str(e)
        logger.info("ValueError during authentication: %s", error_msg)
        
        if error_msg == "missing_credentials":
            return None, {
                "error": "missing_credentials",
                "message": "Please create garmin_config.json with your email and password.",
                "setup_instructions": [
                    "1. Create garmin_config.json with your Garmin email and password",
                    "2. Call the tool again"
                ]
            }
        elif error_msg == "mfa_required":
            return None, {
                "error": "mfa_required", 
                "message": "Multi-factor authentication required. An MFA code should have been sent to your device.",
                "instructions": "Call the tool again with mfa_code='123456' parameter using the 6-digit code from your authenticator app or SMS"
            }
        else:
            raise
            
    except RuntimeError as e:
        logger.error("RuntimeError during authentication: %s", str(e))
        return None, {
            "error": "authentication_failed",
            "message": str(e)
        }


def _handle_garmin_fetch_error(operation_name: str, error_message: Optional[str]) -> dict:
    """Handle errors from Garmin data fetch operations.
    
    Args:
        operation_name: Name of the operation that failed (for logging)
        error_message: Error message from the fetch operation
        
    Returns:
        Dict with error details
    """
    logger = logging.getLogger(__name__)
    logger.error("Failed to fetch %s: %s", operation_name, error_message)
    
    if _is_auth_error(error_message):
        return {
            "error": ERROR_AUTH_FAILED,
            "message": f"Authentication failed: {error_message}"
        }
    return {
        "error": ERROR_FETCH_FAILED,
        "message": f"Failed to fetch {operation_name}: {error_message}"
    }


def _execute_garmin_tool(
    tool_name: str,
    fetch_func: callable,
    mfa_code: Optional[str] = None,
    **fetch_kwargs
) -> dict:
    """Execute a Garmin tool with standardized auth and error handling.
    
    Args:
        tool_name: Name of the tool for logging
        fetch_func: Function to call to fetch data (takes garmin client as first arg)
        mfa_code: Optional MFA code for authentication
        **fetch_kwargs: Additional keyword arguments to pass to fetch_func
        
    Returns:
        Dict with data or error information
    """
    logger = logging.getLogger(__name__)
    logger.info("%s called", tool_name)
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error
    
    # Fetch data
    success, data, err = fetch_func(garmin, **fetch_kwargs)
    
    if not success:
        return _handle_garmin_fetch_error(tool_name, err)
    
    logger.info("Successfully returned %s", tool_name)
    return data

@mcp.tool()
def steps_to_miles(steps: int) -> float:
    """Convert steps to miles.

    Args:
        steps: Number of steps
        
    Returns:
        Number of miles (steps divided by 2000)
    """
    return steps / STEPS_TO_MILES_RATIO


# Minimal MCP tool that returns today's Garmin stats
@mcp.tool()
def daily_stats(mfa_code: Optional[str] = None) -> dict:
    """Return today's Garmin stats with MFA support.

    Args:
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with daily stats: steps, distance_km, calories, floors, date
        
    Behavior:
    - Uses saved tokens from ~/.garminconnect if available
    - Falls back to credentials from garmin_config.json
    - If MFA required but no code provided, returns error with instructions
    - Saves tokens after successful authentication for future use
    
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("daily_stats", get_today_stats, mfa_code)


@mcp.tool()
def last_activity(mfa_code: Optional[str] = None) -> dict:
    """Return the most recent Garmin activity with MFA support.

    Args:
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with last activity data: activity_id, activity_name, activity_type,
        start_time, duration_seconds, distance_meters, calories, avg_heart_rate
        
    Behavior:
    - Uses saved tokens from ~/.garminconnect if available
    - Falls back to credentials from garmin_config.json
    - If MFA required but no code provided, returns error with instructions
    - Saves tokens after successful authentication for future use
    
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("last_activity", get_last_activity, mfa_code)


@mcp.tool()
def body_battery(start_date: str, end_date: Optional[str] = None, mfa_code: Optional[str] = None) -> dict:
    """Return body battery data for specified date range with MFA support.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format (defaults to start_date)
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with body battery data for the specified date range
        
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("body_battery", get_body_battery, mfa_code, 
                                start_date=start_date, end_date=end_date)


@mcp.tool()
def all_day_stress(date: str, mfa_code: Optional[str] = None) -> dict:
    """Return all day stress data for specified date with MFA support.

    Args:
        date: Date in YYYY-MM-DD format
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with stress data for the specified date
        
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("all_day_stress", get_all_day_stress, mfa_code, date=date)


@mcp.tool()
def sleep_data(date: str, mfa_code: Optional[str] = None) -> dict:
    """Return sleep data for specified date with MFA support.

    Args:
        date: Date in YYYY-MM-DD format
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with sleep data for the specified date
        
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("sleep_data", get_sleep_data, mfa_code, date=date)


@mcp.tool()
def hrv_data(date: str, mfa_code: Optional[str] = None) -> dict:
    """Return heart rate variability data for specified date with MFA support.

    Args:
        date: Date in YYYY-MM-DD format
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with HRV data for the specified date
        
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("hrv_data", get_hrv_data, mfa_code, date=date)


@mcp.tool()
def training_readiness(date: str, mfa_code: Optional[str] = None) -> dict:
    """Return training readiness data for specified date with MFA support.

    Args:
        date: Date in YYYY-MM-DD format
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with training readiness data for the specified date
        
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("training_readiness", get_training_readiness, mfa_code, date=date)


@mcp.tool()
def training_status(date: str, mfa_code: Optional[str] = None) -> dict:
    """Return training status data for specified date with MFA support.

    Args:
        date: Date in YYYY-MM-DD format
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with training status data for the specified date
        
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("training_status", get_training_status, mfa_code, date=date)


@mcp.tool()
def activities(start_date: str, end_date: Optional[str] = None, activity_type: Optional[str] = None, 
               sort_order: Optional[str] = None, mfa_code: Optional[str] = None) -> dict:
    """Return activities for specified date range with MFA support.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format (defaults to start_date)
        activity_type: Optional activity type filter (cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other)
        sort_order: Optional sort order ("asc" for oldest to newest, default is newest to oldest)
        mfa_code: Optional MFA code if required for authentication
        
    Returns:
        Dict with activities data for the specified date range
        
    Setup:
    1. Create garmin_config.json with email/password
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    return _execute_garmin_tool("activities", get_activities_by_date, mfa_code,
                                start_date=start_date, end_date=end_date, 
                                activity_type=activity_type, sort_order=sort_order)


@mcp.tool()
def workout_preferences(preferences_data: Optional[dict] = None) -> dict:
    """Get or set workout preferences.
    
    This tool manages user workout preferences stored in a local file. If preferences
    don't exist, it prompts the user to provide them. Once set, preferences are 
    persisted and returned on subsequent calls.
    
    Args:
        preferences_data: Optional dict containing workout preferences to save.
                         If None, attempts to load existing preferences.
                         
    Returns:
        Dict with preferences data or prompt for user to provide preferences
        
    Example preferences_data structure:
    {
        "goals": ["strength", "endurance", "weight_loss"],
        "workout_frequency": 4,
        "preferred_days": ["monday", "wednesday", "friday", "sunday"],
        "session_duration_minutes": 60,
        "intensity_level": "moderate",
        "restrictions": ["no_jumping", "low_impact"]
    }
    """
    logger = logging.getLogger(__name__)
    logger.info("workout_preferences called with data=%s", "provided" if preferences_data else "None")
    
    # If preferences_data provided, save it
    if preferences_data:
        success, err = save_workout_preferences(preferences_data)
        if not success:
            logger.error("Failed to save workout preferences: %s", err)
            return {
                "error": ERROR_SAVE_FAILED,
                "message": f"Failed to save workout preferences: {err}"
            }
        logger.info("Successfully saved workout preferences")
        return {
            "status": STATUS_SAVED,
            "message": "Workout preferences saved successfully",
            "data": preferences_data
        }
    
    # Try to load existing preferences
    success, data, err = load_workout_preferences()
    
    if not success:
        if err == STATUS_NOT_FOUND:
            logger.info("No workout preferences found, prompting user")
            return {
                "status": STATUS_NOT_FOUND,
                "message": "No workout preferences found. Please provide your preferences.",
                "prompt": "Please provide your workout preferences including goals, frequency, preferred days, session duration, intensity level, and any restrictions.",
                "example": {
                    "goals": ["strength", "endurance", "weight_loss"],
                    "workout_frequency": 4,
                    "preferred_days": ["monday", "wednesday", "friday", "sunday"],
                    "session_duration_minutes": 60,
                    "intensity_level": "moderate",
                    "restrictions": ["no_jumping", "low_impact"]
                }
            }
        else:
            logger.error("Failed to load workout preferences: %s", err)
            return {
                "error": ERROR_LOAD_FAILED,
                "message": f"Failed to load workout preferences: {err}"
            }
    
    logger.info("Successfully loaded workout preferences")
    return {
        "status": STATUS_FOUND,
        "data": data
    }


@mcp.tool()
def available_equipment(equipment_data: Optional[dict] = None) -> dict:
    """Get or set available workout equipment.
    
    This tool manages user's available workout equipment stored in a local file. 
    If equipment data doesn't exist, it prompts the user to provide it. Once set, 
    equipment data is persisted and returned on subsequent calls.
    
    Args:
        equipment_data: Optional dict containing available equipment to save.
                       If None, attempts to load existing equipment data.
                       
    Returns:
        Dict with equipment data or prompt for user to provide equipment info
        
    Example equipment_data structure:
    {
        "cardio": ["treadmill", "stationary_bike", "rowing_machine"],
        "strength": ["dumbbells", "barbell", "bench", "pull_up_bar"],
        "weights_available": {
            "dumbbells": "5-50 lbs",
            "barbell": "45 lbs with plates up to 315 lbs"
        },
        "accessories": ["yoga_mat", "resistance_bands", "foam_roller"],
        "location": "home_gym"
    }
    """
    logger = logging.getLogger(__name__)
    logger.info("available_equipment called with data=%s", "provided" if equipment_data else "None")
    
    # If equipment_data provided, save it
    if equipment_data:
        success, err = save_available_equipment(equipment_data)
        if not success:
            logger.error("Failed to save available equipment: %s", err)
            return {
                "error": ERROR_SAVE_FAILED,
                "message": f"Failed to save available equipment: {err}"
            }
        logger.info("Successfully saved available equipment")
        return {
            "status": STATUS_SAVED,
            "message": "Available equipment saved successfully",
            "data": equipment_data
        }
    
    # Try to load existing equipment data
    success, data, err = load_available_equipment()
    
    if not success:
        if err == STATUS_NOT_FOUND:
            logger.info("No equipment data found, prompting user")
            return {
                "status": STATUS_NOT_FOUND,
                "message": "No equipment data found. Please provide your available equipment.",
                "prompt": "Please provide details about your available workout equipment including cardio machines, strength equipment, weights, accessories, and location.",
                "example": {
                    "cardio": ["treadmill", "stationary_bike", "rowing_machine"],
                    "strength": ["dumbbells", "barbell", "bench", "pull_up_bar"],
                    "weights_available": {
                        "dumbbells": "5-50 lbs",
                        "barbell": "45 lbs with plates up to 315 lbs"
                    },
                    "accessories": ["yoga_mat", "resistance_bands", "foam_roller"],
                    "location": "home_gym"
                }
            }
        else:
            logger.error("Failed to load available equipment: %s", err)
            return {
                "error": ERROR_LOAD_FAILED,
                "message": f"Failed to load available equipment: {err}"
            }
    
    logger.info("Successfully loaded available equipment")
    return {
        "status": STATUS_FOUND,
        "data": data
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting MCP server (stdio)")
        mcp.run("stdio")
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received — shutting down cleanly")
        sys.exit(0)