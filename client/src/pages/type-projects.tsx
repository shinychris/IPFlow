import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { PageHeader } from "@/components/page-header";
import { ProjectCard } from "@/components/project-card";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Search, FileCode, Lightbulb, Stamp, FolderOpen } from "lucide-react";
import { queryClient, apiRequest } from "@/lib/queryClient";
import type { Project, ProjectType } from "@shared/schema";
import { projectTypeLabels, projectTypeDescriptions } from "@shared/schema";

const typeIcons: Record<ProjectType, any> = {
  copyright: FileCode,
  patent: Lightbulb,
  trademark: Stamp,
};

interface TypeProjectsPageProps {
  type: ProjectType;
}

export default function TypeProjectsPage({ type }: TypeProjectsPageProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [, setLocation] = useLocation();

  const { data: allProjects, isLoading } = useQuery<Project[]>({
    queryKey: ["/api/projects"],
  });

  const projects = allProjects?.filter(p => p.type === type);

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

  const filteredProjects = projects?.filter((project) => {
    return project.name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const handleNewProject = async () => {
    try {
      const res = await apiRequest("POST", "/api/projects", {
        type,
        name: type === "copyright" ? "新建软著项目" : type === "patent" ? "新建专利项目" : "新建商标项目",
        version: "V1.0",
        subjectType: "enterprise",
        developmentMethod: "independent",
        publicationStatus: "unpublished",
      });
      const project = await res.json();
      setLocation(`/project/${project.id}`);
    } catch (error) {
      console.error("Failed to create project:", error);
    }
  };

  const Icon = typeIcons[type];

  return (
    <div className="p-6 max-w-[1200px] mx-auto space-y-6">
      <PageHeader
        title={projectTypeLabels[type]}
        description={projectTypeDescriptions[type]}
        actions={
          <Button onClick={handleNewProject} data-testid={`button-new-${type}-project`}>
            <Plus className="h-4 w-4 mr-2" />
            新建{projectTypeLabels[type]}项目
          </Button>
        }
      />

      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索项目..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
            data-testid="input-search-projects"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[200px] rounded-md" />
          ))}
        </div>
      ) : filteredProjects && filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onDelete={(id) => deleteProjectMutation.mutate(id)}
              onDuplicate={(id) => duplicateProjectMutation.mutate(id)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Icon || FolderOpen}
          title={`暂无${projectTypeLabels[type]}项目`}
          description={`点击上方按钮创建您的第一个${projectTypeLabels[type]}项目`}
          actionLabel={`创建${projectTypeLabels[type]}项目`}
          onAction={handleNewProject}
        />
      )}
    </div>
  );
}
