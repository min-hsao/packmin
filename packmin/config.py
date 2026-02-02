"""Configuration handling via environment variables with .env fallback."""

import os
from dataclasses import dataclass
from typing import Literal, Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment."""
    
    # AI Provider settings
    ai_provider: Literal["openai", "deepseek"] = "deepseek"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    
    # Weather API
    openweather_api_key: Optional[str] = None
    
    # Defaults
    default_luggage_volume: float = 39.0
    packing_cube_volume: float = 9.0
    
    @classmethod
    def load(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables.
        
        Checks for .env file in current directory or specified path.
        Environment variables take precedence over .env file.
        """
        # Load .env file if it exists
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()  # Loads .env from current directory if present
        
        # Get AI provider (default to deepseek)
        ai_provider = os.getenv("AI_PROVIDER", "deepseek").lower()
        if ai_provider not in ("openai", "deepseek"):
            ai_provider = "deepseek"
        
        return cls(
            ai_provider=ai_provider,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
            default_luggage_volume=float(os.getenv("DEFAULT_LUGGAGE_VOLUME", "39")),
            packing_cube_volume=float(os.getenv("PACKING_CUBE_VOLUME", "9")),
        )
    
    def validate(self) -> list[str]:
        """Validate required API keys are present. Returns list of errors."""
        errors = []
        
        if not self.openweather_api_key:
            errors.append("OPENWEATHER_API_KEY is required")
        
        if self.ai_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI provider")
        
        if self.ai_provider == "deepseek" and not self.deepseek_api_key:
            errors.append("DEEPSEEK_API_KEY is required when using DeepSeek provider")
        
        return errors
    
    def get_active_api_key(self) -> str:
        """Get the API key for the active provider."""
        if self.ai_provider == "openai":
            return self.openai_api_key or ""
        return self.deepseek_api_key or ""
    
    def get_active_model(self) -> str:
        """Get the model name for the active provider."""
        if self.ai_provider == "openai":
            return self.openai_model
        return self.deepseek_model


# Global config instance (lazy-loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reset_config() -> None:
    """Reset the global config (useful for testing)."""
    global _config
    _config = None
