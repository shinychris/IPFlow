import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { FileQuestion, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center">
      <div className="flex h-24 w-24 items-center justify-center rounded-full bg-muted mb-6">
        <FileQuestion className="h-12 w-12 text-muted-foreground" />
      </div>
      <h1 className="text-2xl font-semibold mb-2">页面未找到</h1>
      <p className="text-muted-foreground mb-6 max-w-md">
        抱歉，您访问的页面不存在或已被移除。请检查网址是否正确，或返回首页继续浏览。
      </p>
      <Button asChild data-testid="button-go-home">
        <Link href="/">
          <Home className="h-4 w-4 mr-2" />
          返回首页
        </Link>
      </Button>
    </div>
  );
}
