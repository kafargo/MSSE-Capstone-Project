"""Test utilities and helper functions."""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock

from garminconnect import Garmin


def create_test_config(email: str = "test@example.com", password: str = "test_pass") -> Dict[str, Any]:
    """Create a test configuration dictionary."""
    return {
        "email": email,
        "password": password,
        "token_dir": "~/.garminconnect"
    }


def create_test_config_file(config_data: Dict[str, Any]) -> Path:
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f, indent=2)
        return Path(f.name)


def create_mock_garmin_with_stats(steps: int = 10000, distance_m: int = 8000, 
                                  calories: int = 400, floors: int = 5) -> Mock:
    """Create a mock Garmin instance with predefined stats."""
    mock_garmin = Mock(spec=Garmin)
    mock_garmin.get_user_summary.return_value = {
        "totalSteps": steps,
        "totalDistanceMeters": distance_m,
        "totalKilocalories": calories,
        "floorsClimbed": floors
    }
    return mock_garmin


def create_mock_token_files(token_dir: Path) -> None:
    """Create mock OAuth token files in the specified directory."""
    token_dir.mkdir(exist_ok=True)
    
    oauth1_data = {
        "oauth_token": "test_oauth_token",
        "oauth_token_secret": "test_oauth_secret",
        "domain": "garmin.com"
    }
    
    oauth2_data = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "bearer",
        "expires_in": 3600
    }
    
    (token_dir / "oauth1_token.json").write_text(json.dumps(oauth1_data, indent=2))
    (token_dir / "oauth2_token.json").write_text(json.dumps(oauth2_data, indent=2))


def assert_daily_stats_structure(stats: Dict[str, Any]) -> None:
    """Assert that a daily stats dictionary has the expected structure."""
    required_keys = {"steps", "distance_km", "calories", "floors", "date"}
    assert set(stats.keys()) == required_keys
    
    assert isinstance(stats["steps"], int)
    assert isinstance(stats["distance_km"], float)
    assert isinstance(stats["calories"], int)
    assert isinstance(stats["floors"], int)
    assert isinstance(stats["date"], str)
    
    # Validate ranges
    assert stats["steps"] >= 0
    assert stats["distance_km"] >= 0.0
    assert stats["calories"] >= 0
    assert stats["floors"] >= 0


def assert_mcp_error_response(response: Dict[str, Any], expected_error: str) -> None:
    """Assert that a response is a valid MCP error response."""
    assert "error" in response
    assert response["error"] == expected_error
    assert "message" in response
    assert isinstance(response["message"], str)
    assert len(response["message"]) > 0