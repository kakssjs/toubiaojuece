import json
from unittest.mock import patch

from django.test import TestCase

from tenders.models import AnalysisReport, CompanyProfile, ProjectExperience, Qualification, TenderProject


SAMPLE_TENDER_TEXT = """
智慧园区数字化平台建设项目，采购方式为公开招标，预算金额480万元。
投标人须具备软件开发、系统集成相关能力，具有近三年类似项目业绩。
本项目要求提供CMMI三级认证、ISO9001质量管理体系认证和原厂授权函。
投标保证金为人民币5万元。付款条件为验收合格后支付70%，质保期满后支付30%。
评分标准：技术分50分，商务分30分，价格分20分。
投标截止时间为2026年7月20日09:30。
"""

SAMPLE_COMPANY_PROFILE = {
    "name": "小苏科技",
    "business_scope": ["软件开发", "系统集成", "智慧园区"],
    "qualifications": ["ISO9001质量管理体系认证", "软件企业认证"],
    "project_experiences": ["智慧园区平台建设项目", "政务数据平台项目"],
    "service_regions": ["全国"],
    "max_project_amount": 10000000,
    "forbidden_conditions": ["付款周期超过12个月"],
}


class TenderAnalysisAgentTests(TestCase):
    def test_agent_returns_structured_bid_decision(self):
        from tenders.agents import TenderAnalysisAgent

        report = TenderAnalysisAgent().analyze(
            tender_text=SAMPLE_TENDER_TEXT,
            company_profile=SAMPLE_COMPANY_PROFILE,
        )

        self.assertEqual(report["project_type"], "软件信息化")
        self.assertEqual(report["procurement_method"], "公开招标")
        self.assertIn(report["decision"], ["推荐投标", "谨慎投标", "不建议投标"])
        self.assertGreaterEqual(report["match_score"], 0)
        self.assertLessEqual(report["match_score"], 100)
        self.assertIn("CMMI三级认证", report["qualification_match"]["missing"])
        self.assertTrue(report["risks"])
        self.assertTrue(report["next_actions"])
        self.assertTrue(report["material_checklist"])
        self.assertTrue(report["scoring_breakdown"])
        self.assertIn("review_level", report["review_summary"])
        self.assertTrue(report["key_findings"])
        self.assertEqual(
            [step["agent"] for step in report["agent_trace"]],
            ["信息抽取Agent", "招标分类Agent", "资质匹配Agent", "业绩匹配Agent", "风险识别Agent", "投标决策Agent"],
        )

    def test_extracts_pdf_style_fields_and_matches_profile_aliases(self):
        from tenders.agents import TenderAnalysisAgent

        tender_text = """
        智慧园区数字化平台建设项目
        项目预算 人民币 4,800,000 元
        最高限价 人民币 4,650,000 元
        建设地点 江苏省示范市智慧园区
        投标截止时间 2026 年 8 月 20 日 09:30
        要求CMMI三级认证、信息安全管理体系认证和原厂授权函，并具有智慧园区类似业绩。
        """
        company_profile = {
            "qualifications": [
                "CMMI三级软件能力证明",
                "信息安全管理体系认证",
            ],
            "project_experiences": ["智慧园区综合管理平台"],
            "business_scope": ["政企信息化系统集成"],
        }

        report = TenderAnalysisAgent().analyze(tender_text, company_profile)

        self.assertEqual(report["budget_amount"], 4_800_000)
        self.assertEqual(report["highest_limit_amount"], 4_650_000)
        self.assertEqual(report["region"], "江苏")
        self.assertEqual(report["deadline"], "2026-08-20 09:30")
        self.assertIn("CMMI三级认证", report["qualification_match"]["matched"])
        self.assertIn("信息安全管理体系认证", report["qualification_match"]["matched"])
        self.assertEqual(report["qualification_match"]["missing"], ["原厂授权函"])
        self.assertEqual(report["experience_match"]["matched_cases"], ["智慧园区综合管理平台"])


class TenderAnalysisApiTests(TestCase):
    def test_agent_analyze_api_returns_json_report(self):
        response = self.client.post(
            "/api/agent/analyze/",
            data=json.dumps(
                {
                    "tender_text": SAMPLE_TENDER_TEXT,
                    "company_profile": SAMPLE_COMPANY_PROFILE,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["report"]["project_type"], "软件信息化")
        self.assertIn("risks", payload["report"])
        self.assertIn("scoring_breakdown", payload["report"])
        self.assertIn("review_summary", payload["report"])
        self.assertEqual(payload["report"]["analysis_engine"], "rule_based")

    def test_agent_api_only_uses_openai_when_explicitly_selected(self):
        openai_report = {
            "analysis_engine": "openai",
            "project_type": "软件信息化",
            "risks": [],
        }
        with patch("tenders.views.TenderAnalysisAgent.analyze", return_value=openai_report) as analyze:
            response = self.client.post(
                "/api/agent/analyze/",
                data=json.dumps({
                    "tender_text": SAMPLE_TENDER_TEXT,
                    "company_profile": SAMPLE_COMPANY_PROFILE,
                    "analysis_mode": "openai",
                }),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["report"]["analysis_engine"], "openai")
        analyze.assert_called_once()

    def test_agent_api_rejects_unknown_analysis_mode(self):
        response = self.client.post(
            "/api/agent/analyze/",
            data=json.dumps({
                "tender_text": SAMPLE_TENDER_TEXT,
                "company_profile": SAMPLE_COMPANY_PROFILE,
                "analysis_mode": "automatic",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_agent_api_uses_agnes_when_explicitly_selected(self):
        agnes_report = {
            "analysis_engine": "agnes",
            "project_type": "软件信息化",
            "risks": [],
        }
        with patch("tenders.views.AgnesTenderAnalysisAgent.analyze", return_value=agnes_report) as analyze:
            response = self.client.post(
                "/api/agent/analyze/",
                data=json.dumps({
                    "tender_text": SAMPLE_TENDER_TEXT,
                    "company_profile": SAMPLE_COMPANY_PROFILE,
                    "analysis_mode": "agnes",
                }),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["report"]["analysis_engine"], "agnes")
        analyze.assert_called_once()

    def test_agent_analyze_api_requires_tender_text(self):
        response = self.client.post(
            "/api/agent/analyze/",
            data=json.dumps({"company_profile": SAMPLE_COMPANY_PROFILE}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["ok"], False)

    def test_agent_analyze_api_can_save_project_and_report_for_company(self):
        company = CompanyProfile.objects.create(
            name="小苏科技",
            main_business="软件开发、系统集成、智慧园区",
            service_regions="全国",
            max_project_amount=10000000,
            forbidden_conditions="付款周期超过12个月",
        )
        Qualification.objects.create(
            company=company,
            name="ISO9001质量管理体系认证",
        )
        ProjectExperience.objects.create(
            company=company,
            name="智慧园区平台建设项目",
            industry="软件信息化",
            amount=4800000,
        )

        response = self.client.post(
            "/api/agent/analyze/",
            data=json.dumps(
                {
                    "tender_text": SAMPLE_TENDER_TEXT,
                    "company_id": company.id,
                    "save": True,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertIsNotNone(payload["project_id"])
        self.assertIsNotNone(payload["report_id"])

        project = TenderProject.objects.get(id=payload["project_id"])
        report = AnalysisReport.objects.get(id=payload["report_id"])

        self.assertEqual(project.company, company)
        self.assertEqual(project.name, payload["report"]["project_name"])
        self.assertEqual(project.project_type, "软件信息化")
        self.assertIsNotNone(project.deadline)
        self.assertEqual(project.status, TenderProject.Status.ANALYZED)
        self.assertEqual(report.tender_project, project)
        self.assertEqual(report.match_score, payload["report"]["match_score"])
        self.assertEqual(report.raw_report["decision"], payload["report"]["decision"])

    def test_agent_analyze_api_returns_404_when_company_does_not_exist(self):
        response = self.client.post(
            "/api/agent/analyze/",
            data=json.dumps(
                {
                    "tender_text": SAMPLE_TENDER_TEXT,
                    "company_id": 99999,
                    "save": True,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["ok"], False)
