"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Loader2, Plus, Trash2, Users } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { organizationsApi } from "@/api/organizations";
import type { Organization, OrganizationMember } from "@/types";

const roleLabels: Record<string, string> = {
  admin: "管理员",
  manager: "经理",
  member: "成员",
  viewer: "访客",
};

export default function OrganizationsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSlug, setNewSlug] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);

  const { data: orgs = [], isLoading } = useQuery({
    queryKey: ["/organizations"],
    queryFn: () => organizationsApi.list(),
    retry: false,
  });

  const { data: members = [] } = useQuery({
    queryKey: ["/organizations", selectedOrgId, "members"],
    queryFn: () => organizationsApi.getMembers(selectedOrgId as string),
    enabled: !!selectedOrgId,
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      organizationsApi.create({
        name: newName,
        slug: newSlug || newName,
        description: newDesc || undefined,
      }),
    onSuccess: () => {
      toast({ title: "创建成功", description: "组织已创建" });
      setCreateOpen(false);
      setNewName("");
      setNewSlug("");
      setNewDesc("");
      queryClient.invalidateQueries({ queryKey: ["/organizations"] });
    },
    onError: (error: any) => {
      toast({
        title: "创建失败",
        description: error?.response?.data?.detail || "请重试",
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (orgId: string) => organizationsApi.delete(orgId),
    onSuccess: () => {
      toast({ title: "已删除", description: "组织已删除" });
      setSelectedOrgId(null);
      queryClient.invalidateQueries({ queryKey: ["/organizations"] });
    },
    onError: (error: any) => {
      toast({
        title: "删除失败",
        description: error?.response?.data?.detail || "请重试",
        variant: "destructive",
      });
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: ({ orgId, memberId }: { orgId: string; memberId: string }) =>
      organizationsApi.removeMember(orgId, memberId),
    onSuccess: () => {
      toast({ title: "已移除", description: "成员已移除" });
      if (selectedOrgId) {
        queryClient.invalidateQueries({
          queryKey: ["/organizations", selectedOrgId, "members"],
        });
      }
    },
    onError: (error: any) => {
      toast({
        title: "移除失败",
        description: error?.response?.data?.detail || "请重试",
        variant: "destructive",
      });
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({
      orgId,
      memberId,
      role,
    }: {
      orgId: string;
      memberId: string;
      role: string;
    }) => organizationsApi.updateMemberRole(orgId, memberId, role),
    onSuccess: () => {
      toast({ title: "已更新", description: "成员角色已更新" });
      if (selectedOrgId) {
        queryClient.invalidateQueries({
          queryKey: ["/organizations", selectedOrgId, "members"],
        });
      }
    },
    onError: (error: any) => {
      toast({
        title: "更新失败",
        description: error?.response?.data?.detail || "请重试",
        variant: "destructive",
      });
    },
  });

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const selectedOrg = orgs.find((o: Organization) => o.id === selectedOrgId);

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="组织管理"
        description="管理您的组织与协作成员"
        actions={
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                创建组织
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>创建新组织</DialogTitle>
                <DialogDescription>
                  创建组织后可邀请成员协作管理知识产权材料
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-3 py-2">
                <div className="space-y-2">
                  <Label htmlFor="org-name">组织名称</Label>
                  <Input
                    id="org-name"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="例如：XX科技有限公司"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-slug">标识（slug）</Label>
                  <Input
                    id="org-slug"
                    value={newSlug}
                    onChange={(e) => setNewSlug(e.target.value)}
                    placeholder="留空则自动生成"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-desc">描述</Label>
                  <Textarea
                    id="org-desc"
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    rows={2}
                    placeholder="组织简介（可选）"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  onClick={() => createMutation.mutate()}
                  disabled={!newName || createMutation.isPending}
                >
                  {createMutation.isPending ? "创建中..." : "创建"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* 组织列表 */}
        <Card>
          <CardHeader>
            <CardTitle>我的组织</CardTitle>
            <CardDescription>点击组织查看成员</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {orgs.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                暂无组织，点击右上角创建。
              </p>
            ) : (
              (orgs as Organization[]).map((org) => (
                <div
                  key={org.id}
                  className={`flex items-center justify-between rounded border p-3 cursor-pointer hover:bg-accent ${
                    selectedOrgId === org.id ? "border-primary bg-accent" : ""
                  }`}
                  onClick={() => setSelectedOrgId(org.id)}
                >
                  <div className="min-w-0">
                    <div className="font-medium truncate">{org.name}</div>
                    <div className="text-xs text-muted-foreground truncate">
                      {org.description || "—"}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`确定删除组织「${org.name}」？`)) {
                        deleteMutation.mutate(org.id);
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* 成员管理 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              成员管理
            </CardTitle>
            <CardDescription>
              {selectedOrg
                ? `${selectedOrg.name} 的成员`
                : "请先在左侧选择一个组织"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {!selectedOrgId ? (
              <p className="text-sm text-muted-foreground">未选择组织</p>
            ) : members.length === 0 ? (
              <p className="text-sm text-muted-foreground">暂无成员</p>
            ) : (
              (members as OrganizationMember[]).map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between rounded border p-3"
                >
                  <div className="min-w-0">
                    <div className="font-medium truncate">
                      {m.user?.display_name || m.user?.username || "成员"}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {m.user?.username ?? m.user_id}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      className="h-8 rounded-md border border-input bg-background px-2 text-xs"
                      value={m.role}
                      onChange={(e) =>
                        updateRoleMutation.mutate({
                          orgId: selectedOrgId,
                          memberId: m.id,
                          role: e.target.value,
                        })
                      }
                    >
                      {Object.entries(roleLabels).map(([val, label]) => (
                        <option key={val} value={val}>
                          {label}
                        </option>
                      ))}
                    </select>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        removeMemberMutation.mutate({
                          orgId: selectedOrgId,
                          memberId: m.id,
                        })
                      }
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))
            )}
            {selectedOrgId ? (
              <Badge variant="outline">共 {members.length} 名成员</Badge>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
