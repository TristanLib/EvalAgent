"""Anthropic API client implementation"""

import time
from typing import Optional
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_client import BaseLLMClient
from ..models import Problem, GeneratedCode, LLMConfig


class AnthropicClient(BaseLLMClient):
    """Anthropic API client for code generation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = anthropic.Anthropic(
            api_key=config.api_key,
            base_url=config.base_url if config.base_url != "https://api.anthropic.com" else None
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_code(self, problem: Problem, attempt_number: int = 1) -> GeneratedCode:
        """Generate code using Anthropic API"""
        start_time = time.time()
        
        prompt = self._create_prompt(problem)
        
        try:
            response = self.client.messages.create(
                model=self.config.model_id,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system="You are an expert Python programmer. Provide only clean, efficient Python code without any explanations or markdown formatting.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            generation_time = time.time() - start_time
            
            # Extract generated code
            generated_text = response.content[0].text
            code = self._extract_code_from_response(generated_text)
            
            # Count tokens (Anthropic doesn't provide token count in response)
            tokens_used = response.usage.input_tokens + response.usage.output_tokens if response.usage else self._count_tokens(generated_text)
            
            return GeneratedCode(
                code=code,
                model_name=self.config.name,
                problem_id=problem.id,
                generation_time=generation_time,
                tokens_used=tokens_used,
                temperature=self.config.temperature,
                attempt_number=attempt_number
            )
            
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