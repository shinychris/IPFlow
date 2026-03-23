"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation } from "@tanstack/react-query";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Save, Download, FileCode, Lightbulb, Stamp, Sparkles } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";
import type { Project } from "@shared/types";
import { exportProject } from "@/lib/project-actions";
import {
  softwareInfoApi,
  codeBundlesApi,
  manualsApi,
  complianceApi,
  generationJobsApi,
  exportJobsApi,
} from "@/api/copyright";
import {
  patentInfoApi,
  patentClaimsApi,
  patentDescriptionApi,
  patentGenerationJobsApi,
  patentExportJobsApi,
} from "@/api/patents";
import {
  trademarkInfoApi,
  niceClassesApi,
  trademarkGenerationJobsApi,
  trademarkExportJobsApi,
} from "@/api/trademarks";
import { ManualTemplateType, type SoftwareInfoRequest } from "@/types";
import { PatentWorkbenchPanel } from "@/components/project-workbench/patent-workbench-panel";
import { TrademarkWorkbenchPanel } from "@/components/project-workbench/trademark-workbench-panel";

const projectTypeLabels: Record<string, string> = {
  copyright: "软著申请",
  patent: "专利申请",
  trademark: "商标申请",
};

const projectTypeIcons: Record<string, typeof FileCode> = {
  copyright: FileCode,
  patent: Lightbulb,
  trademark: Stamp,
};

export default function EditProjectPage() {
  const params = useParams();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const router = useRouter();
  const projectId = params.id as string;

  const { data: project, isLoading } = useQuery<Project>({
    queryKey: [`/api/v1/projects/${projectId}`],
  });

  const [formData, setFormData] = useState({
    name: "",
    version: "",
    description: "",
  });
  const [softwareForm, setSoftwareForm] = useState<SoftwareInfoRequest>({
    software_full_name: "",
    software_short_name: "",
    version_number: "1.0",
    development_language: "",
    development_environment: "",
    runtime_environment: "",
    code_line_count: undefined,
    functional_description: "",
    technical_features: "",
    target_domain: "",
  });
  const [manualTitle, setManualTitle] = useState("软件操作说明书");
  const [manualHtml, setManualHtml] = useState("");
  const [selectedManualId, setSelectedManualId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Update form data when project loads
  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name || "",
        version: project.version || "",
        description: project.description || "",
      });
      setSoftwareForm((prev) => ({
        ...prev,
        software_full_name: project.name || prev.software_full_name,
        version_number: project.version || prev.version_number,
      }));
    }
  }, [project]);

  const projectType = (project as any)?.type ?? (project as any)?.project_type;
  const isCopyrightProject = projectType === "copyright";
  const isPatentProject = projectType === "patent";
  const isTrademarkProject = projectType === "trademark";
  const flowStatus = ((project as any)?.flow_status as string | undefined) ?? "human_editing";

  const [patentForm, setPatentForm] = useState({
    patent_type: "invention",
    title: "",
    technical_field: "",
    background_art: "",
    abstract: "",
    abstract_figure_number: "",
  });
  const [patentDescriptionForm, setPatentDescriptionForm] = useState({
    technical_field: "",
    background_art: "",
    problem_solved: "",
    technical_solution: "",
    beneficial_effects: "",
    implementation: "",
  });
  const [newClaimContent, setNewClaimContent] = useState("");
  const [newClaimType, setNewClaimType] = useState<"independent" | "dependent">("independent");
  const [newClaimParent, setNewClaimParent] = useState<number | undefined>(undefined);

  const [trademarkForm, setTrademarkForm] = useState({
    trademark_type: "word",
    trademark_name: "",
    description: "",
    design_description: "",
    color_claim: "",
    special_notes: "",
  });
  const [classNumber, setClassNumber] = useState(35);
  const [goodsServicesText, setGoodsServicesText] = useState("");

  const {
    data: softwareInfo,
    refetch: refetchSoftwareInfo,
    isLoading: softwareLoading,
  } = useQuery({
    queryKey: [`/api/v1/copyright/projects/${projectId}/software-info`],
    queryFn: () => softwareInfoApi.get(projectId),
    enabled: !!projectId && isCopyrightProject,
    retry: false,
  });

  const {
    data: codeBundlesData,
    refetch: refetchCodeBundles,
  } = useQuery({
    queryKey: [`/api/v1/copyright/projects/${projectId}/code-bundles`],
    queryFn: () => codeBundlesApi.list(projectId),
    enabled: !!projectId && isCopyrightProject,
  });

  const {
    data: manualsData,
    refetch: refetchManuals,
  } = useQuery({
    queryKey: [`/api/v1/copyright/projects/${projectId}/manuals`],
    queryFn: () => manualsApi.list(projectId),
    enabled: !!projectId && isCopyrightProject,
  });

  const { data: manualDetail, refetch: refetchManualDetail } = useQuery({
    queryKey: [`/api/v1/copyright/projects/${projectId}/manuals/${selectedManualId}`],
    queryFn: () => manualsApi.getById(projectId, selectedManualId as string),
    enabled: !!projectId && !!selectedManualId && isCopyrightProject,
  });

  const {
    data: complianceData,
    refetch: refetchCompliance,
  } = useQuery({
    queryKey: [`/api/v1/compliance/projects/${projectId}`],
    queryFn: () => complianceApi.getReport(projectId),
    enabled: !!projectId && isCopyrightProject,
    retry: false,
  });

  const { data: generationJobsData, refetch: refetchGenerationJobs } = useQuery({
    queryKey: [`/api/v1/copyright/projects/${projectId}/generation-jobs`],
    queryFn: () => generationJobsApi.listByProject(projectId),
    enabled: !!projectId && isCopyrightProject,
  });

  const { data: exportJobsData, refetch: refetchExportJobs } = useQuery({
    queryKey: [`/api/v1/copyright/projects/${projectId}/export-jobs`],
    queryFn: () => exportJobsApi.listByProject(projectId),
    enabled: !!projectId && isCopyrightProject,
  });

  const { data: patentInfoData, refetch: refetchPatentInfo } = useQuery({
    queryKey: [`/api/v1/patents/projects/${projectId}/patent-info`],
    queryFn: () => patentInfoApi.get(projectId),
    enabled: !!projectId && isPatentProject,
    retry: false,
  });

  const { data: patentClaimsData, refetch: refetchPatentClaims } = useQuery({
    queryKey: [`/api/v1/patents/projects/${projectId}/claims`],
    queryFn: () => patentClaimsApi.list(projectId),
    enabled: !!projectId && isPatentProject,
    retry: false,
  });

  const { data: patentDescriptionData, refetch: refetchPatentDescription } = useQuery({
    queryKey: [`/api/v1/patents/projects/${projectId}/description`],
    queryFn: () => patentDescriptionApi.get(projectId),
    enabled: !!projectId && isPatentProject,
    retry: false,
  });

  const { data: patentGenerationJobsData, refetch: refetchPatentGenerationJobs } = useQuery({
    queryKey: [`/api/v1/patents/projects/${projectId}/generation-jobs`],
    queryFn: () => patentGenerationJobsApi.listByProject(projectId),
    enabled: !!projectId && isPatentProject,
  });

  const { data: patentExportJobsData, refetch: refetchPatentExportJobs } = useQuery({
    queryKey: [`/api/v1/patents/projects/${projectId}/export-jobs`],
    queryFn: () => patentExportJobsApi.listByProject(projectId),
    enabled: !!projectId && isPatentProject,
  });

  const { data: trademarkInfoData, refetch: refetchTrademarkInfo } = useQuery({
    queryKey: [`/api/v1/trademarks/projects/${projectId}/trademark-info`],
    queryFn: () => trademarkInfoApi.get(projectId),
    enabled: !!projectId && isTrademarkProject,
    retry: false,
  });

  const { data: trademarkSelectedClassesData, refetch: refetchTrademarkClasses } = useQuery({
    queryKey: [`/api/v1/trademarks/projects/${projectId}/nice-classes/selected`],
    queryFn: () => niceClassesApi.getSelected(projectId),
    enabled: !!projectId && isTrademarkProject,
    retry: false,
  });

  const { data: trademarkGenerationJobsData, refetch: refetchTrademarkGenerationJobs } = useQuery({
    queryKey: [`/api/v1/trademarks/projects/${projectId}/generation-jobs`],
    queryFn: () => trademarkGenerationJobsApi.listByProject(projectId),
    enabled: !!projectId && isTrademarkProject,
  });

  const { data: trademarkExportJobsData, refetch: refetchTrademarkExportJobs } = useQuery({
    queryKey: [`/api/v1/trademarks/projects/${projectId}/export-jobs`],
    queryFn: () => trademarkExportJobsApi.listByProject(projectId),
    enabled: !!projectId && isTrademarkProject,
  });

  useEffect(() => {
    if (softwareInfo) {
      setSoftwareForm({
        software_full_name: softwareInfo.software_full_name || "",
        software_short_name: softwareInfo.software_short_name || "",
        version_number: softwareInfo.version_number || formData.version || "1.0",
        development_language: softwareInfo.development_language || "",
        development_environment: softwareInfo.development_environment || "",
        runtime_environment: softwareInfo.runtime_environment || "",
        code_line_count: softwareInfo.code_line_count,
        functional_description: softwareInfo.functional_description || "",
        technical_features: softwareInfo.technical_features || "",
        target_domain: softwareInfo.target_domain || "",
      });
    }
  }, [softwareInfo, formData.version]);

  useEffect(() => {
    if (manualsData?.items?.length && !selectedManualId) {
      setSelectedManualId(manualsData.items[0].id);
    }
  }, [manualsData, selectedManualId]);

  useEffect(() => {
    if (manualDetail) {
      setManualTitle(manualDetail.title || "软件操作说明书");
      setManualHtml(manualDetail.content_html || "");
    }
  }, [manualDetail]);

  useEffect(() => {
    if (patentInfoData) {
      setPatentForm({
        patent_type: patentInfoData.patent_type || "invention",
        title: patentInfoData.title || "",
        technical_field: patentInfoData.technical_field || "",
        background_art: patentInfoData.background_art || "",
        abstract: patentInfoData.abstract || "",
        abstract_figure_number: patentInfoData.abstract_figure_number || "",
      });
    }
  }, [patentInfoData]);

  useEffect(() => {
    if (patentDescriptionData) {
      setPatentDescriptionForm({
        technical_field: patentDescriptionData.technical_field || "",
        background_art: patentDescriptionData.background_art || "",
        problem_solved: patentDescriptionData.invention_content?.problem_solved || "",
        technical_solution: patentDescriptionData.invention_content?.technical_solution || "",
        beneficial_effects: patentDescriptionData.invention_content?.beneficial_effects || "",
        implementation: patentDescriptionData.implementation || "",
      });
    }
  }, [patentDescriptionData]);

  useEffect(() => {
    if (trademarkInfoData) {
      setTrademarkForm({
        trademark_type: trademarkInfoData.trademark_type || "word",
        trademark_name: trademarkInfoData.trademark_name || "",
        description: trademarkInfoData.description || "",
        design_description: trademarkInfoData.design_description || "",
        color_claim: trademarkInfoData.color_claim || "",
        special_notes: trademarkInfoData.special_notes || "",
      });
    }
  }, [trademarkInfoData]);

  const updateMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const res = await apiRequest("PATCH", `/api/v1/projects/${projectId}`, data);
      return res.json();
    },
    onSuccess: () => {
      toast({
        title: "保存成功",
        description: "项目信息已更新",
      });
      queryClient.invalidateQueries({ queryKey: [`/api/v1/projects/${projectId}`] });
    },
    onError: () => {
      toast({
        title: "保存失败",
        description: "请重试",
        variant: "destructive",
      });
    },
  });

  const exportMutation = useMutation({
    mutationFn: async () => {
      if (!project) return;
      await exportProject(project);
    },
    onSuccess: () => {
      toast({ title: "导出已开始", description: "文件下载已触发" });
    },
    onError: () => {
      toast({ title: "导出失败", description: "请先完善项目资料后重试", variant: "destructive" });
    },
  });

  const saveSoftwareMutation = useMutation({
    mutationFn: async () => softwareInfoApi.update(projectId, softwareForm),
    onSuccess: async () => {
      toast({ title: "保存成功", description: "软件信息已更新" });
      await refetchSoftwareInfo();
      queryClient.invalidateQueries({ queryKey: [`/api/v1/projects/${projectId}`] });
    },
    onError: () => {
      toast({ title: "保存失败", description: "请检查软件信息后重试", variant: "destructive" });
    },
  });

  const uploadCodeMutation = useMutation({
    mutationFn: async (file: File) =>
      codeBundlesApi.upload(projectId, file, (p) => setUploadProgress(p)),
    onSuccess: async () => {
      toast({ title: "上传成功", description: "代码包已处理完成" });
      setUploadProgress(0);
      await refetchCodeBundles();
      await refetchSoftwareInfo();
    },
    onError: () => {
      toast({ title: "上传失败", description: "请上传 ZIP 代码包", variant: "destructive" });
      setUploadProgress(0);
    },
  });

  const createManualMutation = useMutation({
    mutationFn: async () =>
      manualsApi.create(projectId, {
        template_type: ManualTemplateType.WEB,
        title: manualTitle,
        content_html: manualHtml,
      }),
    onSuccess: async () => {
      toast({ title: "创建成功", description: "说明书已保存" });
      await refetchManuals();
    },
    onError: () => {
      toast({ title: "创建失败", description: "请先填写软件信息和说明书内容", variant: "destructive" });
    },
  });

  const updateManualMutation = useMutation({
    mutationFn: async () =>
      manualsApi.update(projectId, selectedManualId as string, {
        title: manualTitle,
        content_html: manualHtml,
      }),
    onSuccess: async () => {
      toast({ title: "更新成功", description: "说明书已更新" });
      await refetchManuals();
      await refetchManualDetail();
    },
    onError: () => {
      toast({ title: "更新失败", description: "请重试", variant: "destructive" });
    },
  });

  const runComplianceMutation = useMutation({
    mutationFn: async () => complianceApi.check(projectId),
    onSuccess: async () => {
      toast({ title: "检查完成", description: "合规结果已更新" });
      await refetchCompliance();
    },
    onError: () => {
      toast({ title: "检查失败", description: "请补充材料后重试", variant: "destructive" });
    },
  });

  const confirmMaterialsMutation = useMutation({
    mutationFn: async () => generationJobsApi.confirmMaterials(projectId),
    onSuccess: async () => {
      toast({ title: "已确认", description: "草稿已标记为人工确认，可继续导出。" });
      queryClient.invalidateQueries({ queryKey: [`/api/v1/projects/${projectId}`] });
      await refetchGenerationJobs();
    },
    onError: () => {
      toast({ title: "确认失败", description: "请先生成并检查材料", variant: "destructive" });
    },
  });

  const savePatentInfoMutation = useMutation({
    mutationFn: async () => patentInfoApi.save(projectId, patentForm as any),
    onSuccess: async () => {
      toast({ title: "保存成功", description: "专利信息已更新" });
      await refetchPatentInfo();
    },
    onError: () => {
      toast({ title: "保存失败", description: "请检查专利信息", variant: "destructive" });
    },
  });

  const savePatentDescriptionMutation = useMutation({
    mutationFn: async () =>
      patentDescriptionApi.update(projectId, {
        technical_field: patentDescriptionForm.technical_field,
        background_art: patentDescriptionForm.background_art,
        invention_content: {
          problem_solved: patentDescriptionForm.problem_solved,
          technical_solution: patentDescriptionForm.technical_solution,
          beneficial_effects: patentDescriptionForm.beneficial_effects,
        },
        implementation: patentDescriptionForm.implementation,
      }),
    onSuccess: async () => {
      toast({ title: "保存成功", description: "说明书内容已更新" });
      await refetchPatentDescription();
    },
    onError: () => {
      toast({ title: "保存失败", description: "请检查说明书内容", variant: "destructive" });
    },
  });

  const addPatentClaimMutation = useMutation({
    mutationFn: async () =>
      patentClaimsApi.create(projectId, {
        claim_number: (patentClaimsData?.claims?.length ?? 0) + 1,
        claim_type: newClaimType,
        parent_claim_number: newClaimType === "dependent" ? newClaimParent : undefined,
        content: newClaimContent,
      }),
    onSuccess: async () => {
      toast({ title: "新增成功", description: "权利要求已添加" });
      setNewClaimContent("");
      setNewClaimParent(undefined);
      await refetchPatentClaims();
    },
    onError: () => {
      toast({ title: "新增失败", description: "请检查权利要求内容", variant: "destructive" });
    },
  });

  const removePatentClaimMutation = useMutation({
    mutationFn: async (claimId: string) => patentClaimsApi.delete(projectId, claimId),
    onSuccess: async () => {
      toast({ title: "删除成功", description: "权利要求已删除" });
      await refetchPatentClaims();
    },
  });

  const confirmPatentMaterialsMutation = useMutation({
    mutationFn: async () => patentGenerationJobsApi.confirmMaterials(projectId),
    onSuccess: async () => {
      toast({ title: "已确认", description: "专利草稿已确认" });
      queryClient.invalidateQueries({ queryKey: [`/api/v1/projects/${projectId}`] });
      await refetchPatentGenerationJobs();
    },
  });

  const saveTrademarkInfoMutation = useMutation({
    mutationFn: async () => trademarkInfoApi.save(projectId, trademarkForm as any),
    onSuccess: async () => {
      toast({ title: "保存成功", description: "商标信息已更新" });
      await refetchTrademarkInfo();
    },
    onError: () => {
      toast({ title: "保存失败", description: "请检查商标信息", variant: "destructive" });
    },
  });

  const addTrademarkClassMutation = useMutation({
    mutationFn: async () =>
      niceClassesApi.addSelected(projectId, {
        class_number: classNumber,
        goods_services: goodsServicesText
          .split(/[,，\n]/)
          .map((item) => item.trim())
          .filter(Boolean),
      }),
    onSuccess: async () => {
      toast({ title: "添加成功", description: "尼斯分类已添加" });
      setGoodsServicesText("");
      await refetchTrademarkClasses();
    },
    onError: () => {
      toast({ title: "添加失败", description: "请检查分类与商品服务项", variant: "destructive" });
    },
  });

  const removeTrademarkClassMutation = useMutation({
    mutationFn: async (associationId: string) => niceClassesApi.removeSelected(projectId, associationId),
    onSuccess: async () => {
      toast({ title: "移除成功", description: "尼斯分类已移除" });
      await refetchTrademarkClasses();
    },
  });

  const confirmTrademarkMaterialsMutation = useMutation({
    mutationFn: async () => trademarkGenerationJobsApi.confirmMaterials(projectId),
    onSuccess: async () => {
      toast({ title: "已确认", description: "商标草稿已确认" });
      queryClient.invalidateQueries({ queryKey: [`/api/v1/projects/${projectId}`] });
      await refetchTrademarkGenerationJobs();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-1/3 bg-muted rounded" />
          <div className="h-64 bg-muted rounded" />
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-6">
        <p>项目不存在或已被删除</p>
        <Link href="/projects">
          <Button variant="outline" className="mt-4">
            返回项目列表
          </Button>
        </Link>
      </div>
    );
  }

  const Icon = projectTypeIcons[projectType] || FileCode;
  const generateRoute =
    isCopyrightProject
      ? `/project/${projectId}/copyright/generate`
      : isPatentProject
        ? `/project/${projectId}/patent/generate`
        : isTrademarkProject
          ? `/project/${projectId}/trademark/generate`
          : `/project/${projectId}`;

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={project.name}
        description={`${projectTypeLabels[projectType]} - 自由编辑工作台`}
        actions={
          <div className="flex gap-2">
            {isCopyrightProject || isPatentProject || isTrademarkProject ? (
              <Button variant="outline" onClick={() => router.push(generateRoute)}>
                <Sparkles className="mr-2 h-4 w-4" />
                生成材料
              </Button>
            ) : null}
            <Button variant="outline" onClick={() => exportMutation.mutate()} disabled={exportMutation.isPending}>
              <Download className="mr-2 h-4 w-4" />
              {exportMutation.isPending ? "导出中..." : "导出"}
            </Button>
            <Link href="/projects">
              <Button variant="outline">
                <ArrowLeft className="mr-2 h-4 w-4" />
                返回
              </Button>
            </Link>
          </div>
        }
      />

      <div className="max-w-4xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icon className="h-5 w-5" />
              项目基础信息
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">项目名称 *</Label>
                <Input
                  id="name"
                  value={formData.name || project.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="请输入项目名称"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="version">版本号</Label>
                <Input
                  id="version"
                  value={formData.version || project.version}
                  onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                  placeholder="1.0"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">项目描述</Label>
                <Textarea
                  id="description"
                  value={formData.description || project.description || ""}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="简要描述项目内容..."
                  rows={4}
                />
              </div>

              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="flex-1"
                >
                  <Save className="mr-2 h-4 w-4" />
                  {updateMutation.isPending ? "保存中..." : "保存更改"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>

      {isCopyrightProject && (
        <div className="space-y-6 max-w-4xl">
          <Card>
            <CardHeader>
              <CardTitle>流程与任务状态</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm text-muted-foreground space-y-1">
                <p>当前流程状态：{flowStatus}</p>
                <p>最近生成任务：{generationJobsData?.items?.[0]?.status ?? "-"}</p>
                <p>最近导出任务：{exportJobsData?.items?.[0]?.status ?? "-"}</p>
              </div>
              <Button
                variant="outline"
                onClick={() => confirmMaterialsMutation.mutate()}
                disabled={confirmMaterialsMutation.isPending}
              >
                {confirmMaterialsMutation.isPending ? "确认中..." : "确认当前材料为可导出版本"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>软件信息（自由编辑）</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="software_full_name">软件全称 *</Label>
                  <Input
                    id="software_full_name"
                    value={softwareForm.software_full_name}
                    onChange={(e) => setSoftwareForm((p) => ({ ...p, software_full_name: e.target.value }))}
                    placeholder="请输入软件全称"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="software_short_name">软件简称</Label>
                  <Input
                    id="software_short_name"
                    value={softwareForm.software_short_name || ""}
                    onChange={(e) => setSoftwareForm((p) => ({ ...p, software_short_name: e.target.value }))}
                    placeholder="请输入软件简称"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="version_number">版本号 *</Label>
                  <Input
                    id="version_number"
                    value={softwareForm.version_number}
                    onChange={(e) => setSoftwareForm((p) => ({ ...p, version_number: e.target.value }))}
                    placeholder="1.0.0"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="development_language">开发语言 *</Label>
                  <Input
                    id="development_language"
                    value={softwareForm.development_language}
                    onChange={(e) => setSoftwareForm((p) => ({ ...p, development_language: e.target.value }))}
                    placeholder="Python / TypeScript / Java"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="functional_description">功能描述</Label>
                <Textarea
                  id="functional_description"
                  value={softwareForm.functional_description || ""}
                  onChange={(e) => setSoftwareForm((p) => ({ ...p, functional_description: e.target.value }))}
                  rows={4}
                  placeholder="描述软件主要功能"
                />
              </div>
              <Button onClick={() => saveSoftwareMutation.mutate()} disabled={saveSoftwareMutation.isPending || softwareLoading}>
                {saveSoftwareMutation.isPending ? "保存中..." : "保存软件信息"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>代码材料（自由上传）</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                type="file"
                accept=".zip,application/zip"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadCodeMutation.mutate(file);
                }}
              />
              {uploadCodeMutation.isPending && (
                <p className="text-sm text-muted-foreground">正在处理代码包... {uploadProgress}%</p>
              )}
              <p className="text-sm text-muted-foreground">
                已上传代码包：{codeBundlesData?.total ?? 0} 个
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>说明书材料（自由编辑）</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="manual_selector">选择说明书</Label>
                <select
                  id="manual_selector"
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={selectedManualId ?? ""}
                  onChange={(e) => setSelectedManualId(e.target.value || null)}
                >
                  <option value="">新建说明书</option>
                  {(manualsData?.items ?? []).map((manual) => (
                    <option key={manual.id} value={manual.id}>
                      {manual.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="manual_title">说明书标题</Label>
                <Input
                  id="manual_title"
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="manual_html">说明书内容（HTML）</Label>
                <Textarea
                  id="manual_html"
                  value={manualHtml}
                  onChange={(e) => setManualHtml(e.target.value)}
                  rows={6}
                  placeholder="<h1>软件操作说明书</h1><p>请填写内容...</p>"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => createManualMutation.mutate()}
                  disabled={createManualMutation.isPending}
                  variant="outline"
                >
                  {createManualMutation.isPending ? "创建中..." : "新建说明书"}
                </Button>
                <Button
                  onClick={() => updateManualMutation.mutate()}
                  disabled={!selectedManualId || updateManualMutation.isPending}
                >
                  {updateManualMutation.isPending ? "更新中..." : "更新当前说明书"}
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                已创建说明书：{manualsData?.total ?? 0} 份
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>合规与导出</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button variant="outline" onClick={() => runComplianceMutation.mutate()} disabled={runComplianceMutation.isPending}>
                {runComplianceMutation.isPending ? "检查中..." : "执行合规检查"}
              </Button>
              <div className="text-sm text-muted-foreground">
                <p>总规则：{complianceData?.total_rules ?? 0}</p>
                <p>通过：{complianceData?.passed ?? 0}</p>
                <p>警告：{complianceData?.warnings ?? 0}</p>
                <p>失败：{complianceData?.failed ?? 0}</p>
              </div>
              <Button onClick={() => exportMutation.mutate()} disabled={exportMutation.isPending}>
                <Download className="mr-2 h-4 w-4" />
                {exportMutation.isPending ? "导出中..." : "导出申请材料"}
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {isPatentProject && (
        <PatentWorkbenchPanel
          flowStatus={flowStatus}
          generationStatus={patentGenerationJobsData?.items?.[0]?.status}
          exportStatus={patentExportJobsData?.items?.[0]?.status}
          onConfirmMaterials={() => confirmPatentMaterialsMutation.mutate()}
          patentForm={patentForm}
          onPatentFormChange={(field, value) =>
            setPatentForm((prev) => ({ ...prev, [field]: value }))
          }
          onSavePatentInfo={() => savePatentInfoMutation.mutate()}
          savingPatentInfo={savePatentInfoMutation.isPending}
          patentDescriptionForm={patentDescriptionForm}
          onPatentDescriptionChange={(field, value) =>
            setPatentDescriptionForm((prev) => ({ ...prev, [field]: value }))
          }
          onSavePatentDescription={() => savePatentDescriptionMutation.mutate()}
          savingPatentDescription={savePatentDescriptionMutation.isPending}
          claims={(patentClaimsData?.claims ?? []) as Array<{ id: string; claim_number: number; content: string }>}
          onRemoveClaim={(claimId) => removePatentClaimMutation.mutate(claimId)}
          newClaimType={newClaimType}
          onNewClaimTypeChange={setNewClaimType}
          newClaimParent={newClaimParent}
          onNewClaimParentChange={setNewClaimParent}
          newClaimContent={newClaimContent}
          onNewClaimContentChange={setNewClaimContent}
          onAddClaim={() => addPatentClaimMutation.mutate()}
          addingClaim={addPatentClaimMutation.isPending}
        />
      )}

      {isTrademarkProject && (
        <TrademarkWorkbenchPanel
          flowStatus={flowStatus}
          generationStatus={trademarkGenerationJobsData?.items?.[0]?.status}
          exportStatus={trademarkExportJobsData?.items?.[0]?.status}
          onConfirmMaterials={() => confirmTrademarkMaterialsMutation.mutate()}
          trademarkForm={trademarkForm}
          onTrademarkFormChange={(field, value) =>
            setTrademarkForm((prev) => ({ ...prev, [field]: value }))
          }
          onSaveTrademarkInfo={() => saveTrademarkInfoMutation.mutate()}
          savingTrademarkInfo={saveTrademarkInfoMutation.isPending}
          classNumber={classNumber}
          onClassNumberChange={setClassNumber}
          goodsServicesText={goodsServicesText}
          onGoodsServicesTextChange={setGoodsServicesText}
          onAddClass={() => addTrademarkClassMutation.mutate()}
          addingClass={addTrademarkClassMutation.isPending}
          classes={(trademarkSelectedClassesData?.items ?? []) as Array<{
            id: string;
            class_number: number;
            class_name: string;
            goods_services: string[];
          }>}
          onRemoveClass={(associationId) => removeTrademarkClassMutation.mutate(associationId)}
        />
      )}
    </div>
  );
}
