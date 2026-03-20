import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, FileCode } from "lucide-react";

const LINES_PER_PAGE = 50;

interface CodePage {
  pageNumber: number;
  content: string;
  lineStart: number;
  lineEnd: number;
  section: 'first' | 'last';
}

interface CodePreviewProps {
  code: string;
  pages?: CodePage[];
  softwareName?: string;
  version?: string;
  totalPages?: number;
  language?: string;
  className?: string;
}

function addLineNumbers(lines: string[], startLine: number = 1): string[] {
  return lines.map((line, idx) => {
    const lineNum = (startLine + idx).toString().padStart(5, ' ');
    return `${lineNum}  ${line}`;
  });
}

export function CodePreview({
  code,
  pages = [],
  softwareName = "软件名称",
  version = "V1.0",
  totalPages = 60,
  language = "JavaScript",
  className,
}: CodePreviewProps) {
  const [currentPage, setCurrentPage] = useState(1);
  
  const hasPages = pages.length > 0;
  const allLines = code.split("\n");
  
  const fallbackTotalPages = Math.max(1, Math.ceil(allLines.length / LINES_PER_PAGE));
  const effectiveTotalPages = hasPages ? pages.length : Math.min(fallbackTotalPages, totalPages);
  
  useEffect(() => {
    setCurrentPage(1);
  }, [pages, code]);
  
  let displayContent: string;
  let currentSection: 'first' | 'last' | undefined;
  
  if (hasPages) {
    const currentPageData = pages.find(p => p.pageNumber === currentPage);
    displayContent = currentPageData?.content || "";
    currentSection = currentPageData?.section;
  } else {
    const startIdx = (currentPage - 1) * LINES_PER_PAGE;
    const pageLines = allLines.slice(startIdx, startIdx + LINES_PER_PAGE);
    const numberedLines = addLineNumbers(pageLines, startIdx + 1);
    displayContent = numberedLines.join("\n");
    currentSection = currentPage <= 30 ? 'first' : 'last';
  }
  
  const lines = displayContent.split("\n");
  const sectionLabel = currentSection === 'first' ? '前30页' : currentSection === 'last' ? '后30页' : '';

  const goToPage = (page: number) => {
    if (page >= 1 && page <= effectiveTotalPages) {
      setCurrentPage(page);
    }
  };

  return (
    <Card className={cn("flex flex-col h-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <FileCode className="w-5 h-5 text-muted-foreground" />
            <CardTitle className="text-lg">源代码预览</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{language}</Badge>
            {sectionLabel && effectiveTotalPages >= 60 && (
              <Badge variant={currentSection === 'first' ? 'default' : 'secondary'}>
                {sectionLabel}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0">
        <div className="rounded-md border bg-card overflow-hidden flex-1 flex flex-col">
          <div className="border-b bg-muted/50 px-4 py-2 text-center text-sm font-medium">
            {softwareName} {version}
          </div>

          <ScrollArea className="flex-1">
            <div className="p-4 font-mono text-xs leading-6">
              {lines.map((line, index) => (
                <div key={index} className="flex">
                  <pre className="flex-1 overflow-x-auto whitespace-pre text-foreground/90">
                    {line || " "}
                  </pre>
                </div>
              ))}
            </div>
          </ScrollArea>

          <div className="border-t bg-muted/50 px-4 py-2 text-center text-sm text-muted-foreground">
            - {currentPage} -
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-1">
            <Button 
              variant="outline" 
              size="icon" 
              onClick={() => goToPage(1)}
              disabled={currentPage === 1}
              data-testid="button-first-page"
            >
              <ChevronsLeft className="w-4 h-4" />
            </Button>
            <Button 
              variant="outline" 
              size="icon" 
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              data-testid="button-prev-page"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <div className="px-3 py-1.5 text-sm text-muted-foreground min-w-[100px] text-center" data-testid="text-current-page">
              第 {currentPage} / {effectiveTotalPages} 页
            </div>
            <Button 
              variant="outline" 
              size="icon" 
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === effectiveTotalPages}
              data-testid="button-next-page"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button 
              variant="outline" 
              size="icon" 
              onClick={() => goToPage(effectiveTotalPages)}
              disabled={currentPage === effectiveTotalPages}
              data-testid="button-last-page"
            >
              <ChevronsRight className="w-4 h-4" />
            </Button>
          </div>
          
          {effectiveTotalPages >= 60 && (
            <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => goToPage(1)}
                className={cn(currentPage <= 30 && "text-primary")}
                data-testid="button-goto-first-section"
              >
                前30页
              </Button>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => goToPage(31)}
                className={cn(currentPage > 30 && "text-primary")}
                data-testid="button-goto-last-section"
              >
                后30页
              </Button>
            </div>
          )}
        </div>

        <div className="mt-2 text-xs text-muted-foreground text-center">
          每页 50 行 · 等宽字体 · 连续页码
        </div>
      </CardContent>
    </Card>
  );
}
