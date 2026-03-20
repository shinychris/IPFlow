/**
 * 利润测算器组件
 * Pricing calculator - help users calculate cost savings
 */
"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { TrendingDown, Clock, DollarSign } from "lucide-react";
import type { CalculatorResult, CalculatorState } from "@/types/marketing";

const DEFAULT_STATE: CalculatorState = {
  projectCount: 10,
  billingInterval: "yearly",
  currentMethod: "agency",
  agencyFee: 800,
};

const calculateSavings = (state: CalculatorState): CalculatorResult => {
  const { projectCount, currentMethod, agencyFee } = state;

  // 传统代理成本
  const traditionalCost = projectCount * agencyFee;

  // IPFlow 成本
  const ipflowPricePerProject = 19; // 按次付费单价
  const multiplier = state.billingInterval === "yearly" ? 12 : 1;
  const ipflowCost = projectCount * ipflowPricePerProject * multiplier;

  // 计算节省
  const savings = traditionalCost - ipflowCost;
  const savingsPercentage = Math.round((savings / traditionalCost) * 100);

  // 时间节省（每个项目节省1.5天）
  const timeSaved = projectCount * 1.5;

  return {
    traditionalCost,
    ipflowCost,
    savings,
    savingsPercentage,
    timeSaved,
    timeSavedUnit: "天",
  };
};

export function PricingCalculator() {
  const [state, setState] = useState<CalculatorState>(DEFAULT_STATE);
  const result = calculateSavings(state);

  return (
    <Card className="bg-gradient-to-br from-primary/10 to-purple-500/10 border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingDown className="h-6 w-6 text-primary" />
          利润测算器
        </CardTitle>
        <CardDescription>
          计算使用 IPFlow 能为您节省多少成本和时间
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* 项目数量滑块 */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="projectCount">项目数量</Label>
            <span className="text-2xl font-bold">{state.projectCount} 个</span>
          </div>
          <Slider
            id="projectCount"
            min={1}
            max={100}
            step={1}
            value={[state.projectCount]}
            onValueChange={([value]) =>
              setState({ ...state, projectCount: value })
            }
            className="py-4"
          />
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>1个</span>
            <span>100个</span>
          </div>
        </div>

        {/* 当前方式选择 */}
        <div className="space-y-4">
          <Label>当前申请方式</Label>
          <RadioGroup
            value={state.currentMethod}
            onValueChange={(value: any) =>
              setState({ ...state, currentMethod: value })
            }
          >
            <div className="flex items-center space-x-2 border p-4 rounded-lg hover:bg-accent/50 cursor-pointer">
              <RadioGroupItem value="agency" id="agency" />
              <Label htmlFor="agency" className="flex-1 cursor-pointer">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">委托代理机构</div>
                    <div className="text-sm text-muted-foreground">
                      传统方式，平均 ¥{state.agencyFee}/项目
                    </div>
                  </div>
                </div>
              </Label>
            </div>
            <div className="flex items-center space-x-2 border p-4 rounded-lg hover:bg-accent/50 cursor-pointer">
              <RadioGroupItem value="manual" id="manual" />
              <Label htmlFor="manual" className="flex-1 cursor-pointer">
                <div className="font-medium">自己手动准备</div>
                <div className="text-sm text-muted-foreground">
                  耗时1-2天/项目，容易出错
                </div>
              </Label>
            </div>
          </RadioGroup>
        </div>

        {/* 计算结果 */}
        <div className="grid md:grid-cols-3 gap-4 pt-4 border-t">
          {/* 传统成本 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <DollarSign className="h-4 w-4" />
              <span className="text-sm">传统方式成本</span>
            </div>
            <div className="text-2xl font-bold text-muted-foreground line-through">
              ¥{result.traditionalCost.toLocaleString()}
            </div>
          </div>

          {/* IPFlow 成本 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-primary">
              <DollarSign className="h-4 w-4" />
              <span className="text-sm">IPFlow 成本</span>
            </div>
            <div className="text-3xl font-bold text-primary">
              ¥{result.ipflowCost.toLocaleString()}
            </div>
          </div>

          {/* 节省 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
              <TrendingDown className="h-4 w-4" />
              <span className="text-sm">节省</span>
            </div>
            <div className="text-3xl font-bold text-green-600 dark:text-green-400">
              ¥{result.savings.toLocaleString()}
            </div>
            <div className="text-sm text-green-600 dark:text-green-400">
              ({result.savingsPercentage}%)
            </div>
          </div>
        </div>

        {/* 时间节省 */}
        <div className="flex items-center gap-4 p-4 bg-background rounded-lg border">
          <Clock className="h-8 w-8 text-orange-500 flex-shrink-0" />
          <div>
            <div className="text-sm text-muted-foreground">时间节省</div>
            <div className="text-xl font-bold">
              {result.timeSaved} {result.timeSavedUnit}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
