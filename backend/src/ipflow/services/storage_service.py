"""存储服务.

提供 MinIO/S3 兼容的对象存储操作。
"""

import hashlib
import io
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import uuid4

from minio import Minio
from minio.error import S3Error

from ipflow.config import get_settings


class StorageService:
    """存储服务.
    
    提供文件上传、下载、删除等功能。
    """
    
    def __init__(self):
        """初始化存储服务."""
        settings = get_settings()
        
        self.client = Minio(
            settings.STORAGE_ENDPOINT,
            access_key=settings.STORAGE_ACCESS_KEY,
            secret_key=settings.STORAGE_SECRET_KEY,
            region=settings.STORAGE_REGION,
            secure=settings.STORAGE_USE_SSL,
        )
        self.bucket = settings.STORAGE_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self) -> None:
        """确保存储桶存在."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            # 桶可能已经存在或其他错误
            pass
    
    def calculate_checksum(self, data: bytes) -> str:
        """计算 SHA-256 校验和.
        
        Args:
            data: 文件数据
            
        Returns:
            十六进制校验和字符串
        """
        return hashlib.sha256(data).hexdigest()
    
    def upload_file(
        self,
        file_data: BinaryIO,
        original_filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "uploads",
    ) -> dict:
        """上传文件.
        
        Args:
            file_data: 文件数据流
            original_filename: 原始文件名
            content_type: MIME 类型
            folder: 存储文件夹
            
        Returns:
            上传结果信息
        """
        # 读取文件内容
        content = file_data.read()
        content_length = len(content)
        
        # 计算校验和
        checksum = self.calculate_checksum(content)
        
        # 生成存储文件名
        ext = Path(original_filename).suffix
        storage_name = f"{uuid4().hex}{ext}"
        storage_path = f"{folder}/{storage_name}"
        
        # 上传
        data_stream = io.BytesIO(content)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=storage_path,
            data=data_stream,
            length=content_length,
            content_type=content_type,
            metadata={
                "x-amz-meta-original-filename": original_filename,
                "x-amz-meta-checksum": checksum,
            },
        )
        
        return {
            "storage_name": storage_name,
            "storage_path": storage_path,
            "file_size": content_length,
            "checksum": checksum,
        }
    
    def download_file(self, storage_path: str) -> bytes:
        """下载文件.
        
        Args:
            storage_path: 存储路径
            
        Returns:
            文件内容
        """
        response = self.client.get_object(self.bucket, storage_path)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    
    def delete_file(self, storage_path: str) -> None:
        """删除文件.
        
        Args:
            storage_path: 存储路径
        """
        self.client.remove_object(self.bucket, storage_path)
    
    def get_presigned_url(
        self,
        storage_path: str,
        expires: int = 3600,
    ) -> str:
        """获取预签名 URL.
        
        Args:
            storage_path: 存储路径
            expires: 过期时间（秒）
            
        Returns:
            预签名 URL
        """
        return self.client.presigned_get_object(
            self.bucket,
            storage_path,
            expires=expires,
        )


# 全局实例
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """获取存储服务单例."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
