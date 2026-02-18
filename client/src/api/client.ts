/**
 * API 客户端
 * 
 * Axios 封装，支持 JWT 刷新、错误处理
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
} from "axios";
import { useAuthStore } from "@/stores/auth-store";

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 是否正在刷新 token
let isRefreshing = false;
// 等待刷新完成的请求队列
let refreshSubscribers: ((token: string) => void)[] = [];

// 订阅 token 刷新
function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

// 通知所有订阅者新 token
function onTokenRefreshed(newToken: string) {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
}

// 请求拦截器 - 添加认证头
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理错误和 token 刷新
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // 如果是 401 错误且没有重试过
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 如果没有刷新 token，直接登出
      const refreshToken = useAuthStore.getState().refreshToken;
      if (!refreshToken) {
        useAuthStore.getState().logout();
        return Promise.reject(error);
      }

      // 如果正在刷新，加入等待队列
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            resolve(apiClient(originalRequest));
          });
        });
      }

      // 开始刷新 token
      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await useAuthStore.getState().refreshAccessToken();
        onTokenRefreshed(newToken);
        
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// 通用请求方法
export async function apiRequest<T>(
  config: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient(config);
  return response.data;
}

// GET 请求
export async function get<T>(
  url: string,
  params?: Record<string, any>,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.get(url, { params, ...config });
  return response.data;
}

// POST 请求
export async function post<T>(
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.post(url, data, config);
  return response.data;
}

// PUT 请求
export async function put<T>(
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.put(url, data, config);
  return response.data;
}

// PATCH 请求
export async function patch<T>(
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.patch(url, data, config);
  return response.data;
}

// DELETE 请求
export async function del<T>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.delete(url, config);
  return response.data;
}

// 文件上传
export async function uploadFile<T>(
  url: string,
  file: File,
  onProgress?: (progress: number) => void,
  additionalData?: Record<string, any>
): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  
  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }

  const response = await apiClient.post(url, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });

  return response.data;
}

export default apiClient;
