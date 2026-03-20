import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, AlertTriangle, X, Clock, ChevronDown } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useState } from "react";
import type { ComplianceResult } from "@shared/types";

interface ComplianceChecklistProps {
  results: ComplianceResult[];
  className?: string;
}

const categoryLabels: Record<string, string> = {
  code: "源代码材料",
  manual: "操作说明书",
  proof: "证明材料",
  info: "软件信息",
};

const statusConfig = {
  passed: {
    icon: Check,
    label: "通过",
    className: "text-green-600 dark:text-green-400",
    badgeVariant: "default" as const,
  },
  warning: {
    icon: AlertTriangle,
    label: "待完善",
    className: "text-yellow-600 dark:text-yellow-400",
    badgeVariant: "secondary" as const,
  },
  failed: {
    icon: X,
    label: "未通过",
    className: "text-red-600 dark:text-red-400",
    badgeVariant: "destructive" as const,
  },
  pending: {
    icon: Clock,
    label: "待检查",
    className: "text-muted-foreground",
    badgeVariant: "outline" as const,
  },
};

export function ComplianceChecklist({ results, className }: ComplianceChecklistProps) {
  const [expandedCategories, setExpandedCategories] = useState<string[]>(["code", "manual", "proof", "info"]);

  const groupedResults = results.reduce((acc, result) => {
    if (!acc[result.category]) {
      acc[result.category] = [];
    }
    acc[result.category].push(result);
    return acc;
  }, {} as Record<string, ComplianceResult[]>);

  const getCategoryStatus = (categoryResults: ComplianceResult[]) => {
    if (categoryResults.some((r) => r.status === "failed")) return "failed";
    if (categoryResults.some((r) => r.status === "warning")) return "warning";
    if (categoryResults.some((r) => r.status === "pending")) return "pending";
    return "passed";
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  const passedCount = results.filter((r) => r.status === "passed").length;
  const totalCount = results.length;
  const progressPercentage = totalCount > 0 ? Math.round((passedCount / totalCount) * 100) : 0;

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-lg">合规检查清单</CardTitle>
          <Badge variant={progressPercentage === 100 ? "default" : "secondary"}>
            {passedCount}/{totalCount} 已通过
          </Badge>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {Object.entries(groupedResults).map(([category, categoryResults]) => {
          const categoryStatus = getCategoryStatus(categoryResults);
          const StatusIcon = statusConfig[categoryStatus].icon;
          const isExpanded = expandedCategories.includes(category);

          return (
            <Collapsible
              key={category}
              open={isExpanded}
              onOpenChange={() => toggleCategory(category)}
            >
              <CollapsibleTrigger
                className="flex w-full items-center justify-between rounded-md p-2 hover-elevate"
                data-testid={`compliance-category-${category}`}
              >
                <div className="flex items-center gap-2">
                  <StatusIcon
                    className={cn("h-4 w-4", statusConfig[categoryStatus].className)}
                  />
                  <span className="font-medium">{categoryLabels[category]}</span>
                  <Badge variant="outline" className="text-xs">
                    {categoryResults.filter((r) => r.status === "passed").length}/
                    {categoryResults.length}
                  </Badge>
                </div>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    isExpanded && "rotate-180"
                  )}
                />
              </CollapsibleTrigger>
              <CollapsibleContent className="pl-6 pt-2 space-y-2">
                {categoryResults.map((result) => {
                  const ItemIcon = statusConfig[result.status].icon;
                  return (
                    <div
                      key={result.ruleId}
                      className="flex items-start gap-2 text-sm"
                      data-testid={`compliance-rule-${result.ruleId}`}
                    >
                      <ItemIcon
                        className={cn(
                          "h-4 w-4 mt-0.5 flex-shrink-0",
                          statusConfig[result.status].className
                        )}
                      />
                      <div className="flex-1">
                        <div className="font-medium">{result.ruleName}</div>
                        <div className="text-muted-foreground">{result.message}</div>
                      </div>
                    </div>
                  );
                })}
              </CollapsibleContent>
            </Collapsible>
          );
        })}
      </CardContent>
    </Card>
  );
}
