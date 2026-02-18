/**
 * 项目列表页面 (重构版)
 */

import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Plus, Search, MoreVertical, Copy, Trash2, FileText } from "lucide-react";
import { useProjectStore } from "@/stores/project-store";
import { useUIStore } from "@/stores/ui-store";
import { ProjectType, ProjectStatus } from "@/types";

const statusLabels: Record<string, string> = {
  [ProjectStatus.DRAFT]: "草稿",
  [ProjectStatus.IN_PROGRESS]: "进行中",
  [ProjectStatus.REVIEWING]: "审核中",
  [ProjectStatus.PENDING_SUBMIT]: "待提交",
  [ProjectStatus.SUBMITTED]: "已提交",
  [ProjectStatus.APPROVED]: "已通过",
};

const typeLabels: Record<string, string> = {
  [ProjectType.COPYRIGHT]: "软著",
  [ProjectType.PATENT]: "专利",
  [ProjectType.TRADEMARK]: "商标",
};

const typeColors: Record<string, string> = {
  [ProjectType.COPYRIGHT]: "bg-blue-100 text-blue-800",
  [ProjectType.PATENT]: "bg-amber-100 text-amber-800",
  [ProjectType.TRADEMARK]: "bg-green-100 text-green-800",
};

export default function ProjectsPage() {
  const [, setLocation] = useLocation();
  const { projects, isLoading, fetchProjects, deleteProject, duplicateProject } = useProjectStore();
  const { addToast, openConfirmDialog } = useUIStore();

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const filteredProjects = projects.filter((project) => {
    const matchesSearch = project.name.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "all" || project.project_type === typeFilter;
    const matchesStatus = statusFilter === "all" || project.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const handleDelete = (project: typeof projects[0]) => {
    openConfirmDialog({
      title: "确认删除",
      description: `确定要删除项目 "${project.name}" 吗？此操作不可恢复。`,
      onConfirm: async () => {
        try {
          await deleteProject(project.id);
          addToast({
            title: "删除成功",
            variant: "success",
          });
        } catch {
          addToast({
            title: "删除失败",
            description: "请稍后重试",
            variant: "destructive",
          });
        }
      },
    });
  };

  const handleDuplicate = async (project: typeof projects[0]) => {
    try {
      await duplicateProject(project.id);
      addToast({
        title: "复制成功",
        description: "项目已复制",
        variant: "success",
      });
    } catch {
      addToast({
        title: "复制失败",
        description: "请稍后重试",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">全部项目</h1>
          <p className="text-muted-foreground mt-1">
            管理您的所有知识产权申请项目
          </p>
        </div>
        <Button onClick={() => setLocation("/project/new")}>
          <Plus className="mr-2 h-4 w-4" />
          新建项目
        </Button>
      </div>

      {/* 筛选栏 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索项目名称..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2">
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="项目类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              <SelectItem value={ProjectType.COPYRIGHT}>软著</SelectItem>
              <SelectItem value={ProjectType.PATENT}>专利</SelectItem>
              <SelectItem value={ProjectType.TRADEMARK}>商标</SelectItem>
            </SelectContent>
          </Select>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              {Object.entries(statusLabels).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 项目列表 */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="h-16 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-semibold">暂无项目</h3>
            <p className="text-muted-foreground mt-1">
              {search || typeFilter !== "all" || statusFilter !== "all"
                ? "没有符合筛选条件的项目"
                : "开始创建您的第一个项目"}
            </p>
            <Button
              className="mt-4"
              onClick={() => setLocation("/project/new")}
            >
              <Plus className="mr-2 h-4 w-4" />
              新建项目
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredProjects.map((project) => (
            <Card
              key={project.id}
              className="hover:shadow-md transition-shadow"
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => setLocation(`/project/${project.id}`)}
                  >
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-lg">{project.name}</h3>
                      <Badge className={typeColors[project.project_type]}>
                        {typeLabels[project.project_type]}
                      </Badge>
                      <Badge variant="outline">
                        {statusLabels[project.status] || project.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <span>版本: {project.version}</span>
                      <span>步骤: {project.current_step}/5</span>
                      <span>
                        更新: {new Date(project.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => setLocation(`/project/${project.id}`)}
                      >
                        <FileText className="mr-2 h-4 w-4" />
                        编辑
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleDuplicate(project)}
                      >
                        <Copy className="mr-2 h-4 w-4" />
                        复制
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => handleDelete(project)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        删除
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
