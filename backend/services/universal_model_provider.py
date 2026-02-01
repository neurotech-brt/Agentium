"""
Universal Model Provider - supports ANY API endpoint.
Uses adapter pattern for OpenAI-compatible, Anthropic, Google, and custom formats.
"""

import os
import time
import json
from typing import Optional, Dict, Any, AsyncGenerator, Callable
from abc import ABC, abstractmethod
from datetime import datetime

import aiohttp
import requests
from jmespath import search as json_search

from backend.models.database import get_db_context
from backend.models.entities.user_config import UserModelConfig, ModelUsageLog


class BaseModelProvider(ABC):
    """Abstract base for all model providers."""
    
    def __init__(self, config: UserModelConfig):
        self.config = config
        self.api_key = self._decrypt_key(config.api_key_encrypted) if config.api_key_encrypted else None
        self.api_secret = self._decrypt_key(config.api_secret_encrypted) if config.api_secret_encrypted else None
    
    def _decrypt_key(self, encrypted: str) -> str:
        """Decrypt API key."""
        # TODO: Implement Fernet decryption
        return encrypted
    
    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        pass
    
    async def _make_request(self, url: str, headers: Dict, payload: Dict) -> Dict[str, Any]:
        """Universal HTTP request handler."""
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url, 
                    headers=headers, 
                    json=payload,
                    timeout=self.config.timeout_seconds
                ) as response:
                    latency = int((time.time() - start_time) * 1000)
                    
                    if response.status != 200:
                        error_text = await response.text()
                        await self._log_usage(0, latency, False, error_text)
                        raise Exception(f"API Error {response.status}: {error_text}")
                    
                    data = await response.json()
                    return data, latency
                    
            except aiohttp.ClientError as e:
                await self._log_usage(0, 0, False, str(e))
                raise
    
    async def _log_usage(self, tokens: int, latency: int, success: bool, error: str = None, cost: float = 0.0):
        """Log usage to database."""
        with get_db_context() as db:
            self.config.increment_usage(tokens, cost)
            
            db.add(ModelUsageLog(
                config_id=self.config.id,
                provider_name=self.config.provider_name,
                model_used=self.config.default_model,
                total_tokens=tokens,
                latency_ms=latency,
                success=success,
                error_message=error,
                cost_usd=cost
            ))
            db.commit()
    
    def _extract_text(self, response: Dict) -> str:
        """Extract text using configured JSON path."""
        path = self.config.response_path or "choices.0.message.content"
        result = json_search(response, path)
        return result if result else str(response)


class OpenAICompatibleProvider(BaseModelProvider):
    """Universal OpenAI-compatible provider (Groq, Mistral, Kimi, Together, Fireworks, etc.)."""
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        import openai
        
        # Build client with custom base URL if provided
        client_kwargs = {"api_key": self.api_key}
        if self.config.base_url:
            client_kwargs["base_url"] = self.config.base_url
        
        client = openai.AsyncOpenAI(**client_kwargs)
        
        start_time = time.time()
        
        try:
            response = await client.chat.completions.create(
                model=kwargs.get('model', self.config.default_model),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                timeout=self.config.timeout_seconds
            )
            
            latency = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            # Estimate cost (simplified)
            cost = self._estimate_cost(tokens)
            await self._log_usage(tokens, latency, True, cost=cost)
            
            return {
                "content": content,
                "tokens_used": tokens,
                "latency_ms": latency,
                "model": response.model,
                "cost_usd": cost
            }
            
        except Exception as e:
            await self._log_usage(0, 0, False, str(e))
            raise
    
    def _estimate_cost(self, tokens: int) -> float:
        """Rough cost estimation per provider."""
        rates = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.0015,
            "claude-3-opus": 0.015,
            "llama3-70b": 0.0009,  # Groq
            "mixtral-8x22b": 0.002,  # Mistral
        }
        model = self.config.default_model.lower()
        rate = next((r for m, r in rates.items() if m in model), 0.01)
        return (tokens / 1000) * rate


class AnthropicProvider(BaseModelProvider):
    """Anthropic Claude - native API."""
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        import anthropic
        
        client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.config.base_url  # Optional custom endpoint
        )
        
        start_time = time.time()
        
        response = await client.messages.create(
            model=kwargs.get('model', self.config.default_model),
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            temperature=kwargs.get('temperature', self.config.temperature),
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        
        latency = int((time.time() - start_time) * 1000)
        content = response.content[0].text if response.content else ""
        tokens = response.usage.input_tokens + response.usage.output_tokens if response.usage else 0
        cost = (tokens / 1000) * 0.008  # Claude 3 Sonnet rate
        
        await self._log_usage(tokens, latency, True, cost=cost)
        
        return {
            "content": content,
            "tokens_used": tokens,
            "latency_ms": latency,
            "model": response.model,
            "cost_usd": cost
        }


class GoogleProvider(BaseModelProvider):
    """Google Gemini / Vertex AI."""
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        # Google uses different API structure
        url = self.config.base_url or "https://generativelanguage.googleapis.com/v1beta"
        endpoint = f"{url}/models/{self.config.default_model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": system_prompt + "\n\n" + user_message}
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": kwargs.get('max_tokens', self.config.max_tokens),
                "temperature": kwargs.get('temperature', self.config.temperature)
            }
        }
        
        data, latency = await self._make_request(endpoint, headers, payload)
        
        # Extract text from Google format
        content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
        cost = (tokens / 1000) * 0.0005  # Gemini Pro rate
        
        await self._log_usage(tokens, latency, True, cost=cost)
        
        return {
            "content": content,
            "tokens_used": tokens,
            "latency_ms": latency,
            "model": self.config.default_model,
            "cost_usd": cost
        }


class AzureOpenAIProvider(BaseModelProvider):
    """Microsoft Azure OpenAI Service."""
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        import openai
        
        # Azure requires api_version and different base URL
        client = openai.AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.config.base_url,
            api_version=self.config.api_version or "2024-02-15-preview"
        )
        
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model=self.config.default_model,  # deployment name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens)
        )
        
        latency = int((time.time() - start_time) * 1000)
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        await self._log_usage(tokens, latency, True)
        
        return {
            "content": content,
            "tokens_used": tokens,
            "latency_ms": latency,
            "model": response.model
        }


class GenericHTTPProvider(BaseModelProvider):
    """Generic provider for any HTTP API with configurable request/response format."""
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        # Build custom payload from template
        payload_template = self.config.request_format or {
            "prompt": "{system}\n\n{user}",
            "max_tokens": "{max_tokens}",
            "temperature": "{temperature}"
        }
        
        # Format payload
        payload = self._format_payload(payload_template, {
            "system": system_prompt,
            "user": user_message,
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "temperature": kwargs.get('temperature', self.config.temperature)
        })
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            **self.config.custom_headers
        }
        
        data, latency = await self._make_request(
            self.config.base_url, 
            headers, 
            payload
        )
        
        content = self._extract_text(data)
        tokens = self._estimate_tokens(content)  # Fallback estimation
        
        await self._log_usage(tokens, latency, True)
        
        return {
            "content": content,
            "tokens_used": tokens,
            "latency_ms": latency,
            "model": self.config.default_model
        }
    
    def _format_payload(self, template: Dict, values: Dict) -> Dict:
        """Replace template placeholders with values."""
        payload = json.dumps(template)
        for key, val in values.items():
            payload = payload.replace(f"{{{key}}}", str(val))
        return json.loads(payload)
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation."""
        return len(text.split()) * 1.3  # Rough approximation


# Provider factory mapping
PROVIDER_REGISTRY = {
    "openai": OpenAICompatibleProvider,
    "anthropic": AnthropicProvider,
    "claude": AnthropicProvider,
    "google": GoogleProvider,
    "gemini": GoogleProvider,
    "azure": AzureOpenAIProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "generic": GenericHTTPProvider,
    "custom": GenericHTTPProvider
}


class UniversalModelService:
    """Universal service to route to any configured provider."""
    
    @staticmethod
    def get_provider(config: UserModelConfig) -> BaseModelProvider:
        """Get appropriate provider for config."""
        # Try explicit provider type
        provider_class = PROVIDER_REGISTRY.get(config.provider_type)
        
        if not provider_class:
            # Fallback to provider name matching
            provider_class = PROVIDER_REGISTRY.get(config.provider_name.lower())
        
        if not provider_class:
            # Default to OpenAI-compatible (most common)
            provider_class = OpenAICompatibleProvider
        
        return provider_class(config)
    
    @staticmethod
    async def test_connection(config: UserModelConfig) -> Dict[str, Any]:
        """Test any provider configuration."""
        try:
            provider = UniversalModelService.get_provider(config)
            
            result = await provider.generate(
                "You are a helpful assistant.",
                "Say 'Connection successful' and nothing else.",
                max_tokens=20
            )
            
            success = "successful" in result['content'].lower()
            config.mark_tested(success)
            
            return {
                "success": success,
                "latency_ms": result['latency_ms'],
                "model": result['model'],
                "response": result['content'][:100],
                "provider_type": config.provider_type
            }
            
        except Exception as e:
            config.mark_tested(False, str(e))
            return {
                "success": False,
                "error": str(e),
                "provider_type": config.provider_type
            }
    
    @staticmethod
    async def generate_with_agent(agent, user_message: str, config_id: Optional[str] = None, db=None):
        """Generate using agent's preferred config or default."""
        if not db:
            from backend.models.database import get_db_context
            with get_db_context() as db:
                return await UniversalModelService._do_generate(agent, user_message, config_id, db)
        return await UniversalModelService._do_generate(agent, user_message, config_id, db)
    
    @staticmethod
    async def _do_generate(agent, user_message: str, config_id: Optional[str], db):
        """Internal generate method."""
        # Get config
        from backend.models.entities.user_config import UserModelConfig
        
        if config_id:
            config = db.query(UserModelConfig).filter_by(
                id=config_id, 
                user_id="sovereign",
                status='active'
            ).first()
        else:
            config = agent.preferred_config
        
        if not config:
            raise ValueError("No active model configuration. Please configure a provider in settings.")
        
        # Get provider and generate
        provider = UniversalModelService.get_provider(config)
        
        system_prompt = agent.ethos.mission_statement if agent.ethos else "You are an AI assistant."
        
        # Add behavioral rules
        if agent.ethos:
            import json
            rules = json.loads(agent.ethos.behavioral_rules) if agent.ethos.behavioral_rules else []
            if rules:
                system_prompt += "\n\nRules:\n" + "\n".join(f"- {r}" for r in rules)
        
        result = await provider.generate(system_prompt, user_message)
        return result
    
    @staticmethod
    def discover_models(config: UserModelConfig) -> list:
        """Auto-discover available models from provider."""
        try:
            if config.provider_type in ["openai", "openai_compatible"]:
                import openai
                client = openai.OpenAI(
                    api_key=config.api_key_encrypted,  # Should decrypt
                    base_url=config.base_url
                )
                models = client.models.list()
                return [m.id for m in models.data]
            
            # Add other provider discovery logic
            return []
        except Exception as e:
            return []


# Backwards compatibility
ModelService = UniversalModelService