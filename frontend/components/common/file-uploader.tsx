/**
 * 文件上传组件
 * 
 * 支持拖拽上传、进度显示、多文件、错误重试
 */

import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { X, File, Upload, Loader2, AlertCircle, CheckCircle } from "lucide-react";

export interface FileUploadItem {
  id: string;
  file: File;
  name: string;
  size: number;
  progress: number;
  status: "pending" | "uploading" | "completed" | "error";
  error?: string;
}

interface FileUploaderProps {
  onUpload: (files: File[], onProgress?: (id: string, progress: number) => void) => Promise<void>;
  accept?: Record<string, string[]>;
  maxSize?: number; // bytes
  maxFiles?: number;
  disabled?: boolean;
  className?: string;
}

export function FileUploader({
  onUpload,
  accept,
  maxSize = 100 * 1024 * 1024, // 100MB
  maxFiles = 1,
  disabled = false,
  className,
}: FileUploaderProps) {
  const [files, setFiles] = useState<FileUploadItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles: FileUploadItem[] = acceptedFiles.map((file) => ({
        id: Math.random().toString(36).substring(7),
        file,
        name: file.name,
        size: file.size,
        progress: 0,
        status: "pending",
      }));

      setFiles((prev) => [...prev, ...newFiles].slice(0, maxFiles));
    },
    [maxFiles]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept,
    maxSize,
    maxFiles: maxFiles - files.length,
    disabled: disabled || isUploading || files.length >= maxFiles,
  });

  const handleUpload = async () => {
    if (files.length === 0) return;

    setIsUploading(true);

    const pendingFiles = files.filter((f) => f.status === "pending");

    try {
      await onUpload(
        pendingFiles.map((f) => f.file),
        (id, progress) => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === id ? { ...f, progress, status: "uploading" } : f
            )
          );
        }
      );

      // 标记所有文件为完成
      setFiles((prev) =>
        prev.map((f) =>
          f.status === "uploading" ? { ...f, progress: 100, status: "completed" } : f
        )
      );
    } catch (error) {
      // 标记上传中的文件为错误
      setFiles((prev) =>
        prev.map((f) =>
          f.status === "uploading"
            ? { ...f, status: "error", error: "上传失败" }
            : f
        )
      );
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const formatSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const errors = fileRejections.map(({ file, errors }) => ({
    file: file.name,
    errors: errors.map((e) => {
      if (e.code === "file-too-large") return `文件超过 ${formatSize(maxSize)}`;
      if (e.code === "file-invalid-type") return "文件类型不支持";
      if (e.code === "too-many-files") return `最多上传 ${maxFiles} 个文件`;
      return e.message;
    }),
  }));

  return (
    <div className={cn("space-y-4", className)}>
      {/* 拖拽区域 */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50",
          (disabled || isUploading || files.length >= maxFiles) && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-4" />
        <p className="text-sm font-medium">
          {isDragActive ? "松开以上传文件" : "拖拽文件到此处，或点击选择文件"}
        </p>
        <p className="text-xs text-muted-foreground mt-2">
          支持格式: {accept ? Object.values(accept).flat().join(", ") : "所有文件"}
          {maxSize && ` · 最大 ${formatSize(maxSize)}`}
          {maxFiles > 1 && ` · 最多 ${maxFiles} 个文件`}
        </p>
      </div>

      {/* 错误提示 */}
      {errors.length > 0 && (
        <div className="space-y-2">
          {errors.map(({ file, errors }, index) => (
            <div
              key={index}
              className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-sm"
            >
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>
                {file}: {errors.join(", ")}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* 文件列表 */}
      {files.length > 0 && (
        <div className="space-y-3">
          {files.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-3 p-3 rounded-md border bg-card"
            >
              <File className="h-8 w-8 text-muted-foreground flex-shrink-0" />
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium truncate">{file.name}</p>
                  <span className="text-xs text-muted-foreground ml-2">
                    {formatSize(file.size)}
                  </span>
                </div>
                
                {file.status === "uploading" && (
                  <div className="mt-2">
                    <Progress value={file.progress} className="h-1" />
                  </div>
                )}
                
                {file.status === "error" && (
                  <p className="text-xs text-destructive mt-1">{file.error}</p>
                )}
                
                {file.status === "completed" && (
                  <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
                    <CheckCircle className="h-3 w-3" />
                    <span>上传完成</span>
                  </div>
                )}
              </div>

              {file.status !== "uploading" && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 flex-shrink-0"
                  onClick={() => removeFile(file.id)}
                  disabled={isUploading}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
              
              {file.status === "uploading" && (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      )}

      {/* 上传按钮 */}
      {files.length > 0 && files.some((f) => f.status === "pending") && (
        <Button
          onClick={handleUpload}
          disabled={isUploading}
          className="w-full"
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              上传中...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              开始上传
            </>
          )}
        </Button>
      )}
    </div>
  );
}
