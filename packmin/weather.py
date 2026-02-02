"""OpenWeather API integration."""

from datetime import datetime
from typing import Optional

import requests

from .config import get_config
from .models import WeatherData, WeatherForecast

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"


def get_season(month: int) -> str:
    """Get season name from month number."""
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    return "fall"


def get_seasonal_estimate(month: int) -> WeatherForecast:
    """Get seasonal weather estimate when forecast unavailable."""
    season_temps = {
        "winter": {"min": -5, "max": 10},
        "spring": {"min": 10, "max": 20},
        "summer": {"min": 20, "max": 30},
        "fall": {"min": 10, "max": 20},
    }
    season = get_season(month)
    temps = season_temps[season]
    return WeatherForecast(
        date="seasonal average",
        temp_min=temps["min"],
        temp_max=temps["max"],
        description=f"{season} weather",
        rain_chance=30.0,
    )


def get_coordinates(location: str, api_key: str) -> Optional[tuple[float, float]]:
    """Get lat/lon coordinates for a location."""
    url = f"{OPENWEATHER_BASE_URL}/weather?q={location}&appid={api_key}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["coord"]["lat"], data["coord"]["lon"]
    except Exception:
        pass
    return None


def fetch_forecast(
    lat: float, lon: float, api_key: str
) -> list[dict]:
    """Fetch 7-day forecast from OneCall API."""
    url = f"{ONECALL_URL}?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("daily", [])[:7]
    except Exception:
        pass
    return []


def get_weather_data(
    location: str,
    start_date: datetime,
    end_date: datetime,
    api_key: Optional[str] = None,
) -> WeatherData:
    """Get weather data for a location and date range.
    
    Uses OpenWeather OneCall API if trip is within 7 days,
    otherwise falls back to seasonal estimates.
    """
    if api_key is None:
        api_key = get_config().openweather_api_key
    
    weather_data = WeatherData(location=location)
    
    # Only use forecast API if trip starts within 7 days
    days_until_travel = (start_date - datetime.now()).days
    
    if days_until_travel <= 7 and api_key:
        coords = get_coordinates(location, api_key)
        if coords:
            lat, lon = coords
            daily_forecasts = fetch_forecast(lat, lon, api_key)
            
            for day in daily_forecasts:
                forecast_date = datetime.fromtimestamp(day["dt"])
                if start_date <= forecast_date <= end_date:
                    weather_data.forecasts.append(WeatherForecast(
                        date=forecast_date.strftime("%Y-%m-%d"),
                        temp_min=day["temp"]["min"],
                        temp_max=day["temp"]["max"],
                        description=day["weather"][0]["description"],
                        rain_chance=day.get("pop", 0) * 100,
                    ))
    
    # Fall back to seasonal estimate if no forecast data
    if not weather_data.forecasts:
        weather_data.forecasts.append(get_seasonal_estimate(start_date.month))
        weather_data.is_seasonal_estimate = True
    
    return weather_data
