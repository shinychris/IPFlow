"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Sparkles } from "lucide-react";

import { patentGenerationJobsApi } from "@/api/patents";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";

export default function PatentGeneratePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const projectId = params.id as string;

  const { data: context } = useQuery({
    queryKey: [`/api/v1/patents/projects/${projectId}/generation-context`],
    queryFn: () => patentGenerationJobsApi.getContext(projectId),
    enabled: !!projectId,
  });

  const startMutation = useMutation({
    mutationFn: (payload: { extra_brief: string; use_history: boolean; use_org_knowledge: boolean }) =>
      patentGenerationJobsApi.start(projectId, {
        generation_mode: "guided_confirm",
        inputs: {
          extra_brief: payload.extra_brief || undefined,
          history_reuse: { enabled: payload.use_history, source_project_ids: [] },
          org_knowledge: { enabled: payload.use_org_knowledge, dataset_ids: [] },
        },
        policy: { overwrite_strategy: "fill_blank_only" },
      }),
    onSuccess: () => {
      toast({ title: "生成完成", description: "专利草稿已生成，可进入详情编辑。" });
      router.push(`/project/${projectId}`);
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
      use_history: fd.get("use_history") === "on",
      use_org_knowledge: fd.get("use_org_knowledge") === "on",
    });
  };

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="专利 AI 生成引导"
        description="可优先使用历史项目与组织知识库生成草稿"
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
              <Textarea id="extra_brief" name="extra_brief" rows={4} placeholder="补充技术方案、场景和目标..." />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="use_history" className="h-4 w-4" defaultChecked />
              启用历史项目复用（推荐）
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="use_org_knowledge" className="h-4 w-4" defaultChecked />
              启用组织知识库（推荐）
            </label>
            <Button type="submit" disabled={startMutation.isPending}>
              <Sparkles className="mr-2 h-4 w-4" />
              {startMutation.isPending ? "生成中..." : "开始生成专利草稿"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
