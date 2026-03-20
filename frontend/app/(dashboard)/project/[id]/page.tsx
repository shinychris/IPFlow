"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation } from "@tanstack/react-query";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Save, Download, FileCode, Lightbulb, Stamp } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";
import type { Project } from "@shared/types";

const projectTypeLabels: Record<string, string> = {
  copyright: "软著申请",
  patent: "专利申请",
  trademark: "商标申请",
};

const projectTypeIcons: Record<string, typeof FileCode> = {
  copyright: FileCode,
  patent: Lightbulb,
  trademark: Stamp,
};

export default function EditProjectPage() {
  const params = useParams();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const projectId = params.id as string;

  const { data: project, isLoading } = useQuery<Project>({
    queryKey: [`/api/v1/projects/${projectId}`],
    queryFn: async () => {
      const res = await fetch(`/api/v1/projects/${projectId}`);
      if (!res.ok) throw new Error("Failed to fetch project");
      return res.json();
    },
  });

  const [formData, setFormData] = useState({
    name: "",
    version: "",
    description: "",
  });

  // Update form data when project loads
  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name || "",
        version: project.version || "",
        description: project.description || "",
      });
    }
  }, [project]);

  const updateMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const res = await apiRequest("PATCH", `/api/v1/projects/${projectId}`, data);
      return res.json();
    },
    onSuccess: () => {
      toast({
        title: "保存成功",
        description: "项目信息已更新",
      });
      queryClient.invalidateQueries({ queryKey: [`/api/v1/projects/${projectId}`] });
    },
    onError: () => {
      toast({
        title: "保存失败",
        description: "请重试",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-1/3 bg-muted rounded" />
          <div className="h-64 bg-muted rounded" />
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-6">
        <p>项目不存在或已被删除</p>
        <Link href="/projects">
          <Button variant="outline" className="mt-4">
            返回项目列表
          </Button>
        </Link>
      </div>
    );
  }

  const projectType = (project as any).type ?? (project as any).project_type;
  const Icon = projectTypeIcons[projectType] || FileCode;

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={project.name}
        description={`${projectTypeLabels[projectType]} - 编辑项目信息`}
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              导出
            </Button>
            <Link href="/projects">
              <Button variant="outline">
                <ArrowLeft className="mr-2 h-4 w-4" />
                返回
              </Button>
            </Link>
          </div>
        }
      />

      <div className="max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icon className="h-5 w-5" />
              项目信息
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">项目名称 *</Label>
                <Input
                  id="name"
                  value={formData.name || project.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="请输入项目名称"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="version">版本号</Label>
                <Input
                  id="version"
                  value={formData.version || project.version}
                  onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                  placeholder="1.0"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">项目描述</Label>
                <Textarea
                  id="description"
                  value={formData.description || project.description || ""}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="简要描述项目内容..."
                  rows={4}
                />
              </div>

              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="flex-1"
                >
                  <Save className="mr-2 h-4 w-4" />
                  {updateMutation.isPending ? "保存中..." : "保存更改"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
