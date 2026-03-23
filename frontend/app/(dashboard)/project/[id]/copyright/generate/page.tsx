"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Sparkles } from "lucide-react";

import { generationJobsApi } from "@/api/copyright";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";

export default function CopyrightGeneratePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const projectId = params.id as string;

  const { data: context, isLoading } = useQuery({
    queryKey: [`/api/v1/copyright/projects/${projectId}/generation-context`],
    queryFn: () => generationJobsApi.getContext(projectId),
    enabled: !!projectId,
  });

  const startMutation = useMutation({
    mutationFn: (payload: {
      extra_brief: string;
      repo_url: string;
      use_history: boolean;
      use_org_knowledge: boolean;
    }) =>
      generationJobsApi.start(projectId, {
        generation_mode: "guided_confirm",
        inputs: {
          extra_brief: payload.extra_brief || undefined,
          repo: payload.repo_url
            ? { provider: "git", url: payload.repo_url, branch: "main" }
            : undefined,
          history_reuse: {
            enabled: payload.use_history,
            source_project_ids: [],
          },
          org_knowledge: {
            enabled: payload.use_org_knowledge,
            dataset_ids: [],
          },
        },
        policy: { overwrite_strategy: "fill_blank_only" },
      }),
    onSuccess: () => {
      toast({
        title: "已开始生成",
        description: "AI 草稿已生成，可进入工作台继续编辑。",
      });
      router.push(`/project/${projectId}`);
    },
    onError: () => {
      toast({
        title: "启动失败",
        description: "请检查输入后重试",
        variant: "destructive",
      });
    },
  });

  const defaults = {
    extraBrief: context?.optional_inputs?.extra_brief ?? "",
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    startMutation.mutate({
      extra_brief: String(formData.get("extra_brief") || ""),
      repo_url: String(formData.get("repo_url") || ""),
      use_history: formData.get("use_history") === "on",
      use_org_knowledge: formData.get("use_org_knowledge") === "on",
    });
  };

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="AI 材料生成引导"
        description="确认项目信息后，一键生成软著草稿材料"
        actions={
          <Link href={`/project/${projectId}`}>
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回项目
            </Button>
          </Link>
        }
      />

      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>生成上下文</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {isLoading ? (
            <p>加载中...</p>
          ) : (
            <>
              <p>项目名称：{context?.base_profile?.name ?? "-"}</p>
              <p>版本号：{context?.base_profile?.version ?? "-"}</p>
              <p>已有草稿：{context?.draft_exists ? "是" : "否"}</p>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>可选补充信息</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="extra_brief">业务补充描述（可选）</Label>
              <Textarea
                id="extra_brief"
                name="extra_brief"
                defaultValue={defaults.extraBrief}
                placeholder="可补充业务场景、核心流程、目标用户等信息"
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="repo_url">代码仓地址（可选）</Label>
              <Input id="repo_url" name="repo_url" placeholder="https://github.com/org/repo" />
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="use_history" className="h-4 w-4" />
              启用历史项目复用
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="use_org_knowledge" className="h-4 w-4" />
              启用组织知识库辅助
            </label>

            <Button type="submit" disabled={startMutation.isPending}>
              <Sparkles className="mr-2 h-4 w-4" />
              {startMutation.isPending ? "生成中..." : "开始生成 AI 草稿"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
