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
