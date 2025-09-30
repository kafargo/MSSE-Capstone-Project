"""Shared pytest fixtures for MCP server tests."""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

import pytest
from garminconnect import Garmin

from msse_capstone.clients.garmin_client import CONFIG_PATH


@pytest.fixture
def mock_config_data() -> Dict[str, Any]:
    """Sample configuration data for testing."""
    return {
        "email": "test@example.com",
        "password": "test_password",
        "token_dir": "~/.garminconnect"
    }


@pytest.fixture
def mock_config_file(tmp_path: Path, mock_config_data: Dict[str, Any]):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "garmin_config.json"
    config_file.write_text(json.dumps(mock_config_data, indent=2))
    
    # Patch the CONFIG_PATH to use our temporary file
    with patch('msse_capstone.clients.garmin_client.CONFIG_PATH', config_file):
        yield config_file


@pytest.fixture
def mock_garmin_instance():
    """Mock Garmin instance for testing."""
    mock_garmin = Mock(spec=Garmin)
    mock_garmin.login.return_value = None
    mock_garmin.get_full_name.return_value = "Test User"
    mock_garmin.get_user_summary.return_value = {
        "totalSteps": 10000,
        "totalDistanceMeters": 8000,
        "totalKilocalories": 400,
        "floorsClimbed": 5
    }
    return mock_garmin


@pytest.fixture
def mock_token_dir(tmp_path: Path):
    """Create a temporary token directory."""
    token_dir = tmp_path / ".garminconnect"
    token_dir.mkdir()
    
    # Create mock token files
    oauth1_file = token_dir / "oauth1_token.json"
    oauth1_file.write_text(json.dumps({
        "oauth_token": "mock_token",
        "oauth_token_secret": "mock_secret"
    }))
    
    oauth2_file = token_dir / "oauth2_token.json"
    oauth2_file.write_text(json.dumps({
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token"
    }))
    
    return token_dir


@pytest.fixture
def disable_logging():
    """Disable logging during tests to reduce noise."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def sample_daily_stats() -> Dict[str, Any]:
    """Sample daily stats data for testing."""
    return {
        "steps": 10000,
        "distance_km": 8.0,
        "calories": 400,
        "floors": 5,
        "date": "2025-09-29"
    }


@pytest.fixture
def mfa_required_response():
    """Mock MFA required response."""
    return ("needs_mfa", "mock_mfa_token")