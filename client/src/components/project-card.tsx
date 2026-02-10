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
import { MoreHorizontal, FileCode, Lightbulb, Stamp, Edit, Trash2, Copy, Download } from "lucide-react";
import { Link } from "wouter";
import {
  type Project,
  projectStatusLabels,
  projectTypeLabels,
  subjectTypeLabels,
  getMaxSteps,
} from "@shared/schema";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: string) => void;
  onDuplicate?: (id: string) => void;
}

const statusColors: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  in_progress: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  completed: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  exported: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
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

export function ProjectCard({ project, onDelete, onDuplicate }: ProjectCardProps) {
  const maxSteps = getMaxSteps(project.type);
  const progressPercentage = ((project.currentStep - 1) / (maxSteps - 1)) * 100;
  const Icon = typeIcons[project.type] || FileCode;

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
          <div className={cn("flex h-10 w-10 items-center justify-center rounded-md", typeBgColors[project.type])}>
            <Icon className={cn("h-5 w-5", typeColors[project.type])} />
          </div>
          <div className="min-w-0">
            <Link href={`/project/${project.id}`}>
              <h3 className="font-semibold truncate hover:text-primary transition-colors cursor-pointer" data-testid={`link-project-${project.id}`}>
                {project.name}
              </h3>
            </Link>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Badge variant="outline" className="text-xs">
                {projectTypeLabels[project.type]}
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
              <Link href={`/project/${project.id}`} className="flex items-center gap-2">
                <Edit className="h-4 w-4" />
                编辑
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onDuplicate?.(project.id)}
              className="flex items-center gap-2"
            >
              <Copy className="h-4 w-4" />
              复制为新版本
            </DropdownMenuItem>
            <DropdownMenuItem className="flex items-center gap-2">
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
          <span>创建于 {formatDate(project.createdAt)}</span>
          <span>更新于 {formatDate(project.updatedAt)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
