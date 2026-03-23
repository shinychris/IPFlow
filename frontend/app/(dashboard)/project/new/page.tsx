"use client";

import { useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Save, FileCode, Lightbulb, Stamp } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";

const projectTypes = [
  { value: "copyright", label: "软著申请", icon: FileCode },
  { value: "patent", label: "专利申请", icon: Lightbulb },
  { value: "trademark", label: "商标申请", icon: Stamp },
];

export default function NewProjectPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const defaultType = searchParams.get("type") || "copyright";
  
  const [formData, setFormData] = useState({
    type: defaultType,
    name: "",
    version: "1.0",
    description: "",
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const payload = {
        name: data.name,
        project_type: data.type,
        version: data.version,
        description: data.description || undefined,
        subject_type: "individual",
        development_method: "independent",
        publication_status: "unpublished",
      };
      const res = await apiRequest("POST", "/api/v1/projects", payload);
      return res.json();
    },
    onSuccess: (data) => {
      const projectType = data.project_type ?? formData.type;
      const targetPath =
        projectType === "copyright"
          ? `/project/${data.id}/copyright/generate`
          : projectType === "patent"
            ? `/project/${data.id}/patent/generate`
            : projectType === "trademark"
              ? `/project/${data.id}/trademark/generate`
              : `/project/${data.id}`;
      toast({
        title: "创建成功",
        description: "项目已创建，正在跳转...",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/v1/projects"] });
      router.push(targetPath);
    },
    onError: () => {
      toast({
        title: "创建失败",
        description: "请检查输入信息后重试",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const selectedType = projectTypes.find(t => t.value === formData.type);
  const Icon = selectedType?.icon || FileCode;

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="新建项目"
        description="填写基本信息创建新的知识产权申请项目"
        actions={
          <Link href="/projects">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回项目列表
            </Button>
          </Link>
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
                <Label htmlFor="type">项目类型</Label>
                <Select
                  value={formData.type}
                  onValueChange={(value) => setFormData({ ...formData, type: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目类型" />
                  </SelectTrigger>
                  <SelectContent>
                    {projectTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex items-center gap-2">
                          <type.icon className="h-4 w-4" />
                          {type.label}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">项目名称 *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="请输入项目名称"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="version">版本号</Label>
                <Input
                  id="version"
                  value={formData.version}
                  onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                  placeholder="1.0"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">项目描述</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="简要描述项目内容..."
                  rows={4}
                />
              </div>

              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1"
                >
                  <Save className="mr-2 h-4 w-4" />
                  {createMutation.isPending ? "创建中..." : "创建项目"}
                </Button>
                <Link href="/projects">
                  <Button type="button" variant="outline">
                    取消
                  </Button>
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
