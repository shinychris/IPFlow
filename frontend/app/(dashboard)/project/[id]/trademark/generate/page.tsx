"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Sparkles } from "lucide-react";

import { trademarkGenerationJobsApi } from "@/api/trademarks";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";

export default function TrademarkGeneratePage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const projectId = params.id as string;

  const { data: context } = useQuery({
    queryKey: [`/api/v1/trademarks/projects/${projectId}/generation-context`],
    queryFn: () => trademarkGenerationJobsApi.getContext(projectId),
    enabled: !!projectId,
  });

  const startMutation = useMutation({
    mutationFn: (payload: { extra_brief: string }) =>
      trademarkGenerationJobsApi.start(projectId, {
        generation_mode: "guided_confirm",
        inputs: { extra_brief: payload.extra_brief || undefined },
        policy: { overwrite_strategy: "fill_blank_only" },
      }),
    onSuccess: () => {
      toast({ title: "生成完成", description: "商标草稿已生成，可进入详情编辑。" });
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
    });
  };

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="商标 AI 生成引导"
        description="基于商标名称与创建信息生成草稿并推荐分类"
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
              <Label htmlFor="extra_brief">品牌补充说明（可选）</Label>
              <Textarea id="extra_brief" name="extra_brief" rows={4} placeholder="补充品牌定位、目标市场、使用场景..." />
            </div>
            <Button type="submit" disabled={startMutation.isPending}>
              <Sparkles className="mr-2 h-4 w-4" />
              {startMutation.isPending ? "生成中..." : "开始生成商标草稿"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
