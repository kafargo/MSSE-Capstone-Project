"""Unit tests for preferences client functionality."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from msse_capstone.clients.preferences_client import (
    load_workout_preferences,
    save_workout_preferences,
    load_available_equipment,
    save_available_equipment,
    PREFERENCES_PATH,
    EQUIPMENT_PATH,
)


@pytest.fixture
def sample_preferences():
    """Sample workout preferences data."""
    return {
        "goals": ["strength", "endurance"],
        "workout_frequency": 4,
        "preferred_days": ["monday", "wednesday", "friday", "sunday"],
        "session_duration_minutes": 60,
        "intensity_level": "moderate",
        "restrictions": ["no_jumping"]
    }


@pytest.fixture
def sample_equipment():
    """Sample equipment data."""
    return {
        "cardio": ["treadmill", "stationary_bike"],
        "strength": ["dumbbells", "barbell", "bench"],
        "weights_available": {
            "dumbbells": "5-50 lbs",
            "barbell": "45 lbs with plates"
        },
        "accessories": ["yoga_mat", "resistance_bands"],
        "location": "home_gym"
    }


class TestLoadWorkoutPreferences:
    """Tests for loading workout preferences."""
    
    @pytest.mark.unit
    def test_load_preferences_file_not_found(self, tmp_path):
        """Test loading preferences when file doesn't exist."""
        with patch('msse_capstone.clients.preferences_client.PREFERENCES_PATH', tmp_path / "missing.json"):
            success, data, error = load_workout_preferences()
            assert success is False
            assert data is None
            assert error == "not_found"
    
    @pytest.mark.unit
    def test_load_preferences_success(self, tmp_path, sample_preferences):
        """Test successfully loading preferences."""
        pref_file = tmp_path / "workout_preferences.json"
        with open(pref_file, 'w') as f:
            json.dump(sample_preferences, f)
        
        with patch('msse_capstone.clients.preferences_client.PREFERENCES_PATH', pref_file):
            success, data, error = load_workout_preferences()
            assert success is True
            assert data == sample_preferences
            assert error is None
    
    @pytest.mark.unit
    def test_load_preferences_empty_file(self, tmp_path):
        """Test loading preferences from empty file."""
        pref_file = tmp_path / "workout_preferences.json"
        with open(pref_file, 'w') as f:
            json.dump({}, f)
        
        with patch('msse_capstone.clients.preferences_client.PREFERENCES_PATH', pref_file):
            success, data, error = load_workout_preferences()
            assert success is False
            assert data is None
            assert error == "not_found"
    
    @pytest.mark.unit
    def test_load_preferences_invalid_json(self, tmp_path):
        """Test loading preferences with invalid JSON."""
        pref_file = tmp_path / "workout_preferences.json"
        with open(pref_file, 'w') as f:
            f.write("invalid json content {{{")
        
        with patch('msse_capstone.clients.preferences_client.PREFERENCES_PATH', pref_file):
            success, data, error = load_workout_preferences()
            assert success is False
            assert data is None
            assert "Invalid JSON" in error


class TestSaveWorkoutPreferences:
    """Tests for saving workout preferences."""
    
    @pytest.mark.unit
    def test_save_preferences_success(self, tmp_path, sample_preferences):
        """Test successfully saving preferences."""
        pref_file = tmp_path / "workout_preferences.json"
        
        with patch('msse_capstone.clients.preferences_client.PREFERENCES_PATH', pref_file):
            success, error = save_workout_preferences(sample_preferences)
            assert success is True
            assert error is None
            
            # Verify file was created and contains correct data
            assert pref_file.exists()
            with open(pref_file, 'r') as f:
                saved_data = json.load(f)
            assert saved_data == sample_preferences
    
    @pytest.mark.unit
    def test_save_preferences_io_error(self, sample_preferences):
        """Test handling IO error when saving preferences."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            success, error = save_workout_preferences(sample_preferences)
            assert success is False
            assert "Error saving workout preferences" in error


class TestLoadAvailableEquipment:
    """Tests for loading available equipment."""
    
    @pytest.mark.unit
    def test_load_equipment_file_not_found(self, tmp_path):
        """Test loading equipment when file doesn't exist."""
        with patch('msse_capstone.clients.preferences_client.EQUIPMENT_PATH', tmp_path / "missing.json"):
            success, data, error = load_available_equipment()
            assert success is False
            assert data is None
            assert error == "not_found"
    
    @pytest.mark.unit
    def test_load_equipment_success(self, tmp_path, sample_equipment):
        """Test successfully loading equipment."""
        equip_file = tmp_path / "available_equipment.json"
        with open(equip_file, 'w') as f:
            json.dump(sample_equipment, f)
        
        with patch('msse_capstone.clients.preferences_client.EQUIPMENT_PATH', equip_file):
            success, data, error = load_available_equipment()
            assert success is True
            assert data == sample_equipment
            assert error is None
    
    @pytest.mark.unit
    def test_load_equipment_empty_file(self, tmp_path):
        """Test loading equipment from empty file."""
        equip_file = tmp_path / "available_equipment.json"
        with open(equip_file, 'w') as f:
            json.dump({}, f)
        
        with patch('msse_capstone.clients.preferences_client.EQUIPMENT_PATH', equip_file):
            success, data, error = load_available_equipment()
            assert success is False
            assert data is None
            assert error == "not_found"
    
    @pytest.mark.unit
    def test_load_equipment_invalid_json(self, tmp_path):
        """Test loading equipment with invalid JSON."""
        equip_file = tmp_path / "available_equipment.json"
        with open(equip_file, 'w') as f:
            f.write("invalid json content {{{")
        
        with patch('msse_capstone.clients.preferences_client.EQUIPMENT_PATH', equip_file):
            success, data, error = load_available_equipment()
            assert success is False
            assert data is None
            assert "Invalid JSON" in error


class TestSaveAvailableEquipment:
    """Tests for saving available equipment."""
    
    @pytest.mark.unit
    def test_save_equipment_success(self, tmp_path, sample_equipment):
        """Test successfully saving equipment."""
        equip_file = tmp_path / "available_equipment.json"
        
        with patch('msse_capstone.clients.preferences_client.EQUIPMENT_PATH', equip_file):
            success, error = save_available_equipment(sample_equipment)
            assert success is True
            assert error is None
            
            # Verify file was created and contains correct data
            assert equip_file.exists()
            with open(equip_file, 'r') as f:
                saved_data = json.load(f)
            assert saved_data == sample_equipment
    
    @pytest.mark.unit
    def test_save_equipment_io_error(self, sample_equipment):
        """Test handling IO error when saving equipment."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            success, error = save_available_equipment(sample_equipment)
            assert success is False
            assert "Error saving available equipment" in error
