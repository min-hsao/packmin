"""AI provider implementations for OpenAI and DeepSeek."""

import json
import re
from typing import Optional

import requests

from .config import Config, get_config
from .models import PackingCube, PackingItem, PackingList, PackingTotals


SYSTEM_PROMPT = "You are a travel packing expert who creates efficient, comprehensive packing lists using capsule wardrobe principles."


class AIProvider:
    """Base class for AI providers."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
    
    def generate(self, prompt: str) -> str:
        """Generate a response from the AI model."""
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""
    
    def generate(self, prompt: str) -> str:
        """Generate response using OpenAI API."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.config.openai_api_key)
            
            response = client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=4096,
            )
            
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content or ""
            return ""
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")


class DeepSeekProvider(AIProvider):
    """DeepSeek API provider."""
    
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    def generate(self, prompt: str) -> str:
        """Generate response using DeepSeek API."""
        headers = {
            "Authorization": f"Bearer {self.config.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": self.config.deepseek_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
        }
        
        try:
            response = requests.post(self.API_URL, headers=headers, json=data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("choices"):
                    return result["choices"][0].get("message", {}).get("content", "")
            
            raise RuntimeError(f"DeepSeek API error: {response.status_code} - {response.text}")
            
        except requests.RequestException as e:
            raise RuntimeError(f"DeepSeek API request failed: {e}")


def get_provider(config: Optional[Config] = None) -> AIProvider:
    """Get the appropriate AI provider based on config."""
    config = config or get_config()
    
    if config.ai_provider == "openai":
        return OpenAIProvider(config)
    return DeepSeekProvider(config)


def extract_json_block(text: str) -> Optional[dict]:
    """Extract PARSEABLE_JSON block from AI response."""
    try:
        match = re.search(
            r"PARSEABLE_JSON_START\s*(\{.*?\})\s*PARSEABLE_JSON_END",
            text,
            re.DOTALL,
        )
        if match:
            return json.loads(match.group(1))
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


def parse_packing_list(raw_response: str) -> PackingList:
    """Parse AI response into a structured PackingList."""
    packing_list = PackingList(raw_response=raw_response)
    
    parsed = extract_json_block(raw_response)
    if not parsed:
        return packing_list
    
    # Parse total clothes
    for item in parsed.get("total_clothes", []):
        packing_list.total_clothes.append(PackingItem(
            name=item.get("name", ""),
            quantity=int(item.get("qty", 1)),
            per_item_volume_l=float(item.get("per_item_volume_l", 0)),
            total_volume_l=float(item.get("total_volume_l", 0)),
            description=item.get("description", ""),
        ))
    
    # Parse worn on departure
    for item in parsed.get("worn_on_departure", []):
        packing_list.worn_on_departure.append(PackingItem(
            name=item.get("name", ""),
            quantity=int(item.get("qty", 1)),
            per_item_volume_l=float(item.get("per_item_volume_l", 0)),
            total_volume_l=float(item.get("total_volume_l", 0)),
            description=item.get("description", ""),
        ))
    
    # Parse packed in luggage
    for item in parsed.get("packed_in_luggage", []):
        packing_list.packed_in_luggage.append(PackingItem(
            name=item.get("name", ""),
            quantity=int(item.get("qty", 1)),
            per_item_volume_l=float(item.get("per_item_volume_l", 0)),
            total_volume_l=float(item.get("total_volume_l", 0)),
            description=item.get("description", ""),
        ))
    
    # Parse packing cubes
    for cube in parsed.get("packing_cubes", []):
        packing_list.packing_cubes.append(PackingCube(
            name=cube.get("cube", ""),
            items=cube.get("items", []),
            total_volume_l=float(cube.get("total_volume_l", 0)),
        ))
    
    # Parse totals
    totals = parsed.get("totals", {})
    if totals:
        packing_list.totals = PackingTotals(
            estimated_volume_l=float(totals.get("estimated_volume_l", 0)),
            percent_of_capacity=float(totals.get("percent_of_capacity", 0)),
            estimated_weight_kg=float(totals.get("estimated_weight_kg", 0)),
        )
    
    return packing_list


def generate_packing_list(prompt: str, config: Optional[Config] = None) -> PackingList:
    """Generate a packing list from the given prompt."""
    provider = get_provider(config)
    raw_response = provider.generate(prompt)
    return parse_packing_list(raw_response)
