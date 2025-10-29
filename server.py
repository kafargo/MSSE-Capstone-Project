"""
FastMCP base example.

"""
import logging
import sys
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

# Create an MCP server
mcp = FastMCP("Demo")


def _handle_garmin_auth(mfa_code: str = None) -> tuple[object, dict]:
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

# Add a steps to miles tool
@mcp.tool()
def steps_to_miles(steps: int) -> float:
    """
    Convert steps to miles

    Args:
        steps (int): Number of steps
    Returns:
        float: Number of miles
    """
    return steps / 2000.0


# Minimal MCP tool that returns today's Garmin stats
@mcp.tool()
def daily_stats(mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("daily_stats called")
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch today's stats
    success, data, err = get_today_stats(garmin)
    if not success:
        logger.error("Failed to fetch daily stats: %s", err)
        # Check if this is an authentication error
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed",
            "message": f"Failed to fetch daily stats: {err}"
        }

    logger.info("Successfully returned daily stats")
    return data


@mcp.tool()
def last_activity(mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("last_activity called")
    
    # Handle authentication (reusing the helper)
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch last activity
    success, data, err = get_last_activity(garmin)
    
    if not success:
        logger.error("Failed to fetch last activity: %s", err)
        # Check if this is an authentication error
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed", 
            "message": f"Failed to fetch last activity: {err}"
        }

    logger.info("Successfully returned last activity: %s", data.get("activity_name"))
    return data


@mcp.tool()
def body_battery(start_date: str, end_date: str = None, mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("body_battery called for %s to %s", start_date, end_date or start_date)
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch body battery data
    success, data, err = get_body_battery(garmin, start_date, end_date)
    
    if not success:
        logger.error("Failed to fetch body battery data: %s", err)
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed", 
            "message": f"Failed to fetch body battery data: {err}"
        }

    logger.info("Successfully returned body battery data")
    return data


@mcp.tool()
def all_day_stress(date: str, mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("all_day_stress called for %s", date)
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch stress data
    success, data, err = get_all_day_stress(garmin, date)
    
    if not success:
        logger.error("Failed to fetch stress data: %s", err)
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed", 
            "message": f"Failed to fetch stress data: {err}"
        }

    logger.info("Successfully returned stress data")
    return data


@mcp.tool()
def sleep_data(date: str, mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("sleep_data called for %s", date)
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch sleep data
    success, data, err = get_sleep_data(garmin, date)
    
    if not success:
        logger.error("Failed to fetch sleep data: %s", err)
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed", 
            "message": f"Failed to fetch sleep data: {err}"
        }

    logger.info("Successfully returned sleep data")
    return data


@mcp.tool()
def hrv_data(date: str, mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("hrv_data called for %s", date)
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch HRV data
    success, data, err = get_hrv_data(garmin, date)
    
    if not success:
        logger.error("Failed to fetch HRV data: %s", err)
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed", 
            "message": f"Failed to fetch HRV data: {err}"
        }

    logger.info("Successfully returned HRV data")
    return data


@mcp.tool()
def training_readiness(date: str, mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("training_readiness called for %s", date)
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch training readiness data
    success, data, err = get_training_readiness(garmin, date)
    
    if not success:
        logger.error("Failed to fetch training readiness data: %s", err)
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed", 
            "message": f"Failed to fetch training readiness data: {err}"
        }

    logger.info("Successfully returned training readiness data")
    return data


@mcp.tool()
def training_status(date: str, mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("training_status called for %s", date)
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch training status data
    success, data, err = get_training_status(garmin, date)
    
    if not success:
        logger.error("Failed to fetch training status data: %s", err)
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed", 
            "message": f"Failed to fetch training status data: {err}"
        }

    logger.info("Successfully returned training status data")
    return data


@mcp.tool()
def activities(start_date: str, end_date: str = None, activity_type: str = None, 
               sort_order: str = None, mfa_code: str = None) -> dict:
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
    logger = logging.getLogger(__name__)
    logger.info("activities called for %s to %s, type=%s", start_date, end_date or start_date, activity_type)
    
    # Handle authentication
    garmin, auth_error = _handle_garmin_auth(mfa_code)
    if auth_error:
        return auth_error

    # Fetch activities data
    success, data, err = get_activities_by_date(garmin, start_date, end_date, activity_type, sort_order)
    
    if not success:
        logger.error("Failed to fetch activities data: %s", err)
        if err and any(keyword in err.lower() for keyword in ['credential', 'auth', 'login', 'unauthorized', 'forbidden']):
            return {
                "error": "auth_failed",
                "message": f"Authentication failed: {err}"
            }
        return {
            "error": "fetch_failed", 
            "message": f"Failed to fetch activities data: {err}"
        }

    logger.info("Successfully returned %d activities", data.get("count", 0))
    return data


@mcp.tool()
def workout_preferences(preferences_data: dict = None) -> dict:
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
                "error": "save_failed",
                "message": f"Failed to save workout preferences: {err}"
            }
        logger.info("Successfully saved workout preferences")
        return {
            "status": "saved",
            "message": "Workout preferences saved successfully",
            "data": preferences_data
        }
    
    # Try to load existing preferences
    success, data, err = load_workout_preferences()
    
    if not success:
        if err == "not_found":
            logger.info("No workout preferences found, prompting user")
            return {
                "status": "not_found",
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
                "error": "load_failed",
                "message": f"Failed to load workout preferences: {err}"
            }
    
    logger.info("Successfully loaded workout preferences")
    return {
        "status": "found",
        "data": data
    }


@mcp.tool()
def available_equipment(equipment_data: dict = None) -> dict:
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
                "error": "save_failed",
                "message": f"Failed to save available equipment: {err}"
            }
        logger.info("Successfully saved available equipment")
        return {
            "status": "saved",
            "message": "Available equipment saved successfully",
            "data": equipment_data
        }
    
    # Try to load existing equipment data
    success, data, err = load_available_equipment()
    
    if not success:
        if err == "not_found":
            logger.info("No equipment data found, prompting user")
            return {
                "status": "not_found",
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
                "error": "load_failed",
                "message": f"Failed to load available equipment: {err}"
            }
    
    logger.info("Successfully loaded available equipment")
    return {
        "status": "found",
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