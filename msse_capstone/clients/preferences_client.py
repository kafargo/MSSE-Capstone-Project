"""User preferences client for workout and equipment data.

This module handles loading and saving user workout preferences and available equipment
to local JSON files, following the same pattern as garmin_client.py.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

PREFERENCES_PATH = Path("workout_preferences.json")
EQUIPMENT_PATH = Path("available_equipment.json")


def load_workout_preferences() -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Load workout preferences from local file.
    
    Returns:
        Tuple of (success, data, error_message)
        - If file exists and loads successfully: (True, preferences_dict, None)
        - If file doesn't exist or is empty: (False, None, "not_found")
        - If file exists but is invalid JSON: (False, None, error_message)
    """
    try:
        if not PREFERENCES_PATH.exists():
            logger.info("Workout preferences file not found at %s", PREFERENCES_PATH)
            return False, None, "not_found"
        
        with open(PREFERENCES_PATH, 'r') as f:
            data = json.load(f)
        
        if not data:
            logger.info("Workout preferences file is empty")
            return False, None, "not_found"
        
        logger.info("Successfully loaded workout preferences")
        return True, data, None
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in workout preferences file: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Error loading workout preferences: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def save_workout_preferences(preferences: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Save workout preferences to local file.
    
    Args:
        preferences: Dictionary containing workout preferences data
        
    Returns:
        Tuple of (success, error_message)
        - If saved successfully: (True, None)
        - If save failed: (False, error_message)
    """
    try:
        with open(PREFERENCES_PATH, 'w') as f:
            json.dump(preferences, f, indent=2)
        
        logger.info("Successfully saved workout preferences to %s", PREFERENCES_PATH)
        return True, None
        
    except Exception as e:
        error_msg = f"Error saving workout preferences: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def load_available_equipment() -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Load available equipment from local file.
    
    Returns:
        Tuple of (success, data, error_message)
        - If file exists and loads successfully: (True, equipment_dict, None)
        - If file doesn't exist or is empty: (False, None, "not_found")
        - If file exists but is invalid JSON: (False, None, error_message)
    """
    try:
        if not EQUIPMENT_PATH.exists():
            logger.info("Available equipment file not found at %s", EQUIPMENT_PATH)
            return False, None, "not_found"
        
        with open(EQUIPMENT_PATH, 'r') as f:
            data = json.load(f)
        
        if not data:
            logger.info("Available equipment file is empty")
            return False, None, "not_found"
        
        logger.info("Successfully loaded available equipment")
        return True, data, None
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in available equipment file: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Error loading available equipment: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def save_available_equipment(equipment: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Save available equipment to local file.
    
    Args:
        equipment: Dictionary containing available equipment data
        
    Returns:
        Tuple of (success, error_message)
        - If saved successfully: (True, None)
        - If save failed: (False, error_message)
    """
    try:
        with open(EQUIPMENT_PATH, 'w') as f:
            json.dump(equipment, f, indent=2)
        
        logger.info("Successfully saved available equipment to %s", EQUIPMENT_PATH)
        return True, None
        
    except Exception as e:
        error_msg = f"Error saving available equipment: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
