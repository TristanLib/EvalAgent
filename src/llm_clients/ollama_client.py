"""Ollama API client implementation"""

import time
import json
from typing import Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_client import BaseLLMClient
from ..models import Problem, GeneratedCode, LLMConfig


class OllamaClient(BaseLLMClient):
    """Ollama API client for code generation with local models"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url.rstrip('/')
        self.session = requests.Session()
        # Set default timeout for requests
        self.session.timeout = config.timeout
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_code(self, problem: Problem, attempt_number: int = 1) -> GeneratedCode:
        """Generate code using Ollama API"""
        start_time = time.time()
        
        prompt = self._create_prompt(problem)
        
        try:
            # Check if model is available
            if not self._is_model_available():
                raise Exception(f"Model {self.config.model_id} is not available on Ollama server")
            
            # Prepare request payload
            payload = {
                "model": self.config.model_id,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                }
            }
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            generation_time = time.time() - start_time
            
            # Parse response
            result = response.json()
            generated_text = result.get('response', '')
            
            # Extract code from response
            code = self._extract_code_from_response(generated_text)
            
            # Estimate token usage (Ollama doesn't provide exact counts)
            tokens_used = self._count_tokens(generated_text)
            
            return GeneratedCode(
                code=code,
                model_name=self.config.name,
                problem_id=problem.id,
                generation_time=generation_time,
                tokens_used=tokens_used,
                temperature=self.config.temperature,
                attempt_number=attempt_number
            )
            
        except requests.exceptions.Timeout:
            generation_time = time.time() - start_time
            raise Exception(f"Ollama request timed out after {self.config.timeout}s")
            
        except requests.exceptions.ConnectionError:
            generation_time = time.time() - start_time
            raise Exception(f"Cannot connect to Ollama server at {self.base_url}")
            
        except Exception as e:
            generation_time = time.time() - start_time
            
            # Return empty code on failure
            return GeneratedCode(
                code="",
                model_name=self.config.name,
                problem_id=problem.id,
                generation_time=generation_time,
                tokens_used=0,
                temperature=self.config.temperature,
                attempt_number=attempt_number
            )
    
    def _is_model_available(self) -> bool:
        """Check if the model is available on the Ollama server"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            # Check if our model is in the list (handle both exact match and tag variations)
            model_id = self.config.model_id
            return any(
                model_id == model or model_id in model or model in model_id
                for model in available_models
            )
            
        except Exception:
            # If we can't check, assume it's available and let the generate call fail
            return True
    
    def list_available_models(self) -> list:
        """List all models available on the Ollama server"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            models_data = response.json()
            return [model['name'] for model in models_data.get('models', [])]
            
        except Exception as e:
            print(f"Warning: Could not fetch available models from Ollama: {e}")
            return []
    
    def _create_prompt(self, problem: Problem) -> str:
        """Create a more specific prompt for Ollama models"""
        # Ollama models often work better with more structured prompts
        prompt = f"""You are an expert Python programmer. Solve the following coding problem.

PROBLEM: {problem.title}

DESCRIPTION:
{problem.description}

FUNCTION SIGNATURE:
{problem.function_signature}

REQUIREMENTS:
{problem.docstring}

INSTRUCTIONS:
- Implement the function according to the requirements
- Write clean, efficient Python code
- Handle edge cases appropriately
- Return only the function implementation
- Do not include test cases or examples
- Do not include explanations or comments

RESPONSE FORMAT:
Provide only the Python function implementation without any markdown formatting or additional text.

SOLUTION:"""
        
        return prompt
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model to the Ollama server if not available"""
        try:
            print(f"Pulling model {model_name} to Ollama server...")
            
            payload = {"name": model_name}
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=300  # 5 minutes timeout for model pulling
            )
            
            response.raise_for_status()
            print(f"Successfully pulled model {model_name}")
            return True
            
        except Exception as e:
            print(f"Failed to pull model {model_name}: {e}")
            return False
    
    def check_server_status(self) -> dict:
        """Check Ollama server status and information"""
        try:
            # Check if server is running
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            return {
                "status": "running",
                "url": self.base_url,
                "available_models": available_models,
                "model_count": len(available_models)
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "status": "offline",
                "url": self.base_url,
                "error": "Cannot connect to Ollama server"
            }
        except Exception as e:
            return {
                "status": "error",
                "url": self.base_url,
                "error": str(e)
            }