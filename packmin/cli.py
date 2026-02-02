"""Click-based CLI for packmin."""

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from .ai import generate_packing_list, estimate_luggage_volume
from .config import get_config, Config
from .models import (
    LaundryInfo,
    PackingList,
    TravelerInfo,
    TripDestination,
    TripInfo,
)
from .prompts import build_prompt
from .weather import get_weather_data


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def prompt_with_default(prompt_text: str, default: str = "") -> str:
    """Interactive prompt with optional default value."""
    if default:
        result = click.prompt(prompt_text, default=default, show_default=True)
    else:
        result = click.prompt(prompt_text, default="", show_default=False)
    return result


def interactive_destinations() -> list[TripDestination]:
    """Interactively collect destination information."""
    click.echo("\n📍 Enter destinations (semicolon-separated)")
    click.echo("   Example: Paris, France; Rome, Italy")
    
    locations_input = click.prompt("Destinations")
    locations = [loc.strip() for loc in locations_input.split(";") if loc.strip()]
    
    destinations = []
    for location in locations:
        click.echo(f"\n📅 Dates for {location}:")
        
        while True:
            try:
                start_str = click.prompt("  Start date (YYYY-MM-DD)")
                end_str = click.prompt("  End date (YYYY-MM-DD)")
                
                start_date = parse_date(start_str)
                end_date = parse_date(end_str)
                
                if end_date < start_date:
                    click.echo("  ❌ End date must be after start date")
                    continue
                
                duration = (end_date - start_date).days + 1
                click.echo(f"  ✓ {duration} days")
                
                destinations.append(TripDestination(
                    location=location,
                    start_date=start_date.date(),
                    end_date=end_date.date(),
                ))
                break
                
            except ValueError:
                click.echo("  ❌ Invalid date format. Use YYYY-MM-DD")
    
    return destinations


def interactive_traveler() -> TravelerInfo:
    """Interactively collect traveler information."""
    click.echo("\n👤 Traveler Information:")
    
    return TravelerInfo(
        gender=prompt_with_default("  Gender"),
        age=int(prompt_with_default("  Age", "30") or "30"),
        clothing_size=prompt_with_default("  Clothing size (e.g., Men's M)"),
        shoe_size=prompt_with_default("  Shoe size (e.g., US 10)"),
        sleepwear=click.prompt("  Sleepwear preference", type=click.Choice(["dedicated", "minimal", "none"]), default="minimal"),
    )


def interactive_trip_details(destinations: list[TripDestination], traveler: TravelerInfo) -> TripInfo:
    """Interactively collect remaining trip details."""
    click.echo("\n🎒 Trip Details:")
    
    activities = prompt_with_default("  Activities (e.g., hiking, business)")
    
    laundry_available = click.confirm("  Laundry available?", default=False)
    
    click.echo("\n📦 Luggage:")
    click.echo("  1. Enter volume in liters")
    click.echo("  2. Enter dimensions (L x W x H cm)")
    click.echo("  3. Enter luggage name/model (AI lookup)")
    choice = click.prompt("  Choose option", type=int, default=1)
    
    volume = 39.0
    luggage_name = ""
    
    if choice == 3:
        luggage_name = click.prompt("  Luggage name (e.g. 'Away Carry-On')")
        click.echo("  🔍 Looking up volume...")
        volume = estimate_luggage_volume(luggage_name)
        click.echo(f"  Found/Estimated: {volume}L")
        
    elif choice == 2:
        dims = click.prompt("  Dimensions (e.g., 55 x 35 x 20)")
        try:
            parts = [float(d.strip()) for d in dims.split("x")]
            volume = (parts[0] * parts[1] * parts[2]) / 1000
            click.echo(f"  Calculated: {volume:.1f}L")
        except (ValueError, IndexError):
            volume = 39.0
            click.echo(f"  Invalid format, using default: {volume}L")
    else:
        volume = float(click.prompt("  Volume (liters)", default="39"))
    
    additional = prompt_with_default("\n📝 Additional notes (optional)")
    
    return TripInfo(
        destinations=destinations,
        traveler=traveler,
        activities=activities,
        additional_notes=additional,
        laundry=LaundryInfo(available=laundry_available),
        luggage_volume_liters=volume,
        luggage_name=luggage_name,
    )


def print_packing_list(packing_list: PackingList) -> None:
    """Print formatted packing list to console."""
    click.echo("\n" + "=" * 60)
    click.echo("📋 PACKING LIST")
    click.echo("=" * 60)
    
    def print_items(title: str, items: list) -> None:
        if not items:
            return
        click.echo(f"\n### {title}")
        click.echo(f"{'Qty':<5} {'Item':<25} {'Volume':<12} {'Description'}")
        click.echo("-" * 60)
        for item in items:
            click.echo(f"{item.quantity:<5} {item.name:<25} {item.total_volume_l:<12.1f} {item.description}")
    
    print_items("Total Clothes", packing_list.total_clothes)
    print_items("Worn on Departure", packing_list.worn_on_departure)
    print_items("Packed in Luggage", packing_list.packed_in_luggage)
    
    if packing_list.packing_cubes:
        click.echo("\n### Packing Cubes")
        for cube in packing_list.packing_cubes:
            click.echo(f"  {cube.name}: {', '.join(cube.items)} ({cube.total_volume_l:.1f}L)")
    
    if packing_list.totals.estimated_volume_l:
        click.echo("\n### Totals")
        click.echo(f"  Volume: {packing_list.totals.estimated_volume_l:.1f}L ({packing_list.totals.percent_of_capacity:.0f}% capacity)")
        click.echo(f"  Weight: {packing_list.totals.estimated_weight_kg:.1f}kg")
    
    # Validation
    ok, msg = packing_list.validate_quantities()
    if not ok:
        click.echo(f"\n⚠️  Validation warning: {msg}")
    
    click.echo("\n" + "=" * 60)


def save_packing_list(
    packing_list: PackingList,
    trip_info: TripInfo,
    format_type: str,
    output_path: Optional[Path] = None,
) -> Path:
    """Save packing list to file."""
    first_dest = trip_info.destinations[0]
    base_name = f"packing_{first_dest.start_date}_{first_dest.location.replace(' ', '_').replace(',', '')}"
    
    if output_path:
        filepath = output_path
    elif format_type == "csv":
        filepath = Path(f"{base_name}.csv")
    elif format_type == "md":
        filepath = Path(f"{base_name}.md")
    else:
        filepath = Path(f"{base_name}.txt")
    
    locations_str = ", ".join(trip_info.locations)
    
    if format_type == "csv":
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Item", "Quantity", "Volume (L)", "Description"])
            
            for item in packing_list.packed_in_luggage:
                writer.writerow(["Packed", item.name, item.quantity, item.total_volume_l, item.description])
            for item in packing_list.worn_on_departure:
                writer.writerow(["Worn", item.name, item.quantity, item.total_volume_l, item.description])
    
    elif format_type == "md":
        with open(filepath, "w") as f:
            f.write(f"# Packing List for {locations_str}\n\n")
            f.write(f"**Duration:** {trip_info.total_duration_days} days\n")
            f.write(f"**Luggage:** {trip_info.luggage_volume_liters}L\n\n")
            f.write("---\n\n")
            f.write(packing_list.raw_response)
    
    else:  # txt
        with open(filepath, "w") as f:
            f.write(f"Packing List for {locations_str}\n")
            f.write(f"Duration: {trip_info.total_duration_days} days\n")
            f.write(f"Luggage: {trip_info.luggage_volume_liters}L\n")
            f.write("=" * 50 + "\n\n")
            f.write(packing_list.raw_response)
    
    return filepath


@click.command()
@click.option("--destination", "-d", multiple=True, help="Destination (can be repeated)")
@click.option("--start-date", "-s", multiple=True, help="Start date YYYY-MM-DD (pairs with --destination)")
@click.option("--end-date", "-e", multiple=True, help="End date YYYY-MM-DD (pairs with --destination)")
@click.option("--gender", "-g", help="Traveler gender")
@click.option("--age", "-a", type=int, help="Traveler age")
@click.option("--size", help="Clothing size")
@click.option("--shoe-size", help="Shoe size")
@click.option("--sleepwear", type=click.Choice(["dedicated", "minimal", "none"]), default="minimal", help="Sleepwear preference")
@click.option("--activities", help="Activities (comma-separated)")
@click.option("--laundry/--no-laundry", default=False, help="Laundry available")
@click.option("--volume", "-v", type=float, help="Luggage volume in liters")
@click.option("--luggage-name", help="Luggage brand/model name (overrides volume if found)")
@click.option("--notes", "-n", help="Additional notes for AI")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "output_format", type=click.Choice(["txt", "md", "csv"]), help="Output format")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.option("--interactive", "-i", is_flag=True, help="Force interactive mode")
def main(
    destination: tuple,
    start_date: tuple,
    end_date: tuple,
    gender: Optional[str],
    age: Optional[int],
    size: Optional[str],
    shoe_size: Optional[str],
    sleepwear: str,
    activities: Optional[str],
    laundry: bool,
    volume: Optional[float],
    luggage_name: Optional[str],
    notes: Optional[str],
    output: Optional[str],
    output_format: Optional[str],
    debug: bool,
    interactive: bool,
) -> None:
    """🎒 PackMin - Minimalist Packing List Generator
    
    Generate AI-powered packing lists using capsule wardrobe principles.
    
    Run without arguments for interactive mode, or use flags for scripted use.
    
    Examples:
    
        packmin  # Interactive mode
        
        packmin -d "Paris, France" -s 2025-06-01 -e 2025-06-07 -g male -a 30
    """
    # Load and validate config
    config = get_config()
    errors = config.validate()
    if errors:
        click.echo("❌ Configuration errors:", err=True)
        for error in errors:
            click.echo(f"   - {error}", err=True)
        click.echo("\nSet environment variables or create a .env file.", err=True)
        sys.exit(1)
    
    click.echo(f"🎒 PackMin - Using {config.ai_provider.upper()} AI")
    
    # Determine if we should use interactive mode
    has_required = destination and start_date and end_date
    use_interactive = interactive or not has_required
    
    if use_interactive:
        # Interactive mode
        destinations = interactive_destinations()
        traveler = interactive_traveler()
        trip_info = interactive_trip_details(destinations, traveler)
    else:
        # Non-interactive mode
        if len(destination) != len(start_date) or len(destination) != len(end_date):
            click.echo("❌ Must provide equal numbers of --destination, --start-date, and --end-date", err=True)
            sys.exit(1)
        
        destinations = []
        for dest, start, end in zip(destination, start_date, end_date):
            try:
                destinations.append(TripDestination(
                    location=dest,
                    start_date=parse_date(start).date(),
                    end_date=parse_date(end).date(),
                ))
            except ValueError as e:
                click.echo(f"❌ Invalid date format: {e}", err=True)
                sys.exit(1)
        
        traveler = TravelerInfo(
            gender=gender or "",
            age=age,
            clothing_size=size or "",
            shoe_size=shoe_size or "",
            sleepwear=sleepwear,
        )
        
        # Resolve luggage volume
        final_volume = 39.0
        if volume:
            final_volume = volume
        elif luggage_name:
            click.echo(f"🔍 Looking up volume for '{luggage_name}'...")
            final_volume = estimate_luggage_volume(luggage_name)
            click.echo(f"   Found/Estimated: {final_volume}L")
        
        trip_info = TripInfo(
            destinations=destinations,
            traveler=traveler,
            activities=activities or "",
            additional_notes=notes or "",
            laundry=LaundryInfo(available=laundry),
            luggage_volume_liters=final_volume,
            luggage_name=luggage_name or "",
        )
    
    # Fetch weather data
    click.echo("\n🌤️  Fetching weather data...")
    weather_data = {}
    for dest in trip_info.destinations:
        weather = get_weather_data(
            dest.location,
            datetime.combine(dest.start_date, datetime.min.time()),
            datetime.combine(dest.end_date, datetime.min.time()),
        )
        weather_data[dest.location] = weather
        status = "📊 seasonal" if weather.is_seasonal_estimate else "✓ forecast"
        click.echo(f"   {dest.location}: {status}")
    
    # Build prompt and generate
    prompt = build_prompt(trip_info, weather_data)
    
    if debug:
        click.echo("\n--- DEBUG: Prompt ---")
        click.echo(prompt)
        click.echo("--- END Prompt ---\n")
    
    click.echo("\n🤖 Generating packing list...")
    
    try:
        packing_list = generate_packing_list(prompt, config)
    except Exception as e:
        click.echo(f"❌ AI generation failed: {e}", err=True)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    # Display results
    if packing_list.total_clothes:
        print_packing_list(packing_list)
    else:
        click.echo("\n📋 Raw AI Response:")
        click.echo(packing_list.raw_response)
    
    # Save options
    if output_format or output:
        fmt = output_format or "txt"
        filepath = save_packing_list(
            packing_list,
            trip_info,
            fmt,
            Path(output) if output else None,
        )
        click.echo(f"\n💾 Saved to {filepath}")
    elif use_interactive:
        click.echo("\n💾 Save packing list?")
        click.echo("   1. Plain text (.txt)")
        click.echo("   2. Markdown (.md)")
        click.echo("   3. CSV (for todo apps)")
        click.echo("   Enter to skip")
        
        choice = click.prompt("Choose format", default="", show_default=False)
        
        format_map = {"1": "txt", "2": "md", "3": "csv"}
        if choice in format_map:
            filepath = save_packing_list(packing_list, trip_info, format_map[choice])
            click.echo(f"   ✓ Saved to {filepath}")


if __name__ == "__main__":
    main()
