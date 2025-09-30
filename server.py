"""
FastMCP base example.

"""
import logging
import sys
from mcp.server.fastmcp import FastMCP
from clients.garmin_client import init_garmin, get_today_stats, load_config, save_config

# Create an MCP server
mcp = FastMCP("Demo")

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
    - If MFA required but no code provided, raises ValueError with instructions
    - Saves tokens after successful authentication for future use
    
    Setup:
    1. Create garmin_config.json with email/password (copy from template)
    2. Call this tool - if MFA required, call again with mfa_code parameter
    """
    logger = logging.getLogger(__name__)
    logger.info("daily_stats called with mfa_code=%s", "***" if mfa_code else None)
    
    try:
        # Try to initialize Garmin (will check for saved tokens first)
        garmin = init_garmin(mfa_code)
    except ValueError as e:
        error_msg = str(e)
        logger.info("ValueError during init_garmin: %s", error_msg)
        if error_msg == "missing_credentials":
            return {
                "error": "missing_credentials",
                "message": "Please create garmin_config.json with your email and password. Copy garmin_config.json.template and fill in your credentials.",
                "setup_instructions": [
                    "1. Copy garmin_config.json.template to garmin_config.json",
                    "2. Edit garmin_config.json with your Garmin email and password",
                    "3. Call daily_stats() again"
                ]
            }
        elif error_msg == "mfa_required":
            return {
                "error": "mfa_required", 
                "message": "Multi-factor authentication required. An MFA code should have been sent to your device.",
                "instructions": "Call daily_stats(mfa_code='123456') with the 6-digit code from your authenticator app or SMS"
            }
        else:
            raise
    except RuntimeError as e:
        logger.error("RuntimeError during init_garmin: %s", str(e))
        return {
            "error": "authentication_failed",
            "message": str(e)
        }

    # Fetch today's stats
    success, data, err = get_today_stats(garmin)
    if not success:
        logger.error("Failed to fetch stats: %s", err)
        return {
            "error": "fetch_failed",
            "message": f"Failed to fetch daily stats: {err}"
        }

    logger.info("Successfully returned daily stats")
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