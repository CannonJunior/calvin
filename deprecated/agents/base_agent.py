import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

from app.core.config import settings


class BaseAgent(ABC):
    def __init__(self, model_name: str, max_tokens: int = 1000, temperature: float = 0.7):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.ollama_url = settings.OLLAMA_BASE_URL
        
    async def _call_ollama(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API call to Ollama service"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "response": result.get("message", {}).get("content", ""),
                            "model": result.get("model", self.model_name),
                            "total_duration": result.get("total_duration", 0),
                            "load_duration": result.get("load_duration", 0),
                            "prompt_eval_count": result.get("prompt_eval_count", 0),
                            "eval_count": result.get("eval_count", 0),
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                        
        except Exception as e:
            raise Exception(f"Failed to call Ollama: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if Ollama service is available and model is loaded"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if Ollama is running
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status != 200:
                        return False
                    
                    models = await response.json()
                    model_names = [model["name"] for model in models.get("models", [])]
                    
                    # Check if our model is available
                    return any(self.model_name in name for name in model_names)
                    
        except Exception:
            return False
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return response"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt for this agent"""
        pass