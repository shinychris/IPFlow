/**
 * 组织切换器组件
 * 
 * 用于在侧边栏切换当前组织
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Building2, ChevronDown, Plus, Settings, Users } from "lucide-react";
import { useOrganizationStore } from "@/stores/organization-store";
import { useUIStore } from "@/stores/ui-store";

const planLabels: Record<string, string> = {
  free: "按次付费",
  single: "按次付费",
  pro: "专业版",
  enterprise: "企业版",
};

const planColors: Record<string, string> = {
  free: "bg-emerald-100 text-emerald-800",
  single: "bg-emerald-100 text-emerald-800",
  pro: "bg-blue-100 text-blue-800",
  enterprise: "bg-purple-100 text-purple-800",
};

export function OrganizationSwitcher() {
  const router = useRouter();
  const {
    organizations,
    currentOrganization,
    isLoading,
    fetchOrganizations,
    setCurrentOrganization,
    createOrganization,
  } = useOrganizationStore();
  const { addToast } = useUIStore();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    slug: "",
    description: "",
  });

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  const handleCreate = async () => {
    try {
      await createOrganization(createForm);
      setIsCreateOpen(false);
      setCreateForm({ name: "", slug: "", description: "" });
      addToast({
        title: "创建成功",
        description: "组织已创建",
        variant: "success",
      });
    } catch {
      // 错误已在 store 中处理
    }
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/[\s_-]+/g, "-")
      .replace(/^-+|-+$/g, "");
  };

  if (!currentOrganization) {
    return (
      <Button
        variant="outline"
        className="w-full justify-start"
        onClick={() => setIsCreateOpen(true)}
      >
        <Plus className="mr-2 h-4 w-4" />
        创建组织
      </Button>
    );
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="w-full justify-between"
            disabled={isLoading}
          >
            <div className="flex items-center gap-2 truncate">
              <Building2 className="h-4 w-4" />
              <span className="truncate">{currentOrganization.name}</span>
            </div>
            <ChevronDown className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-64" align="start">
          <DropdownMenuLabel>
            <div className="flex items-center justify-between">
              <span>我的组织</span>
              <Badge
                variant="secondary"
                className={planColors[currentOrganization.plan_type || "free"]}
              >
                {planLabels[currentOrganization.plan_type || "free"]}
              </Badge>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />

          {organizations.map((org) => (
            <DropdownMenuItem
              key={org.id}
              className="cursor-pointer"
              onClick={() => setCurrentOrganization(org)}
            >
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  <span className={org.id === currentOrganization.id ? "font-medium" : ""}>
                    {org.name}
                  </span>
                </div>
                {org.id === currentOrganization.id && (
                  <div className="h-2 w-2 rounded-full bg-primary" />
                )}
              </div>
            </DropdownMenuItem>
          ))}

          <DropdownMenuSeparator />

          <DropdownMenuItem
            className="cursor-pointer"
            onClick={() => setIsCreateOpen(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
            创建新组织
          </DropdownMenuItem>

          <DropdownMenuItem
            className="cursor-pointer"
            onClick={() => router.push("/settings/organization")}
          >
            <Settings className="mr-2 h-4 w-4" />
            组织设置
          </DropdownMenuItem>

          <DropdownMenuItem
            className="cursor-pointer"
            onClick={() => router.push("/settings/members")}
          >
            <Users className="mr-2 h-4 w-4" />
            成员管理
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* 创建组织对话框 */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建组织</DialogTitle>
            <DialogDescription>
              创建一个新的组织来管理您的项目
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">组织名称</Label>
              <Input
                id="name"
                placeholder="输入组织名称"
                value={createForm.name}
                onChange={(e) => {
                  const name = e.target.value;
                  setCreateForm({
                    ...createForm,
                    name,
                    slug: generateSlug(name),
                  });
                }}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="slug">组织标识</Label>
              <Input
                id="slug"
                placeholder="organization-slug"
                value={createForm.slug}
                onChange={(e) =>
                  setCreateForm({ ...createForm, slug: e.target.value })
                }
              />
              <p className="text-xs text-muted-foreground">
                用于 URL 和组织唯一标识
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">描述（可选）</Label>
              <Input
                id="description"
                placeholder="组织描述"
                value={createForm.description}
                onChange={(e) =>
                  setCreateForm({ ...createForm, description: e.target.value })
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!createForm.name || !createForm.slug || isLoading}
            >
              {isLoading ? "创建中..." : "创建"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
