"""Pydantic models for packmin data structures."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class TravelerInfo(BaseModel):
    """Information about the traveler."""
    gender: str = ""
    age: Optional[int] = None
    clothing_size: str = ""
    shoe_size: str = ""
    
    
class TripDestination(BaseModel):
    """A single destination with date range."""
    location: str
    start_date: date
    end_date: date
    
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


class LaundryInfo(BaseModel):
    """Laundry availability configuration."""
    available: bool = False
    date_ranges: list[dict] = Field(default_factory=list)  # [{"from": "2025-06-01", "to": "2025-06-03"}] or ["all"]


class TripInfo(BaseModel):
    """Complete trip information."""
    destinations: list[TripDestination]
    traveler: TravelerInfo
    activities: str = ""
    additional_notes: str = ""
    laundry: LaundryInfo = Field(default_factory=LaundryInfo)
    luggage_volume_liters: float = 39.0
    
    @property
    def total_duration_days(self) -> int:
        return sum(d.duration_days for d in self.destinations)
    
    @property
    def locations(self) -> list[str]:
        return [d.location for d in self.destinations]


class WeatherForecast(BaseModel):
    """Single day weather forecast."""
    date: str
    temp_min: float
    temp_max: float
    description: str
    rain_chance: float = 0.0


class WeatherData(BaseModel):
    """Weather data for a location."""
    location: str
    forecasts: list[WeatherForecast] = Field(default_factory=list)
    is_seasonal_estimate: bool = False


class PackingItem(BaseModel):
    """A single packing item."""
    name: str
    quantity: int = 1
    per_item_volume_l: float = 0.0
    total_volume_l: float = 0.0
    description: str = ""
    category: str = ""


class PackingCube(BaseModel):
    """Packing cube configuration."""
    name: str
    items: list[str] = Field(default_factory=list)
    total_volume_l: float = 0.0


class PackingTotals(BaseModel):
    """Packing list totals."""
    estimated_volume_l: float = 0.0
    percent_of_capacity: float = 0.0
    estimated_weight_kg: float = 0.0


class PackingList(BaseModel):
    """Complete packing list parsed from AI response."""
    total_clothes: list[PackingItem] = Field(default_factory=list)
    worn_on_departure: list[PackingItem] = Field(default_factory=list)
    packed_in_luggage: list[PackingItem] = Field(default_factory=list)
    packing_cubes: list[PackingCube] = Field(default_factory=list)
    totals: PackingTotals = Field(default_factory=PackingTotals)
    raw_response: str = ""
    
    def validate_quantities(self) -> tuple[bool, str]:
        """Validate that totals match packed + worn."""
        total_qty = sum(i.quantity for i in self.total_clothes)
        packed_qty = sum(i.quantity for i in self.packed_in_luggage)
        worn_qty = sum(i.quantity for i in self.worn_on_departure)
        
        total_vol = sum(i.total_volume_l for i in self.total_clothes)
        packed_vol = sum(i.total_volume_l for i in self.packed_in_luggage)
        worn_vol = sum(i.total_volume_l for i in self.worn_on_departure)
        
        issues = []
        if total_qty != (packed_qty + worn_qty):
            issues.append(f"Quantity mismatch: total {total_qty} != packed {packed_qty} + worn {worn_qty}")
        if abs(total_vol - (packed_vol + worn_vol)) > 0.01:
            issues.append(f"Volume mismatch: total {total_vol:.2f}L != packed {packed_vol:.2f}L + worn {worn_vol:.2f}L")
        
        return (len(issues) == 0, "; ".join(issues))
