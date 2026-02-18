/**
 * 工作台页面 (重构版)
 * 
 * 使用新的 Zustand store
 */

import { useEffect } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, FileText, Sparkles, Copyright, Lightbulb, Hash } from "lucide-react";
import { useProjectStore } from "@/stores/project-store";
import { useAuthStore } from "@/stores/auth-store";
import { ProjectType } from "@/types";

const projectTypeConfig = {
  [ProjectType.COPYRIGHT]: {
    label: "软件著作权",
    icon: Copyright,
    color: "bg-blue-100 text-blue-800",
  },
  [ProjectType.PATENT]: {
    label: "专利",
    icon: Lightbulb,
    color: "bg-amber-100 text-amber-800",
  },
  [ProjectType.TRADEMARK]: {
    label: "商标",
    icon: Hash,
    color: "bg-green-100 text-green-800",
  },
};

export default function DashboardPage() {
  const [, setLocation] = useLocation();
  const { user } = useAuthStore();
  const { projects, isLoading, fetchProjects } = useProjectStore();

  useEffect(() => {
    fetchProjects({ limit: 5 });
  }, [fetchProjects]);

  const recentProjects = projects.slice(0, 5);

  return (
    <div className="p-6 space-y-6">
      {/* 欢迎区域 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            欢迎回来，{user?.display_name || user?.username}
          </h1>
          <p className="text-muted-foreground mt-1">
            这里是您的工作台，开始管理您的知识产权申请
          </p>
        </div>
        <Button onClick={() => setLocation("/project/new")}>
          <Plus className="mr-2 h-4 w-4" />
          新建项目
        </Button>
      </div>

      {/* 快捷入口 */}
      <div className="grid gap-4 md:grid-cols-3">
        {Object.entries(projectTypeConfig).map(([type, config]) => {
          const Icon = config.icon;
          return (
            <Card
              key={type}
              className="cursor-pointer hover:border-primary transition-colors"
              onClick={() => setLocation(`/${type}`)}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {config.label}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {projects.filter((p) => p.project_type === type).length}
                </div>
                <p className="text-xs text-muted-foreground">个项目</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 最近项目 */}
      <Card>
        <CardHeader>
          <CardTitle>最近项目</CardTitle>
          <CardDescription>您最近编辑的项目</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : recentProjects.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-semibold">暂无项目</h3>
              <p className="text-muted-foreground">开始创建您的第一个项目</p>
              <Button
                className="mt-4"
                onClick={() => setLocation("/project/new")}
              >
                <Plus className="mr-2 h-4 w-4" />
                新建项目
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {recentProjects.map((project) => {
                const config = projectTypeConfig[project.project_type];
                const Icon = config.icon;

                return (
                  <div
                    key={project.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => setLocation(`/project/${project.id}`)}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-lg ${config.color}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="font-medium">{project.name}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className={config.color}>
                            {config.label}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {project.version}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">
                        步骤 {project.current_step}/5
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(project.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI 助手提示 */}
      <Card className="bg-gradient-to-r from-primary/10 via-primary/5 to-background border-primary/20">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-full bg-primary/10">
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold">AI 智能助手</h3>
              <p className="text-sm text-muted-foreground mt-1">
                使用 AI 辅助撰写功能描述、技术特点、操作说明书等内容，
                提升申请效率
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => setLocation("/help")}
              >
                了解更多
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
