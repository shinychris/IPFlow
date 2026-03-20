"""LLM 服务 - 支持多种 AI 提供商 (Ollama, OpenAI, Anthropic)."""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import httpx
from fastapi import HTTPException

from ipflow.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """LLM 消息."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """LLM 响应."""
    content: str
    model: str
    usage: Optional[dict] = None


class BaseLLMProvider(ABC):
    """LLM 提供商基类."""

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    async def chat(self, messages: list[LLMMessage], temperature: float = 0.7) -> LLMResponse:
        """发送聊天请求."""
        pass

    @abstractmethod
    async def stream_chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """流式聊天请求."""
        pass

    @abstractmethod
    async def list_models(self) -> list[dict]:
        """获取可用模型列表."""
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama 提供商."""

    def __init__(self, base_url: str, model: str, timeout: int = 120):
        super().__init__(model)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> LLMResponse:
        """发送聊天请求到 Ollama."""
        try:
            # 转换消息格式
            ollama_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=self.model,
                usage=data.get("usage", {}),
            )
        except httpx.ConnectError as e:
            logger.error(f"无法连接到 Ollama 服务: {e}")
            raise HTTPException(
                status_code=503, detail=f"无法连接到 Ollama 服务 ({self.base_url})，请检查服务是否运行"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API 错误: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ollama API 错误: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Ollama 请求失败: {e}")
            raise HTTPException(status_code=500, detail=f"Ollama 请求失败: {str(e)}")

    async def stream_chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """流式聊天请求到 Ollama."""
        try:
            ollama_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": ollama_messages,
                    "stream": True,
                    "options": {"temperature": temperature},
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as e:
            logger.error(f"无法连接到 Ollama 服务: {e}")
            raise HTTPException(
                status_code=503, detail=f"无法连接到 Ollama 服务 ({self.base_url})"
            )
        except Exception as e:
            logger.error(f"Ollama 流式请求失败: {e}")
            raise HTTPException(status_code=500, detail=f"Ollama 流式请求失败: {str(e)}")

    async def list_models(self) -> list[dict]:
        """获取 Ollama 可用模型列表."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("models", []):
                models.append({
                    "id": model.get("name", ""),
                    "name": model.get("name", ""),
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", ""),
                    "provider": "ollama",
                })
            return models
        except httpx.ConnectError:
            logger.warning(f"无法连接到 Ollama 服务 ({self.base_url})")
            return []
        except Exception as e:
            logger.error(f"获取 Ollama 模型列表失败: {e}")
            return []

    async def pull_model(self, model_name: str) -> dict:
        """拉取 Ollama 模型."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=300,  # 拉取模型可能需要更长时间
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"拉取 Ollama 模型失败: {e}")
            raise HTTPException(status_code=500, detail=f"拉取模型失败: {str(e)}")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI 提供商."""

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        super().__init__(model)
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com").rstrip("/")
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60,
        )

    async def chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> LLMResponse:
        """发送聊天请求到 OpenAI."""
        try:
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": openai_messages,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model,
                usage=data.get("usage", {}),
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API 错误: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"OpenAI API 错误: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"OpenAI 请求失败: {e}")
            raise HTTPException(status_code=500, detail=f"OpenAI 请求失败: {str(e)}")

    async def stream_chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """流式聊天请求到 OpenAI."""
        try:
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            async with self.client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": openai_messages,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip() and line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            logger.error(f"OpenAI 流式请求失败: {e}")
            raise HTTPException(status_code=500, detail=f"OpenAI 流式请求失败: {str(e)}")

    async def list_models(self) -> list[dict]:
        """获取 OpenAI 可用模型列表."""
        # OpenAI 模型列表是固定的，直接返回常用模型
        return [
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"},
        ]


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude 提供商."""

    def __init__(self, api_key: str, model: str):
        super().__init__(model)
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=60,
        )

    async def chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> LLMResponse:
        """发送聊天请求到 Anthropic."""
        try:
            # 分离系统消息和用户消息
            system_msg = ""
            anthropic_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_msg = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            payload = {
                "model": self.model,
                "messages": anthropic_messages,
                "temperature": temperature,
                "max_tokens": 4096,
            }
            if system_msg:
                payload["system"] = system_msg

            response = await self.client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["content"][0]["text"],
                model=self.model,
                usage=data.get("usage", {}),
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API 错误: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Anthropic API 错误: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Anthropic 请求失败: {e}")
            raise HTTPException(status_code=500, detail=f"Anthropic 请求失败: {str(e)}")

    async def stream_chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """流式聊天请求到 Anthropic."""
        try:
            system_msg = ""
            anthropic_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_msg = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            payload = {
                "model": self.model,
                "messages": anthropic_messages,
                "temperature": temperature,
                "max_tokens": 4096,
                "stream": True,
            }
            if system_msg:
                payload["system"] = system_msg

            async with self.client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip().startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content_block_delta":
                                yield data["delta"].get("text", "")
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Anthropic 流式请求失败: {e}")
            raise HTTPException(status_code=500, detail=f"Anthropic 流式请求失败: {str(e)}")

    async def list_models(self) -> list[dict]:
        """获取 Anthropic 可用模型列表."""
        return [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "provider": "anthropic"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "provider": "anthropic"},
        ]


class LLMService:
    """LLM 服务工厂类."""

    def __init__(self):
        self.settings = get_settings()
        self._provider: Optional[BaseLLMProvider] = None

    def get_provider(self) -> BaseLLMProvider:
        """获取当前配置的 LLM 提供商."""
        if self._provider is None:
            self._provider = self._create_provider()
        return self._provider

    def _create_provider(self) -> BaseLLMProvider:
        """根据配置创建对应的 LLM 提供商."""
        provider = self.settings.AI_PROVIDER.lower()

        if provider == "ollama":
            return OllamaProvider(
                base_url=self.settings.OLLAMA_BASE_URL,
                model=self.settings.OLLAMA_DEFAULT_MODEL,
                timeout=self.settings.OLLAMA_TIMEOUT,
            )
        elif provider == "openai":
            if not self.settings.OPENAI_API_KEY:
                raise HTTPException(
                    status_code=503, detail="OpenAI API Key 未配置"
                )
            return OpenAIProvider(
                api_key=self.settings.OPENAI_API_KEY,
                model=self.settings.OPENAI_DEFAULT_MODEL,
                base_url=self.settings.OPENAI_BASE_URL,
            )
        elif provider == "anthropic":
            if not self.settings.ANTHROPIC_API_KEY:
                raise HTTPException(
                    status_code=503, detail="Anthropic API Key 未配置"
                )
            return AnthropicProvider(
                api_key=self.settings.ANTHROPIC_API_KEY,
                model=self.settings.ANTHROPIC_DEFAULT_MODEL,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"不支持的 AI 提供商: {provider}"
            )

    def refresh_provider(self):
        """刷新提供商（用于配置更改后）."""
        self._provider = None

    async def chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> LLMResponse:
        """发送聊天请求."""
        provider = self.get_provider()
        return await provider.chat(messages, temperature)

    async def stream_chat(
        self, messages: list[LLMMessage], temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """流式聊天请求."""
        provider = self.get_provider()
        async for chunk in provider.stream_chat(messages, temperature):
            yield chunk

    async def list_models(self, provider_name: Optional[str] = None) -> list[dict]:
        """获取可用模型列表."""
        if provider_name:
            # 获取指定提供商的模型
            if provider_name.lower() == "ollama":
                provider = OllamaProvider(
                    base_url=self.settings.OLLAMA_BASE_URL,
                    model=self.settings.OLLAMA_DEFAULT_MODEL,
                )
                return await provider.list_models()
            elif provider_name.lower() == "openai":
                provider = OpenAIProvider(
                    api_key=self.settings.OPENAI_API_KEY or "",
                    model=self.settings.OPENAI_DEFAULT_MODEL,
                )
                return await provider.list_models()
            elif provider_name.lower() == "anthropic":
                provider = AnthropicProvider(
                    api_key=self.settings.ANTHROPIC_API_KEY or "",
                    model=self.settings.ANTHROPIC_DEFAULT_MODEL,
                )
                return await provider.list_models()
            return []
        else:
            # 获取当前提供商的模型
            provider = self.get_provider()
            return await provider.list_models()


# 全局 LLM 服务实例
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """获取 LLM 服务实例."""
    return llm_service
