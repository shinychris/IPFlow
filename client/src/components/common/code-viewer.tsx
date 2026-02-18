/**
 * 代码查看器组件
 * 
 * 支持语法高亮、行号显示、分页浏览、搜索功能
 */

import React, { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ChevronLeft,
  ChevronRight,
  Search,
  FileCode,
  Eye,
} from "lucide-react";

interface CodeFile {
  path: string;
  content: string;
  language: string;
  lines: number;
}

interface CodeViewerProps {
  files: CodeFile[];
  className?: string;
  showLineNumbers?: boolean;
  maxHeight?: string;
}

// 简单的语法高亮
function highlightCode(content: string, language: string): string {
  // 转义 HTML
  let highlighted = content
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // 关键字高亮
  const keywords = [
    "import", "export", "from", "const", "let", "var", "function",
    "class", "interface", "type", "return", "if", "else", "for",
    "while", "switch", "case", "break", "continue", "try", "catch",
    "async", "await", "new", "this", "super", "extends", "implements",
    "public", "private", "protected", "static", "readonly",
  ];

  const keywordRegex = new RegExp(
    `\\b(${keywords.join("|")})\\b`,
    "g"
  );

  highlighted = highlighted.replace(
    keywordRegex,
    '<span class="text-purple-600 dark:text-purple-400 font-medium">$1</span>'
  );

  // 字符串高亮
  highlighted = highlighted.replace(
    /(".*?"|'.*?'|`.*?`)/g,
    '<span class="text-green-600 dark:text-green-400">$1</span>'
  );

  // 注释高亮
  highlighted = highlighted.replace(
    /(\/\/.*$|\/\*[\s\S]*?\*\/|#.*$)/gm,
    '<span class="text-gray-500 dark:text-gray-400 italic">$1</span>'
  );

  // 数字高亮
  highlighted = highlighted.replace(
    /\b(\d+)\b/g,
    '<span class="text-blue-600 dark:text-blue-400">$1</span>'
  );

  return highlighted;
}

export function CodeViewer({
  files,
  className,
  showLineNumbers = true,
  maxHeight = "600px",
}: CodeViewerProps) {
  const [selectedFile, setSelectedFile] = useState<string>(files[0]?.path || "");
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const linesPerPage = 50;

  const currentFile = useMemo(
    () => files.find((f) => f.path === selectedFile) || files[0],
    [files, selectedFile]
  );

  const allLines = useMemo(
    () => currentFile?.content.split("\n") || [],
    [currentFile]
  );

  const filteredLines = useMemo(() => {
    if (!searchQuery) return allLines;
    return allLines.filter((line) =>
      line.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [allLines, searchQuery]);

  const totalPages = Math.ceil(filteredLines.length / linesPerPage);

  const displayLines = useMemo(() => {
    const start = (currentPage - 1) * linesPerPage;
    return filteredLines.slice(start, start + linesPerPage);
  }, [filteredLines, currentPage]);

  const highlightedContent = useMemo(() => {
    return displayLines.map((line) => highlightCode(line, currentFile?.language || ""));
  }, [displayLines, currentFile?.language]);

  const getLanguageColor = (lang: string): string => {
    const colors: Record<string, string> = {
      typescript: "bg-blue-100 text-blue-800",
      javascript: "bg-yellow-100 text-yellow-800",
      python: "bg-green-100 text-green-800",
      java: "bg-orange-100 text-orange-800",
      go: "bg-cyan-100 text-cyan-800",
      rust: "bg-red-100 text-red-800",
      html: "bg-orange-100 text-orange-800",
      css: "bg-blue-100 text-blue-800",
      json: "bg-gray-100 text-gray-800",
    };
    return colors[lang] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className={cn("flex flex-col border rounded-lg bg-card", className)}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-2">
          <FileCode className="h-4 w-4 text-muted-foreground" />
          <Select value={selectedFile} onValueChange={setSelectedFile}>
            <SelectTrigger className="w-[250px]">
              <SelectValue placeholder="选择文件" />
            </SelectTrigger>
            <SelectContent>
              {files.map((file) => (
                <SelectItem key={file.path} value={file.path}>
                  <div className="flex items-center gap-2">
                    <span className="truncate">{file.path}</span>
                    <Badge
                      variant="secondary"
                      className={cn("text-xs", getLanguageColor(file.language))}
                    >
                      {file.language}
                    </Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          {/* 搜索 */}
          {isSearchOpen ? (
            <div className="flex items-center gap-2">
              <Input
                type="text"
                placeholder="搜索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-40 h-8"
                autoFocus
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSearchQuery("");
                  setIsSearchOpen(false);
                }}
              >
                取消
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsSearchOpen(true)}
            >
              <Search className="h-4 w-4" />
            </Button>
          )}

          {/* 分页 */}
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-muted-foreground min-w-[60px] text-center">
              {currentPage} / {totalPages || 1}
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages || totalPages === 0}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* 代码内容 */}
      <div
        className="overflow-auto font-mono text-sm"
        style={{ maxHeight }}
      >
        <table className="w-full border-collapse">
          <tbody>
            {displayLines.map((line, index) => {
              const lineNumber = (currentPage - 1) * linesPerPage + index + 1;
              return (
                <tr
                  key={lineNumber}
                  className="hover:bg-muted/50 transition-colors"
                >
                  {showLineNumbers && (
                    <td className="w-12 py-0.5 pr-3 text-right text-muted-foreground select-none bg-muted/30">
                      {lineNumber}
                    </td>
                  )}
                  <td className="py-0.5 px-4 whitespace-pre">
                    <code
                      dangerouslySetInnerHTML={{
                        __html: highlightedContent[index] || " ",
                      }}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 状态栏 */}
      <div className="flex items-center justify-between px-3 py-2 border-t text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          <span>{currentFile?.language || "unknown"}</span>
          <span>{currentFile?.lines || 0} 行</span>
          {searchQuery && (
            <span className="text-primary">
              找到 {filteredLines.length} 个匹配
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Eye className="h-3 w-3" />
          <span>UTF-8</span>
        </div>
      </div>
    </div>
  );
}
