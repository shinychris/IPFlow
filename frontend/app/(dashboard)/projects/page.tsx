"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Search, FileCode, Lightbulb, Stamp } from "lucide-react";
import type { Project } from "@shared/types";
import { ProjectCard } from "@/components/project-card";
import { apiRequest } from "@/lib/queryClient";
import { PageHeader } from "@/components/page-header";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";

const typeIcons = {
  copyright: FileCode,
  patent: Lightbulb,
  trademark: Stamp,
};

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");

  const { data: projects = [], isLoading } = useQuery<Project[]>({
    queryKey: ["/api/v1/projects"],
  });

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  const duplicateMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiRequest("POST", `/api/v1/projects/${id}/duplicate`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/v1/projects"] });
    },
  });

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="项目列表"
        description="管理您的所有知识产权申请项目"
        actions={
          <Link href="/project/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              新建项目
            </Button>
          </Link>
        }
      />

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索项目..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6 h-32" />
            </Card>
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="p-8 text-center">
            {search ? (
              <p className="text-muted-foreground">没有找到匹配的项目</p>
            ) : (
              <div className="space-y-4">
                <p className="text-muted-foreground">暂无项目</p>
                <Link href="/project/new">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    创建第一个项目
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
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
