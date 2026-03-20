"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/page-header";
import { HelpCircle, Book, MessageCircle, Mail } from "lucide-react";

const faqs = [
  {
    question: "如何创建新项目？",
    answer: "在工作台选择对应的业务类型（软著/专利/商标），点击新建项目按钮即可开始创建。",
  },
  {
    question: "项目支持哪些导出格式？",
    answer: "目前支持导出为 PDF 格式和 Word 文档格式，方便您提交到相应的申请系统。",
  },
  {
    question: "如何修改已创建的项目？",
    answer: "在项目列表中找到需要修改的项目，点击编辑按钮即可进入编辑页面。",
  },
  {
    question: "数据是否安全？",
    answer: "您的数据仅存储在您的设备本地，不会上传到服务器，确保数据隐私安全。",
  },
];

export default function HelpPage() {
  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="帮助文档"
        description="常见问题解答和使用指南"
      />

      <div className="grid gap-6 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Book className="h-5 w-5" />
              快速入门
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              知识产权助手是一款帮助您高效准备知识产权申请材料的工具。
              支持软件著作权、专利和商标三大类型的申请。
            </p>
            <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
              <li>选择业务类型并创建新项目</li>
              <li>按照向导填写申请信息</li>
              <li>上传必要的附件材料</li>
              <li>预览并导出申请材料</li>
            </ol>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HelpCircle className="h-5 w-5" />
              常见问题
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {faqs.map((faq, index) => (
              <div key={index} className="space-y-1">
                <h4 className="font-medium">{faq.question}</h4>
                <p className="text-sm text-muted-foreground">{faq.answer}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              联系我们
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              如果您遇到问题或有任何建议，欢迎联系我们。
            </p>
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4" />
              <span>support@ipflow.com</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
