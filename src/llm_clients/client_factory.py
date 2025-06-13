"""Factory for creating LLM clients"""

from typing import Dict, Type
from .base_client import BaseLLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .ollama_client import OllamaClient
from ..models import LLMConfig


class LLMClientFactory:
    """Factory class for creating LLM clients"""
    
    def __init__(self):
        self._clients: Dict[str, Type[BaseLLMClient]] = {
            'openai': OpenAIClient,
            'anthropic': AnthropicClient,
            'ollama': OllamaClient,
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
        elif 'ollama' in config.name.lower() or 'localhost' in config.base_url or '127.0.0.1' in config.base_url:
            return 'ollama'
        elif 'google' in config.name.lower() or 'gemini' in config.model_id.lower():
            return 'google'
        elif 'cohere' in config.name.lower() or 'command' in config.model_id.lower():
            return 'cohere'
        
        # Check base URL
        if 'openai' in config.base_url:
            return 'openai'
        elif 'anthropic' in config.base_url:
            return 'anthropic'
        elif ':11434' in config.base_url or 'ollama' in config.base_url:
            return 'ollama'
        
        # Check for common Ollama models
        ollama_models = ['llama', 'mistral', 'codellama', 'vicuna', 'alpaca', 'wizard', 'orca']
        if any(model in config.model_id.lower() for model in ollama_models):
            return 'ollama'
        
        # Default to OpenAI if unclear
        return 'openai'
    
    def list_supported_providers(self) -> list:
        """List all supported providers"""
        return list(self._clients.keys())