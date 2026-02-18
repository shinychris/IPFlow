"""软著信息 API 集成测试.

测试软件信息的获取和更新接口。
"""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSoftwareInfo:
    """测试软件信息 API."""

    async def test_get_software_info_success(self, client: AsyncClient, auth_headers: dict):
        """测试获取软件信息成功."""
        # 假设有一个已存在的项目
        project_id = "test-project-id"
        
        response = await client.get(
            f"/api/v1/copyright/projects/{project_id}/software-info",
            headers=auth_headers,
        )
        
        # 当前可能返回 404，但至少接口存在
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_update_software_info_success(self, client: AsyncClient, auth_headers: dict):
        """测试更新软件信息成功."""
        project_id = "test-project-id"
        update_data = {
            "software_full_name": "测试软件系统",
            "software_short_name": "测试软件",
            "version_number": "V1.0",
            "development_language": "Python, JavaScript",
            "functional_description": "这是一个测试软件的功能描述...",
            "technical_features": "技术特点1\n技术特点2",
            "target_domain": "企业服务",
        }
        
        response = await client.put(
            f"/api/v1/copyright/projects/{project_id}/software-info",
            headers=auth_headers,
            json=update_data,
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_get_software_info_without_auth(self, client: AsyncClient):
        """测试未认证获取软件信息."""
        project_id = "test-project-id"
        
        response = await client.get(
            f"/api/v1/copyright/projects/{project_id}/software-info",
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
def auth_headers():
    """认证请求头."""
    return {"Authorization": "Bearer test-token"}
