/**
 * 富文本编辑器组件
 * 
 * 基于 contentEditable 的简单实现
 * 支持：粗体、斜体、标题、列表、图片插入
 */

import React, { useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Bold,
  Italic,
  Underline,
  List,
  ListOrdered,
  Image as ImageIcon,
  Heading1,
  Heading2,
  Quote,
  Link,
  Undo,
  Redo,
} from "lucide-react";

interface RichEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  minHeight?: string;
  maxHeight?: string;
  onImageUpload?: (file: File) => Promise<string>;
}

export function RichEditor({
  value,
  onChange,
  placeholder = "开始输入...",
  className,
  minHeight = "300px",
  maxHeight = "600px",
  onImageUpload,
}: RichEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [wordCount, setWordCount] = useState(0);

  // 执行编辑命令
  const execCommand = useCallback((command: string, value: string = "") => {
    document.execCommand(command, false, value);
    if (editorRef.current) {
      onChange(editorRef.current.innerHTML);
      updateWordCount();
    }
  }, [onChange]);

  // 更新字数统计
  const updateWordCount = useCallback(() => {
    if (editorRef.current) {
      const text = editorRef.current.innerText || "";
      setWordCount(text.trim().length);
    }
  }, []);

  // 处理输入
  const handleInput = useCallback(() => {
    if (editorRef.current) {
      onChange(editorRef.current.innerHTML);
      updateWordCount();
    }
  }, [onChange, updateWordCount]);

  // 处理图片上传
  const handleImageUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !onImageUpload) return;

    try {
      const url = await onImageUpload(file);
      execCommand("insertImage", url);
    } catch (error) {
      console.error("Image upload failed:", error);
    }

    // 重置 input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [execCommand, onImageUpload]);

  // 工具栏按钮
  const ToolbarButton = ({
    icon: Icon,
    command,
    value,
    title,
  }: {
    icon: React.ElementType;
    command: string;
    value?: string;
    title: string;
  }) => (
    <Button
      variant="ghost"
      size="icon"
      className="h-8 w-8"
      onClick={() => execCommand(command, value || "")}
      title={title}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );

  return (
    <div className={cn("border rounded-lg bg-card", className)}>
      {/* 工具栏 */}
      <div className="flex items-center gap-1 p-2 border-b flex-wrap">
        {/* 撤销/重做 */}
        <ToolbarButton icon={Undo} command="undo" title="撤销" />
        <ToolbarButton icon={Redo} command="redo" title="重做" />
        
        <Separator orientation="vertical" className="h-6 mx-1" />
        
        {/* 标题 */}
        <ToolbarButton icon={Heading1} command="formatBlock" value="H1" title="标题 1" />
        <ToolbarButton icon={Heading2} command="formatBlock" value="H2" title="标题 2" />
        
        <Separator orientation="vertical" className="h-6 mx-1" />
        
        {/* 格式 */}
        <ToolbarButton icon={Bold} command="bold" title="粗体" />
        <ToolbarButton icon={Italic} command="italic" title="斜体" />
        <ToolbarButton icon={Underline} command="underline" title="下划线" />
        
        <Separator orientation="vertical" className="h-6 mx-1" />
        
        {/* 列表 */}
        <ToolbarButton icon={List} command="insertUnorderedList" title="无序列表" />
        <ToolbarButton icon={ListOrdered} command="insertOrderedList" title="有序列表" />
        <ToolbarButton icon={Quote} command="formatBlock" value="BLOCKQUOTE" title="引用" />
        
        <Separator orientation="vertical" className="h-6 mx-1" />
        
        {/* 链接 */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => {
            const url = prompt("输入链接 URL:");
            if (url) execCommand("createLink", url);
          }}
          title="插入链接"
        >
          <Link className="h-4 w-4" />
        </Button>
        
        {/* 图片 */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => fileInputRef.current?.click()}
          title="插入图片"
          disabled={!onImageUpload}
        >
          <ImageIcon className="h-4 w-4" />
        </Button>
        
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleImageUpload}
        />
      </div>

      {/* 编辑区域 */}
      <div
        ref={editorRef}
        className="p-4 outline-none prose prose-sm dark:prose-invert max-w-none"
        style={{ minHeight, maxHeight, overflow: "auto" }}
        contentEditable
        onInput={handleInput}
        onBlur={handleInput}
        dangerouslySetInnerHTML={{ __html: value }}
        data-placeholder={placeholder}
      />

      {/* 字数统计 */}
      <div className="flex items-center justify-between px-4 py-2 border-t text-xs text-muted-foreground">
        <span>{wordCount} 字</span>
        <span>建议不少于 3000 字</span>
      </div>
    </div>
  );
}

// 添加 placeholder 样式
const style = document.createElement("style");
style.textContent = `
  [data-placeholder]:empty:before {
    content: attr(data-placeholder);
    color: hsl(var(--muted-foreground));
    pointer-events: none;
  }
`;
document.head.appendChild(style);
