# 🎒 PackMin

AI-powered minimalist packing list generator using capsule wardrobe principles.

PackMin uses AI (OpenAI or DeepSeek) combined with weather data to generate smart, efficient packing lists that maximize versatility while minimizing what you carry.

## Features

- 🌤️ **Weather-aware** - Fetches real forecast data for your destinations
- 🔄 **Capsule wardrobe** - Maximizes mix-and-match versatility
- 📍 **Multi-destination** - Plan trips with multiple stops
- 🧺 **Laundry-aware** - Adjusts quantities based on laundry access
- 📦 **Volume tracking** - Estimates packing cube needs and luggage fit
- 💾 **Multiple export formats** - TXT, Markdown, CSV (for todo apps)

## Installation

### From source

```bash
git clone https://github.com/minhsao/packmin.git
cd packmin
pip install -e .
```

### Using pip

```bash
pip install -r requirements.txt
pip install -e .
```

## Configuration

PackMin uses environment variables for API keys. Create a `.env` file in your working directory or export them directly.

### Required Environment Variables

```bash
# Weather API (required)
OPENWEATHER_API_KEY=your_openweather_api_key

# AI Provider - choose one
AI_PROVIDER=deepseek  # or "openai"

# DeepSeek API (if using DeepSeek)
DEEPSEEK_API_KEY=your_deepseek_api_key

# OpenAI API (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key
```

### Optional Settings

```bash
# Models (defaults shown)
OPENAI_MODEL=gpt-4-turbo-preview
DEEPSEEK_MODEL=deepseek-chat

# Defaults
DEFAULT_LUGGAGE_VOLUME=39  # liters
PACKING_CUBE_VOLUME=9      # liters
```

### Getting API Keys

1. **OpenWeather**: Sign up at [openweathermap.org](https://openweathermap.org/api) (free tier available)
2. **DeepSeek**: Get key from [platform.deepseek.com](https://platform.deepseek.com)
3. **OpenAI**: Get key from [platform.openai.com](https://platform.openai.com)

## Usage

### Interactive Mode (default)

Simply run `packmin` and follow the prompts:

```bash
packmin
```

The interactive wizard will ask for:
- Destinations with dates
- Traveler info (gender, age, clothing size)
- Activities and special events
- Laundry availability
- Luggage size

### Command-Line Mode

For scripted or quick use, provide flags directly:

```bash
# Single destination
packmin \
  -d "Paris, France" \
  -s 2025-06-01 \
  -e 2025-06-07 \
  -g male \
  -a 30 \
  --activities "sightseeing, nice dinners" \
  --volume 39

# Multiple destinations
packmin \
  -d "Paris, France" -s 2025-06-01 -e 2025-06-03 \
  -d "Rome, Italy" -s 2025-06-04 -e 2025-06-07 \
  -g female \
  --laundry \
  --format md \
  -o my_trip.md
```

### CLI Options

```
Options:
  -d, --destination TEXT    Destination (can be repeated)
  -s, --start-date TEXT     Start date YYYY-MM-DD (pairs with --destination)
  -e, --end-date TEXT       End date YYYY-MM-DD (pairs with --destination)
  -g, --gender TEXT         Traveler gender
  -a, --age INTEGER         Traveler age
  --size TEXT               Clothing size
  --shoe-size TEXT          Shoe size
  --activities TEXT         Activities (comma-separated)
  --laundry / --no-laundry  Laundry available
  -v, --volume FLOAT        Luggage volume in liters [default: 39.0]
  -n, --notes TEXT          Additional notes for AI
  -o, --output PATH         Output file path
  --format [txt|md|csv]     Output format
  --debug                   Enable debug output
  -i, --interactive         Force interactive mode
  --help                    Show this message and exit.
```

## Output Formats

### Text (.txt)
Plain text packing list with all details.

### Markdown (.md)
Formatted markdown suitable for notes apps or documentation.

### CSV (.csv)
Simple format for importing into:
- Microsoft To Do
- Apple Reminders
- Any task manager that accepts CSV

## Development

### Setup

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
ruff check .
ruff format .
```

## Project Structure

```
packmin/
├── packmin/
│   ├── __init__.py     # Package exports
│   ├── cli.py          # Click-based CLI
│   ├── config.py       # Environment config
│   ├── weather.py      # OpenWeather integration
│   ├── ai.py           # AI providers (OpenAI/DeepSeek)
│   ├── prompts.py      # AI prompt templates
│   └── models.py       # Pydantic data models
├── tests/
│   └── test_models.py  # Unit tests
├── pyproject.toml      # Package config
├── requirements.txt    # Dependencies
└── README.md
```

## License

MIT
