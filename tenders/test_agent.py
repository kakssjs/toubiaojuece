import json

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
        self.assertEqual(
            [step["agent"] for step in report["agent_trace"]],
            ["信息抽取Agent", "招标分类Agent", "资质匹配Agent", "业绩匹配Agent", "风险识别Agent", "投标决策Agent"],
        )


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
