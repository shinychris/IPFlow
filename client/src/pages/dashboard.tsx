import { useQuery } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { FileCode, Lightbulb, Stamp, Plus, ArrowRight, Clock, CheckCircle2 } from "lucide-react";
import { type Project, projectTypeLabels, projectStatusLabels, getMaxSteps } from "@shared/schema";
import { cn } from "@/lib/utils";
import { ProjectCard } from "@/components/project-card";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useMutation } from "@tanstack/react-query";
import { PageHeader } from "@/components/page-header";

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
  const [, setLocation] = useLocation();

  const { data: projects, isLoading } = useQuery<Project[]>({
    queryKey: ["/api/projects"],
  });

  const deleteProjectMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiRequest("DELETE", `/api/projects/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/projects"] });
    },
  });

  const duplicateProjectMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiRequest("POST", `/api/projects/${id}/duplicate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/projects"] });
    },
  });

  const getCountByType = (type: string) => {
    return projects?.filter(p => p.type === type).length || 0;
  };

  const getInProgressCount = () => {
    return projects?.filter(p => p.status === "in_progress" || p.status === "draft").length || 0;
  };

  const getCompletedCount = () => {
    return projects?.filter(p => p.status === "completed" || p.status === "exported").length || 0;
  };

  const recentProjects = projects?.slice(0, 6) || [];

  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-8">
      <PageHeader
        title="工作台"
        description="知识产权申请材料准备助手"
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {typeConfig.map((config) => {
          const count = getCountByType(config.type);
          return (
            <Card
              key={config.type}
              className="hover-elevate cursor-pointer"
              onClick={() => setLocation(config.url)}
              data-testid={`card-type-${config.type}`}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className={cn("flex h-12 w-12 items-center justify-center rounded-lg", config.bgColor)}>
                      <config.icon className={cn("h-6 w-6", config.color)} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-base">{config.label}</h3>
                      <p className="text-xs text-muted-foreground mt-0.5">{config.description}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="text-2xl font-bold">{count}</span>
                    <span className="text-xs text-muted-foreground">个项目</span>
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-between">
                  <Button variant="ghost" size="sm" className="gap-1 text-xs" data-testid={`button-new-${config.type}`}>
                    <Plus className="h-3.5 w-3.5" />
                    新建
                  </Button>
                  <Button variant="ghost" size="sm" className="gap-1 text-xs" data-testid={`button-view-${config.type}`}>
                    查看全部
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500/10">
                <Clock className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{getInProgressCount()}</p>
                <p className="text-sm text-muted-foreground">进行中的项目</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{getCompletedCount()}</p>
                <p className="text-sm text-muted-foreground">已完成的项目</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {recentProjects.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">最近项目</h2>
            <Button variant="ghost" size="sm" onClick={() => setLocation("/projects")} data-testid="button-view-all-projects">
              查看全部
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={(id) => deleteProjectMutation.mutate(id)}
                onDuplicate={(id) => duplicateProjectMutation.mutate(id)}
              />
            ))}
          </div>
        </div>
      )}

      {(!projects || projects.length === 0) && !isLoading && (
        <Card className="border-dashed">
          <CardContent className="p-12 flex flex-col items-center justify-center text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4">
              <Plus className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">开始您的知识产权申请</h3>
            <p className="text-muted-foreground mb-6 max-w-md">
              选择上方的业务类型，开始准备软著、专利或商标申请材料
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
