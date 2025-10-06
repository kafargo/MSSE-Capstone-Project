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
    load_config, 
    save_config
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting MCP server (stdio)")
        mcp.run("stdio")
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received — shutting down cleanly")
        sys.exit(0)