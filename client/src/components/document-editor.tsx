import { useState } from "react";
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
} from "lucide-react";
import { templateTypeLabels, type TemplateType } from "@shared/schema";

interface DocumentSection {
  id: string;
  title: string;
  content: string;
  level: number;
}

const defaultSections: DocumentSection[] = [
  { id: "1", title: "摘要与版本信息", content: "", level: 1 },
  { id: "2", title: "系统概述", content: "", level: 1 },
  { id: "2.1", title: "系统目标", content: "", level: 2 },
  { id: "2.2", title: "目标用户", content: "", level: 2 },
  { id: "2.3", title: "系统边界", content: "", level: 2 },
  { id: "3", title: "安装与运行环境", content: "", level: 1 },
  { id: "4", title: "功能说明", content: "", level: 1 },
  { id: "4.1", title: "功能模块一", content: "", level: 2 },
  { id: "4.2", title: "功能模块二", content: "", level: 2 },
  { id: "5", title: "数据结构/接口", content: "", level: 1 },
  { id: "6", title: "权限与日志", content: "", level: 1 },
  { id: "7", title: "典型业务流程", content: "", level: 1 },
  { id: "8", title: "性能与限制", content: "", level: 1 },
  { id: "9", title: "版本更新记录", content: "", level: 1 },
  { id: "10", title: "版权与声明", content: "", level: 1 },
];

interface DocumentEditorProps {
  templateType: TemplateType;
  initialContent?: DocumentSection[];
  onSave?: (sections: DocumentSection[]) => void;
  className?: string;
}

export function DocumentEditor({
  templateType,
  initialContent,
  onSave,
  className,
}: DocumentEditorProps) {
  const [sections, setSections] = useState<DocumentSection[]>(
    initialContent || defaultSections
  );
  const [activeSection, setActiveSection] = useState<string>("1");
  const [mode, setMode] = useState<"edit" | "preview">("edit");

  const currentSection = sections.find((s) => s.id === activeSection);

  const updateSectionContent = (id: string, content: string) => {
    setSections((prev) =>
      prev.map((s) => (s.id === id ? { ...s, content } : s))
    );
  };

  const getTotalWordCount = () => {
    return sections.reduce((acc, s) => acc + s.content.length, 0);
  };

  const getEstimatedPages = () => {
    const chars = getTotalWordCount();
    const charsPerPage = 30 * 40;
    return Math.max(1, Math.ceil(chars / charsPerPage));
  };

  return (
    <div className={cn("flex gap-4 h-full", className)}>
      <Card className="w-64 flex-shrink-0">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">章节大纲</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[400px]">
            <div className="p-2 space-y-1">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                    section.level === 2 && "pl-6",
                    activeSection === section.id
                      ? "bg-primary text-primary-foreground"
                      : "hover-elevate"
                  )}
                  data-testid={`section-${section.id}`}
                >
                  <span className="text-muted-foreground mr-2">{section.id}</span>
                  {section.title}
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
              <Badge variant="outline">{templateTypeLabels[templateType]}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-sm text-muted-foreground mr-4">
                <span>{getTotalWordCount()} 字</span>
                <span>·</span>
                <span>约 {getEstimatedPages()} 页</span>
              </div>
              <Tabs value={mode} onValueChange={(v) => setMode(v as "edit" | "preview")}>
                <TabsList className="h-8">
                  <TabsTrigger value="edit" className="gap-1 text-xs">
                    <Edit3 className="h-3 w-3" />
                    编辑
                  </TabsTrigger>
                  <TabsTrigger value="preview" className="gap-1 text-xs">
                    <Eye className="h-3 w-3" />
                    预览
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
                <Button variant="ghost" size="icon" data-testid="button-image">
                  <Image className="h-4 w-4" />
                </Button>
              </div>
              <Textarea
                value={currentSection?.content || ""}
                onChange={(e) =>
                  currentSection && updateSectionContent(currentSection.id, e.target.value)
                }
                placeholder={`在此编写「${currentSection?.title}」的内容...`}
                className="flex-1 resize-none text-base"
                data-testid="textarea-section-content"
              />
            </>
          )}
          {mode === "preview" && (
            <ScrollArea className="flex-1">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <h2>{currentSection?.id}. {currentSection?.title}</h2>
                {currentSection?.content ? (
                  <div className="whitespace-pre-wrap">{currentSection.content}</div>
                ) : (
                  <p className="text-muted-foreground">暂无内容</p>
                )}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
