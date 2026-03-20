"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Lightbulb } from "lucide-react";
import type { Project } from "@shared/types";
import { ProjectCard } from "@/components/project-card";
import { apiRequest } from "@/lib/queryClient";
import { PageHeader } from "@/components/page-header";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";

export default function PatentPage() {
  const queryClient = useQueryClient();

  const { data: projects = [], isLoading } = useQuery<Project[]>({
    queryKey: ["/api/v1/projects?project_type=patent"],
    queryFn: async () => {
      const res = await fetch("/api/v1/projects?project_type=patent");
      if (!res.ok) throw new Error("Failed to fetch projects");
      return res.json();
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiRequest("POST", `/api/v1/projects/${id}/duplicate`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/v1/projects?project_type=patent"] });
    },
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="专利申请"
        description="发明/实用新型/外观设计专利项目"
        actions={
          <Link href="/project/new?type=patent">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              新建专利项目
            </Button>
          </Link>
        }
      />

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6 h-32" />
            </Card>
          ))}
        </div>
      ) : projects.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="p-8 text-center">
            <Lightbulb className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">暂无专利项目</p>
            <Link href="/project/new?type=patent">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                创建专利项目
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onDuplicate={() => duplicateMutation.mutate(project.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
