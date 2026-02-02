"""AI prompt templates for packing list generation."""

from .models import TripInfo, WeatherData

# Simplified prompt template - core requirements in a more readable format
PACKING_PROMPT = """Create a comprehensive packing list for this trip:

## Trip Details
{trip_details}

## Weather Conditions
{weather_details}

## Requirements

### Packing Philosophy
- Use **capsule wardrobe** principles: maximize mix-and-match versatility
- Prioritize multi-use, lightweight, quick-drying items
- Only pack what is truly necessary

### Output Structure (REQUIRED)
Provide these 4 sections in order:

1. **Total Clothes for the Trip** - All clothing needed (packed + worn)
2. **Worn on Departure Day** - Items worn, not packed
3. **Packed in Luggage** - Total minus departure clothes
4. **Packing Cubes** - How items fit in 9L cubes (1-2 cubes typically)

### Format for Items
Each item: `Item Name: Quantity (X.XL each, Y.YL total)` with description

### JSON Block (REQUIRED)
End your response with a machine-parseable JSON block:

```
PARSEABLE_JSON_START
{{
  "total_clothes": [
    {{"name": "T-shirt", "qty": 3, "per_item_volume_l": 0.7, "total_volume_l": 2.1, "description": "quick-dry"}}
  ],
  "worn_on_departure": [...],
  "packed_in_luggage": [...],
  "packing_cubes": [
    {{"cube": "Cube 1", "items": ["T-shirt", "Underwear"], "total_volume_l": 8.5}}
  ],
  "totals": {{"estimated_volume_l": 18.5, "percent_of_capacity": 47.4, "estimated_weight_kg": 5.2}}
}}
PARSEABLE_JSON_END
```

### Validation
- Sum of worn + packed MUST equal total clothes (quantities and volumes)
- Include all categories: clothing, toiletries, electronics, documents, accessories

{additional_notes}
"""


def format_trip_details(trip_info: TripInfo) -> str:
    """Format trip information for the prompt."""
    lines = []
    
    # Destinations with dates
    lines.append("**Destinations:**")
    for dest in trip_info.destinations:
        lines.append(f"- {dest.location}: {dest.start_date} to {dest.end_date} ({dest.duration_days} days)")
    
    lines.append(f"\n**Total Duration:** {trip_info.total_duration_days} days")
    
    # Traveler info
    traveler = trip_info.traveler
    if traveler.gender:
        lines.append(f"**Gender:** {traveler.gender}")
    if traveler.age:
        lines.append(f"**Age:** {traveler.age}")
    if traveler.clothing_size:
        lines.append(f"**Clothing Size:** {traveler.clothing_size}")
    if traveler.shoe_size:
        lines.append(f"**Shoe Size:** {traveler.shoe_size}")
    if traveler.sleepwear:
        lines.append(f"**Sleepwear Preference:** {traveler.sleepwear} (dedicated=pack pajamas, minimal=use underwear/undershirt, none=sleep naked)")
    
    # Activities and luggage
    if trip_info.activities:
        lines.append(f"**Activities:** {trip_info.activities}")
    
    laundry_status = "Yes" if trip_info.laundry.available else "No"
    lines.append(f"**Laundry Available:** {laundry_status}")
    lines.append(f"**Luggage:** {trip_info.luggage_volume_liters}L" + (f" ({trip_info.luggage_name})" if trip_info.luggage_name else ""))
    
    return "\n".join(lines)


def format_weather_details(weather_by_location: dict[str, WeatherData]) -> str:
    """Format weather data for the prompt."""
    lines = []
    
    for location, weather in weather_by_location.items():
        lines.append(f"**{location}:**")
        for forecast in weather.forecasts:
            rain_pct = f"{forecast.rain_chance:.0f}%" if forecast.rain_chance else "0%"
            lines.append(
                f"  - {forecast.date}: {forecast.temp_min}°C to {forecast.temp_max}°C, "
                f"{forecast.description}, {rain_pct} rain"
            )
        if weather.is_seasonal_estimate:
            lines.append("  *(seasonal estimate - trip is >7 days away)*")
    
    return "\n".join(lines)


def build_prompt(trip_info: TripInfo, weather_data: dict[str, WeatherData]) -> str:
    """Build the complete packing list prompt."""
    additional = ""
    if trip_info.additional_notes:
        additional = f"## Additional Notes\n{trip_info.additional_notes}"
    
    return PACKING_PROMPT.format(
        trip_details=format_trip_details(trip_info),
        weather_details=format_weather_details(weather_data),
        additional_notes=additional,
    )
