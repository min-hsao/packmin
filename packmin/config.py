"""Configuration handling via environment variables with .env fallback."""

import os
from dataclasses import dataclass
from typing import Literal, Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment."""
    
    # AI Provider settings
    ai_provider: Literal["openai", "deepseek", "glm", "gemini", "anthropic"] = "deepseek"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    
    # DeepSeek
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    
    # GLM (ZhipuAI)
    glm_api_key: Optional[str] = None
    glm_model: str = "glm-4"
    
    # Google Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"
    
    # Anthropic Claude
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-sonnet-20240229"
    
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
        if ai_provider not in ("openai", "deepseek", "glm", "gemini", "anthropic"):
            ai_provider = "deepseek"
        
        return cls(
            ai_provider=ai_provider,
            # OpenAI
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            # DeepSeek
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            # GLM
            glm_api_key=os.getenv("GLM_API_KEY"),
            glm_model=os.getenv("GLM_MODEL", "glm-4"),
            # Gemini
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-pro"),
            # Anthropic
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            # Weather
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
            # Defaults
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
        
        if self.ai_provider == "glm" and not self.glm_api_key:
            errors.append("GLM_API_KEY is required when using GLM provider")
        
        if self.ai_provider == "gemini" and not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required when using Gemini provider")
        
        if self.ai_provider == "anthropic" and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")
        
        return errors
    
    def get_active_api_key(self) -> str:
        """Get the API key for the active provider."""
        keys = {
            "openai": self.openai_api_key,
            "deepseek": self.deepseek_api_key,
            "glm": self.glm_api_key,
            "gemini": self.gemini_api_key,
            "anthropic": self.anthropic_api_key,
        }
        return keys.get(self.ai_provider, "") or ""
    
    def get_active_model(self) -> str:
        """Get the model name for the active provider."""
        models = {
            "openai": self.openai_model,
            "deepseek": self.deepseek_model,
            "glm": self.glm_model,
            "gemini": self.gemini_model,
            "anthropic": self.anthropic_model,
        }
        return models.get(self.ai_provider, self.deepseek_model)


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
