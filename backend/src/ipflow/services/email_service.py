"""邮件发送服务.

支持组织邀请等通知邮件。采用「优先 SMTP，降级日志」策略：

- **SMTP 已配置**（``SMTP_HOST`` + ``SMTP_USER``）：通过 ``aiosmtplib`` 异步发送。
- **SMTP 未配置**（本地 / 仿真环境）：在日志中记录邮件内容（含邀请链接），
  不抛异常，保证业务流程（如邀请记录创建）不受影响。

环境变量见 ``config.py`` 的 ``SMTP_*`` 配置项。
"""

import logging
from email.message import EmailMessage
from typing import Optional

from ipflow.config import get_settings

logger = logging.getLogger(__name__)


def _get_from_address(settings) -> str:
    """获取发件人地址（优先 SMTP_USER）。"""
    return getattr(settings, "SMTP_FROM", None) or settings.SMTP_USER or "noreply@ipflow.local"


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
) -> bool:
    """发送邮件.

    Args:
        to_email: 收件人邮箱
        subject: 邮件主题
        body: 纯文本正文
        html: 可选 HTML 正文

    Returns:
        ``True`` 表示发送成功（或降级记录）；``False`` 表示发送失败
    """
    settings = get_settings()

    # SMTP 未配置：降级到日志记录
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.info(
            "邮件发送（SMTP 未配置，降级日志）→ to=%s subject=%s\n%s",
            to_email, subject, body,
        )
        return True

    try:
        import aiosmtplib  # type: ignore

        message = EmailMessage()
        message["From"] = _get_from_address(settings)
        message["To"] = to_email
        message["Subject"] = subject
        if html:
            message.set_content(body)
            message.add_alternative(html, subtype="html")
        else:
            message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_TLS,
        )
        logger.info("邮件已发送：to=%s subject=%s", to_email, subject)
        return True
    except ImportError:
        logger.warning(
            "aiosmtplib 未安装，邮件降级日志 → to=%s subject=%s", to_email, subject
        )
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("邮件发送失败（to=%s）：%s", to_email, e)
        return False


async def send_organization_invitation(
    to_email: str,
    organization_name: str,
    inviter_name: str,
    invite_url: str,
    role: str = "member",
    expires_in_days: int = 7,
) -> bool:
    """发送组织邀请邮件.

    Args:
        to_email: 被邀请人邮箱
        organization_name: 组织名称
        inviter_name: 邀请人名称
        invite_url: 接受邀请的链接（含 token）
        role: 被分配的角色
        expires_in_days: 邀请有效期（天）

    Returns:
        发送是否成功
    """
    role_labels = {
        "admin": "管理员",
        "manager": "经理",
        "member": "成员",
        "viewer": "访客",
    }
    role_label = role_labels.get(role, role)

    subject = f"【IPFlow】{inviter_name} 邀请您加入组织「{organization_name}」"
    body = f"""您好，

{inviter_name} 邀请您以「{role_label}」身份加入组织「{organization_name}」，
共同管理知识产权申报材料。

点击以下链接接受邀请（{expires_in_days} 天内有效）：
{invite_url}

如非本人操作，请忽略本邮件。

—— IPFlow 知识产权申报材料辅助工具
"""
    html = f"""
<html><body style="font-family: -apple-system, sans-serif; line-height: 1.6; color: #333;">
<h2 style="color: #2563eb;">您收到一份组织邀请</h2>
<p>您好，</p>
<p><strong>{inviter_name}</strong> 邀请您以「<strong>{role_label}</strong>」身份加入组织
<strong>「{organization_name}」</strong>，共同管理知识产权申报材料。</p>
<p>
  <a href="{invite_url}"
     style="display:inline-block;background:#2563eb;color:#fff;padding:10px 24px;
            border-radius:6px;text-decoration:none;font-weight:bold;">
    接受邀请
  </a>
</p>
<p style="color:#666;font-size:13px;">
  邀请链接 {expires_in_days} 天内有效。如非本人操作，请忽略本邮件。
</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
<p style="color:#999;font-size:12px;">—— IPFlow 知识产权申报材料辅助工具</p>
</body></html>
"""
    return await send_email(to_email, subject, body, html=html)


async def send_email_verification(
    to_email: str,
    username: str,
    verify_url: str,
) -> bool:
    """发送邮箱验证邮件.

    Args:
        to_email: 收件人邮箱
        username: 用户名（用于称呼）
        verify_url: 验证链接（含 token，前端回跳后调用验证端点）

    Returns:
        发送是否成功
    """
    subject = "【IPFlow】请验证您的邮箱"
    body = f"""您好，{username}：

感谢您注册 IPFlow。请点击以下链接完成邮箱验证（24 小时内有效）：
{verify_url}

如非本人操作，请忽略本邮件。

—— IPFlow 知识产权申报材料辅助工具
"""
    html = f"""
<html><body style="font-family: -apple-system, sans-serif; line-height: 1.6; color: #333;">
<h2 style="color: #2563eb;">验证您的邮箱</h2>
<p>您好，<strong>{username}</strong>：</p>
<p>感谢您注册 IPFlow。请点击以下按钮完成邮箱验证：</p>
<p>
  <a href="{verify_url}"
     style="display:inline-block;background:#2563eb;color:#fff;padding:10px 24px;
            border-radius:6px;text-decoration:none;font-weight:bold;">
    验证邮箱
  </a>
</p>
<p style="color:#666;font-size:13px;">
  链接 24 小时内有效。如非本人操作，请忽略本邮件。
</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
<p style="color:#999;font-size:12px;">—— IPFlow 知识产权申报材料辅助工具</p>
</body></html>
"""
    return await send_email(to_email, subject, body, html=html)


async def send_password_reset(
    to_email: str,
    username: str,
    reset_url: str,
) -> bool:
    """发送密码重置邮件.

    Args:
        to_email: 收件人邮箱
        username: 用户名（用于称呼）
        reset_url: 重置链接（含 token，前端回跳后展示重置表单）

    Returns:
        发送是否成功
    """
    subject = "【IPFlow】重置您的密码"
    body = f"""您好，{username}：

我们收到了您的密码重置请求。请点击以下链接设置新密码（1 小时内有效）：
{reset_url}

如非本人操作，请忽略本邮件，您的密码不会被更改。

—— IPFlow 知识产权申报材料辅助工具
"""
    html = f"""
<html><body style="font-family: -apple-system, sans-serif; line-height: 1.6; color: #333;">
<h2 style="color: #2563eb;">重置您的密码</h2>
<p>您好，<strong>{username}</strong>：</p>
<p>我们收到了您的密码重置请求。请点击以下按钮设置新密码：</p>
<p>
  <a href="{reset_url}"
     style="display:inline-block;background:#2563eb;color:#fff;padding:10px 24px;
            border-radius:6px;text-decoration:none;font-weight:bold;">
    重置密码
  </a>
</p>
<p style="color:#666;font-size:13px;">
  链接 1 小时内有效。如非本人操作，请忽略本邮件，您的密码不会被更改。
</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
<p style="color:#999;font-size:12px;">—— IPFlow 知识产权申报材料辅助工具</p>
</body></html>
"""
    return await send_email(to_email, subject, body, html=html)
