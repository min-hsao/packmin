"""Tests for packmin models and config."""

import os
from datetime import date

import pytest

from packmin.config import Config, reset_config
from packmin.models import (
    PackingItem,
    PackingList,
    TravelerInfo,
    TripDestination,
    TripInfo,
    WeatherForecast,
)


class TestTripDestination:
    """Tests for TripDestination model."""
    
    def test_duration_calculation(self):
        """Test duration_days property calculation."""
        dest = TripDestination(
            location="Paris, France",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 7),
        )
        assert dest.duration_days == 7
    
    def test_single_day_trip(self):
        """Test single day trip duration."""
        dest = TripDestination(
            location="London, UK",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 1),
        )
        assert dest.duration_days == 1


class TestTripInfo:
    """Tests for TripInfo model."""
    
    def test_total_duration_multiple_destinations(self):
        """Test total duration with multiple destinations."""
        trip = TripInfo(
            destinations=[
                TripDestination(
                    location="Paris",
                    start_date=date(2025, 6, 1),
                    end_date=date(2025, 6, 3),
                ),
                TripDestination(
                    location="Rome",
                    start_date=date(2025, 6, 4),
                    end_date=date(2025, 6, 7),
                ),
            ],
            traveler=TravelerInfo(),
        )
        assert trip.total_duration_days == 7  # 3 + 4
    
    def test_locations_property(self):
        """Test locations list extraction."""
        trip = TripInfo(
            destinations=[
                TripDestination(
                    location="Paris",
                    start_date=date(2025, 6, 1),
                    end_date=date(2025, 6, 3),
                ),
                TripDestination(
                    location="Rome",
                    start_date=date(2025, 6, 4),
                    end_date=date(2025, 6, 7),
                ),
            ],
            traveler=TravelerInfo(),
        )
        assert trip.locations == ["Paris", "Rome"]


class TestTravelerInfo:
    """Tests for TravelerInfo model."""
    
    def test_default_values(self):
        """Test default values are empty."""
        traveler = TravelerInfo()
        assert traveler.gender == ""
        assert traveler.age is None
        assert traveler.clothing_size == ""
    
    def test_with_values(self):
        """Test with actual values."""
        traveler = TravelerInfo(
            gender="male",
            age=30,
            clothing_size="M",
            shoe_size="US 10",
        )
        assert traveler.gender == "male"
        assert traveler.age == 30


class TestPackingList:
    """Tests for PackingList model."""
    
    def test_validation_passes(self):
        """Test validation passes when quantities match."""
        packing = PackingList(
            total_clothes=[
                PackingItem(name="Shirt", quantity=3, total_volume_l=2.1),
                PackingItem(name="Pants", quantity=2, total_volume_l=3.0),
            ],
            worn_on_departure=[
                PackingItem(name="Shirt", quantity=1, total_volume_l=0.7),
                PackingItem(name="Pants", quantity=1, total_volume_l=1.5),
            ],
            packed_in_luggage=[
                PackingItem(name="Shirt", quantity=2, total_volume_l=1.4),
                PackingItem(name="Pants", quantity=1, total_volume_l=1.5),
            ],
        )
        ok, msg = packing.validate_quantities()
        assert ok is True
        assert msg == ""
    
    def test_validation_fails_quantity_mismatch(self):
        """Test validation fails with quantity mismatch."""
        packing = PackingList(
            total_clothes=[
                PackingItem(name="Shirt", quantity=5, total_volume_l=3.5),
            ],
            worn_on_departure=[
                PackingItem(name="Shirt", quantity=1, total_volume_l=0.7),
            ],
            packed_in_luggage=[
                PackingItem(name="Shirt", quantity=2, total_volume_l=1.4),
            ],
        )
        ok, msg = packing.validate_quantities()
        assert ok is False
        assert "Quantity mismatch" in msg


class TestWeatherForecast:
    """Tests for WeatherForecast model."""
    
    def test_defaults(self):
        """Test rain_chance default."""
        forecast = WeatherForecast(
            date="2025-06-01",
            temp_min=15.0,
            temp_max=25.0,
            description="clear sky",
        )
        assert forecast.rain_chance == 0.0


class TestConfig:
    """Tests for Config loading."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
        # Clear relevant env vars
        for key in ["AI_PROVIDER", "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENWEATHER_API_KEY"]:
            os.environ.pop(key, None)
    
    def test_default_provider(self):
        """Test default AI provider is deepseek."""
        config = Config.load()
        assert config.ai_provider == "deepseek"
    
    def test_env_override(self):
        """Test environment variable override."""
        os.environ["AI_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        config = Config.load()
        assert config.ai_provider == "openai"
        assert config.openai_api_key == "test-key"
    
    def test_validation_missing_weather_key(self):
        """Test validation catches missing weather API key."""
        config = Config.load()
        errors = config.validate()
        assert any("OPENWEATHER_API_KEY" in e for e in errors)
    
    def test_validation_missing_ai_key(self):
        """Test validation catches missing AI API key."""
        os.environ["AI_PROVIDER"] = "openai"
        os.environ["OPENWEATHER_API_KEY"] = "weather-key"
        
        config = Config.load()
        errors = config.validate()
        assert any("OPENAI_API_KEY" in e for e in errors)
    
    def test_get_active_api_key(self):
        """Test getting active provider's API key."""
        os.environ["AI_PROVIDER"] = "deepseek"
        os.environ["DEEPSEEK_API_KEY"] = "ds-key"
        
        config = Config.load()
        assert config.get_active_api_key() == "ds-key"
    
    def test_get_active_model(self):
        """Test getting active provider's model."""
        os.environ["AI_PROVIDER"] = "openai"
        os.environ["OPENAI_MODEL"] = "gpt-4o"
        
        config = Config.load()
        assert config.get_active_model() == "gpt-4o"
    
    def teardown_method(self):
        """Clean up env vars after each test."""
        reset_config()
        for key in ["AI_PROVIDER", "OPENAI_API_KEY", "DEEPSEEK_API_KEY", 
                    "OPENWEATHER_API_KEY", "OPENAI_MODEL"]:
            os.environ.pop(key, None)
