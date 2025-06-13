"""OpenAI API client implementation"""

import time
from typing import Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_client import BaseLLMClient
from ..models import Problem, GeneratedCode, LLMConfig


class OpenAIClient(BaseLLMClient):
    """OpenAI API client for code generation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_code(self, problem: Problem, attempt_number: int = 1) -> GeneratedCode:
        """Generate code using OpenAI API"""
        start_time = time.time()
        
        prompt = self._create_prompt(problem)
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_id,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python programmer. Provide only clean, efficient Python code without any explanations or markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
            
            generation_time = time.time() - start_time
            
            # Extract generated code
            generated_text = response.choices[0].message.content
            code = self._extract_code_from_response(generated_text)
            
            # Count tokens
            tokens_used = response.usage.total_tokens if response.usage else self._count_tokens(generated_text)
            
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