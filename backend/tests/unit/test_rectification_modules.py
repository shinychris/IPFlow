"""新增整改模块的单元测试.

覆盖 commit 042ad3a + 第三轮修复引入的模块，提供回归保护：
- utils.enums.enum_value（枚举/字符串统一处理）
- core.token_blacklist（令牌吊销，Redis 降级内存）
- services.compliance（专利/商标合规规则引擎）
- services.copyright.draft_providers._parse_llm_json（LLM 草稿 JSON 解析）
- services.export.docx_writer（DOCX 导出）
- services.subscriptions.service（webhook 事件应用与布尔值转换）
"""

import pytest

from ipflow.utils.enums import enum_value
from ipflow.models.patent import PatentType
from ipflow.models.trademark import TrademarkType


# =============================================================================
# enum_value
# =============================================================================


class TestEnumValue:
    """enum_value 应同时处理枚举成员、字符串与 None。"""

    def test_enum_member_returns_value(self) -> None:
        assert enum_value(PatentType.INVENTION) == "invention"
        assert enum_value(TrademarkType.WORD) == "word"

    def test_plain_string_passthrough(self) -> None:
        # SQLite/字符串列场景
        assert enum_value("invention") == "invention"
        assert enum_value("utility_model") == "utility_model"

    def test_none_returns_none(self) -> None:
        assert enum_value(None) is None

    def test_empty_string(self) -> None:
        assert enum_value("") == ""


# =============================================================================
# token_blacklist
# =============================================================================


class TestTokenBlacklist:
    """令牌黑名单（Redis 不可用时降级到进程内集合）。"""

    def setup_method(self) -> None:
        from ipflow.core.token_blacklist import clear_in_memory_blacklist

        clear_in_memory_blacklist()

    def test_revoke_then_check(self) -> None:
        from ipflow.core.token_blacklist import revoke_token, is_token_revoked

        assert is_token_revoked("jti-abc") is False
        revoke_token("jti-abc", exp=9999999999)
        assert is_token_revoked("jti-abc") is True

    def test_empty_jti_is_never_revoked(self) -> None:
        from ipflow.core.token_blacklist import is_token_revoked, revoke_token

        revoke_token("")  # no-op
        assert is_token_revoked("") is False

    def test_unrevoked_jti_still_valid(self) -> None:
        from ipflow.core.token_blacklist import is_token_revoked

        assert is_token_revoked("never-revoked") is False

    def test_access_token_lifecycle(self) -> None:
        """端到端：access token 在 revoke 后被 decode/verify 拒绝。"""
        from ipflow.core.security import (
            create_access_token,
            decode_access_token,
            verify_access_token,
        )

        token = create_access_token("user-lifecycle")
        # 创建后有效
        assert decode_access_token(token) is not None
        # 吊销后无效
        payload = decode_access_token(token)
        assert payload is not None
        from ipflow.core.token_blacklist import revoke_token

        revoke_token(payload["jti"], payload["exp"])
        assert decode_access_token(token) is None
        with pytest.raises(ValueError, match="revoked"):
            verify_access_token(token)


# =============================================================================
# 专利 / 商标合规检查器
# =============================================================================


class TestPatentComplianceChecker:
    def _checker(self):
        from ipflow.services.compliance import PatentComplianceChecker

        return PatentComplianceChecker()

    def test_complete_patent_passes(self) -> None:
        from uuid import uuid4

        report = self._checker().check(
            uuid4(),
            patent_info={
                "title": "一种XXX系统",
                "abstract": "这是一段超过三十个字的摘要内容，用于测试专利摘要规则引擎工作正常。",
                "patent_type": "invention",
            },
            description={
                "technical_field": "本发明涉及技术领域，具体涉及一种系统。",
                "background_art": "现有技术存在不足需要改进。",
                "problem_solved": "本发明要解决的技术问题是XXX。",
                "technical_solution": "为解决上述问题，本发明采用如下方案。",
                "beneficial_effects": "采用本发明具有如下有益效果。",
                "implementation": "下面结合实施例对本发明作进一步说明。",
            },
            claims=[
                {
                    "claim_number": 1,
                    "claim_type": "independent",
                    "parent_claim_number": None,
                    "content": "一种系统，其特征在于。",
                }
            ],
        )
        # 完整材料：无失败项，可导出（允许仅 warning 不阻断导出）
        assert report.failed == 0
        assert report.can_export is True

    def test_missing_claims_fails(self) -> None:
        from uuid import uuid4

        report = self._checker().check(
            uuid4(), patent_info=None, description=None, claims=[]
        )
        assert report.failed > 0
        assert report.can_export is False

    def test_claims_without_independent_fails(self) -> None:
        from uuid import uuid4

        report = self._checker().check(
            uuid4(),
            patent_info={"title": "X", "abstract": "x", "patent_type": "invention"},
            description={},
            claims=[
                {
                    "claim_number": 1,
                    "claim_type": "dependent",
                    "parent_claim_number": 0,
                    "content": "依前述。",
                }
            ],
        )
        # 缺独立权利要求应失败
        assert any(r.rule_id == "P_CLAIM_002" and r.status.value == "failed" for r in report.results)


class TestTrademarkComplianceChecker:
    def _checker(self):
        from ipflow.services.compliance import TrademarkComplianceChecker

        return TrademarkComplianceChecker()

    def test_word_trademark_with_classes_passes(self) -> None:
        from uuid import uuid4

        report = self._checker().check(
            uuid4(),
            trademark_info={"trademark_name": "IPFlow", "trademark_type": "word"},
            nice_classes=[{"goods_services": ["软件即服务"]}],
        )
        assert report.failed == 0

    def test_device_trademark_without_image_fails(self) -> None:
        from uuid import uuid4

        report = self._checker().check(
            uuid4(),
            trademark_info={"trademark_name": "Logo", "trademark_type": "device"},
            nice_classes=[{"goods_services": ["广告"]}],
        )
        # 图形商标必须上传图样
        assert any(
            r.rule_id == "T_INFO_003" and r.status.value == "failed"
            for r in report.results
        )

    def test_no_nice_class_fails(self) -> None:
        from uuid import uuid4

        report = self._checker().check(
            uuid4(),
            trademark_info={"trademark_name": "X", "trademark_type": "word"},
            nice_classes=[],
        )
        assert report.failed > 0


# =============================================================================
# LLM 草稿 JSON 解析（含 markdown 围栏）
# =============================================================================


class TestParseLlmJson:
    def _provider(self):
        from ipflow.services.copyright.draft_providers import (
            LLMCopyrightDraftProvider,
        )

        return LLMCopyrightDraftProvider()

    def _project(self):
        class FakeProject:
            name = "测试软件"
            version = "2.0"

        return FakeProject()

    def test_plain_json(self) -> None:
        result = self._provider()._parse_llm_json(
            '{"software_info":{"software_full_name":"X"},"manual":{"title":"T","content_html":"<p>x</p>"}}',
            self._project(),
        )
        assert result.software_info["software_full_name"] == "X"
        assert result.manual["title"] == "T"

    def test_multiline_fenced_json(self) -> None:
        result = self._provider()._parse_llm_json(
            '```json\n{"software_info":{"software_full_name":"Y"},"manual":{"title":"M","content_html":""}}\n```',
            self._project(),
        )
        assert result.software_info["software_full_name"] == "Y"

    def test_single_line_fenced_json(self) -> None:
        """单行 ```json{...}``` 也应正确解析（FIX 4）。"""
        result = self._provider()._parse_llm_json(
            '```json{"software_info":{"software_full_name":"Z"},"manual":{"title":"N","content_html":""}}```',
            self._project(),
        )
        assert result.software_info["software_full_name"] == "Z"

    def test_invalid_json_falls_back_to_template(self) -> None:
        """非 JSON 内容应回退到模板而非崩溃。

        模板 provider 返回固定的占位草稿（含 software_full_name 等），
        source 字段不作为判据（模板默认也标 ai）；只验证不抛异常且回退成功。
        """
        result = self._provider()._parse_llm_json("这不是 JSON", self._project())
        # 回退成功：返回非空 DraftResult
        assert result.software_info is not None
        assert "software_full_name" in result.software_info


# =============================================================================
# DOCX 导出
# =============================================================================


class TestDocxWriter:
    def test_render_docx_produces_valid_ooxml(self) -> None:
        from ipflow.services.export import render_docx, docx_available

        if not docx_available():
            pytest.skip("python-docx 未安装")

        b = render_docx(
            "测试文档",
            [
                {"heading": "第一节", "paragraphs": ["段落一", "段落二"]},
                {"list_items": ["项A", "项B"], "key_values": [("k", "v")]},
            ],
            subtitle="副标题",
        )
        # OOXML 是 zip，magic = PK
        assert b[:2] == b"PK"
        assert len(b) > 1000

    def test_render_docx_empty_sections(self) -> None:
        from ipflow.services.export import render_docx, docx_available

        if not docx_available():
            pytest.skip("python-docx 未安装")

        b = render_docx("空文档", [])
        assert b[:2] == b"PK"

    def test_render_docx_with_html(self) -> None:
        from ipflow.services.export import render_docx, docx_available

        if not docx_available():
            pytest.skip("python-docx 未安装")

        b = render_docx(
            "HTML 文档", [{"html": "<h1>标题</h1><p>正文</p><li>列表项</li>"}]
        )
        assert b[:2] == b"PK"


# =============================================================================
# 订阅 webhook 事件应用与布尔值转换
# =============================================================================


class TestApplySubscriptionEvent:
    def _make_subscription(self):
        """构造一个最小可变的订阅 mock。"""
        from ipflow.models.subscription import SubscriptionStatus

        class FakeSub:
            def __init__(self):
                self.status = SubscriptionStatus.ACTIVE
                self.current_period_end = None
                self.cancel_at_period_end = False

        return FakeSub()

    def test_string_false_not_treated_as_true(self) -> None:
        """FIX 2: 'false' 字符串不应被当作 True。"""
        from ipflow.services.subscriptions.service import _apply_subscription_event

        sub = self._make_subscription()
        _apply_subscription_event(
            sub, "customer.subscription.updated", {"cancel_at_period_end": "false"}
        )
        assert sub.cancel_at_period_end is False

    def test_string_true_is_true(self) -> None:
        from ipflow.services.subscriptions.service import _apply_subscription_event

        sub = self._make_subscription()
        _apply_subscription_event(
            sub, "customer.subscription.updated", {"cancel_at_period_end": "true"}
        )
        assert sub.cancel_at_period_end is True

    def test_delete_event_cancels(self) -> None:
        from ipflow.services.subscriptions.service import _apply_subscription_event
        from ipflow.models.subscription import SubscriptionStatus

        sub = self._make_subscription()
        _apply_subscription_event(sub, "customer.subscription.deleted", {})
        assert sub.status == SubscriptionStatus.CANCELED

    def test_payment_failed_marks_past_due(self) -> None:
        from ipflow.services.subscriptions.service import _apply_subscription_event
        from ipflow.models.subscription import SubscriptionStatus

        sub = self._make_subscription()
        _apply_subscription_event(sub, "payment.failed", {})
        assert sub.status == SubscriptionStatus.PAST_DUE

    def test_extract_event_wechat_success(self) -> None:
        from ipflow.services.subscriptions.service import _extract_webhook_event

        et, sid, _ = _extract_webhook_event(
            "wechat", {"trade_state": "SUCCESS", "out_trade_no": "sub_123"}
        )
        assert et == "payment.success"
        assert sid == "sub_123"

    def test_extract_event_stripe(self) -> None:
        from ipflow.services.subscriptions.service import _extract_webhook_event

        et, sid, _ = _extract_webhook_event(
            "stripe",
            {"type": "invoice.paid", "data": {"object": {"subscription": "sub_x"}}},
        )
        assert et == "invoice.paid"
        assert sid == "sub_x"
