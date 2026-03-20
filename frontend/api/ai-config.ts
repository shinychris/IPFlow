/**
 * AI 配置 API 客户端
 */

import apiClient from "./client";

export interface AIConfig {
  provider: string;
  model: string;
  enabled: boolean;
  ollama_base_url: string;
  available_providers: string[];
}

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  size?: number;
  modified_at?: string;
}

export interface ModelsResponse {
  provider: string;
  models: AIModel[];
}

export interface AIProvider {
  id: string;
  name: string;
  description: string;
  requires_api_key: boolean;
  requires_base_url: boolean;
}

export interface ChatRequest {
  message: string;
  system_prompt?: string;
  temperature?: number;
  model?: string;
}

export interface ChatResponse {
  content: string;
  model: string;
}

/**
 * 获取 AI 配置
 */
export async function getAIConfig(): Promise<AIConfig> {
  const response = await apiClient.get<AIConfig>("/ai/config");
  return response.data;
}

/**
 * 获取可用模型列表
 * @param provider 指定提供商，不指定则使用当前配置的提供商
 */
export async function getModels(provider?: string): Promise<ModelsResponse> {
  const params = provider ? { provider } : undefined;
  const response = await apiClient.get<ModelsResponse>("/ai/models", { params });
  return response.data;
}

/**
 * 获取 Ollama 模型列表
 */
export async function getOllamaModels(): Promise<ModelsResponse> {
  const response = await apiClient.get<ModelsResponse>("/ai/models/ollama");
  return response.data;
}

/**
 * 获取支持的 AI 提供商列表
 */
export async function getProviders(): Promise<{ providers: AIProvider[] }> {
  const response = await apiClient.get<{ providers: AIProvider[] }>("/ai/providers");
  return response.data;
}

/**
 * 发送聊天请求
 */
export async function chat(request: ChatRequest): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>("/ai/chat", request);
  return response.data;
}

/**
 * 流式聊天请求
 */
export async function* streamChat(request: ChatRequest): AsyncGenerator<string> {
  const response = await fetch(`${apiClient.defaults.baseURL || ""}/ai/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Response body is null");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("data: ")) {
        const data = trimmed.slice(6);
        if (data === "[DONE]") {
          return;
        }
        if (data.startsWith("[ERROR:")) {
          throw new Error(data.slice(8, -1));
        }
        yield data;
      }
    }
  }
}
