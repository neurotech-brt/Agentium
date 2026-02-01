"""
Universal Model Provider Service for Agentium.
Supports ANY OpenAI-compatible API provider.
"""

import os
import time
import json
from typing import Optional, Dict, Any, AsyncGenerator, List
from abc import ABC, abstractmethod
from datetime import datetime

from backend.models.database import get_db_context
from backend.models.entities.user_config import UserModelConfig, ProviderType, ModelUsageLog


class BaseModelProvider(ABC):
    """Abstract base for all model providers."""
    
    def __init__(self, config: UserModelConfig):
        self.config = config
        self.api_key = self._get_api_key() if config.requires_api_key() else None
        self.base_url = config.get_effective_base_url()
    
    def _get_api_key(self) -> Optional[str]:
        """Decrypt API key."""
        if not self.config.api_key_encrypted:
            return None
        from backend.core.security import decrypt_api_key
        try:
            return decrypt_api_key(self.config.api_key_encrypted)
        except:
            return None
    
    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def stream_generate(self, system_prompt: str, user_message: str, **kwargs) -> AsyncGenerator[str, None]:
        pass
    
    async def _log_usage(self, tokens: int, latency: int, success: bool, error: str = None):
        """Log usage."""
        with get_db_context() as db:
            self.config.increment_usage(tokens)
            
            # Estimate cost (rough approximation)
            cost = self._estimate_cost(tokens)
            
            db.add(ModelUsageLog(
                config_id=self.config.id,
                provider=self.config.provider,
                model_used=self.config.default_model,
                total_tokens=tokens,
                latency_ms=latency,
                success=success,
                error_message=error,
                cost_usd=cost,
                request_type="chat"
            ))
            db.commit()
    
    def _estimate_cost(self, tokens: int) -> float:
        """Rough cost estimation per provider."""
        # Approximate costs per 1K tokens
        costs = {
            ProviderType.OPENAI: 0.03,      # GPT-4
            ProviderType.ANTHROPIC: 0.03,   # Claude-3
            ProviderType.GROQ: 0.0005,      # Very cheap
            ProviderType.MISTRAL: 0.002,    # Mistral medium
            ProviderType.TOGETHER: 0.001,   # Competitive
            ProviderType.LOCAL: 0.0,        # Free
            ProviderType.CUSTOM: 0.001,     # Assume competitive
        }
        rate = costs.get(self.config.provider, 0.01)
        return (tokens / 1000) * rate


class OpenAICompatibleProvider(BaseModelProvider):
    """
    Universal provider for ANY OpenAI-compatible API.
    Works with Groq, Mistral, Together, Fireworks, Local models, etc.
    """
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        import openai
        
        client = openai.AsyncOpenAI(
            api_key=self.api_key or "not-needed",
            base_url=self.base_url,
            timeout=self.config.timeout_seconds
        )
        
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
                top_p=kwargs.get('top_p', self.config.top_p),
            )
            
            latency = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            await self._log_usage(tokens, latency, success=True)
            
            return {
                "content": content,
                "tokens_used": tokens,
                "latency_ms": latency,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            await self._log_usage(0, 0, success=False, error=str(e))
            raise
    
    async def stream_generate(self, system_prompt: str, user_message: str, **kwargs):
        import openai
        
        client = openai.AsyncOpenAI(
            api_key=self.api_key or "not-needed",
            base_url=self.base_url,
            timeout=self.config.timeout_seconds
        )
        
        stream = await client.chat.completions.create(
            model=kwargs.get('model', self.config.default_model),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=True,
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            temperature=kwargs.get('temperature', self.config.temperature),
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(BaseModelProvider):
    """Anthropic Claude API."""
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        import anthropic
        
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
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
        
        return {
            "content": content,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens if response.usage else 0,
            "latency_ms": latency,
            "model": response.model
        }
    
    async def stream_generate(self, system_prompt: str, user_message: str, **kwargs):
        import anthropic
        
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        async with client.messages.stream(
            model=kwargs.get('model', self.config.default_model),
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            temperature=kwargs.get('temperature', self.config.temperature),
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        ) as stream:
            async for text in stream.text_stream:
                yield text


class GeminiProvider(BaseModelProvider):
    """Google Gemini API."""
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        # Gemini uses different client, but we can use OpenAI compatibility layer
        # or native gemini library. Using OpenAI compat for simplicity:
        import openai
        
        client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=self.config.timeout_seconds
        )
        
        start_time = time.time()
        response = await client.chat.completions.create(
            model=kwargs.get('model', self.config.default_model),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
        )
        
        latency = int((time.time() - start_time) * 1000)
        
        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
            "latency_ms": latency,
            "model": response.model
        }
    
    async def stream_generate(self, system_prompt: str, user_message: str, **kwargs):
        import openai
        
        client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        stream = await client.chat.completions.create(
            model=kwargs.get('model', self.config.default_model),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=True,
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LocalProvider(OpenAICompatibleProvider):
    """Local models via Ollama, llama.cpp, LM Studio, etc."""
    
    async def generate(self, system_prompt: str, user_message: str, **kwargs) -> Dict[str, Any]:
        # Local models might not support system prompts the same way
        # Combine system + user for compatibility
        combined_prompt = f"{system_prompt}\n\nUser: {user_message}"
        
        import openai
        
        client = openai.AsyncOpenAI(
            base_url=self.base_url or "http://localhost:11434/v1",
            api_key="ollama"  # Required but ignored by most local servers
        )
        
        start_time = time.time()
        try:
            response = await client.chat.completions.create(
                model=self.config.default_model,
                messages=[{"role": "user", "content": combined_prompt}],
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
            )
            
            latency = int((time.time() - start_time) * 1000)
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else len(combined_prompt.split()) + len(response.choices[0].message.content.split()),
                "latency_ms": latency,
                "model": response.model or self.config.default_model
            }
        except Exception as e:
            # Fallback for non-OpenAI-compatible local servers
            return await self._fallback_local_generate(system_prompt, user_message, kwargs)
    
    async def _fallback_local_generate(self, system_prompt, user_message, kwargs):
        """Fallback for raw HTTP local servers."""
        import aiohttp
        
        url = f"{self.base_url}/generate" if self.base_url else "http://localhost:11434/api/generate"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "model": self.config.default_model,
                "prompt": f"{system_prompt}\n\nUser: {user_message}\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.config.temperature),
                    "num_predict": kwargs.get('max_tokens', self.config.max_tokens)
                }
            }) as response:
                data = await response.json()
                return {
                    "content": data.get('response', ''),
                    "tokens_used": data.get('eval_count', 0),
                    "latency_ms": 0,
                    "model": self.config.default_model
                }


# Provider factory - UNIVERSAL mapping
PROVIDERS = {
    # Specific providers with special handling
    ProviderType.ANTHROPIC: AnthropicProvider,
    ProviderType.GEMINI: GeminiProvider,
    
    # All others use OpenAI-compatible endpoint
    ProviderType.OPENAI: OpenAICompatibleProvider,
    ProviderType.GROQ: OpenAICompatibleProvider,
    ProviderType.MISTRAL: OpenAICompatibleProvider,
    ProviderType.COHERE: OpenAICompatibleProvider,
    ProviderType.TOGETHER: OpenAICompatibleProvider,
    ProviderType.FIREWORKS: OpenAICompatibleProvider,
    ProviderType.PERPLEXITY: OpenAICompatibleProvider,
    ProviderType.AI21: OpenAICompatibleProvider,
    ProviderType.MOONSHOT: OpenAICompatibleProvider,
    ProviderType.DEEPSEEK: OpenAICompatibleProvider,
    ProviderType.QIANWEN: OpenAICompatibleProvider,
    ProviderType.ZHIPU: OpenAICompatibleProvider,
    ProviderType.AZURE_OPENAI: OpenAICompatibleProvider,
    ProviderType.CUSTOM: OpenAICompatibleProvider,
    ProviderType.OPENAI_COMPATIBLE: OpenAICompatibleProvider,
    ProviderType.LOCAL: LocalProvider,
}


class ModelService:
    """Service to manage model interactions with any provider."""
    
    @staticmethod
    async def get_provider(user_id: str, preferred_config_id: Optional[str] = None) -> Optional[BaseModelProvider]:
        """Get provider instance for user."""
        with get_db_context() as db:
            if preferred_config_id:
                config = db.query(UserModelConfig).filter_by(
                    id=preferred_config_id, 
                    user_id=user_id,
                    status='active'
                ).first()
            else:
                # Get default config
                config = db.query(UserModelConfig).filter_by(
                    user_id=user_id,
                    is_default=True,
                    status='active'
                ).first()
            
            if not config:
                return None
            
            provider_class = PROVIDERS.get(config.provider)
            if not provider_class:
                raise ValueError(f"Unknown provider: {config.provider}")
            
            return provider_class(config)
    
    @staticmethod
    async def generate_with_agent(
        agent, 
        user_message: str, 
        user_id: str = "sovereign",
        config_id: Optional[str] = None,
        system_prompt_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using agent's ethos and user-selected model."""
        provider = await ModelService.get_provider(user_id, config_id)
        
        if not provider:
            raise ValueError("No active model configuration found. Please configure in settings.")
        
        # Get system prompt from agent's ethos
        system_prompt = system_prompt_override or (
            agent.ethos.mission_statement if agent.ethos else "You are an AI assistant."
        )
        
        # Add behavioral rules to system prompt
        if agent.ethos:
            import json
            try:
                rules = json.loads(agent.ethos.behavioral_rules) if agent.ethos.behavioral_rules else []
                if rules:
                    system_prompt += "\n\nBehavioral Rules:\n" + "\n".join(f"- {r}" for r in rules[:10])  # Limit rules
            except:
                pass
        
        return await provider.generate(system_prompt, user_message)
    
    @staticmethod
    async def test_connection(config: UserModelConfig) -> Dict[str, Any]:
        """Test any provider configuration."""
        try:
            provider_class = PROVIDERS.get(config.provider)
            if not provider_class:
                return {"success": False, "error": f"Unknown provider: {config.provider}"}
            
            provider = provider_class(config)
            
            # Test with simple prompt
            result = await provider.generate(
                "You are a test assistant.",
                "Say 'Connection successful' and nothing else.",
                max_tokens=20
            )
            
            success = "successful" in result['content'].lower() or len(result['content']) > 0
            config.mark_tested(success)
            
            return {
                "success": success,
                "latency_ms": result['latency_ms'],
                "model": result['model'],
                "response": result['content'][:100],
                "tokens": result['tokens_used']
            }
            
        except Exception as e:
            config.mark_tested(False, str(e))
            return {
                "success": False,
                "error": str(e)[:200]
            }
    
    @staticmethod
    async def list_models_for_provider(provider: ProviderType, api_key: Optional[str] = None, base_url: Optional[str] = None) -> List[str]:
        """Fetch available models from provider API."""
        try:
            if provider == ProviderType.OPENAI and api_key:
                import openai
                client = openai.AsyncOpenAI(api_key=api_key)
                models = await client.models.list()
                return [m.id for m in models.data if "gpt" in m.id or "text-" in m.id]
            
            elif provider == ProviderType.GROQ and api_key:
                import openai
                client = openai.AsyncOpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
                models = await client.models.list()
                return [m.id for m in models.data]
            
            elif provider == ProviderType.LOCAL:
                # Try Ollama
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base_url or 'http://localhost:11434'}/api/tags") as resp:
                        data = await resp.json()
                        return [m['name'] for m in data.get('models', [])]
            
            # Default: return common models
            default_models = {
                ProviderType.OPENAI: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                ProviderType.ANTHROPIC: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                ProviderType.GROQ: ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
                ProviderType.MISTRAL: ["mistral-large", "mistral-medium", "mistral-small"],
                ProviderType.TOGETHER: ["meta-llama/Llama-3-70b", "mistralai/Mixtral-8x7B"],
                ProviderType.GEMINI: ["gemini-pro", "gemini-pro-vision"],
                ProviderType.MOONSHOT: ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                ProviderType.LOCAL: ["llama3", "mistral", "mixtral", "qwen2"],
            }
            return default_models.get(provider, ["custom-model"])
            
        except Exception as e:
            print(f"Error listing models for {provider}: {e}")
            return ["model-1", "model-2"]  # Fallback