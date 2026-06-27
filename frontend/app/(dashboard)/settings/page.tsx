"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/page-header";
import {
  getAIConfig,
  getModels,
  getOllamaModels,
  getProviders,
  updateAIConfig,
  type AIConfig,
  type AIModel,
  type AIProvider,
} from "@/api/ai-config";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/stores/auth-store";
import { Loader2, RefreshCw, Bot, Server } from "lucide-react";

/** 本地存储 key：通知偏好 */
const NOTIF_PREF_KEY = "ipflow:notification-prefs";

export default function SettingsPage() {
  const { toast } = useToast();
  const user = useAuthStore((s) => s.user);
  const fetchUser = useAuthStore((s) => s.fetchUser);

  const [aiConfig, setAIConfig] = useState<AIConfig | null>(null);
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [models, setModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [ollamaUrl, setOllamaUrl] = useState<string>("");
  const [aiEnabled, setAiEnabled] = useState<boolean>(false);

  // 个人信息表单
  const [displayName, setDisplayName] = useState<string>("");
  const [profileSaving, setProfileSaving] = useState(false);
  // AI 配置保存
  const [aiSaving, setAiSaving] = useState(false);

  // 通知偏好（本地存储）
  const [emailNotif, setEmailNotif] = useState(true);
  const [browserNotif, setBrowserNotif] = useState(false);

  // 加载用户昵称
  useEffect(() => {
    const name = user?.display_name || user?.displayName || user?.name || "";
    setDisplayName(name);
  }, [user]);

  // 加载 AI 配置
  useEffect(() => {
    loadAIConfig();
    loadProviders();
    loadNotifPrefs();
  }, []);

  // 当提供商改变时加载模型列表
  useEffect(() => {
    if (selectedProvider) {
      loadModels(selectedProvider);
    }
  }, [selectedProvider]);

  const loadNotifPrefs = () => {
    try {
      const raw = localStorage.getItem(NOTIF_PREF_KEY);
      if (raw) {
        const prefs = JSON.parse(raw) as { email?: boolean; browser?: boolean };
        setEmailNotif(prefs.email ?? true);
        setBrowserNotif(prefs.browser ?? false);
      }
    } catch {
      // 忽略解析错误，使用默认值
    }
  };

  const persistNotifPrefs = (email: boolean, browser: boolean) => {
    try {
      localStorage.setItem(
        NOTIF_PREF_KEY,
        JSON.stringify({ email, browser }),
      );
    } catch {
      // 存储失败忽略
    }
  };

  const loadAIConfig = async () => {
    try {
      const config = await getAIConfig();
      setAIConfig(config);
      setSelectedProvider(config.provider);
      setSelectedModel(config.model);
      setOllamaUrl(config.ollama_base_url || "");
      setAiEnabled(config.enabled);
    } catch (error) {
      toast({
        title: "加载失败",
        description: "无法加载 AI 配置",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const data = await getProviders();
      setProviders(data.providers);
    } catch (error) {
      console.error("Failed to load providers:", error);
    }
  };

  const loadModels = async (provider: string) => {
    setModelsLoading(true);
    try {
      let data;
      if (provider === "ollama") {
        data = await getOllamaModels();
      } else {
        data = await getModels(provider);
      }
      setModels(data.models);
    } catch (error) {
      toast({
        title: "获取模型失败",
        description: `无法获取 ${provider} 的模型列表`,
        variant: "destructive",
      });
      setModels([]);
    } finally {
      setModelsLoading(false);
    }
  };

  const handleRefreshModels = () => {
    if (selectedProvider) {
      loadModels(selectedProvider);
    }
  };

  // 保存个人信息
  const handleSaveProfile = async () => {
    setProfileSaving(true);
    try {
      await authApi.updateMe({ display_name: displayName });
      await fetchUser();
      toast({
        title: "保存成功",
        description: "个人信息已更新",
      });
    } catch (error: any) {
      const msg = error?.response?.data?.detail || error?.message || "保存失败";
      toast({
        title: "保存失败",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setProfileSaving(false);
    }
  };

  // 保存 AI 配置
  const handleSaveAIConfig = async () => {
    setAiSaving(true);
    try {
      const updated = await updateAIConfig({
        provider: selectedProvider,
        model: selectedModel || undefined,
        enabled: aiEnabled,
        ollama_base_url:
          selectedProvider === "ollama" && ollamaUrl ? ollamaUrl : undefined,
      });
      setAIConfig(updated);
      toast({
        title: "保存成功",
        description: "AI 配置已更新（运行实例热生效）",
      });
    } catch (error: any) {
      const msg =
        error?.response?.data?.detail || error?.message || "保存 AI 配置失败";
      toast({
        title: "保存失败",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setAiSaving(false);
    }
  };

  const formatModelSize = (bytes?: number): string => {
    if (!bytes) return "";
    const gb = bytes / (1024 * 1024 * 1024);
    if (gb >= 1) {
      return `${gb.toFixed(1)} GB`;
    }
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(0)} MB`;
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="设置"
        description="管理您的账户和系统偏好"
      />

      <div className="grid gap-6 max-w-2xl">
        {/* 个人信息 */}
        <Card>
          <CardHeader>
            <CardTitle>个人信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                value={user?.username || ""}
                disabled
                placeholder="用户名"
              />
              <p className="text-xs text-muted-foreground">用户名创建后不可修改</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">邮箱</Label>
              <Input
                id="email"
                value={user?.email || ""}
                disabled
                placeholder="邮箱"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="displayName">昵称</Label>
              <Input
                id="displayName"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="您的昵称"
              />
            </div>
            <Button onClick={handleSaveProfile} disabled={profileSaving}>
              {profileSaving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              保存更改
            </Button>
          </CardContent>
        </Card>

        {/* AI 模型配置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              AI 模型配置
            </CardTitle>
            <CardDescription>
              配置您想要使用的 AI 模型提供商和模型
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* AI 功能开关 */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-base">启用 AI 助手</Label>
                <p className="text-sm text-muted-foreground">
                  开启后可在项目中使用 AI 辅助功能
                </p>
              </div>
              <Switch
                checked={aiEnabled}
                onCheckedChange={setAiEnabled}
              />
            </div>

            <Separator />

            {/* 提供商选择 */}
            <div className="space-y-2">
              <Label htmlFor="provider">AI 提供商</Label>
              <Select
                value={selectedProvider}
                onValueChange={(v) => {
                  setSelectedProvider(v);
                  setSelectedModel("");
                }}
              >
                <SelectTrigger id="provider">
                  <SelectValue placeholder="选择 AI 提供商" />
                </SelectTrigger>
                <SelectContent>
                  {providers.map((provider) => (
                    <SelectItem key={provider.id} value={provider.id}>
                      <div className="flex flex-col items-start">
                        <span>{provider.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {provider.description}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {providers.find((p) => p.id === selectedProvider)?.description}
              </p>
            </div>

            {/* Ollama 特定配置 */}
            {selectedProvider === "ollama" && (
              <div className="space-y-2">
                <Label htmlFor="ollamaUrl" className="flex items-center gap-2">
                  <Server className="h-4 w-4" />
                  Ollama 服务地址
                </Label>
                <Input
                  id="ollamaUrl"
                  placeholder="http://localhost:11434"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  本地 Ollama 服务地址，默认 http://localhost:11434
                </p>
              </div>
            )}

            {/* 模型选择 */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="model">模型</Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefreshModels}
                  disabled={modelsLoading}
                >
                  <RefreshCw className={`h-4 w-4 ${modelsLoading ? "animate-spin" : ""}`} />
                  刷新
                </Button>
              </div>
              <Select
                value={selectedModel}
                onValueChange={setSelectedModel}
              >
                <SelectTrigger id="model">
                  <SelectValue placeholder={modelsLoading ? "加载中..." : "选择模型"} />
                </SelectTrigger>
                <SelectContent>
                  {models.length === 0 && !modelsLoading ? (
                    <SelectItem value="__empty__" disabled>
                      暂无可用模型
                    </SelectItem>
                  ) : (
                    models.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        <div className="flex items-center justify-between w-full gap-4">
                          <span>{model.name}</span>
                          {model.size && (
                            <span className="text-xs text-muted-foreground">
                              {formatModelSize(model.size)}
                            </span>
                          )}
                        </div>
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {selectedProvider === "ollama" && models.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  未检测到本地模型，请先运行 ollama pull 命令下载模型
                </p>
              )}
            </div>

            <Button
              className="w-full"
              onClick={handleSaveAIConfig}
              disabled={aiSaving}
            >
              {aiSaving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              保存 AI 配置
            </Button>
          </CardContent>
        </Card>

        {/* 通知设置 */}
        <Card>
          <CardHeader>
            <CardTitle>通知设置</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>邮件通知</Label>
                <p className="text-sm text-muted-foreground">接收项目更新和重要通知</p>
              </div>
              <Switch
                checked={emailNotif}
                onCheckedChange={(v) => {
                  setEmailNotif(v);
                  persistNotifPrefs(v, browserNotif);
                }}
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>浏览器通知</Label>
                <p className="text-sm text-muted-foreground">在浏览器中显示通知</p>
              </div>
              <Switch
                checked={browserNotif}
                onCheckedChange={(v) => {
                  setBrowserNotif(v);
                  persistNotifPrefs(emailNotif, v);
                }}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
