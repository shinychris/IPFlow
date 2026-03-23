"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface PatentWorkbenchPanelProps {
  flowStatus: string;
  generationStatus?: string;
  exportStatus?: string;
  onConfirmMaterials: () => void;
  patentForm: {
    patent_type: string;
    title: string;
    abstract: string;
  };
  onPatentFormChange: (field: string, value: string) => void;
  onSavePatentInfo: () => void;
  savingPatentInfo: boolean;
  patentDescriptionForm: {
    technical_field: string;
    background_art: string;
    problem_solved: string;
    technical_solution: string;
    beneficial_effects: string;
    implementation: string;
  };
  onPatentDescriptionChange: (field: string, value: string) => void;
  onSavePatentDescription: () => void;
  savingPatentDescription: boolean;
  claims: Array<{ id: string; claim_number: number; content: string }>;
  onRemoveClaim: (claimId: string) => void;
  newClaimType: "independent" | "dependent";
  onNewClaimTypeChange: (value: "independent" | "dependent") => void;
  newClaimParent?: number;
  onNewClaimParentChange: (value?: number) => void;
  newClaimContent: string;
  onNewClaimContentChange: (value: string) => void;
  onAddClaim: () => void;
  addingClaim: boolean;
}

export function PatentWorkbenchPanel({
  flowStatus,
  generationStatus,
  exportStatus,
  onConfirmMaterials,
  patentForm,
  onPatentFormChange,
  onSavePatentInfo,
  savingPatentInfo,
  patentDescriptionForm,
  onPatentDescriptionChange,
  onSavePatentDescription,
  savingPatentDescription,
  claims,
  onRemoveClaim,
  newClaimType,
  onNewClaimTypeChange,
  newClaimParent,
  onNewClaimParentChange,
  newClaimContent,
  onNewClaimContentChange,
  onAddClaim,
  addingClaim,
}: PatentWorkbenchPanelProps) {
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
            确认专利材料
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>专利信息（自由编辑）</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-4 md:grid-cols-2">
            <Input
              value={patentForm.title}
              onChange={(e) => onPatentFormChange("title", e.target.value)}
              placeholder="专利名称"
            />
            <select
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={patentForm.patent_type}
              onChange={(e) => onPatentFormChange("patent_type", e.target.value)}
            >
              <option value="invention">发明</option>
              <option value="utility_model">实用新型</option>
              <option value="design">外观设计</option>
            </select>
          </div>
          <Textarea
            value={patentForm.abstract}
            onChange={(e) => onPatentFormChange("abstract", e.target.value)}
            rows={3}
            placeholder="摘要"
          />
          <Button onClick={onSavePatentInfo} disabled={savingPatentInfo}>
            {savingPatentInfo ? "保存中..." : "保存专利信息"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>说明书（自由编辑）</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            value={patentDescriptionForm.technical_field}
            onChange={(e) => onPatentDescriptionChange("technical_field", e.target.value)}
            rows={2}
            placeholder="技术领域"
          />
          <Textarea
            value={patentDescriptionForm.background_art}
            onChange={(e) => onPatentDescriptionChange("background_art", e.target.value)}
            rows={3}
            placeholder="背景技术"
          />
          <Textarea
            value={patentDescriptionForm.problem_solved}
            onChange={(e) => onPatentDescriptionChange("problem_solved", e.target.value)}
            rows={2}
            placeholder="要解决的技术问题"
          />
          <Textarea
            value={patentDescriptionForm.technical_solution}
            onChange={(e) => onPatentDescriptionChange("technical_solution", e.target.value)}
            rows={2}
            placeholder="技术方案"
          />
          <Textarea
            value={patentDescriptionForm.beneficial_effects}
            onChange={(e) => onPatentDescriptionChange("beneficial_effects", e.target.value)}
            rows={2}
            placeholder="有益效果"
          />
          <Textarea
            value={patentDescriptionForm.implementation}
            onChange={(e) => onPatentDescriptionChange("implementation", e.target.value)}
            rows={3}
            placeholder="具体实施方式"
          />
          <Button onClick={onSavePatentDescription} disabled={savingPatentDescription}>
            {savingPatentDescription ? "保存中..." : "保存说明书"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>权利要求（自由编辑）</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2 text-sm text-muted-foreground">
            {claims.map((claim) => (
              <div key={claim.id} className="flex items-start justify-between gap-2 rounded border p-2">
                <span>
                  {claim.claim_number}. {claim.content}
                </span>
                <Button variant="ghost" size="sm" onClick={() => onRemoveClaim(claim.id)}>
                  删除
                </Button>
              </div>
            ))}
          </div>
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={newClaimType}
            onChange={(e) => onNewClaimTypeChange(e.target.value as "independent" | "dependent")}
          >
            <option value="independent">独立权利要求</option>
            <option value="dependent">从属权利要求</option>
          </select>
          {newClaimType === "dependent" ? (
            <Input
              type="number"
              value={newClaimParent ?? ""}
              onChange={(e) => onNewClaimParentChange(e.target.value ? Number(e.target.value) : undefined)}
              placeholder="引用权利要求编号"
            />
          ) : null}
          <Textarea
            value={newClaimContent}
            onChange={(e) => onNewClaimContentChange(e.target.value)}
            rows={3}
            placeholder="新增权利要求内容"
          />
          <Button onClick={onAddClaim} disabled={!newClaimContent || addingClaim}>
            新增权利要求
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
