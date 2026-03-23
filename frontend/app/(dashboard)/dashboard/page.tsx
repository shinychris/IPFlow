"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileCode, Lightbulb, Stamp, ArrowRight } from "lucide-react";
import { type Project } from "@shared/types";
import { cn } from "@/lib/utils";
import { ProjectCard } from "@/components/project-card";
import { apiRequest } from "@/lib/queryClient";
import { PageHeader } from "@/components/page-header";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { deleteProject, exportProject } from "@/lib/project-actions";

const typeConfig = [
  {
    type: "copyright" as const,
    label: "软著申请",
    description: "计算机软件著作权登记",
    icon: FileCode,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-200 dark:border-blue-800",
    url: "/copyright",
  },
  {
    type: "patent" as const,
    label: "专利申请",
    description: "发明/实用新型/外观设计",
    icon: Lightbulb,
    color: "text-amber-500",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-200 dark:border-amber-800",
    url: "/patent",
  },
  {
    type: "trademark" as const,
    label: "商标申请",
    description: "商标注册申请",
    icon: Stamp,
    color: "text-emerald-500",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-200 dark:border-emerald-800",
    url: "/trademark",
  },
];

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: recentProjects = [] } = useQuery<Project[]>({
    queryKey: ["/api/v1/projects?limit=4"],
  });

  const duplicateMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiRequest("POST", `/api/v1/projects/${id}/duplicate`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/v1/projects?limit=4"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/v1/projects?limit=4"] });
      queryClient.invalidateQueries({ queryKey: ["/api/v1/projects"] });
      toast({ title: "删除成功", description: "项目已删除" });
    },
    onError: () => {
      toast({ title: "删除失败", description: "请稍后重试", variant: "destructive" });
    },
  });

  const handleExport = async (project: Project) => {
    try {
      await exportProject(project);
      toast({ title: "导出已开始", description: "文件下载已触发" });
    } catch {
      toast({ title: "导出失败", description: "请先完善项目资料后重试", variant: "destructive" });
    }
  };

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="工作台"
        description="选择业务类型开始新的申请，或继续已有项目"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {typeConfig.map(({ type, label, description, icon: Icon, color, bgColor, borderColor, url }) => (
          <Link key={type} href={url} className="block">
            <Card className={cn("h-full cursor-pointer transition-colors hover:bg-accent/50", borderColor)}>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={cn("p-3 rounded-lg shrink-0", bgColor)}>
                    <Icon className={cn("h-6 w-6", color)} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{label}</h3>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{description}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">最近项目</h2>
          <Link href="/projects">
            <Button variant="ghost" size="sm">
              查看全部
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </div>

        {recentProjects.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="p-8 text-center text-muted-foreground">
              暂无项目，点击上方业务类型开始创建
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {recentProjects.slice(0, 4).map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDuplicate={() => duplicateMutation.mutate(project.id)}
                onDelete={() => deleteMutation.mutate(project.id)}
                onExport={() => void handleExport(project)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
