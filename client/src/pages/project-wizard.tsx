import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useRoute, useLocation } from "wouter";
import { PageHeader } from "@/components/page-header";
import { StepIndicator } from "@/components/step-indicator";
import { ComplianceChecklist } from "@/components/compliance-checklist";
import { FileUploader } from "@/components/file-uploader";
import { CodePreview } from "@/components/code-preview";
import { DocumentEditor } from "@/components/document-editor";
import { ExportPreview } from "@/components/export-preview";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { queryClient, apiRequest } from "@/lib/queryClient";
import {
  ArrowLeft,
  ArrowRight,
  Save,
  Download,
  FileCode,
  Building2,
  User,
  GraduationCap,
  CheckCircle,
} from "lucide-react";
import {
  type Project,
  type SoftwareInfo,
  type PatentInfo,
  type TrademarkInfo,
  type ComplianceResult,
  type ProjectType,
  type PatentType,
  type TrademarkType,
  subjectTypes,
  developmentMethods,
  publicationStatuses,
  templateTypes,
  patentTypes,
  trademarkTypes,
  niceClassifications,
  subjectTypeLabels,
  developmentMethodLabels,
  publicationStatusLabels,
  templateTypeLabels,
  patentTypeLabels,
  trademarkTypeLabels,
  projectTypeLabels,
  getMaxSteps,
  getWizardSteps,
  type SubjectType,
  type DevelopmentMethod,
  type PublicationStatus,
  type TemplateType,
  type NiceClassSelection,
} from "@shared/schema";

const subjectTypeIcons = {
  individual: User,
  enterprise: Building2,
  institution: GraduationCap,
};

function getInitialComplianceResults(type: ProjectType): ComplianceResult[] {
  switch (type) {
    case "copyright":
      return [
        { ruleId: "info-name", ruleName: "软件名称", category: "info", status: "pending", message: "请填写软件全称" },
        { ruleId: "info-version", ruleName: "版本号", category: "info", status: "pending", message: "请填写版本号" },
        { ruleId: "info-language", ruleName: "开发语言", category: "info", status: "pending", message: "请填写开发语言" },
        { ruleId: "code-upload", ruleName: "源代码上传", category: "code", status: "pending", message: "请上传源代码文件" },
        { ruleId: "code-pages", ruleName: "页数要求(60页)", category: "code", status: "pending", message: "需生成60页源代码" },
        { ruleId: "code-lines", ruleName: "每页行数(≥50行)", category: "code", status: "pending", message: "每页至少50行" },
        { ruleId: "code-header", ruleName: "页眉格式", category: "code", status: "pending", message: "需包含软件全称+版本号" },
        { ruleId: "manual-pages", ruleName: "说明书页数(≥15页)", category: "manual", status: "pending", message: "说明书至少15页" },
        { ruleId: "manual-lines", ruleName: "每页行数(≥30行)", category: "manual", status: "pending", message: "每页至少30行" },
        { ruleId: "manual-toc", ruleName: "目录结构", category: "manual", status: "pending", message: "需包含完整目录" },
        { ruleId: "proof-identity", ruleName: "身份证明", category: "proof", status: "pending", message: "请上传身份证明文件" },
      ];
    case "patent":
      return [
        { ruleId: "patent-title", ruleName: "发明名称", category: "info", status: "pending", message: "请填写发明名称" },
        { ruleId: "patent-abstract", ruleName: "摘要", category: "info", status: "pending", message: "请填写摘要" },
        { ruleId: "patent-applicant", ruleName: "申请人信息", category: "info", status: "pending", message: "请填写申请人信息" },
        { ruleId: "patent-claims", ruleName: "权利要求书", category: "claims", status: "pending", message: "请编写权利要求书" },
      ];
    case "trademark":
      return [
        { ruleId: "trademark-name", ruleName: "商标名称", category: "info", status: "pending", message: "请填写商标名称" },
        { ruleId: "trademark-image", ruleName: "商标图样", category: "info", status: "pending", message: "请上传商标图样" },
        { ruleId: "trademark-class", ruleName: "商品分类", category: "classification", status: "pending", message: "请选择至少一个尼斯分类" },
      ];
  }
}

export default function ProjectWizardPage() {
  const [, params] = useRoute("/project/:id");
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const projectId = params?.id;
  const isNew = projectId === "new";

  const urlProjectType = (new URLSearchParams(window.location.search).get("type") || "copyright") as ProjectType;

  const [currentStep, setCurrentStep] = useState(1);
  const [isNavigating, setIsNavigating] = useState(false);
  const [projectType, setProjectType] = useState<ProjectType>(urlProjectType);

  const [formData, setFormData] = useState({
    name: "",
    version: "V1.0",
    subjectType: "individual" as SubjectType,
    developmentMethod: "independent" as DevelopmentMethod,
    publicationStatus: "unpublished" as PublicationStatus,
    fullName: "",
    shortName: "",
    versionNumber: "V1.0",
    developmentLanguage: "",
    developmentEnvironment: "",
    runtimeEnvironment: "",
    codeLineCount: 0,
    functionalDescription: "",
    technicalFeatures: "",
    targetDomain: "",
    completionDate: "",
    templateType: "web" as TemplateType,
  });

  const [patentFormData, setPatentFormData] = useState({
    patentType: "invention" as PatentType,
    title: "",
    abstract: "",
    applicantName: "",
    applicantAddress: "",
    inventorNames: "",
    agencyName: "",
    agentName: "",
    claimsText: "",
    technicalField: "",
    backgroundArt: "",
    technicalProblem: "",
    technicalSolution: "",
    beneficialEffects: "",
    drawingsDescription: "",
  });

  const [trademarkFormData, setTrademarkFormData] = useState({
    trademarkType: "text" as TrademarkType,
    trademarkName: "",
    applicantName: "",
    applicantAddress: "",
    applicantType: "enterprise" as "individual" | "enterprise" | "institution",
    contactPerson: "",
    contactPhone: "",
    contactEmail: "",
    colorClaim: "",
    designDescription: "",
  });

  const [niceClasses, setNiceClasses] = useState<NiceClassSelection[]>([]);

  const [codeContent, setCodeContent] = useState("");
  const [complianceResults, setComplianceResults] = useState<ComplianceResult[]>(
    getInitialComplianceResults(projectType)
  );

  const { data: project, isLoading: isLoadingProject } = useQuery<Project>({
    queryKey: ["/api/projects", projectId],
    enabled: !isNew && !!projectId,
  });

  const { data: softwareInfo } = useQuery<SoftwareInfo>({
    queryKey: ["/api/projects", projectId, "software-info"],
    enabled: !isNew && !!projectId && projectType === "copyright",
  });

  const { data: patentInfo } = useQuery<PatentInfo>({
    queryKey: ["/api/projects", projectId, "patent-info"],
    enabled: !isNew && !!projectId && projectType === "patent",
  });

  const { data: trademarkInfo } = useQuery<TrademarkInfo>({
    queryKey: ["/api/projects", projectId, "trademark-info"],
    enabled: !isNew && !!projectId && projectType === "trademark",
  });

  const { data: codeBundles } = useQuery<{
    id: string;
    fileName: string;
    extractedContent: string | null;
    extractedPages: number;
    pagesData: {
      pageNumber: number;
      content: string;
      lineStart: number;
      lineEnd: number;
      section: 'first' | 'last';
    }[] | null;
    hasEnoughCode: boolean;
    totalLines: number;
  }[]>({
    queryKey: ["/api/projects", projectId, "code-bundles"],
    enabled: !isNew && !!projectId && projectType === "copyright",
  });

  useEffect(() => {
    if (project) {
      setProjectType(project.type as ProjectType);
      if (!isNavigating) {
        setCurrentStep(project.currentStep);
      }
      setFormData((prev) => ({
        ...prev,
        name: project.name,
        version: project.version,
        subjectType: project.subjectType,
        developmentMethod: project.developmentMethod,
        publicationStatus: project.publicationStatus,
      }));
      setComplianceResults(getInitialComplianceResults(project.type as ProjectType));
    }
  }, [project]);

  useEffect(() => {
    if (softwareInfo) {
      setFormData((prev) => ({
        ...prev,
        fullName: softwareInfo.fullName,
        shortName: softwareInfo.shortName || "",
        versionNumber: softwareInfo.versionNumber,
        developmentLanguage: softwareInfo.developmentLanguage,
        developmentEnvironment: softwareInfo.developmentEnvironment || "",
        runtimeEnvironment: softwareInfo.runtimeEnvironment || "",
        codeLineCount: softwareInfo.codeLineCount || 0,
        functionalDescription: softwareInfo.functionalDescription || "",
        technicalFeatures: softwareInfo.technicalFeatures || "",
        targetDomain: softwareInfo.targetDomain || "",
        completionDate: softwareInfo.completionDate || "",
      }));
    }
  }, [softwareInfo]);

  useEffect(() => {
    if (patentInfo) {
      setPatentFormData({
        patentType: patentInfo.patentType,
        title: patentInfo.title || "",
        abstract: patentInfo.abstract || "",
        applicantName: patentInfo.applicantName || "",
        applicantAddress: patentInfo.applicantAddress || "",
        inventorNames: (patentInfo.inventorNames || []).join(", "),
        agencyName: patentInfo.agencyName || "",
        agentName: patentInfo.agentName || "",
        claimsText: patentInfo.claimsText || "",
        technicalField: patentInfo.technicalField || "",
        backgroundArt: patentInfo.backgroundArt || "",
        technicalProblem: patentInfo.technicalProblem || "",
        technicalSolution: patentInfo.technicalSolution || "",
        beneficialEffects: patentInfo.beneficialEffects || "",
        drawingsDescription: patentInfo.drawingsDescription || "",
      });
    }
  }, [patentInfo]);

  useEffect(() => {
    if (trademarkInfo) {
      setTrademarkFormData({
        trademarkType: trademarkInfo.trademarkType,
        trademarkName: trademarkInfo.trademarkName || "",
        applicantName: trademarkInfo.applicantName || "",
        applicantAddress: trademarkInfo.applicantAddress || "",
        applicantType: (trademarkInfo.applicantType as "individual" | "enterprise" | "institution") || "enterprise",
        contactPerson: trademarkInfo.contactPerson || "",
        contactPhone: trademarkInfo.contactPhone || "",
        contactEmail: trademarkInfo.contactEmail || "",
        colorClaim: trademarkInfo.colorClaim || "",
        designDescription: trademarkInfo.designDescription || "",
      });
      setNiceClasses(trademarkInfo.niceClasses || []);
    }
  }, [trademarkInfo]);

  useEffect(() => {
    if (codeBundles && codeBundles.length > 0) {
      const latestBundle = codeBundles[codeBundles.length - 1];
      setCodeContent(latestBundle.extractedContent || "");
      if (latestBundle.pagesData) {
        setCodeProcessingResult({
          totalFiles: 0,
          totalLines: latestBundle.totalLines,
          pageCount: latestBundle.extractedPages,
          fileTypes: {},
          largestFiles: [],
          warnings: [],
          hasEnoughCode: latestBundle.hasEnoughCode,
          pages: latestBundle.pagesData,
        });
        setComplianceResults((prev) =>
          prev.map((r) => {
            if (r.ruleId === "code-upload") {
              return { ...r, status: "passed", message: `已上传 ${latestBundle.fileName}` };
            }
            if (r.ruleId === "code-pages") {
              return { 
                ...r, 
                status: latestBundle.extractedPages >= 60 ? "passed" : "warning",
                message: latestBundle.hasEnoughCode 
                  ? `已生成 ${latestBundle.extractedPages} 页` 
                  : `已生成 ${latestBundle.extractedPages} 页（代码不足，已自动填充）`
              };
            }
            if (r.ruleId === "code-lines") {
              return { ...r, status: "passed", message: "每页50行，已自动格式化" };
            }
            if (r.ruleId === "code-header") {
              return { ...r, status: "passed", message: "已添加行号格式" };
            }
            return r;
          })
        );
      }
    }
  }, [codeBundles]);

  const maxSteps = getMaxSteps(projectType);

  const createProjectMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest("POST", "/api/projects", {
        type: projectType,
        name: formData.name,
        version: formData.version,
        subjectType: formData.subjectType,
        developmentMethod: formData.developmentMethod,
        publicationStatus: formData.publicationStatus,
        status: "in_progress",
        currentStep: 2,
      });
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/projects"] });
      setLocation(`/project/${data.id}`);
      setCurrentStep(2);
      const stepLabel = projectType === "copyright" ? "软件信息" : projectType === "patent" ? "专利信息" : "商标信息";
      toast({ title: "项目创建成功", description: `请继续填写${stepLabel}` });
    },
  });

  const updateProjectMutation = useMutation({
    mutationFn: async (step: number) => {
      await apiRequest("PATCH", `/api/projects/${projectId}`, {
        currentStep: step,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/projects", projectId] });
    },
    onSettled: () => {
      setIsNavigating(false);
    },
    onError: () => {
      toast({ title: "步骤更新失败", description: "请重试", variant: "destructive" });
    },
  });

  const saveSoftwareInfoMutation = useMutation({
    mutationFn: async () => {
      await apiRequest("POST", `/api/projects/${projectId}/software-info`, {
        projectId,
        fullName: formData.fullName,
        shortName: formData.shortName,
        versionNumber: formData.versionNumber,
        developmentLanguage: formData.developmentLanguage,
        developmentEnvironment: formData.developmentEnvironment,
        runtimeEnvironment: formData.runtimeEnvironment,
        codeLineCount: formData.codeLineCount,
        functionalDescription: formData.functionalDescription,
        technicalFeatures: formData.technicalFeatures,
        targetDomain: formData.targetDomain,
        completionDate: formData.completionDate,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/projects", projectId, "software-info"] });
      toast({ title: "保存成功" });
    },
  });

  const savePatentInfoMutation = useMutation({
    mutationFn: async () => {
      await apiRequest("POST", `/api/projects/${projectId}/patent-info`, {
        projectId,
        patentType: patentFormData.patentType,
        title: patentFormData.title,
        abstract: patentFormData.abstract,
        applicantName: patentFormData.applicantName,
        applicantAddress: patentFormData.applicantAddress,
        inventorNames: patentFormData.inventorNames.split(",").map((s) => s.trim()).filter(Boolean),
        agencyName: patentFormData.agencyName,
        agentName: patentFormData.agentName,
        claimsText: patentFormData.claimsText,
        technicalField: patentFormData.technicalField,
        backgroundArt: patentFormData.backgroundArt,
        technicalProblem: patentFormData.technicalProblem,
        technicalSolution: patentFormData.technicalSolution,
        beneficialEffects: patentFormData.beneficialEffects,
        drawingsDescription: patentFormData.drawingsDescription,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/projects", projectId, "patent-info"] });
      toast({ title: "保存成功" });
    },
  });

  const saveTrademarkInfoMutation = useMutation({
    mutationFn: async () => {
      await apiRequest("POST", `/api/projects/${projectId}/trademark-info`, {
        projectId,
        trademarkType: trademarkFormData.trademarkType,
        trademarkName: trademarkFormData.trademarkName,
        applicantName: trademarkFormData.applicantName,
        applicantAddress: trademarkFormData.applicantAddress,
        applicantType: trademarkFormData.applicantType,
        contactPerson: trademarkFormData.contactPerson,
        contactPhone: trademarkFormData.contactPhone,
        contactEmail: trademarkFormData.contactEmail,
        colorClaim: trademarkFormData.colorClaim,
        designDescription: trademarkFormData.designDescription,
        niceClasses,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/projects", projectId, "trademark-info"] });
      toast({ title: "保存成功" });
    },
  });

  const handleSaveDraft = () => {
    switch (projectType) {
      case "copyright":
        saveSoftwareInfoMutation.mutate();
        break;
      case "patent":
        savePatentInfoMutation.mutate();
        break;
      case "trademark":
        saveTrademarkInfoMutation.mutate();
        break;
    }
  };

  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    if (!projectId || isNew) return;
    
    setIsExporting(true);
    toast({ title: "正在生成导出包", description: "请稍候..." });
    
    try {
      await apiRequest("POST", `/api/projects/${projectId}/export`, {});
      
      const downloadUrl = `/api/projects/${projectId}/export/download`;
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = "";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({ title: "导出成功", description: "文件已开始下载" });
      queryClient.invalidateQueries({ queryKey: ["/api/projects", projectId] });
    } catch (error) {
      console.error("Export error:", error);
      toast({ title: "导出失败", description: "请重试", variant: "destructive" });
    } finally {
      setIsExporting(false);
    }
  };

  const handleNext = () => {
    if (isNew && currentStep === 1) {
      if (!formData.name) {
        toast({ title: "请填写项目名称", variant: "destructive" });
        return;
      }
      createProjectMutation.mutate();
    } else {
      const nextStep = Math.min(currentStep + 1, maxSteps);
      setCurrentStep(nextStep);
      updateProjectMutation.mutate(nextStep);
    }
  };

  const handlePrev = () => {
    const prevStep = Math.max(currentStep - 1, 1);
    setCurrentStep(prevStep);
    if (!isNew) {
      updateProjectMutation.mutate(prevStep);
    }
  };

  const [isUploadingCode, setIsUploadingCode] = useState(false);
  const [codeProcessingResult, setCodeProcessingResult] = useState<{
    totalFiles: number;
    totalLines: number;
    pageCount: number;
    fileTypes: Record<string, number>;
    largestFiles: { path: string; lines: number }[];
    warnings: string[];
    hasEnoughCode: boolean;
    pages: {
      pageNumber: number;
      content: string;
      lineStart: number;
      lineEnd: number;
      section: 'first' | 'last';
    }[];
  } | null>(null);

  const handleCodeUpload = async (files: File[]) => {
    if (!projectId || files.length === 0) return;
    
    setIsUploadingCode(true);
    toast({ title: "正在上传文件", description: "请稍候..." });
    
    try {
      const formDataUpload = new FormData();
      formDataUpload.append("file", files[0]);
      
      const response = await fetch(`/api/projects/${projectId}/upload-code`, {
        method: "POST",
        body: formDataUpload,
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        const errorMessage = result.message || "请检查文件格式后重试";
        setCodeContent("");
        setCodeProcessingResult(null);
        setComplianceResults((prev) =>
          prev.map((r) => {
            if (r.category === "code") {
              if (r.ruleId === "code-upload") {
                return { ...r, status: "failed", message: errorMessage };
              }
              return { ...r, status: "pending", message: "请先上传有效的源代码文件" };
            }
            return r;
          })
        );
        toast({ 
          title: "上传失败", 
          description: errorMessage,
          variant: "destructive"
        });
        return;
      }
      
      setCodeContent(result.bundle.extractedContent || "");
      setCodeProcessingResult(result.processingResult);
      
      setComplianceResults((prev) =>
        prev.map((r) => {
          if (r.ruleId === "code-upload") {
            return { ...r, status: "passed", message: `已上传 ${files[0]?.name}` };
          }
          if (r.ruleId === "code-pages") {
            const hasEnough = result.processingResult.hasEnoughCode;
            const pageCount = result.processingResult.pageCount;
            return { 
              ...r, 
              status: pageCount >= 60 ? "passed" : "warning",
              message: hasEnough 
                ? `已生成 ${pageCount} 页` 
                : `已生成 ${pageCount} 页（代码不足，已自动填充）`
            };
          }
          if (r.ruleId === "code-lines") {
            return { ...r, status: "passed", message: "每页50行，已自动格式化" };
          }
          if (r.ruleId === "code-header") {
            return { ...r, status: "passed", message: "已添加行号格式" };
          }
          return r;
        })
      );
      
      queryClient.invalidateQueries({ queryKey: ["/api/projects", projectId, "code-bundles"] });
      
      toast({ 
        title: "文件上传成功", 
        description: `已处理 ${result.processingResult.totalFiles} 个文件，共 ${result.processingResult.totalLines} 行代码`
      });
    } catch (error) {
      console.error("Code upload error:", error);
      setCodeContent("");
      setCodeProcessingResult(null);
      setComplianceResults((prev) =>
        prev.map((r) => {
          if (r.category === "code") {
            if (r.ruleId === "code-upload") {
              return { ...r, status: "failed", message: "上传失败，请重试" };
            }
            return { ...r, status: "pending", message: "请先上传有效的源代码文件" };
          }
          return r;
        })
      );
      toast({ 
        title: "上传失败", 
        description: "请检查文件格式后重试",
        variant: "destructive"
      });
    } finally {
      setIsUploadingCode(false);
    }
  };

  const toggleNiceClass = (classNumber: number, className: string) => {
    setNiceClasses((prev) => {
      const existing = prev.find((c) => c.classNumber === classNumber);
      if (existing) {
        return prev.filter((c) => c.classNumber !== classNumber);
      }
      return [...prev, { classNumber, className, selectedItems: [] }];
    });
  };

  const updateNiceClassItems = (classNumber: number, items: string) => {
    setNiceClasses((prev) =>
      prev.map((c) =>
        c.classNumber === classNumber
          ? { ...c, selectedItems: items.split(",").map((s) => s.trim()).filter(Boolean) }
          : c
      )
    );
  };

  if (!isNew && isLoadingProject) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  const renderExportStep = () => (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              最终合规检查
            </CardTitle>
            <CardDescription>
              请确保所有项目都已通过检查，方可导出申请包
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ComplianceChecklist results={complianceResults} />
          </CardContent>
        </Card>

        <ExportPreview
          projectName={formData.name || "项目名称"}
          version={formData.version}
        />
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">导出选项</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              className="w-full" 
              data-testid="button-export-zip"
              onClick={handleExport}
              disabled={isExporting}
            >
              <Download className="h-4 w-4 mr-2" />
              {isExporting ? "正在导出..." : "导出 ZIP 包"}
            </Button>
            <Button
              variant="outline"
              className="w-full"
              data-testid="button-print-guide"
            >
              生成打印指南
            </Button>
            <Button
              variant="outline"
              className="w-full"
              data-testid="button-field-mapping"
            >
              查看网报对照表
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">打印说明</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>使用 A4 纸张打印</p>
            <p>源代码材料单面打印</p>
            <p>说明书可双面打印</p>
            <p>签章位预留于指定页面底部</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderCopyrightStep = (step: number) => {
    switch (step) {
      case 2:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>软件基本信息</CardTitle>
                  <CardDescription>填写软件的详细信息</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="fullName">
                        软件全称 <span className="text-destructive">*</span>
                      </Label>
                      <Input
                        id="fullName"
                        placeholder="例如：智能办公管理系统软件"
                        value={formData.fullName}
                        onChange={(e) =>
                          setFormData({ ...formData, fullName: e.target.value })
                        }
                        data-testid="input-full-name"
                      />
                      <p className="text-xs text-muted-foreground">
                        建议以"系统"、"平台"、"软件"、"APP"结尾
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="shortName">软件简称</Label>
                      <Input
                        id="shortName"
                        placeholder="例如：智办"
                        value={formData.shortName}
                        onChange={(e) =>
                          setFormData({ ...formData, shortName: e.target.value })
                        }
                        data-testid="input-short-name"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="versionNumber">
                        版本号 <span className="text-destructive">*</span>
                      </Label>
                      <Input
                        id="versionNumber"
                        placeholder="V1.0"
                        value={formData.versionNumber}
                        onChange={(e) =>
                          setFormData({ ...formData, versionNumber: e.target.value })
                        }
                        data-testid="input-version-number"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="completionDate">完成日期</Label>
                      <Input
                        id="completionDate"
                        type="date"
                        value={formData.completionDate}
                        onChange={(e) =>
                          setFormData({ ...formData, completionDate: e.target.value })
                        }
                        data-testid="input-completion-date"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>开发与运行环境</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="developmentLanguage">
                        开发语言 <span className="text-destructive">*</span>
                      </Label>
                      <Input
                        id="developmentLanguage"
                        placeholder="例如：JavaScript, Python, Java"
                        value={formData.developmentLanguage}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            developmentLanguage: e.target.value,
                          })
                        }
                        data-testid="input-development-language"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="codeLineCount">源程序量（行）</Label>
                      <Input
                        id="codeLineCount"
                        type="number"
                        placeholder="例如：10000"
                        value={formData.codeLineCount || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            codeLineCount: parseInt(e.target.value) || 0,
                          })
                        }
                        data-testid="input-code-line-count"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="developmentEnvironment">开发环境</Label>
                    <Input
                      id="developmentEnvironment"
                      placeholder="例如：Windows 10, Node.js 18, VS Code"
                      value={formData.developmentEnvironment}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          developmentEnvironment: e.target.value,
                        })
                      }
                      data-testid="input-development-environment"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="runtimeEnvironment">运行环境</Label>
                    <Input
                      id="runtimeEnvironment"
                      placeholder="例如：Chrome浏览器, Windows/Mac/Linux"
                      value={formData.runtimeEnvironment}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          runtimeEnvironment: e.target.value,
                        })
                      }
                      data-testid="input-runtime-environment"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>功能与技术特点</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="functionalDescription">功能描述</Label>
                    <Textarea
                      id="functionalDescription"
                      placeholder="简要描述软件的主要功能..."
                      rows={4}
                      value={formData.functionalDescription}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          functionalDescription: e.target.value,
                        })
                      }
                      data-testid="textarea-functional-description"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="technicalFeatures">技术特点</Label>
                    <Textarea
                      id="technicalFeatures"
                      placeholder="描述软件的技术特点、创新点..."
                      rows={3}
                      value={formData.technicalFeatures}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          technicalFeatures: e.target.value,
                        })
                      }
                      data-testid="textarea-technical-features"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="targetDomain">面向领域</Label>
                    <Input
                      id="targetDomain"
                      placeholder="例如：企业办公、教育培训、电子商务"
                      value={formData.targetDomain}
                      onChange={(e) =>
                        setFormData({ ...formData, targetDomain: e.target.value })
                      }
                      data-testid="input-target-domain"
                    />
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <ComplianceChecklist
                results={complianceResults.filter((r) => r.category === "info")}
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>上传源代码</CardTitle>
                  <CardDescription>
                    支持 ZIP 压缩包格式，系统将自动抽取前30页和后30页
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <FileUploader
                    accept=".zip"
                    maxSize={100 * 1024 * 1024}
                    onUpload={handleCodeUpload}
                    description={isUploadingCode ? "正在处理中..." : "拖拽 ZIP 文件到此处，或点击选择"}
                    disabled={isUploadingCode}
                  />

                  {codeProcessingResult && (
                    <div className="mt-4 p-4 rounded-md bg-muted/50 border border-border">
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        处理完成
                      </h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">文件数：</span>
                          <span className="font-medium">{codeProcessingResult.totalFiles}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">总行数：</span>
                          <span className="font-medium">{codeProcessingResult.totalLines.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">生成页数：</span>
                          <span className="font-medium">{codeProcessingResult.pageCount}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">文件类型：</span>
                          <span className="font-medium">{Object.keys(codeProcessingResult.fileTypes).length}</span>
                        </div>
                      </div>
                      {codeProcessingResult.warnings.length > 0 && (
                        <div className="mt-2 text-sm text-amber-600">
                          {codeProcessingResult.warnings.slice(0, 3).map((w, i) => (
                            <div key={i}>{w}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="mt-4 p-4 rounded-md bg-muted/50">
                    <h4 className="font-medium mb-2">代码抽取规则</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>自动抽取前30页和后30页共60页源代码</li>
                      <li>每页包含50行代码，自动添加行号</li>
                      <li>忽略 node_modules、.git 等目录</li>
                      <li>支持常见编程语言文件</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              <ComplianceChecklist
                results={complianceResults.filter((r) => r.category === "code")}
              />
            </div>

            <CodePreview
              code={codeContent || "// 请上传源代码文件以预览"}
              pages={codeProcessingResult?.pages || []}
              softwareName={formData.fullName || "软件名称"}
              version={formData.versionNumber || "V1.0"}
              language={formData.developmentLanguage || "JavaScript"}
            />
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>选择说明书模板</CardTitle>
                <CardDescription>
                  根据软件类型选择合适的模板，系统将自动生成章节结构
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {templateTypes.map((type) => (
                    <Label
                      key={type}
                      htmlFor={`template-${type}`}
                      className="flex flex-col items-center gap-2 rounded-md border p-4 cursor-pointer hover-elevate text-center [&:has(:checked)]:border-primary [&:has(:checked)]:bg-primary/5"
                    >
                      <input
                        type="radio"
                        id={`template-${type}`}
                        name="templateType"
                        value={type}
                        checked={formData.templateType === type}
                        onChange={() =>
                          setFormData({ ...formData, templateType: type })
                        }
                        className="sr-only"
                        data-testid={`radio-template-${type}`}
                      />
                      <FileCode className="h-8 w-8 text-muted-foreground" />
                      <span className="text-sm font-medium">
                        {templateTypeLabels[type]}
                      </span>
                    </Label>
                  ))}
                </div>
              </CardContent>
            </Card>

            <DocumentEditor
              templateType={formData.templateType}
              softwareName={formData.fullName || formData.name || "软件名称"}
              version={formData.versionNumber || formData.version || "V1.0"}
              onSave={(sections) => {
                toast({ title: "文档已保存" });
              }}
            />
          </div>
        );

      case 5:
        return renderExportStep();

      default:
        return null;
    }
  };

  const renderPatentStep = (step: number) => {
    switch (step) {
      case 2:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>专利类型</CardTitle>
                  <CardDescription>选择要申请的专利类型</CardDescription>
                </CardHeader>
                <CardContent>
                  <RadioGroup
                    value={patentFormData.patentType}
                    onValueChange={(value) =>
                      setPatentFormData({ ...patentFormData, patentType: value as PatentType })
                    }
                    className="grid grid-cols-1 md:grid-cols-3 gap-4"
                  >
                    {patentTypes.map((type) => (
                      <Label
                        key={type}
                        htmlFor={`patent-type-${type}`}
                        className="flex items-center gap-3 rounded-md border p-4 cursor-pointer hover-elevate [&:has(:checked)]:border-primary [&:has(:checked)]:bg-primary/5"
                      >
                        <RadioGroupItem
                          value={type}
                          id={`patent-type-${type}`}
                          data-testid={`radio-patent-type-${type}`}
                        />
                        <span>{patentTypeLabels[type]}</span>
                      </Label>
                    ))}
                  </RadioGroup>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>发明基本信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="patent-title">
                      发明名称 <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="patent-title"
                      placeholder="例如：一种基于深度学习的图像识别方法"
                      value={patentFormData.title}
                      onChange={(e) =>
                        setPatentFormData({ ...patentFormData, title: e.target.value })
                      }
                      data-testid="input-patent-title"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="patent-abstract">摘要</Label>
                    <Textarea
                      id="patent-abstract"
                      placeholder="简要描述发明的技术方案和主要用途..."
                      rows={4}
                      value={patentFormData.abstract}
                      onChange={(e) =>
                        setPatentFormData({ ...patentFormData, abstract: e.target.value })
                      }
                      data-testid="textarea-patent-abstract"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>申请人与发明人信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="patent-applicant-name">
                        申请人姓名/名称 <span className="text-destructive">*</span>
                      </Label>
                      <Input
                        id="patent-applicant-name"
                        placeholder="个人姓名或企业名称"
                        value={patentFormData.applicantName}
                        onChange={(e) =>
                          setPatentFormData({ ...patentFormData, applicantName: e.target.value })
                        }
                        data-testid="input-patent-applicant-name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="patent-applicant-address">申请人地址</Label>
                      <Input
                        id="patent-applicant-address"
                        placeholder="详细地址"
                        value={patentFormData.applicantAddress}
                        onChange={(e) =>
                          setPatentFormData({ ...patentFormData, applicantAddress: e.target.value })
                        }
                        data-testid="input-patent-applicant-address"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="patent-inventor-names">发明人</Label>
                    <Input
                      id="patent-inventor-names"
                      placeholder="多个发明人用逗号分隔，例如：张三, 李四"
                      value={patentFormData.inventorNames}
                      onChange={(e) =>
                        setPatentFormData({ ...patentFormData, inventorNames: e.target.value })
                      }
                      data-testid="input-patent-inventor-names"
                    />
                    <p className="text-xs text-muted-foreground">多个发明人请用逗号分隔</p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="patent-agency-name">代理机构名称</Label>
                      <Input
                        id="patent-agency-name"
                        placeholder="专利代理机构名称"
                        value={patentFormData.agencyName}
                        onChange={(e) =>
                          setPatentFormData({ ...patentFormData, agencyName: e.target.value })
                        }
                        data-testid="input-patent-agency-name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="patent-agent-name">代理人姓名</Label>
                      <Input
                        id="patent-agent-name"
                        placeholder="专利代理人姓名"
                        value={patentFormData.agentName}
                        onChange={(e) =>
                          setPatentFormData({ ...patentFormData, agentName: e.target.value })
                        }
                        data-testid="input-patent-agent-name"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <ComplianceChecklist
                results={complianceResults.filter((r) => r.category === "info")}
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>权利要求书</CardTitle>
                  <CardDescription>
                    编写专利的权利要求，明确保护范围
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    id="patent-claims"
                    placeholder={"1. 一种...的方法，其特征在于，包括以下步骤：\n   (1) ...\n   (2) ...\n\n2. 根据权利要求1所述的方法，其特征在于..."}
                    rows={20}
                    value={patentFormData.claimsText}
                    onChange={(e) =>
                      setPatentFormData({ ...patentFormData, claimsText: e.target.value })
                    }
                    data-testid="textarea-patent-claims"
                  />
                  <div className="p-4 rounded-md bg-muted/50">
                    <h4 className="font-medium mb-2">撰写提示</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>权利要求1应为独立权利要求，描述核心技术方案</li>
                      <li>从属权利要求引用前述权利要求并进一步限定</li>
                      <li>使用"其特征在于"连接前序部分和特征部分</li>
                      <li>表述应清楚、简要、完整</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <ComplianceChecklist
                results={complianceResults.filter((r) => r.category === "claims")}
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>技术领域</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    id="patent-technical-field"
                    placeholder="本发明涉及...技术领域，特别涉及..."
                    rows={3}
                    value={patentFormData.technicalField}
                    onChange={(e) =>
                      setPatentFormData({ ...patentFormData, technicalField: e.target.value })
                    }
                    data-testid="textarea-patent-technical-field"
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>背景技术</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    id="patent-background-art"
                    placeholder="描述与本发明最接近的现有技术及其不足..."
                    rows={5}
                    value={patentFormData.backgroundArt}
                    onChange={(e) =>
                      setPatentFormData({ ...patentFormData, backgroundArt: e.target.value })
                    }
                    data-testid="textarea-patent-background-art"
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>技术问题</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    id="patent-technical-problem"
                    placeholder="本发明要解决的技术问题是..."
                    rows={3}
                    value={patentFormData.technicalProblem}
                    onChange={(e) =>
                      setPatentFormData({ ...patentFormData, technicalProblem: e.target.value })
                    }
                    data-testid="textarea-patent-technical-problem"
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>技术方案</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    id="patent-technical-solution"
                    placeholder="为解决上述技术问题，本发明采用以下技术方案..."
                    rows={8}
                    value={patentFormData.technicalSolution}
                    onChange={(e) =>
                      setPatentFormData({ ...patentFormData, technicalSolution: e.target.value })
                    }
                    data-testid="textarea-patent-technical-solution"
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>有益效果</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    id="patent-beneficial-effects"
                    placeholder="与现有技术相比，本发明的有益效果是..."
                    rows={4}
                    value={patentFormData.beneficialEffects}
                    onChange={(e) =>
                      setPatentFormData({ ...patentFormData, beneficialEffects: e.target.value })
                    }
                    data-testid="textarea-patent-beneficial-effects"
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>附图说明</CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea
                    id="patent-drawings-description"
                    placeholder="图1是...的结构示意图；\n图2是...的流程图；"
                    rows={4}
                    value={patentFormData.drawingsDescription}
                    onChange={(e) =>
                      setPatentFormData({ ...patentFormData, drawingsDescription: e.target.value })
                    }
                    data-testid="textarea-patent-drawings-description"
                  />
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">说明书撰写指南</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-3">
                  <p><strong>技术领域</strong>：说明发明所属技术领域</p>
                  <p><strong>背景技术</strong>：描述现有技术及其缺点</p>
                  <p><strong>技术问题</strong>：阐明要解决的问题</p>
                  <p><strong>技术方案</strong>：详细描述实现方式</p>
                  <p><strong>有益效果</strong>：与现有技术的对比优势</p>
                </CardContent>
              </Card>
            </div>
          </div>
        );

      case 5:
        return renderExportStep();

      default:
        return null;
    }
  };

  const renderTrademarkStep = (step: number) => {
    switch (step) {
      case 2:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>商标类型</CardTitle>
                  <CardDescription>选择要注册的商标类型</CardDescription>
                </CardHeader>
                <CardContent>
                  <RadioGroup
                    value={trademarkFormData.trademarkType}
                    onValueChange={(value) =>
                      setTrademarkFormData({ ...trademarkFormData, trademarkType: value as TrademarkType })
                    }
                    className="grid grid-cols-2 md:grid-cols-3 gap-4"
                  >
                    {trademarkTypes.map((type) => (
                      <Label
                        key={type}
                        htmlFor={`trademark-type-${type}`}
                        className="flex items-center gap-3 rounded-md border p-4 cursor-pointer hover-elevate [&:has(:checked)]:border-primary [&:has(:checked)]:bg-primary/5"
                      >
                        <RadioGroupItem
                          value={type}
                          id={`trademark-type-${type}`}
                          data-testid={`radio-trademark-type-${type}`}
                        />
                        <span>{trademarkTypeLabels[type]}</span>
                      </Label>
                    ))}
                  </RadioGroup>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>商标基本信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="trademark-name">
                      商标名称 <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="trademark-name"
                      placeholder="输入商标名称"
                      value={trademarkFormData.trademarkName}
                      onChange={(e) =>
                        setTrademarkFormData({ ...trademarkFormData, trademarkName: e.target.value })
                      }
                      data-testid="input-trademark-name"
                    />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="trademark-color-claim">颜色声明</Label>
                      <Input
                        id="trademark-color-claim"
                        placeholder="如：红色、蓝色组合"
                        value={trademarkFormData.colorClaim}
                        onChange={(e) =>
                          setTrademarkFormData({ ...trademarkFormData, colorClaim: e.target.value })
                        }
                        data-testid="input-trademark-color-claim"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="trademark-design-description">图样描述</Label>
                      <Input
                        id="trademark-design-description"
                        placeholder="描述商标图样的构成要素"
                        value={trademarkFormData.designDescription}
                        onChange={(e) =>
                          setTrademarkFormData({ ...trademarkFormData, designDescription: e.target.value })
                        }
                        data-testid="input-trademark-design-description"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>申请人信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>申请人类型</Label>
                    <Select
                      value={trademarkFormData.applicantType}
                      onValueChange={(value) =>
                        setTrademarkFormData({
                          ...trademarkFormData,
                          applicantType: value as "individual" | "enterprise" | "institution",
                        })
                      }
                    >
                      <SelectTrigger data-testid="select-trademark-applicant-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {subjectTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {subjectTypeLabels[type]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="trademark-applicant-name">
                        申请人姓名/名称 <span className="text-destructive">*</span>
                      </Label>
                      <Input
                        id="trademark-applicant-name"
                        placeholder="个人姓名或企业名称"
                        value={trademarkFormData.applicantName}
                        onChange={(e) =>
                          setTrademarkFormData({ ...trademarkFormData, applicantName: e.target.value })
                        }
                        data-testid="input-trademark-applicant-name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="trademark-applicant-address">申请人地址</Label>
                      <Input
                        id="trademark-applicant-address"
                        placeholder="详细地址"
                        value={trademarkFormData.applicantAddress}
                        onChange={(e) =>
                          setTrademarkFormData({ ...trademarkFormData, applicantAddress: e.target.value })
                        }
                        data-testid="input-trademark-applicant-address"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="trademark-contact-person">联系人</Label>
                      <Input
                        id="trademark-contact-person"
                        placeholder="联系人姓名"
                        value={trademarkFormData.contactPerson}
                        onChange={(e) =>
                          setTrademarkFormData({ ...trademarkFormData, contactPerson: e.target.value })
                        }
                        data-testid="input-trademark-contact-person"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="trademark-contact-phone">联系电话</Label>
                      <Input
                        id="trademark-contact-phone"
                        placeholder="手机号码"
                        value={trademarkFormData.contactPhone}
                        onChange={(e) =>
                          setTrademarkFormData({ ...trademarkFormData, contactPhone: e.target.value })
                        }
                        data-testid="input-trademark-contact-phone"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="trademark-contact-email">电子邮箱</Label>
                      <Input
                        id="trademark-contact-email"
                        type="email"
                        placeholder="email@example.com"
                        value={trademarkFormData.contactEmail}
                        onChange={(e) =>
                          setTrademarkFormData({ ...trademarkFormData, contactEmail: e.target.value })
                        }
                        data-testid="input-trademark-contact-email"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <ComplianceChecklist
                results={complianceResults.filter((r) => r.category === "info")}
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>尼斯分类选择</CardTitle>
                <CardDescription>
                  选择商标注册的商品/服务类别，并填写具体商品或服务项目
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {niceClassifications.map((cls) => {
                    const isSelected = niceClasses.some((c) => c.classNumber === cls.classNumber);
                    return (
                      <div
                        key={cls.classNumber}
                        className={`rounded-md border p-3 cursor-pointer hover-elevate transition-colors ${
                          isSelected ? "border-primary bg-primary/5" : ""
                        }`}
                        onClick={() => toggleNiceClass(cls.classNumber, cls.name)}
                        data-testid={`nice-class-${cls.classNumber}`}
                      >
                        <div className="flex items-center gap-2">
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => toggleNiceClass(cls.classNumber, cls.name)}
                            data-testid={`checkbox-nice-class-${cls.classNumber}`}
                          />
                          <div>
                            <div className="text-sm font-medium">
                              第{cls.classNumber}类 - {cls.name}
                            </div>
                            <div className="text-xs text-muted-foreground">{cls.description}</div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {niceClasses.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>已选分类的商品/服务项目</CardTitle>
                  <CardDescription>
                    为每个已选分类填写具体的商品或服务项目，多个项目用逗号分隔
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {niceClasses.map((cls) => (
                    <div key={cls.classNumber} className="space-y-2">
                      <Label htmlFor={`nice-items-${cls.classNumber}`}>
                        第{cls.classNumber}类 - {cls.className}
                      </Label>
                      <Input
                        id={`nice-items-${cls.classNumber}`}
                        placeholder="例如：计算机软件, 移动应用程序, 数据处理"
                        value={cls.selectedItems.join(", ")}
                        onChange={(e) => updateNiceClassItems(cls.classNumber, e.target.value)}
                        data-testid={`input-nice-items-${cls.classNumber}`}
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            <ComplianceChecklist
              results={complianceResults.filter((r) => r.category === "classification")}
            />
          </div>
        );

      case 4:
        return renderExportStep();

      default:
        return null;
    }
  };

  const renderStepContent = () => {
    if (currentStep === 1) {
      return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>项目基本信息</CardTitle>
                <CardDescription>填写{projectTypeLabels[projectType]}项目的基本信息</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">
                      项目名称 <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="name"
                      placeholder="例如：智能办公管理系统"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      data-testid="input-project-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="version">版本号</Label>
                    <Input
                      id="version"
                      placeholder="V1.0"
                      value={formData.version}
                      onChange={(e) =>
                        setFormData({ ...formData, version: e.target.value })
                      }
                      data-testid="input-version"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>主体类型</CardTitle>
                <CardDescription>选择著作权人类型</CardDescription>
              </CardHeader>
              <CardContent>
                <RadioGroup
                  value={formData.subjectType}
                  onValueChange={(value) =>
                    setFormData({ ...formData, subjectType: value as SubjectType })
                  }
                  className="grid grid-cols-1 md:grid-cols-3 gap-4"
                >
                  {subjectTypes.map((type) => {
                    const Icon = subjectTypeIcons[type];
                    return (
                      <Label
                        key={type}
                        htmlFor={`subject-${type}`}
                        className="flex items-center gap-3 rounded-md border p-4 cursor-pointer hover-elevate [&:has(:checked)]:border-primary [&:has(:checked)]:bg-primary/5"
                      >
                        <RadioGroupItem
                          value={type}
                          id={`subject-${type}`}
                          data-testid={`radio-subject-${type}`}
                        />
                        <Icon className="h-5 w-5 text-muted-foreground" />
                        <span>{subjectTypeLabels[type]}</span>
                      </Label>
                    );
                  })}
                </RadioGroup>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>开发方式</CardTitle>
                <CardDescription>选择软件的开发方式</CardDescription>
              </CardHeader>
              <CardContent>
                <Select
                  value={formData.developmentMethod}
                  onValueChange={(value) =>
                    setFormData({
                      ...formData,
                      developmentMethod: value as DevelopmentMethod,
                    })
                  }
                >
                  <SelectTrigger data-testid="select-development-method">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {developmentMethods.map((method) => (
                      <SelectItem key={method} value={method}>
                        {developmentMethodLabels[method]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>发表状态</CardTitle>
                <CardDescription>选择软件的发表状态</CardDescription>
              </CardHeader>
              <CardContent>
                <RadioGroup
                  value={formData.publicationStatus}
                  onValueChange={(value) =>
                    setFormData({
                      ...formData,
                      publicationStatus: value as PublicationStatus,
                    })
                  }
                  className="flex gap-4"
                >
                  {publicationStatuses.map((status) => (
                    <Label
                      key={status}
                      htmlFor={`publication-${status}`}
                      className="flex items-center gap-2 rounded-md border p-4 cursor-pointer hover-elevate [&:has(:checked)]:border-primary [&:has(:checked)]:bg-primary/5"
                    >
                      <RadioGroupItem
                        value={status}
                        id={`publication-${status}`}
                        data-testid={`radio-publication-${status}`}
                      />
                      <span>{publicationStatusLabels[status]}</span>
                    </Label>
                  ))}
                </RadioGroup>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">规则说明</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground space-y-3">
                <p>
                  <strong>主体类型</strong>
                  将决定所需的身份证明材料类型
                </p>
                <p>
                  <strong>开发方式</strong>
                  若选择合作/委托/二次开发，需额外提供相关证明
                </p>
                <p>
                  <strong>发表状态</strong>
                  已发表的软件需提供首次发表证明
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      );
    }

    switch (projectType) {
      case "copyright":
        return renderCopyrightStep(currentStep);
      case "patent":
        return renderPatentStep(currentStep);
      case "trademark":
        return renderTrademarkStep(currentStep);
      default:
        return null;
    }
  };

  const isSaving = saveSoftwareInfoMutation.isPending || savePatentInfoMutation.isPending || saveTrademarkInfoMutation.isPending;

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={isNew ? "创建新项目" : formData.name || "项目详情"}
        breadcrumbs={[
          { label: "项目列表", href: "/" },
          { label: isNew ? "新建项目" : formData.name || "项目" },
        ]}
      />

      <StepIndicator 
        currentStep={currentStep} 
        projectType={projectType}
        className="mb-8"
        onStepClick={(step) => {
          setIsNavigating(true);
          setCurrentStep(step);
          if (!isNew && projectId) {
            updateProjectMutation.mutate(step);
          } else {
            setIsNavigating(false);
          }
        }}
      />

      {renderStepContent()}

      <div className="fixed bottom-0 left-0 right-0 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <Button
            variant="outline"
            onClick={handleSaveDraft}
            disabled={isNew || isSaving}
            data-testid="button-save-draft"
          >
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? "保存中..." : "保存草稿"}
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handlePrev}
              disabled={currentStep === 1}
              data-testid="button-prev-step"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              上一步
            </Button>
            <Button
              onClick={handleNext}
              disabled={
                createProjectMutation.isPending || updateProjectMutation.isPending
              }
              data-testid="button-next-step"
            >
              {currentStep === maxSteps ? (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  导出
                </>
              ) : (
                <>
                  下一步
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
