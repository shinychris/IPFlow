import { useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface FileItem {
  id: string;
  file: File;
  progress: number;
  status: "uploading" | "completed" | "error";
  error?: string;
}

interface FileUploaderProps {
  accept?: string;
  maxSize?: number;
  multiple?: boolean;
  onUpload: (files: File[]) => Promise<void>;
  className?: string;
  description?: string;
}

export function FileUploader({
  accept = ".zip",
  maxSize = 100 * 1024 * 1024,
  multiple = false,
  onUpload,
  className,
  description = "拖拽文件到此处，或点击选择",
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<FileItem[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const processFiles = async (fileList: FileList | null) => {
    if (!fileList) return;

    const newFiles = Array.from(fileList).filter((file) => {
      if (file.size > maxSize) {
        return false;
      }
      return true;
    });

    if (newFiles.length === 0) return;

    const fileItems: FileItem[] = newFiles.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      progress: 0,
      status: "uploading" as const,
    }));

    setFiles((prev) => (multiple ? [...prev, ...fileItems] : fileItems));

    try {
      await onUpload(newFiles);
      setFiles((prev) =>
        prev.map((f) =>
          fileItems.some((nf) => nf.id === f.id)
            ? { ...f, progress: 100, status: "completed" as const }
            : f
        )
      );
    } catch (error) {
      setFiles((prev) =>
        prev.map((f) =>
          fileItems.some((nf) => nf.id === f.id)
            ? { ...f, status: "error" as const, error: "上传失败" }
            : f
        )
      );
    }
  };

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      await processFiles(e.dataTransfer.files);
    },
    [maxSize, multiple, onUpload]
  );

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    await processFiles(e.target.files);
    e.target.value = "";
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div
        className={cn(
          "relative flex flex-col items-center justify-center rounded-md border-2 border-dashed p-8 transition-colors",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50",
          "cursor-pointer"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        data-testid="file-upload-zone"
      >
        <input
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleFileSelect}
          className="absolute inset-0 cursor-pointer opacity-0"
          data-testid="file-input"
        />
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="rounded-full bg-primary/10 p-3">
            <Upload className="h-6 w-6 text-primary" />
          </div>
          <div>
            <p className="font-medium">{description}</p>
            <p className="text-sm text-muted-foreground">
              支持 {accept} 格式，最大 {formatFileSize(maxSize)}
            </p>
          </div>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((fileItem) => (
            <div
              key={fileItem.id}
              className="flex items-center gap-3 rounded-md border bg-card p-3"
              data-testid={`file-item-${fileItem.id}`}
            >
              <File className="h-8 w-8 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium truncate">{fileItem.file.name}</span>
                  <span className="text-sm text-muted-foreground flex-shrink-0">
                    {formatFileSize(fileItem.file.size)}
                  </span>
                </div>
                {fileItem.status === "uploading" && (
                  <Progress value={fileItem.progress} className="mt-1 h-1" />
                )}
                {fileItem.status === "error" && (
                  <p className="text-sm text-destructive mt-1">{fileItem.error}</p>
                )}
              </div>
              <div className="flex-shrink-0">
                {fileItem.status === "uploading" && (
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                )}
                {fileItem.status === "completed" && (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                )}
                {fileItem.status === "error" && (
                  <AlertCircle className="h-5 w-5 text-destructive" />
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeFile(fileItem.id)}
                data-testid={`remove-file-${fileItem.id}`}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
