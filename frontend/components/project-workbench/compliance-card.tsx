"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

/** 合规报告数据结构（与后端 ComplianceReport 一致） */
export interface ComplianceReportData {
  total_rules?: number;
  passed?: number;
  warnings?: number;
  failed?: number;
  overall_status?: string;
  can_export?: boolean;
  results?: Array<{
    rule_id: string;
    rule_name: string;
    category: string;
    status: "passed" | "warning" | "failed" | "skipped";
    message: string;
    suggestion?: string | null;
  }>;
}

interface ComplianceCardProps {
  /** 合规检查结果（可为空表示尚未检查） */
  report?: ComplianceReportData | null;
  /** 是否正在执行检查 */
  checking: boolean;
  /** 触发检查回调 */
  onCheck: () => void;
}

const statusVariantMap: Record<
  string,
  { label: string; className: string }
> = {
  passed: { label: "通过", className: "bg-green-100 text-green-700" },
  warning: { label: "警告", className: "bg-yellow-100 text-yellow-700" },
  failed: { label: "失败", className: "bg-red-100 text-red-700" },
  skipped: { label: "跳过", className: "bg-gray-100 text-gray-500" },
};

/**
 * 合规检查卡片（软著/专利/商标通用）。
 * 展示规则统计与逐条结果，并提供「执行合规检查」入口。
 */
export function ComplianceCard({ report, checking, onCheck }: ComplianceCardProps) {
  const results = report?.results ?? [];
  const overall = report?.overall_status;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>合规检查</span>
          {overall ? (
            <span
              className={
                "text-xs px-2 py-0.5 rounded " +
                (statusVariantMap[overall]?.className ?? "")
              }
            >
              {statusVariantMap[overall]?.label ?? overall}
            </span>
          ) : null}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button
          variant="outline"
          onClick={onCheck}
          disabled={checking}
        >
          {checking ? "检查中..." : "执行合规检查"}
        </Button>

        {report ? (
          <>
            <div className="grid grid-cols-4 gap-2 text-center text-sm">
              <div className="rounded border p-2">
                <div className="text-muted-foreground">总规则</div>
                <div className="font-semibold">{report.total_rules ?? 0}</div>
              </div>
              <div className="rounded border p-2">
                <div className="text-muted-foreground">通过</div>
                <div className="font-semibold text-green-600">
                  {report.passed ?? 0}
                </div>
              </div>
              <div className="rounded border p-2">
                <div className="text-muted-foreground">警告</div>
                <div className="font-semibold text-yellow-600">
                  {report.warnings ?? 0}
                </div>
              </div>
              <div className="rounded border p-2">
                <div className="text-muted-foreground">失败</div>
                <div className="font-semibold text-red-600">
                  {report.failed ?? 0}
                </div>
              </div>
            </div>

            {results.length > 0 ? (
              <div className="space-y-1 max-h-60 overflow-auto">
                {results.map((r) => {
                  const v = statusVariantMap[r.status] ?? statusVariantMap.skipped;
                  return (
                    <div
                      key={r.rule_id}
                      className="flex items-start gap-2 rounded border p-2 text-sm"
                    >
                      <Badge
                        variant="secondary"
                        className={"shrink-0 " + v.className}
                      >
                        {v.label}
                      </Badge>
                      <div className="min-w-0">
                        <div className="font-medium">{r.rule_name}</div>
                        <div className="text-muted-foreground">{r.message}</div>
                        {r.suggestion ? (
                          <div className="text-xs text-muted-foreground">
                            建议：{r.suggestion}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}

            <div className="text-xs text-muted-foreground">
              {report.can_export
                ? "当前材料可导出（存在警告不影响）"
                : "存在失败项，请修正后导出"}
            </div>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">
            尚未执行合规检查，点击上方按钮开始检查。
          </p>
        )}
      </CardContent>
    </Card>
  );
}
