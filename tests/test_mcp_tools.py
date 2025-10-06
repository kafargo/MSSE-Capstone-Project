"""Integration tests for MCP tools."""

import pytest
from unittest.mock import Mock, patch

# Import the actual MCP tools from server
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStepsToMiles:
    """Tests for the steps_to_miles MCP tool."""
    
    @pytest.mark.mcp
    @pytest.mark.unit
    def test_steps_to_miles_conversion(self):
        """Test steps to miles conversion."""
        from server import steps_to_miles
        
        # Test standard conversion (2000 steps = 1 mile)
        assert steps_to_miles(2000) == 1.0
        assert steps_to_miles(4000) == 2.0
        assert steps_to_miles(1000) == 0.5
        assert steps_to_miles(0) == 0.0
    
    @pytest.mark.mcp
    @pytest.mark.unit
    def test_steps_to_miles_edge_cases(self):
        """Test edge cases for steps to miles conversion."""
        from server import steps_to_miles
        
        # Large numbers
        assert steps_to_miles(20000) == 10.0
        
        # Fractional results
        assert steps_to_miles(1500) == 0.75
        assert steps_to_miles(2500) == 1.25


class TestDailyStats:
    """Tests for the daily_stats MCP tool."""
    
    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_today_stats')
    def test_daily_stats_success(self, mock_get_stats, mock_init, sample_daily_stats, mock_garmin_instance):
        """Test successful daily stats retrieval."""
        from server import daily_stats
        
        # Configure mocks
        mock_init.return_value = mock_garmin_instance
        mock_get_stats.return_value = (True, sample_daily_stats, None)
        
        result = daily_stats()
        
        assert result == sample_daily_stats
        mock_init.assert_called_once_with(None)
        mock_get_stats.assert_called_once_with(mock_garmin_instance)
    
    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    def test_daily_stats_missing_credentials(self, mock_init):
        """Test response when credentials are missing."""
        from server import daily_stats
        
        mock_init.side_effect = ValueError("missing_credentials")
        
        result = daily_stats()
        
        assert result["error"] == "missing_credentials"
        assert "garmin_config.json" in result["message"]
        assert "setup_instructions" in result
    
    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    def test_daily_stats_mfa_required(self, mock_init):
        """Test response when MFA is required."""
        from server import daily_stats
        
        mock_init.side_effect = ValueError("mfa_required")
        
        result = daily_stats()
        
        assert result["error"] == "mfa_required"
        assert "Multi-factor authentication required" in result["message"]
        assert "instructions" in result
    
    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_today_stats')
    def test_daily_stats_with_mfa_code(self, mock_get_stats, mock_init, sample_daily_stats, mock_garmin_instance):
        """Test daily stats with MFA code provided."""
        from server import daily_stats
        
        mock_init.return_value = mock_garmin_instance
        mock_get_stats.return_value = (True, sample_daily_stats, None)
        
        result = daily_stats(mfa_code="123456")
        
        assert result == sample_daily_stats
        mock_init.assert_called_once_with("123456")
    
    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    def test_daily_stats_authentication_failed(self, mock_init):
        """Test response when authentication fails."""
        from server import daily_stats
        
        mock_init.side_effect = RuntimeError("Invalid credentials")
        
        result = daily_stats()
        
        assert result["error"] == "authentication_failed"
        assert "Invalid credentials" in result["message"]
    
    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_today_stats')
    def test_daily_stats_fetch_failed(self, mock_get_stats, mock_init, mock_garmin_instance):
        """Test response when stats fetch fails."""
        from server import daily_stats
        
        mock_init.return_value = mock_garmin_instance
        mock_get_stats.return_value = (False, None, "API Error")
        
        result = daily_stats()
        
        assert result["error"] == "fetch_failed"
        assert "API Error" in result["message"]

    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_last_activity')
    def test_last_activity_success(self, mock_get_activity, mock_init, mock_garmin_instance):
        """Test successful last activity retrieval."""
        from server import last_activity
        
        mock_init.return_value = mock_garmin_instance
        mock_get_activity.return_value = (
            True, 
            {"activityName": "Morning Run", "distance": 5.2, "duration": "30:15"}, 
            None
        )
        
        result = last_activity()
        
        assert "activityName" in result
        assert result["activityName"] == "Morning Run"
        assert "distance" in result
        assert "duration" in result

    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_last_activity')
    def test_last_activity_auth_failed(self, mock_get_activity, mock_init, mock_garmin_instance):
        """Test response when authentication fails for last activity."""
        from server import last_activity
        
        mock_init.return_value = mock_garmin_instance
        mock_get_activity.return_value = (False, None, "Invalid credentials")
        
        result = last_activity()
        
        assert result["error"] == "auth_failed"
        assert "Invalid credentials" in result["message"]

    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_last_activity')
    def test_last_activity_fetch_failed(self, mock_get_activity, mock_init, mock_garmin_instance):
        """Test response when last activity fetch fails."""
        from server import last_activity
        
        mock_init.return_value = mock_garmin_instance
        mock_get_activity.return_value = (False, None, "API Error")
        
        result = last_activity()
        
        assert result["error"] == "fetch_failed"
        assert "API Error" in result["message"]


class TestNewGarminTools:
    """Test new Garmin MCP tools."""
    
    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_body_battery')
    def test_body_battery_success(self, mock_get_data, mock_init, mock_garmin_instance):
        """Test successful body battery retrieval."""
        from server import body_battery
        
        mock_init.return_value = mock_garmin_instance
        mock_get_data.return_value = (
            True, 
            {"body_battery": [{"date": "2025-10-06", "charged": 85}], "start_date": "2025-10-06", "end_date": "2025-10-06"}, 
            None
        )
        
        result = body_battery("2025-10-06")
        
        assert "body_battery" in result
        assert result["start_date"] == "2025-10-06"

    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_all_day_stress')
    def test_all_day_stress_success(self, mock_get_data, mock_init, mock_garmin_instance):
        """Test successful stress data retrieval."""
        from server import all_day_stress
        
        mock_init.return_value = mock_garmin_instance
        mock_get_data.return_value = (
            True, 
            {"stress_data": {"overallStressLevel": 25}, "date": "2025-10-06"}, 
            None
        )
        
        result = all_day_stress("2025-10-06")
        
        assert "stress_data" in result
        assert result["date"] == "2025-10-06"

    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_sleep_data')
    def test_sleep_data_success(self, mock_get_data, mock_init, mock_garmin_instance):
        """Test successful sleep data retrieval."""
        from server import sleep_data
        
        mock_init.return_value = mock_garmin_instance
        mock_get_data.return_value = (
            True, 
            {"sleep_data": {"totalSleepTimeSeconds": 28800}, "date": "2025-10-06"}, 
            None
        )
        
        result = sleep_data("2025-10-06")
        
        assert "sleep_data" in result
        assert result["date"] == "2025-10-06"

    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_activities_by_date')
    def test_activities_success(self, mock_get_data, mock_init, mock_garmin_instance):
        """Test successful activities retrieval."""
        from server import activities
        
        mock_init.return_value = mock_garmin_instance
        mock_get_data.return_value = (
            True, 
            {
                "activities": [{"activityName": "Morning Run"}], 
                "start_date": "2025-10-06", 
                "end_date": "2025-10-06",
                "count": 1
            }, 
            None
        )
        
        result = activities("2025-10-06")
        
        assert "activities" in result
        assert result["count"] == 1
        assert result["start_date"] == "2025-10-06"

    @pytest.mark.mcp
    @pytest.mark.unit
    @patch('server.init_garmin')
    @patch('server.get_body_battery')
    def test_body_battery_auth_failed(self, mock_get_data, mock_init, mock_garmin_instance):
        """Test authentication failure for body battery."""
        from server import body_battery
        
        mock_init.return_value = mock_garmin_instance
        mock_get_data.return_value = (False, None, "Invalid credentials")
        
        result = body_battery("2025-10-06")
        
        assert result["error"] == "auth_failed"
        assert "Invalid credentials" in result["message"]