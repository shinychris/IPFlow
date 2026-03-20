import { HardDrive, Users, FolderKanban, AlertTriangle } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import type { UsageStats } from '@/types/subscription';

interface UsageStatsProps {
  stats: UsageStats;
}

export function UsageStatsCard({ stats }: UsageStatsProps) {
  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-destructive';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-primary';
  };

  const showWarning = 
    stats.projects.percentage >= 80 ||
    stats.storage.percentage >= 80 ||
    stats.members.percentage >= 80;

  return (
    <div className="space-y-6">
      {showWarning && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>资源使用警告</AlertTitle>
          <AlertDescription>
            您的某些资源即将达到限额，请考虑升级计划。
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        {/* 项目使用 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">项目</CardTitle>
            <FolderKanban className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.projects.used} / {stats.projects.limit}
            </div>
            <Progress 
              value={stats.projects.percentage} 
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-2">
              剩余 {stats.projects.remaining} 个项目
            </p>
          </CardContent>
        </Card>

        {/* 存储使用 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">存储空间</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.storage.used_gb}GB / {stats.storage.limit_gb}GB
            </div>
            <Progress 
              value={stats.storage.percentage} 
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-2">
              剩余 {Math.round(stats.storage.remaining_bytes / 1024 / 1024 / 1024 * 100) / 100}GB
            </p>
          </CardContent>
        </Card>

        {/* 成员使用 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">成员</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.members.used} / {stats.members.limit}
            </div>
            <Progress 
              value={stats.members.percentage} 
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-2">
              剩余 {stats.members.remaining} 个名额
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
