"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Sparkles } from "lucide-react";

import { patentGenerationJobsApi } from "@/api/patents";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { usePatentGenerationJob } from "@/hooks/use-copyright-jobs";

export default function PatentGeneratePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const projectId = params.id as string;
  const [pendingJobId, setPendingJobId] = useState<string | null>(null);

  const { data: context } = useQuery({
    queryKey: [`/api/v1/patents/projects/${projectId}/generation-context`],
    queryFn: () => patentGenerationJobsApi.getContext(projectId),
    enabled: !!projectId,
  });

  const { data: job } = usePatentGenerationJob(pendingJobId ?? undefined);

  useEffect(() => {
    if (!job || !pendingJobId) return;
    if (job.status === "succeeded") {
      toast({
        title: "生成完成",
        description: "专利草稿已就绪，可进入详情编辑。",
      });
      setPendingJobId(null);
      router.push(`/project/${projectId}`);
    }
    if (job.status === "failed") {
      toast({
        title: "生成失败",
        description: job.error ?? "请稍后重试",
        variant: "destructive",
      });
      setPendingJobId(null);
    }
  }, [job, pendingJobId, projectId, router, toast]);

  const startMutation = useMutation({
    mutationFn: (payload: {
      extra_brief: string;
      repo_url: string;
      source_type: string;
      ref: string;
      use_history: boolean;
      use_org_knowledge: boolean;
    }) => {
      const url = payload.repo_url.trim();
      return patentGenerationJobsApi.start(projectId, {
        generation_mode: "guided_confirm",
        inputs: {
          extra_brief: payload.extra_brief || undefined,
          repo: url
            ? {
                source_type: payload.source_type as "auto" | "git" | "zip",
                source_url: url,
                ref: payload.ref.trim() || undefined,
              }
            : undefined,
          history_reuse: { enabled: payload.use_history, source_project_ids: [] },
          org_knowledge: { enabled: payload.use_org_knowledge, dataset_ids: [] },
        },
        policy: { overwrite_strategy: "fill_blank_only" },
      });
    },
    onSuccess: (res) => {
      setPendingJobId(res.job_id);
      toast({ title: "任务已排队", description: "后台正在生成，请稍候…" });
    },
    onError: () => {
      toast({ title: "生成失败", description: "请稍后重试", variant: "destructive" });
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    startMutation.mutate({
      extra_brief: String(fd.get("extra_brief") || ""),
      repo_url: String(fd.get("repo_url") || ""),
      source_type: String(fd.get("source_type") || "auto"),
      ref: String(fd.get("ref") || ""),
      use_history: fd.get("use_history") === "on",
      use_org_knowledge: fd.get("use_org_knowledge") === "on",
    });
  };

  const remoteConfigured = context?.repo_hint?.remote_fetch_configured ?? false;

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="专利 AI 生成引导"
        description="可补充技术说明与可选源码链接，后台生成草稿"
        actions={
          <Link href={`/project/${projectId}`}>
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回详情
            </Button>
          </Link>
        }
      />

      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>基础信息</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-1">
          <p>项目名称：{context?.base_profile?.name ?? "-"}</p>
          <p>版本号：{context?.base_profile?.version ?? "-"}</p>
        </CardContent>
      </Card>

      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>生成参数</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="extra_brief">补充说明（可选）</Label>
              <Textarea
                id="extra_brief"
                name="extra_brief"
                rows={4}
                placeholder="补充技术方案、场景和目标..."
                disabled={Boolean(pendingJobId) || startMutation.isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="repo_url">技术资料 / 源码链接（可选）</Label>
              <Input
                id="repo_url"
                name="repo_url"
                placeholder="Git HTTPS / SSH，或 .zip 直链"
                disabled={Boolean(pendingJobId) || startMutation.isPending}
              />
              <p className="text-xs text-muted-foreground">
                填写后由服务端在允许的主机范围内拉取，供 Claude Code 阅读（若已启用）。
              </p>
              {!remoteConfigured ? (
                <p className="text-xs text-amber-600 dark:text-amber-500">
                  服务端未配置 SOURCE_FETCH_ALLOWED_HOSTS 时远程拉取将失败。
                </p>
              ) : null}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="source_type">链接类型</Label>
                <select
                  id="source_type"
                  name="source_type"
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  defaultValue="auto"
                  disabled={Boolean(pendingJobId) || startMutation.isPending}
                >
                  <option value="auto">自动识别</option>
                  <option value="git">Git 仓库</option>
                  <option value="zip">Zip 压缩包</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="ref">分支 / 标签（Git，可选）</Label>
                <Input
                  id="ref"
                  name="ref"
                  placeholder="例如 main"
                  disabled={Boolean(pendingJobId) || startMutation.isPending}
                />
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="use_history" className="h-4 w-4" defaultChecked />
              启用历史项目复用（推荐）
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="use_org_knowledge" className="h-4 w-4" defaultChecked />
              启用组织知识库（推荐）
            </label>
            <Button type="submit" disabled={Boolean(pendingJobId) || startMutation.isPending}>
              <Sparkles className="mr-2 h-4 w-4" />
              {pendingJobId || startMutation.isPending ? "生成进行中…" : "开始生成专利草稿"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
