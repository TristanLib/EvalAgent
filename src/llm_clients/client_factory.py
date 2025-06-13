"""Factory for creating LLM clients"""

from typing import Dict, Type
from .base_client import BaseLLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from ..models import LLMConfig


class LLMClientFactory:
    """Factory class for creating LLM clients"""
    
    def __init__(self):
        self._clients: Dict[str, Type[BaseLLMClient]] = {
            'openai': OpenAIClient,
            'anthropic': AnthropicClient,
        }
    
    def register_client(self, provider: str, client_class: Type[BaseLLMClient]):
        """Register a new client implementation"""
        self._clients[provider] = client_class
    
    def create_client(self, config: LLMConfig) -> BaseLLMClient:
        """Create an LLM client based on configuration"""
        
        # Determine provider from model name or config
        provider = self._detect_provider(config)
        
        if provider not in self._clients:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        client_class = self._clients[provider]
        return client_class(config)
    
    def _detect_provider(self, config: LLMConfig) -> str:
        """Detect provider from configuration"""
        
        # Check if provider is explicitly set in config name
        if 'openai' in config.name.lower() or 'gpt' in config.model_id.lower():
            return 'openai'
        elif 'anthropic' in config.name.lower() or 'claude' in config.model_id.lower():
            return 'anthropic'
        elif 'google' in config.name.lower() or 'gemini' in config.model_id.lower():
            return 'google'
        elif 'cohere' in config.name.lower() or 'command' in config.model_id.lower():
            return 'cohere'
        
        # Check base URL
        if 'openai' in config.base_url:
            return 'openai'
        elif 'anthropic' in config.base_url:
            return 'anthropic'
        
        # Default to OpenAI if unclear
        return 'openai'
    
    def list_supported_providers(self) -> list:
        """List all supported providers"""
        return list(self._clients.keys())