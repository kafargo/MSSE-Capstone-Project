"""Unit tests for Garmin client functionality."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from msse_capstone.clients.garmin_client import (
    load_config,
    save_config,
    init_garmin,
    get_today_stats
)
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError
)


class TestConfigManagement:
    """Tests for config file operations."""
    
    @pytest.mark.unit
    def test_load_config_existing_file(self, mock_config_file, mock_config_data):
        """Test loading configuration from existing file."""
        config = load_config()
        assert config == mock_config_data
    
    @pytest.mark.unit
    def test_load_config_missing_file(self, tmp_path):
        """Test loading configuration when file doesn't exist."""
        with patch('msse_capstone.clients.garmin_client.CONFIG_PATH', tmp_path / "missing.json"):
            config = load_config()
            assert config == {}
    
    @pytest.mark.unit
    def test_save_config(self, tmp_path, mock_config_data):
        """Test saving configuration to file."""
        config_file = tmp_path / "test_config.json"
        with patch('msse_capstone.clients.garmin_client.CONFIG_PATH', config_file):
            save_config(mock_config_data)
            
            # Verify file was created and contains correct data
            assert config_file.exists()
            saved_data = json.loads(config_file.read_text())
            assert saved_data == mock_config_data


class TestGarminInit:
    """Tests for Garmin client initialization."""
    
    @pytest.mark.unit
    def test_init_garmin_missing_credentials(self, tmp_path):
        """Test init_garmin raises ValueError when credentials are missing."""
        empty_config = tmp_path / "empty_config.json"
        empty_config.write_text('{}')
        
        with patch('msse_capstone.clients.garmin_client.CONFIG_PATH', empty_config):
            with pytest.raises(ValueError, match="missing_credentials"):
                init_garmin()
    
    @pytest.mark.unit
    @patch('msse_capstone.clients.garmin_client.Garmin')
    def test_init_garmin_with_valid_tokens(self, mock_garmin_class, mock_config_file, mock_token_dir):
        """Test successful login with existing tokens."""
        mock_garmin = Mock()
        mock_garmin.login.return_value = None
        mock_garmin_class.return_value = mock_garmin
        
        with patch('msse_capstone.clients.garmin_client.Path') as mock_path:
            mock_path.return_value.expanduser.return_value = mock_token_dir
            
            result = init_garmin()
            
            assert result == mock_garmin
            mock_garmin.login.assert_called_once()
    
    @pytest.mark.unit
    @patch('msse_capstone.clients.garmin_client.Garmin')
    def test_init_garmin_mfa_required(self, mock_garmin_class, mock_config_file, mfa_required_response):
        """Test MFA required scenario."""
        mock_garmin = Mock()
        mock_garmin.login.return_value = mfa_required_response
        mock_garmin_class.return_value = mock_garmin
        
        # First call should fail with token login, second should require MFA
        mock_garmin.login.side_effect = [FileNotFoundError(), mfa_required_response]
        
        with pytest.raises(ValueError, match="mfa_required"):
            init_garmin()
    
    @pytest.mark.unit
    @patch('msse_capstone.clients.garmin_client.Garmin')
    def test_init_garmin_with_mfa_code(self, mock_garmin_class, mock_config_file, mfa_required_response):
        """Test successful MFA authentication."""
        mock_garmin = Mock()
        mock_garmin.login.return_value = mfa_required_response
        mock_garmin.resume_login.return_value = None
        mock_garmin.garth.dump.return_value = None
        mock_garmin_class.return_value = mock_garmin
        
        # Token login fails, credential login needs MFA
        mock_garmin.login.side_effect = [FileNotFoundError(), mfa_required_response]
        
        result = init_garmin(mfa_code="123456")
        
        assert result == mock_garmin
        mock_garmin.resume_login.assert_called_once_with("mock_mfa_token", "123456")
        mock_garmin.garth.dump.assert_called_once()


class TestGetTodayStats:
    """Tests for fetching daily statistics."""
    
    @pytest.mark.unit
    def test_get_today_stats_success(self, mock_garmin_instance, sample_daily_stats):
        """Test successful stats retrieval."""
        # Configure mock to return sample data
        mock_garmin_instance.get_user_summary.return_value = {
            "totalSteps": sample_daily_stats["steps"],
            "totalDistanceMeters": sample_daily_stats["distance_km"] * 1000,
            "totalKilocalories": sample_daily_stats["calories"],
            "floorsClimbed": sample_daily_stats["floors"]
        }
        
        success, data, error = get_today_stats(mock_garmin_instance)
        
        assert success is True
        assert error is None
        assert data["steps"] == sample_daily_stats["steps"]
        assert data["distance_km"] == sample_daily_stats["distance_km"]
        assert data["calories"] == sample_daily_stats["calories"]
        assert data["floors"] == sample_daily_stats["floors"]
        assert "date" in data
    
    @pytest.mark.unit
    def test_get_today_stats_no_data(self, mock_garmin_instance):
        """Test when no summary data is available."""
        mock_garmin_instance.get_user_summary.return_value = None
        
        success, data, error = get_today_stats(mock_garmin_instance)
        
        assert success is False
        assert data is None
        assert "No activity summary available" in error
    
    @pytest.mark.unit
    def test_get_today_stats_api_error(self, mock_garmin_instance):
        """Test handling of API errors."""
        mock_garmin_instance.get_user_summary.side_effect = Exception("API Error")
        
        success, data, error = get_today_stats(mock_garmin_instance)
        
        assert success is False
        assert data is None
        assert "API Error" in error


class TestNewGarminClientFunctions:
    """Test new Garmin client functions."""
    
    @pytest.mark.unit
    def test_get_body_battery_success(self, mock_garmin_instance):
        """Test successful body battery data retrieval."""
        from msse_capstone.clients.garmin_client import get_body_battery
        
        mock_garmin_instance.get_body_battery.return_value = [{"date": "2025-10-06", "charged": 85}]
        
        success, data, error = get_body_battery(mock_garmin_instance, "2025-10-06")
        
        assert success is True
        assert data["body_battery"] == [{"date": "2025-10-06", "charged": 85}]
        assert data["start_date"] == "2025-10-06"
        assert error is None

    @pytest.mark.unit
    def test_get_activities_by_date_success(self, mock_garmin_instance):
        """Test successful activities retrieval."""
        from msse_capstone.clients.garmin_client import get_activities_by_date
        
        mock_garmin_instance.get_activities_by_date.return_value = [
            {"activityName": "Morning Run", "activityId": 123}
        ]
        
        success, data, error = get_activities_by_date(mock_garmin_instance, "2025-10-06")
        
        assert success is True
        assert len(data["activities"]) == 1
        assert data["activities"][0]["activityName"] == "Morning Run"
        assert data["count"] == 1
        assert error is None

    @pytest.mark.unit
    def test_get_sleep_data_error(self, mock_garmin_instance):
        """Test sleep data API error handling."""
        from msse_capstone.clients.garmin_client import get_sleep_data
        
        mock_garmin_instance.get_sleep_data.side_effect = Exception("Sleep API Error")
        
        success, data, error = get_sleep_data(mock_garmin_instance, "2025-10-06")
        
        assert success is False
        assert data is None
        assert "Sleep API Error" in error