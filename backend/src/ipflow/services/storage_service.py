"""存储服务.

提供 MinIO/S3 兼容的对象存储，以及无 MinIO 时的本地文件系统存储
（STORAGE_TYPE=local，便于开发与仿真测试环境）。
"""

import hashlib
import io
import shutil
from pathlib import Path
from typing import BinaryIO, Optional, Union
from uuid import uuid4

from ipflow.config import get_settings


class StorageService:
    """存储服务.

    根据 ``STORAGE_TYPE`` 选择后端：
    - ``minio``（默认）：MinIO/S3 兼容对象存储；
    - ``local``：本地文件系统（``STORAGE_BASE_PATH``），无外部依赖。

    对外接口（upload_file/download_file/delete_file/get_presigned_url/
    calculate_checksum）在后端间保持一致。
    """

    def __init__(self):
        """初始化存储服务."""
        settings = get_settings()
        self.storage_type = (settings.STORAGE_TYPE or "minio").lower()
        self.bucket = settings.STORAGE_BUCKET

        if self.storage_type == "local":
            # 本地文件系统后端
            self.base_path = Path(settings.STORAGE_BASE_PATH).expanduser()
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.client = None
            return

        # MinIO/S3 后端（默认）
        from minio import Minio  # 延迟导入，避免 local 模式硬依赖 minio
        from minio.error import S3Error  # noqa: F401  保留供调用方按需使用

        self.client = Minio(
            settings.STORAGE_ENDPOINT,
            access_key=settings.STORAGE_ACCESS_KEY,
            secret_key=settings.STORAGE_SECRET_KEY,
            region=settings.STORAGE_REGION,
            secure=settings.STORAGE_USE_SSL,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """确保存储桶存在（仅 MinIO 后端）."""
        if self.client is None:
            return
        try:
            from minio.error import S3Error

            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error:
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

    def _safe_local_path(self, storage_path: str) -> Path:
        """规范化并校验本地存储路径，防止路径穿越.

        最终路径必须位于 ``base_path`` 之下（含等于 base_path）。
        使用 ``resolve()`` 比较，避免符号链接/相对路径让字符串前缀校验失效。
        """
        base = self.base_path.resolve()
        target = (self.base_path / storage_path).resolve()
        if target != base and base not in target.parents:
            raise ValueError("invalid storage_path")
        return target

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

        if self.client is None:
            # 本地文件系统：写入 base_path/storage_path
            target = self._safe_local_path(storage_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        else:
            # MinIO/S3
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
        if self.client is None:
            target = self._safe_local_path(storage_path)
            return target.read_bytes()
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
        if self.client is None:
            target = self._safe_local_path(storage_path)
            if target.exists():
                target.unlink()
            return
        self.client.remove_object(self.bucket, storage_path)

    def get_presigned_url(
        self,
        storage_path: str,
        expires: int = 3600,
    ) -> str:
        """获取预签名下载 URL.

        Args:
            storage_path: 存储路径
            expires: 过期时间（秒）

        Returns:
            预签名 URL（local 后端返回 file:// 路径，仅供开发/仿真使用）
        """
        if self.client is None:
            # 本地后端无签名概念，返回绝对路径（仅开发环境）
            return str(self._safe_local_path(storage_path))
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
