import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 使用 SSR 模式以支持动态路由
  // 如需静态导出，请使用 "output: 'export'" 但需要处理动态路由
  distDir: 'dist',
  images: {
    unoptimized: true,
  },
  // API 代理到 Python 后端（仅在开发时生效）
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
      {
        source: '/api/auth/:path*',
        destination: 'http://localhost:8000/api/v1/auth/:path*',
      },
    ];
  },
};

export default nextConfig;
