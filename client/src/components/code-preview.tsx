import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface CodePreviewProps {
  code: string;
  softwareName?: string;
  version?: string;
  currentPage?: number;
  totalPages?: number;
  language?: string;
  className?: string;
}

export function CodePreview({
  code,
  softwareName = "软件名称",
  version = "V1.0",
  currentPage = 1,
  totalPages = 60,
  language = "JavaScript",
  className,
}: CodePreviewProps) {
  const lines = code.split("\n");
  const linesPerPage = 50;
  const startLine = (currentPage - 1) * linesPerPage + 1;

  return (
    <Card className={cn("flex flex-col h-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <CardTitle className="text-lg">源代码预览</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{language}</Badge>
            <Badge variant="secondary">
              第 {currentPage}/{totalPages} 页
            </Badge>
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
              {lines.slice(0, linesPerPage).map((line, index) => (
                <div key={index} className="flex">
                  <span className="w-12 flex-shrink-0 text-muted-foreground select-none text-right pr-4">
                    {startLine + index}
                  </span>
                  <pre className="flex-1 overflow-x-auto whitespace-pre">
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

        <div className="mt-3 flex items-center justify-between text-sm text-muted-foreground">
          <span>行数: {lines.length} 行</span>
          <span>每页 50 行 · 等宽字体 · 连续页码</span>
        </div>
      </CardContent>
    </Card>
  );
}
