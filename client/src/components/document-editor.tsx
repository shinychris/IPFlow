import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Image,
  Heading1,
  Heading2,
  Heading3,
  Eye,
  Edit3,
  Save,
  FileText,
  Upload,
  Plus,
  Trash2,
} from "lucide-react";
import { templateTypeLabels, type TemplateType } from "@shared/schema";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export interface DocumentSection {
  id: string;
  title: string;
  content: string;
  level: number;
  images?: { id: string; url: string; caption: string }[];
}

const templateSections: Record<TemplateType, DocumentSection[]> = {
  web: [
    { id: "1", title: "摘要与版本信息", content: "", level: 1 },
    { id: "2", title: "系统概述", content: "", level: 1 },
    { id: "2.1", title: "系统目标", content: "", level: 2 },
    { id: "2.2", title: "目标用户", content: "", level: 2 },
    { id: "2.3", title: "系统架构", content: "", level: 2 },
    { id: "3", title: "安装与部署说明", content: "", level: 1 },
    { id: "3.1", title: "服务器配置要求", content: "", level: 2 },
    { id: "3.2", title: "浏览器兼容性", content: "", level: 2 },
    { id: "4", title: "功能说明", content: "", level: 1 },
    { id: "4.1", title: "用户登录与注册", content: "", level: 2 },
    { id: "4.2", title: "首页与导航", content: "", level: 2 },
    { id: "4.3", title: "核心业务功能", content: "", level: 2 },
    { id: "4.4", title: "用户中心", content: "", level: 2 },
    { id: "5", title: "数据结构与接口", content: "", level: 1 },
    { id: "6", title: "权限管理", content: "", level: 1 },
    { id: "7", title: "典型业务流程", content: "", level: 1 },
    { id: "8", title: "性能与限制", content: "", level: 1 },
    { id: "9", title: "版本更新记录", content: "", level: 1 },
    { id: "10", title: "版权与声明", content: "", level: 1 },
  ],
  mobile: [
    { id: "1", title: "摘要与版本信息", content: "", level: 1 },
    { id: "2", title: "应用概述", content: "", level: 1 },
    { id: "2.1", title: "应用目标", content: "", level: 2 },
    { id: "2.2", title: "目标用户", content: "", level: 2 },
    { id: "2.3", title: "技术架构", content: "", level: 2 },
    { id: "3", title: "安装与运行环境", content: "", level: 1 },
    { id: "3.1", title: "系统要求", content: "", level: 2 },
    { id: "3.2", title: "安装步骤", content: "", level: 2 },
    { id: "4", title: "功能说明", content: "", level: 1 },
    { id: "4.1", title: "启动与登录", content: "", level: 2 },
    { id: "4.2", title: "主界面导航", content: "", level: 2 },
    { id: "4.3", title: "核心功能模块", content: "", level: 2 },
    { id: "4.4", title: "设置与个人中心", content: "", level: 2 },
    { id: "5", title: "数据存储与同步", content: "", level: 1 },
    { id: "6", title: "权限申请说明", content: "", level: 1 },
    { id: "7", title: "典型使用流程", content: "", level: 1 },
    { id: "8", title: "性能与限制", content: "", level: 1 },
    { id: "9", title: "版本更新记录", content: "", level: 1 },
    { id: "10", title: "版权与声明", content: "", level: 1 },
  ],
  algorithm: [
    { id: "1", title: "摘要与版本信息", content: "", level: 1 },
    { id: "2", title: "算法概述", content: "", level: 1 },
    { id: "2.1", title: "算法目标", content: "", level: 2 },
    { id: "2.2", title: "应用场景", content: "", level: 2 },
    { id: "2.3", title: "技术原理", content: "", level: 2 },
    { id: "3", title: "运行环境配置", content: "", level: 1 },
    { id: "3.1", title: "硬件要求", content: "", level: 2 },
    { id: "3.2", title: "软件依赖", content: "", level: 2 },
    { id: "4", title: "算法功能说明", content: "", level: 1 },
    { id: "4.1", title: "数据输入处理", content: "", level: 2 },
    { id: "4.2", title: "核心算法流程", content: "", level: 2 },
    { id: "4.3", title: "结果输出格式", content: "", level: 2 },
    { id: "5", title: "数据结构定义", content: "", level: 1 },
    { id: "6", title: "API接口文档", content: "", level: 1 },
    { id: "7", title: "性能指标与测试", content: "", level: 1 },
    { id: "8", title: "使用示例", content: "", level: 1 },
    { id: "9", title: "版本更新记录", content: "", level: 1 },
    { id: "10", title: "版权与声明", content: "", level: 1 },
  ],
  script: [
    { id: "1", title: "摘要与版本信息", content: "", level: 1 },
    { id: "2", title: "脚本概述", content: "", level: 1 },
    { id: "2.1", title: "脚本目的", content: "", level: 2 },
    { id: "2.2", title: "适用场景", content: "", level: 2 },
    { id: "3", title: "运行环境", content: "", level: 1 },
    { id: "3.1", title: "解释器要求", content: "", level: 2 },
    { id: "3.2", title: "依赖安装", content: "", level: 2 },
    { id: "4", title: "功能说明", content: "", level: 1 },
    { id: "4.1", title: "参数说明", content: "", level: 2 },
    { id: "4.2", title: "执行步骤", content: "", level: 2 },
    { id: "4.3", title: "输出结果", content: "", level: 2 },
    { id: "5", title: "配置文件说明", content: "", level: 1 },
    { id: "6", title: "错误处理", content: "", level: 1 },
    { id: "7", title: "使用示例", content: "", level: 1 },
    { id: "8", title: "版本更新记录", content: "", level: 1 },
    { id: "9", title: "版权与声明", content: "", level: 1 },
  ],
  desktop: [
    { id: "1", title: "摘要与版本信息", content: "", level: 1 },
    { id: "2", title: "系统概述", content: "", level: 1 },
    { id: "2.1", title: "系统目标", content: "", level: 2 },
    { id: "2.2", title: "目标用户", content: "", level: 2 },
    { id: "2.3", title: "系统架构", content: "", level: 2 },
    { id: "3", title: "安装与卸载", content: "", level: 1 },
    { id: "3.1", title: "系统要求", content: "", level: 2 },
    { id: "3.2", title: "安装步骤", content: "", level: 2 },
    { id: "3.3", title: "卸载说明", content: "", level: 2 },
    { id: "4", title: "功能说明", content: "", level: 1 },
    { id: "4.1", title: "主界面介绍", content: "", level: 2 },
    { id: "4.2", title: "菜单功能", content: "", level: 2 },
    { id: "4.3", title: "核心功能模块", content: "", level: 2 },
    { id: "4.4", title: "系统设置", content: "", level: 2 },
    { id: "5", title: "数据管理", content: "", level: 1 },
    { id: "6", title: "快捷键说明", content: "", level: 1 },
    { id: "7", title: "典型操作流程", content: "", level: 1 },
    { id: "8", title: "常见问题", content: "", level: 1 },
    { id: "9", title: "版本更新记录", content: "", level: 1 },
    { id: "10", title: "版权与声明", content: "", level: 1 },
  ],
};

interface DocumentEditorProps {
  templateType: TemplateType;
  initialContent?: DocumentSection[];
  onSave?: (sections: DocumentSection[]) => void;
  softwareName?: string;
  version?: string;
  className?: string;
}

export function DocumentEditor({
  templateType,
  initialContent,
  onSave,
  softwareName = "软件名称",
  version = "V1.0",
  className,
}: DocumentEditorProps) {
  const defaultSections = templateSections[templateType] || templateSections.web;
  const [sections, setSections] = useState<DocumentSection[]>(
    initialContent || defaultSections
  );
  const [activeSection, setActiveSection] = useState<string>("1");
  const [mode, setMode] = useState<"edit" | "preview" | "toc">("edit");
  const [showImageDialog, setShowImageDialog] = useState(false);
  const [imageCaption, setImageCaption] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!initialContent) {
      setSections(templateSections[templateType] || templateSections.web);
      setActiveSection("1");
    }
  }, [templateType, initialContent]);

  const currentSection = sections.find((s) => s.id === activeSection);

  const updateSectionContent = (id: string, content: string) => {
    setSections((prev) =>
      prev.map((s) => (s.id === id ? { ...s, content } : s))
    );
  };

  const addImageToSection = (id: string, imageUrl: string, caption: string) => {
    setSections((prev) =>
      prev.map((s) => {
        if (s.id === id) {
          const newImage = {
            id: `img-${Date.now()}`,
            url: imageUrl,
            caption,
          };
          return { ...s, images: [...(s.images || []), newImage] };
        }
        return s;
      })
    );
  };

  const removeImageFromSection = (sectionId: string, imageId: string) => {
    setSections((prev) =>
      prev.map((s) => {
        if (s.id === sectionId) {
          return { ...s, images: (s.images || []).filter(img => img.id !== imageId) };
        }
        return s;
      })
    );
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && currentSection) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const imageUrl = event.target?.result as string;
        addImageToSection(currentSection.id, imageUrl, imageCaption || `图 ${(currentSection.images?.length || 0) + 1}`);
        setImageCaption("");
        setShowImageDialog(false);
      };
      reader.readAsDataURL(file);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getTotalWordCount = () => {
    return sections.reduce((acc, s) => acc + s.content.length, 0);
  };

  const getTotalImageCount = () => {
    return sections.reduce((acc, s) => acc + (s.images?.length || 0), 0);
  };

  const getEstimatedPages = () => {
    const chars = getTotalWordCount();
    const images = getTotalImageCount();
    const charsPerPage = 30 * 40;
    const pagesFromText = chars / charsPerPage;
    const pagesFromImages = images * 0.5;
    return Math.max(1, Math.ceil(pagesFromText + pagesFromImages));
  };

  const generateTOC = () => {
    return sections.map((s) => ({
      id: s.id,
      title: s.title,
      level: s.level,
      hasContent: s.content.length > 0 || (s.images?.length || 0) > 0,
    }));
  };

  return (
    <div className={cn("flex gap-4 h-full", className)}>
      <Card className="w-64 flex-shrink-0">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">章节大纲</CardTitle>
            <Badge variant="outline" className="text-xs">
              {templateTypeLabels[templateType]}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[400px]">
            <div className="p-2 space-y-1">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-md text-sm transition-colors flex items-center gap-2",
                    section.level === 2 && "pl-6",
                    activeSection === section.id
                      ? "bg-primary text-primary-foreground"
                      : "hover-elevate"
                  )}
                  data-testid={`section-${section.id}`}
                >
                  <span className={cn(
                    "text-xs mr-1",
                    activeSection === section.id ? "text-primary-foreground/70" : "text-muted-foreground"
                  )}>
                    {section.id}
                  </span>
                  <span className="flex-1 truncate">{section.title}</span>
                  {(section.content || (section.images?.length || 0) > 0) && (
                    <span className={cn(
                      "w-2 h-2 rounded-full flex-shrink-0",
                      activeSection === section.id ? "bg-primary-foreground/50" : "bg-green-500"
                    )} />
                  )}
                </button>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <Card className="flex-1 flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <CardTitle className="text-lg">
                {currentSection?.id}. {currentSection?.title}
              </CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-sm text-muted-foreground mr-4">
                <span>{getTotalWordCount()} 字</span>
                <span>·</span>
                <span>{getTotalImageCount()} 图</span>
                <span>·</span>
                <span>约 {getEstimatedPages()} 页</span>
              </div>
              <Tabs value={mode} onValueChange={(v) => setMode(v as "edit" | "preview" | "toc")}>
                <TabsList className="h-8">
                  <TabsTrigger value="edit" className="gap-1 text-xs" data-testid="tab-edit">
                    <Edit3 className="h-3 w-3" />
                    编辑
                  </TabsTrigger>
                  <TabsTrigger value="preview" className="gap-1 text-xs" data-testid="tab-preview">
                    <Eye className="h-3 w-3" />
                    预览
                  </TabsTrigger>
                  <TabsTrigger value="toc" className="gap-1 text-xs" data-testid="tab-toc">
                    <FileText className="h-3 w-3" />
                    目录
                  </TabsTrigger>
                </TabsList>
              </Tabs>
              <Button
                size="sm"
                onClick={() => onSave?.(sections)}
                data-testid="button-save-document"
              >
                <Save className="h-4 w-4 mr-1" />
                保存
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col min-h-0">
          {mode === "edit" && (
            <>
              <div className="flex items-center gap-1 pb-3 border-b mb-3 flex-wrap">
                <Button variant="ghost" size="icon" data-testid="button-bold">
                  <Bold className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" data-testid="button-italic">
                  <Italic className="h-4 w-4" />
                </Button>
                <div className="w-px h-6 bg-border mx-1" />
                <Button variant="ghost" size="icon" data-testid="button-h1">
                  <Heading1 className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" data-testid="button-h2">
                  <Heading2 className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" data-testid="button-h3">
                  <Heading3 className="h-4 w-4" />
                </Button>
                <div className="w-px h-6 bg-border mx-1" />
                <Button variant="ghost" size="icon" data-testid="button-list">
                  <List className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" data-testid="button-ordered-list">
                  <ListOrdered className="h-4 w-4" />
                </Button>
                <div className="w-px h-6 bg-border mx-1" />
                <Dialog open={showImageDialog} onOpenChange={setShowImageDialog}>
                  <DialogTrigger asChild>
                    <Button variant="ghost" size="icon" data-testid="button-image">
                      <Image className="h-4 w-4" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>插入截图</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">图片说明</label>
                        <Input
                          value={imageCaption}
                          onChange={(e) => setImageCaption(e.target.value)}
                          placeholder={`图 ${(currentSection?.images?.length || 0) + 1}`}
                          data-testid="input-image-caption"
                        />
                      </div>
                      <div className="border-2 border-dashed rounded-lg p-8 text-center">
                        <Upload className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
                        <p className="text-sm text-muted-foreground mb-3">点击或拖拽上传截图</p>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*"
                          onChange={handleImageUpload}
                          className="hidden"
                          data-testid="input-image-file"
                        />
                        <Button
                          variant="outline"
                          onClick={() => fileInputRef.current?.click()}
                          data-testid="button-select-image"
                        >
                          选择图片
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
              <Textarea
                value={currentSection?.content || ""}
                onChange={(e) =>
                  currentSection && updateSectionContent(currentSection.id, e.target.value)
                }
                placeholder={`在此编写「${currentSection?.title}」的内容...\n\n提示：\n- 描述该章节的主要功能和操作步骤\n- 可以使用截图按钮插入界面截图\n- 建议每个章节300-500字`}
                className="flex-1 resize-none text-base"
                data-testid="textarea-section-content"
              />
              {currentSection?.images && currentSection.images.length > 0 && (
                <div className="mt-3 space-y-2">
                  <div className="text-sm font-medium">已插入的截图</div>
                  <div className="grid grid-cols-3 gap-2">
                    {currentSection.images.map((img) => (
                      <div key={img.id} className="relative group rounded-md overflow-hidden border">
                        <img
                          src={img.url}
                          alt={img.caption}
                          className="w-full h-20 object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <Button
                            variant="destructive"
                            size="icon"
                            onClick={() => removeImageFromSection(currentSection.id, img.id)}
                            data-testid={`button-remove-image-${img.id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white text-xs p-1 truncate">
                          {img.caption}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
          {mode === "preview" && (
            <ScrollArea className="flex-1">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <div className="text-center mb-6 pb-4 border-b">
                  <h1 className="text-xl font-bold mb-1">{softwareName}</h1>
                  <p className="text-muted-foreground">操作说明书 {version}</p>
                </div>
                <h2>{currentSection?.id}. {currentSection?.title}</h2>
                {currentSection?.content ? (
                  <div className="whitespace-pre-wrap">{currentSection.content}</div>
                ) : (
                  <p className="text-muted-foreground">暂无内容</p>
                )}
                {currentSection?.images && currentSection.images.length > 0 && (
                  <div className="mt-4 space-y-4">
                    {currentSection.images.map((img) => (
                      <figure key={img.id} className="text-center">
                        <img
                          src={img.url}
                          alt={img.caption}
                          className="max-w-full mx-auto rounded-md border"
                        />
                        <figcaption className="text-sm text-muted-foreground mt-2">
                          {img.caption}
                        </figcaption>
                      </figure>
                    ))}
                  </div>
                )}
              </div>
            </ScrollArea>
          )}
          {mode === "toc" && (
            <ScrollArea className="flex-1">
              <div className="space-y-4">
                <div className="text-center pb-4 border-b">
                  <h2 className="text-lg font-bold">{softwareName}</h2>
                  <p className="text-sm text-muted-foreground">操作说明书 {version}</p>
                </div>
                <div className="space-y-1">
                  <h3 className="font-medium mb-3">目 录</h3>
                  {generateTOC().map((item) => (
                    <div
                      key={item.id}
                      className={cn(
                        "flex items-center justify-between py-1.5 border-b border-dotted",
                        item.level === 2 && "pl-4"
                      )}
                    >
                      <span className="flex items-center gap-2">
                        <span className="text-muted-foreground">{item.id}</span>
                        <span>{item.title}</span>
                        {!item.hasContent && (
                          <Badge variant="outline" className="text-xs text-amber-600">
                            待编写
                          </Badge>
                        )}
                      </span>
                      <span className="text-muted-foreground text-sm">
                        {item.hasContent ? "---" : ""}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="mt-6 p-4 rounded-md bg-muted/50">
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    编写进度
                  </h4>
                  <div className="text-sm text-muted-foreground">
                    <p>已完成章节: {generateTOC().filter(i => i.hasContent).length} / {sections.length}</p>
                    <p>总字数: {getTotalWordCount()} 字</p>
                    <p>总截图: {getTotalImageCount()} 张</p>
                    <p>预计页数: {getEstimatedPages()} 页</p>
                    {getEstimatedPages() < 15 && (
                      <p className="text-amber-600 mt-2">
                        提示: 说明书需至少15页，请继续补充内容
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
