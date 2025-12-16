import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  FileCode,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  File,
} from "lucide-react";
import { useState } from "react";

interface FileNode {
  name: string;
  type: "file" | "folder";
  size?: string;
  status?: "ready" | "pending" | "missing";
  children?: FileNode[];
}

interface ExportPreviewProps {
  projectName: string;
  version: string;
  className?: string;
}

const defaultStructure: FileNode[] = [
  {
    name: "01_申请表_占位.pdf",
    type: "file",
    size: "128 KB",
    status: "ready",
  },
  {
    name: "02_源代码_鉴别材料.pdf",
    type: "file",
    size: "2.4 MB",
    status: "ready",
  },
  {
    name: "03_操作说明书.pdf",
    type: "file",
    size: "1.8 MB",
    status: "ready",
  },
  {
    name: "04_证明材料",
    type: "folder",
    children: [
      { name: "身份证明.pdf", type: "file", size: "256 KB", status: "ready" },
      { name: "授权书.pdf", type: "file", size: "128 KB", status: "pending" },
    ],
  },
  {
    name: "05_材料核对清单.pdf",
    type: "file",
    size: "64 KB",
    status: "ready",
  },
  {
    name: "06_打印与网报操作指南.pdf",
    type: "file",
    size: "96 KB",
    status: "ready",
  },
];

export function ExportPreview({ projectName, version, className }: ExportPreviewProps) {
  const [expandedFolders, setExpandedFolders] = useState<string[]>(["04_证明材料"]);

  const toggleFolder = (name: string) => {
    setExpandedFolders((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  const getFileIcon = (node: FileNode) => {
    if (node.type === "folder") {
      return <FolderOpen className="h-4 w-4 text-yellow-500" />;
    }
    if (node.name.includes("源代码")) {
      return <FileCode className="h-4 w-4 text-blue-500" />;
    }
    return <FileText className="h-4 w-4 text-muted-foreground" />;
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "ready":
        return (
          <Badge variant="secondary" className="text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
            已就绪
          </Badge>
        );
      case "pending":
        return (
          <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
            待上传
          </Badge>
        );
      case "missing":
        return (
          <Badge variant="destructive" className="text-xs">
            缺失
          </Badge>
        );
      default:
        return null;
    }
  };

  const renderNode = (node: FileNode, depth: number = 0) => {
    const isExpanded = expandedFolders.includes(node.name);

    return (
      <div key={node.name}>
        <div
          className={cn(
            "flex items-center gap-2 py-1.5 px-2 rounded-md hover-elevate cursor-pointer",
            depth > 0 && "ml-5"
          )}
          onClick={() => node.type === "folder" && toggleFolder(node.name)}
          data-testid={`export-file-${node.name}`}
        >
          {node.type === "folder" && (
            isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )
          )}
          {node.type === "file" && <div className="w-4" />}
          {getFileIcon(node)}
          <span className="flex-1 text-sm">{node.name}</span>
          {node.size && (
            <span className="text-xs text-muted-foreground">{node.size}</span>
          )}
          {getStatusBadge(node.status)}
        </div>
        {node.type === "folder" && isExpanded && node.children && (
          <div>
            {node.children.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">导出包预览</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border bg-card p-4">
          <div className="flex items-center gap-2 pb-3 border-b mb-3">
            <FolderOpen className="h-5 w-5 text-yellow-500" />
            <span className="font-medium">
              SoftCopyrightKit_{projectName}_{version}
            </span>
          </div>
          <div className="space-y-0.5">
            {defaultStructure.map((node) => renderNode(node))}
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
          <span>共 6 个文件</span>
          <span>预计压缩后约 4.8 MB</span>
        </div>
      </CardContent>
    </Card>
  );
}
