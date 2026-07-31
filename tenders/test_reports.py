from django.test import TestCase
from zipfile import ZipFile
from io import BytesIO
import json
from datetime import datetime

from django.utils import timezone

from tenders.models import AnalysisReport, CompanyProfile, TenderProject


class ReportDetailApiTests(TestCase):
    def test_report_detail_api_returns_saved_report(self):
        company = CompanyProfile.objects.create(name="小苏科技")
        project = TenderProject.objects.create(
            company=company,
            name="智慧园区数字化平台建设项目",
            procurement_method="公开招标",
            project_type="软件信息化",
            budget_amount=4800000,
            source_text="招标文本内容",
            status=TenderProject.Status.ANALYZED,
        )
        report = AnalysisReport.objects.create(
            tender_project=project,
            decision=AnalysisReport.Decision.CAUTIOUS,
            match_score=76,
            summary="项目方向匹配，但需要补充材料。",
            risks=[{"type": "材料风险", "level": "高", "description": "缺少原厂授权函"}],
            missing_materials=["原厂授权函"],
            next_actions=["确认原厂授权"],
            raw_report={
                "project_type": "软件信息化",
                "agent_trace": [{"agent": "投标决策Agent"}],
                "review_summary": {"review_level": "需复核", "average_dimension_score": 76},
                "scoring_breakdown": [{"dimension": "资质匹配", "score": 76, "weight": "35%", "comment": "需补材料"}],
                "key_findings": ["缺少原厂授权函"],
            },
        )

        response = self.client.get(f"/api/reports/{report.id}/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["report"]["id"], report.id)
        self.assertEqual(payload["report"]["project"]["name"], "智慧园区数字化平台建设项目")
        self.assertEqual(payload["report"]["decision_label"], "谨慎投标")
        self.assertEqual(payload["report"]["risks"][0]["type"], "材料风险")
        self.assertEqual(payload["report"]["review_summary"]["review_level"], "需复核")
        self.assertEqual(payload["report"]["scoring_breakdown"][0]["dimension"], "资质匹配")
        self.assertEqual(payload["report"]["key_findings"][0], "缺少原厂授权函")

    def test_report_detail_api_returns_404_for_missing_report(self):
        response = self.client.get("/api/reports/99999/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["ok"], False)

    def test_report_detail_api_enriches_legacy_report_sections(self):
        company = CompanyProfile.objects.create(name="历史报告企业")
        project = TenderProject.objects.create(company=company, name="历史报告项目")
        report = AnalysisReport.objects.create(
            tender_project=project,
            decision=AnalysisReport.Decision.CAUTIOUS,
            match_score=64,
            risks=[{"type": "合规风险", "level": "高", "description": "资质待补"}],
            missing_materials=["原厂授权函"],
            raw_report={
                "qualification_match": {"status": "partial", "score": 60},
                "experience_match": {"score": 72},
            },
        )

        response = self.client.get(f"/api/reports/{report.id}/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()["report"]
        self.assertEqual(payload["review_summary"]["review_level"], "需复核")
        self.assertEqual(payload["review_summary"]["material_status"], "少量材料待补")
        self.assertEqual(payload["review_summary"]["high_risk_count"], 1)
        self.assertEqual(len(payload["scoring_breakdown"]), 4)
        self.assertIn("系统建议：谨慎投标", payload["key_findings"][0])

    def test_report_export_pdf_returns_pdf_file(self):
        report = self._create_report()

        response = self.client.get(f"/api/reports/{report.id}/export/pdf/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(".pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_report_export_word_returns_docx_file(self):
        report = self._create_report()

        response = self.client.get(f"/api/reports/{report.id}/export/word/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(".docx", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"PK"))
        with ZipFile(BytesIO(response.content)) as docx:
            document_xml = docx.read("word/document.xml").decode("utf-8")

        self.assertIn("资质匹配", document_xml)
        self.assertIn("业绩匹配", document_xml)
        self.assertIn("材料清单", document_xml)
        self.assertIn("Agent执行轨迹", document_xml)
        self.assertIn("最高限价", document_xml)
        self.assertIn("4,650,000 元", document_xml)
        self.assertIn("江苏", document_xml)
        self.assertIn("2026-08-20 09:30", document_xml)
        self.assertIn("部分匹配", document_xml)
        self.assertIn("需准备", document_xml)
        self.assertIn("已完成", document_xml)
        self.assertNotIn(">partial<", document_xml)
        self.assertNotIn(">required<", document_xml)
        self.assertNotIn(">completed<", document_xml)

    def test_report_ask_api_answers_bid_decision_question(self):
        report = self._create_report()

        response = self.client.post(
            f"/api/reports/{report.id}/ask/",
            data=json.dumps({"question": "这份标我们能投吗？"}, ensure_ascii=False),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertIn("谨慎投标", payload["answer"])
        self.assertIn("76", payload["answer"])
        self.assertEqual(payload["question"], "这份标我们能投吗？")
        self.assertTrue(payload["references"])

    def test_report_ask_api_answers_missing_material_question(self):
        report = self._create_report()

        response = self.client.post(
            f"/api/reports/{report.id}/ask/",
            data=json.dumps({"question": "需要补充哪些材料？"}, ensure_ascii=False),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertIn("原厂授权函", payload["answer"])
        self.assertIn("投标保证金缴纳凭证", payload["answer"])

    def test_report_ask_api_rejects_empty_question(self):
        report = self._create_report()

        response = self.client.post(
            f"/api/reports/{report.id}/ask/",
            data=json.dumps({"question": ""}, ensure_ascii=False),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["ok"], False)

    def _create_report(self):
        company = CompanyProfile.objects.create(name="小苏科技")
        project = TenderProject.objects.create(
            company=company,
            name="智慧园区数字化平台建设项目",
            procurement_method="公开招标",
            project_type="软件信息化",
            region="江苏",
            budget_amount=4800000,
            deadline=timezone.make_aware(datetime(2026, 8, 20, 9, 30)),
            source_text="招标文本内容",
            status=TenderProject.Status.ANALYZED,
        )
        return AnalysisReport.objects.create(
            tender_project=project,
            decision=AnalysisReport.Decision.CAUTIOUS,
            match_score=76,
            summary="项目方向匹配，但需要补充材料。",
            risks=[{"type": "材料风险", "level": "高", "description": "缺少原厂授权函"}],
            missing_materials=["原厂授权函"],
            next_actions=["确认原厂授权"],
            raw_report={
                "project_type": "软件信息化",
                "highest_limit_amount": 4650000,
                "deadline": "2026-08-20 09:30",
                "qualification_match": {"status": "partial", "score": 76, "matched": ["ISO9001"], "missing": ["原厂授权函"]},
                "experience_match": {"score": 80, "summary": "存在类似项目经验", "matched_cases": ["智慧园区平台建设项目"]},
                "material_checklist": [{"category": "商务材料", "name": "投标保证金缴纳凭证", "status": "required"}],
                "agent_trace": [{"agent": "投标决策Agent", "status": "completed"}],
                "review_summary": {"review_level": "需复核", "average_dimension_score": 76, "high_risk_count": 1},
                "scoring_breakdown": [{"dimension": "资质匹配", "score": 76, "weight": "35%", "comment": "需补原厂授权函"}],
                "key_findings": ["缺少原厂授权函"],
            },
        )


class ReportFrontendRouteTests(TestCase):
    def test_report_frontend_route_returns_vue_app(self):
        response = self.client.get("/reports/1/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div id="app"></div>', html=True)
