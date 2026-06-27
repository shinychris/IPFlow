import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import { MoreHorizontal, FileCode, Lightbulb, Stamp, Edit, Trash2, Copy, Download, Sparkles, Eye } from "lucide-react";
import Link from "next/link";
import {
  type Project,
  projectStatusLabels,
  projectTypeLabels,
  subjectTypeLabels,
  getMaxSteps,
} from "@shared/types";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: string) => void;
  onDuplicate?: (id: string) => void;
  onExport?: (id: string) => void;
}

const statusColors: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  in_progress: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  completed: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  exported: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
};

const flowStatusLabels: Record<string, string> = {
  draft_pending: "待生成",
  generating: "生成中",
  draft_ready: "草稿已生成",
  human_editing: "人工编辑中",
  exporting: "打包中",
  export_ready: "可下载",
};

const typeIcons = {
  copyright: FileCode,
  patent: Lightbulb,
  trademark: Stamp,
};

const typeColors = {
  copyright: "text-blue-500",
  patent: "text-amber-500",
  trademark: "text-emerald-500",
};

const typeBgColors = {
  copyright: "bg-blue-500/10",
  patent: "bg-amber-500/10",
  trademark: "bg-emerald-500/10",
};

export function ProjectCard({ project, onDelete, onDuplicate, onExport }: ProjectCardProps) {
  const rawProjectType = project.project_type ?? project.type;
  const projectType: "copyright" | "patent" | "trademark" =
    rawProjectType === "patent" || rawProjectType === "trademark" ? rawProjectType : "copyright";
  const currentStep = project.current_step ?? 1;
  const flowStatus = project.flow_status;
  const createdAt = project.created_at;
  const updatedAt = project.updated_at;
  const maxSteps = getMaxSteps(projectType);
  const progressPercentage = ((currentStep - 1) / (maxSteps - 1)) * 100;
  const Icon = typeIcons[projectType] || FileCode;
  const detailHref = `/project/${project.id}`;
  const generateHref =
    projectType === "patent"
      ? `/project/${project.id}/patent/generate`
      : projectType === "trademark"
        ? `/project/${project.id}/trademark/generate`
        : `/project/${project.id}/copyright/generate`;

  const formatDate = (date: Date | string | null) => {
    if (!date) return "-";
    const d = new Date(date);
    return d.toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <Card
      className="group transition-all hover-elevate"
      data-testid={`card-project-${project.id}`}
    >
      <CardHeader className="flex flex-row items-start justify-between gap-4 pb-2">
        <div className="flex items-start gap-3">
          <div className={cn("flex h-10 w-10 items-center justify-center rounded-md", typeBgColors[projectType])}>
            <Icon className={cn("h-5 w-5", typeColors[projectType])} />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold truncate" data-testid={`text-project-${project.id}`}>
              {project.name}
            </h3>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Badge variant="outline" className="text-xs">
                {projectTypeLabels[projectType]}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {project.version}
              </Badge>
              <Badge
                className={cn("text-xs", statusColors[project.status])}
                variant="secondary"
              >
                {projectStatusLabels[project.status]}
              </Badge>
              {flowStatus ? (
                <Badge variant="secondary" className="text-xs">
                  {flowStatusLabels[flowStatus] ?? flowStatus}
                </Badge>
              ) : null}
            </div>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              data-testid={`button-project-menu-${project.id}`}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link href={detailHref} className="flex items-center gap-2">
                <Edit className="h-4 w-4" />
                编辑
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href={generateHref} className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                生成材料
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onDuplicate?.(project.id)}
              className="flex items-center gap-2"
            >
              <Copy className="h-4 w-4" />
              复制为新版本
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onExport?.(project.id)}
              disabled={!onExport}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              导出
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => onDelete?.(project.id)}
              className="flex items-center gap-2 text-destructive focus:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
              删除
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">完成进度</span>
            <span className="font-medium">{Math.round(progressPercentage)}%</span>
          </div>
          <Progress value={progressPercentage} className="h-1.5" />
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
          <span>创建于 {formatDate(createdAt)}</span>
          <span>更新于 {formatDate(updatedAt)}</span>
        </div>
        <div className="flex gap-2">
          <Link href={detailHref} className="flex-1">
            <Button size="sm" variant="outline" className="w-full">
              <Eye className="mr-2 h-4 w-4" />
              详情
            </Button>
          </Link>
          <Link href={generateHref} className="flex-1">
            <Button size="sm" className="w-full">
              <Sparkles className="mr-2 h-4 w-4" />
              生成
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
