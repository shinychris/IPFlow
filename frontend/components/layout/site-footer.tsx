/**
 * 公共页脚组件
 * Public site footer - links and company information
 */
import Link from "next/link";
import { Github, Twitter, Mail, MapPin } from "lucide-react";

const footerSections = [
  {
    title: "产品",
    links: [
      { label: "软著申请", href: "/features#copyright" },
      { label: "专利申请", href: "/features#patent" },
      { label: "商标注册", href: "/features#trademark" },
      { label: "定价", href: "/pricing" },
    ],
  },
  {
    title: "资源",
    links: [
      { label: "帮助文档", href: "/help" },
    ],
  },
  {
    title: "法律",
    links: [
      { label: "隐私政策", href: "/privacy" },
      { label: "用户协议", href: "/terms" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="container py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <span className="text-sm font-bold">IP</span>
              </div>
              <span className="text-lg font-bold">IPFlow</span>
            </div>
            <p className="text-sm text-muted-foreground">
              专业的知识产权申请管理平台，帮助企业和个人高效完成软著、专利、商标申请。
            </p>
            <div className="flex space-x-4">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground"
              >
                <Github className="h-5 w-5" />
                <span className="sr-only">GitHub</span>
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground"
              >
                <Twitter className="h-5 w-5" />
                <span className="sr-only">Twitter</span>
              </a>
            </div>
          </div>

          {/* Footer Links */}
          {footerSections.map((section) => (
            <div key={section.title} className="space-y-4">
              <h3 className="text-sm font-semibold">{section.title}</h3>
              <ul className="space-y-3">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Contact Section */}
        <div className="mt-12 pt-8 border-t">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            <div className="flex items-start space-x-3">
              <Mail className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">邮箱</p>
                <p className="text-muted-foreground">support@ipflow.com</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <MapPin className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">地址</p>
                <p className="text-muted-foreground">北京市海淀区中关村科技园</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div>
                <p className="font-medium">工作时间</p>
                <p className="text-muted-foreground">周一至周五 9:00-18:00</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-8 border-t flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} IPFlow. All rights reserved.
          </p>
          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            <Link href="/privacy" className="hover:text-foreground">
              隐私政策
            </Link>
            <Link href="/terms" className="hover:text-foreground">
              用户协议
            </Link>
            <span>京ICP备XXXXXXXX号</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
