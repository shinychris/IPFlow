import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useAuth } from "@/hooks/use-auth";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, KeyRound, Save, Eye, EyeOff } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [displayName, setDisplayName] = useState(user?.displayName || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  const initials = (user?.displayName || user?.username || "U").slice(0, 2).toUpperCase();

  const profileMutation = useMutation({
    mutationFn: async (data: { displayName: string }) => {
      const res = await apiRequest("PATCH", "/api/auth/profile", data);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/auth/me"] });
      toast({ title: "保存成功", description: "个人信息已更新" });
    },
    onError: (error: Error) => {
      toast({ title: "保存失败", description: error.message, variant: "destructive" });
    },
  });

  const passwordMutation = useMutation({
    mutationFn: async (data: { currentPassword: string; newPassword: string }) => {
      const res = await apiRequest("POST", "/api/auth/change-password", data);
      return res.json();
    },
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast({ title: "修改成功", description: "密码已更新，下次登录时请使用新密码" });
    },
    onError: (error: Error) => {
      toast({ title: "修改失败", description: error.message, variant: "destructive" });
    },
  });

  const handleProfileSave = () => {
    if (!displayName.trim()) {
      toast({ title: "请输入昵称", variant: "destructive" });
      return;
    }
    profileMutation.mutate({ displayName: displayName.trim() });
  };

  const handlePasswordChange = () => {
    if (!currentPassword) {
      toast({ title: "请输入当前密码", variant: "destructive" });
      return;
    }
    if (newPassword.length < 6) {
      toast({ title: "新密码长度不能少于6个字符", variant: "destructive" });
      return;
    }
    if (newPassword !== confirmPassword) {
      toast({ title: "两次输入的新密码不一致", variant: "destructive" });
      return;
    }
    passwordMutation.mutate({ currentPassword, newPassword });
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="text-settings-title">个人设置</h1>
        <p className="text-muted-foreground mt-1">管理您的账户信息和安全设置</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <User className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle className="text-base">基本信息</CardTitle>
              <CardDescription>修改您的显示名称</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-lg">{initials}</AvatarFallback>
            </Avatar>
            <div>
              <div className="font-medium" data-testid="text-settings-username">{user?.username}</div>
              <div className="text-sm text-muted-foreground">
                {user?.role === "admin" ? "管理员" : "普通用户"} · 注册于 {user?.createdAt ? new Date(user.createdAt).toLocaleDateString("zh-CN") : ""}
              </div>
            </div>
          </div>

          <Separator />

          <div className="space-y-2">
            <Label htmlFor="username">用户名</Label>
            <Input
              id="username"
              value={user?.username || ""}
              disabled
              data-testid="input-settings-username"
            />
            <p className="text-xs text-muted-foreground">用户名注册后不可修改</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="displayName">昵称</Label>
            <Input
              id="displayName"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="输入您的昵称"
              maxLength={30}
              data-testid="input-settings-display-name"
            />
          </div>

          <div className="flex justify-end">
            <Button
              onClick={handleProfileSave}
              disabled={profileMutation.isPending || displayName === (user?.displayName || "")}
              data-testid="button-save-profile"
            >
              <Save className="h-4 w-4 mr-2" />
              {profileMutation.isPending ? "保存中..." : "保存信息"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <KeyRound className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle className="text-base">修改密码</CardTitle>
              <CardDescription>更新您的登录密码</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="currentPassword">当前密码</Label>
            <div className="relative">
              <Input
                id="currentPassword"
                type={showCurrentPassword ? "text" : "password"}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="输入当前密码"
                data-testid="input-current-password"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                data-testid="button-toggle-current-password"
              >
                {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="newPassword">新密码</Label>
            <div className="relative">
              <Input
                id="newPassword"
                type={showNewPassword ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="输入新密码（至少6个字符）"
                data-testid="input-new-password"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0"
                onClick={() => setShowNewPassword(!showNewPassword)}
                data-testid="button-toggle-new-password"
              >
                {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">确认新密码</Label>
            <Input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="再次输入新密码"
              data-testid="input-confirm-password"
            />
            {confirmPassword && newPassword !== confirmPassword && (
              <p className="text-xs text-destructive">两次输入的密码不一致</p>
            )}
          </div>

          <div className="flex justify-end">
            <Button
              onClick={handlePasswordChange}
              disabled={passwordMutation.isPending || !currentPassword || !newPassword || !confirmPassword}
              data-testid="button-change-password"
            >
              <KeyRound className="h-4 w-4 mr-2" />
              {passwordMutation.isPending ? "修改中..." : "修改密码"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
