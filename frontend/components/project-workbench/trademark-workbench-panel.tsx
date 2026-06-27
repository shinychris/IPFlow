"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ComplianceCard, type ComplianceReportData } from "./compliance-card";

interface TrademarkClassItem {
  id: string;
  class_number: number;
  class_name: string;
  goods_services: string[];
}

interface TrademarkWorkbenchPanelProps {
  flowStatus: string;
  generationStatus?: string;
  exportStatus?: string;
  onConfirmMaterials: () => void;
  trademarkForm: {
    trademark_type: string;
    trademark_name: string;
    description: string;
    special_notes: string;
  };
  onTrademarkFormChange: (field: string, value: string) => void;
  onSaveTrademarkInfo: () => void;
  savingTrademarkInfo: boolean;
  classNumber: number;
  onClassNumberChange: (value: number) => void;
  goodsServicesText: string;
  onGoodsServicesTextChange: (value: string) => void;
  onAddClass: () => void;
  addingClass: boolean;
  classes: TrademarkClassItem[];
  onRemoveClass: (associationId: string) => void;
  // 合规检查
  complianceReport?: ComplianceReportData | null;
  complianceChecking?: boolean;
  onRunCompliance?: () => void;
}

export function TrademarkWorkbenchPanel({
  flowStatus,
  generationStatus,
  exportStatus,
  onConfirmMaterials,
  trademarkForm,
  onTrademarkFormChange,
  onSaveTrademarkInfo,
  savingTrademarkInfo,
  classNumber,
  onClassNumberChange,
  goodsServicesText,
  onGoodsServicesTextChange,
  onAddClass,
  addingClass,
  classes,
  onRemoveClass,
  complianceReport,
  complianceChecking,
  onRunCompliance,
}: TrademarkWorkbenchPanelProps) {
  return (
    <div className="space-y-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle>流程与任务状态</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>当前流程状态：{flowStatus}</p>
          <p>最近生成任务：{generationStatus ?? "-"}</p>
          <p>最近导出任务：{exportStatus ?? "-"}</p>
          <Button variant="outline" onClick={onConfirmMaterials}>
            确认商标材料
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>商标信息（自由编辑）</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={trademarkForm.trademark_type}
            onChange={(e) => onTrademarkFormChange("trademark_type", e.target.value)}
          >
            <option value="word">文字商标</option>
            <option value="device">图形商标</option>
            <option value="composite">组合商标</option>
            <option value="3d">三维商标</option>
            <option value="sound">声音商标</option>
            <option value="color">颜色商标</option>
          </select>
          <Input
            value={trademarkForm.trademark_name}
            onChange={(e) => onTrademarkFormChange("trademark_name", e.target.value)}
            placeholder="商标名称"
          />
          <Textarea
            value={trademarkForm.description}
            onChange={(e) => onTrademarkFormChange("description", e.target.value)}
            rows={3}
            placeholder="商标描述"
          />
          <Textarea
            value={trademarkForm.special_notes}
            onChange={(e) => onTrademarkFormChange("special_notes", e.target.value)}
            rows={2}
            placeholder="特殊说明"
          />
          <Button onClick={onSaveTrademarkInfo} disabled={savingTrademarkInfo}>
            {savingTrademarkInfo ? "保存中..." : "保存商标信息"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>尼斯分类（自由编辑）</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <Input
              type="number"
              min={1}
              max={45}
              value={classNumber}
              onChange={(e) => onClassNumberChange(Number(e.target.value || 1))}
              placeholder="类别号"
            />
            <Input
              value={goodsServicesText}
              onChange={(e) => onGoodsServicesTextChange(e.target.value)}
              placeholder="商品/服务项，逗号分隔"
            />
          </div>
          <Button onClick={onAddClass} disabled={addingClass}>
            添加分类
          </Button>
          <div className="space-y-2 text-sm text-muted-foreground">
            {classes.map((item) => (
              <div key={item.id} className="flex items-start justify-between gap-2 rounded border p-2">
                <span>
                  第{item.class_number}类 {item.class_name}：{(item.goods_services || []).join("、")}
                </span>
                <Button variant="ghost" size="sm" onClick={() => onRemoveClass(item.id)}>
                  删除
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {onRunCompliance ? (
        <ComplianceCard
          report={complianceReport}
          checking={!!complianceChecking}
          onCheck={onRunCompliance}
        />
      ) : null}
    </div>
  );
}
