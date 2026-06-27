"""AI 配置 API 端点."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ipflow.config import get_settings, Settings
from ipflow.services.llm_service import get_llm_service, LLMService, LLMMessage

router = APIRouter(prefix="/ai", tags=["AI 配置"])


class AIConfigResponse(BaseModel):
    """AI 配置响应."""
    provider: str = Field(..., description="当前 AI 提供商")
    model: str = Field(..., description="当前模型")
    enabled: bool = Field(..., description="AI 功能是否启用")
    ollama_base_url: str = Field(..., description="Ollama 服务地址")
    available_providers: list[str] = Field(default_factory=list, description="可用提供商列表")


class ModelsResponse(BaseModel):
    """模型列表响应."""
    provider: str = Field(..., description="提供商")
    models: list[dict] = Field(default_factory=list, description="模型列表")


class UpdateAIConfigRequest(BaseModel):
    """更新 AI 配置请求."""
    provider: Optional[str] = Field(None, description="AI 提供商")
    model: Optional[str] = Field(None, description="模型名称")
    enabled: Optional[bool] = Field(None, description="是否启用 AI")
    ollama_base_url: Optional[str] = Field(None, description="Ollama 服务地址")


class ChatRequest(BaseModel):
    """聊天请求."""
    message: str = Field(..., description="用户消息")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: float = Field(0.7, ge=0, le=2, description="温度参数")
    model: Optional[str] = Field(None, description="指定模型（可选）")


class ChatResponse(BaseModel):
    """聊天响应."""
    content: str = Field(..., description="AI 回复内容")
    model: str = Field(..., description="使用的模型")


@router.get("/config", response_model=AIConfigResponse)
async def get_ai_config(settings: Settings = Depends(get_settings)):
    """获取当前 AI 配置."""
    return AIConfigResponse(
        provider=settings.AI_PROVIDER,
        model=settings.AI_MODEL,
        enabled=settings.ENABLE_AI_ASSISTANT,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        available_providers=["ollama", "openai", "anthropic"],
    )


@router.put("/config", response_model=AIConfigResponse)
async def update_ai_config(
    request: UpdateAIConfigRequest,
    settings: Settings = Depends(get_settings),
):
    """更新当前运行实例的 AI 配置.

    在单实例部署中将配置热更新到内存中的配置单例，无需重启即可生效。
    持久化到 ``.env`` 不在此端点职责范围内（敏感凭据应通过环境变量管理）。

    Args:
        request: 待更新的配置字段（均为可选，未提供则保持原值）

    Returns:
        更新后的完整 AI 配置
    """
    if request.provider is not None:
        if request.provider not in ("ollama", "openai", "anthropic"):
            raise HTTPException(
                status_code=400, detail=f"不支持的 AI 提供商: {request.provider}"
            )
        settings.AI_PROVIDER = request.provider
    if request.model is not None:
        settings.AI_MODEL = request.model
    if request.enabled is not None:
        settings.ENABLE_AI_ASSISTANT = request.enabled
    if request.ollama_base_url is not None:
        settings.OLLAMA_BASE_URL = request.ollama_base_url

    # 配置变更后让 LLM 服务重建提供商缓存
    try:
        from ipflow.services.llm_service import get_llm_service

        get_llm_service().reset_provider()
    except Exception:
        # 重置失败不应阻断配置保存
        pass

    return AIConfigResponse(
        provider=settings.AI_PROVIDER,
        model=settings.AI_MODEL,
        enabled=settings.ENABLE_AI_ASSISTANT,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        available_providers=["ollama", "openai", "anthropic"],
    )


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    provider: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
):
    """获取可用模型列表.
    
    Args:
        provider: 指定提供商，不指定则使用当前配置的提供商
    """
    try:
        models = await llm_service.list_models(provider)
        return ModelsResponse(
            provider=provider or settings.AI_PROVIDER,
            models=models,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/models/ollama", response_model=ModelsResponse)
async def list_ollama_models(
    llm_service: LLMService = Depends(get_llm_service),
):
    """获取 Ollama 可用模型列表."""
    try:
        models = await llm_service.list_models("ollama")
        return ModelsResponse(
            provider="ollama",
            models=models,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Ollama 模型列表失败: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
):
    """发送聊天请求到 AI.
    
    需要 AI 功能已启用。
    """
    if not settings.ENABLE_AI_ASSISTANT:
        raise HTTPException(status_code=403, detail="AI 助手功能未启用")

    try:
        messages = []
        if request.system_prompt:
            messages.append(LLMMessage(role="system", content=request.system_prompt))
        messages.append(LLMMessage(role="user", content=request.message))

        response = await llm_service.chat(messages, request.temperature)
        
        return ChatResponse(
            content=response.content,
            model=response.model,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 请求失败: {str(e)}")


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
):
    """流式聊天请求到 AI.
    
    需要 AI 功能已启用。
    """
    if not settings.ENABLE_AI_ASSISTANT:
        raise HTTPException(status_code=403, detail="AI 助手功能未启用")

    from fastapi.responses import StreamingResponse

    async def generate():
        try:
            messages = []
            if request.system_prompt:
                messages.append(LLMMessage(role="system", content=request.system_prompt))
            messages.append(LLMMessage(role="user", content=request.message))

            async for chunk in llm_service.stream_chat(messages, request.temperature):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR: {str(e)}]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/providers")
async def list_providers():
    """获取支持的 AI 提供商列表."""
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "本地运行的开源 LLM",
                "requires_api_key": False,
                "requires_base_url": True,
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "OpenAI GPT 模型",
                "requires_api_key": True,
                "requires_base_url": False,
            },
            {
                "id": "anthropic",
                "name": "Anthropic Claude",
                "description": "Anthropic Claude 模型",
                "requires_api_key": True,
                "requires_base_url": False,
            },
        ]
    }
