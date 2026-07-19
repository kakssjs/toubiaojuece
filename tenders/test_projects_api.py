import json

from django.test import TestCase

from tenders.models import AnalysisReport, CompanyProfile, TenderProject, TenderReference


class ProjectDashboardApiTests(TestCase):
    def test_project_dashboard_api_returns_project_rows_and_summary(self):
        company = CompanyProfile.objects.create(name="小苏科技")
        project = TenderProject.objects.create(
            company=company,
            name="智慧园区数字化平台建设项目",
            procurement_method="公开招标",
            project_type="软件信息化",
            region="江苏",
            budget_amount=4800000,
            status=TenderProject.Status.ANALYZED,
        )
        AnalysisReport.objects.create(
            tender_project=project,
            decision=AnalysisReport.Decision.RECOMMENDED,
            match_score=91,
            summary="项目方向高度匹配。",
            risks=[{"type": "商务风险", "level": "中", "description": "付款周期较长"}],
        )

        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertEqual(payload["summary"]["recommended"], 1)
        self.assertEqual(payload["summary"]["high_risk"], 0)
        self.assertEqual(payload["projects"][0]["name"], "智慧园区数字化平台建设项目")
        self.assertEqual(payload["projects"][0]["company_name"], "小苏科技")
        self.assertEqual(payload["projects"][0]["decision_label"], "推荐投标")
        self.assertEqual(payload["projects"][0]["match_score"], 91)
        self.assertEqual(payload["projects"][0]["risk_level"], "中")
        self.assertIsNotNone(payload["projects"][0]["report_id"])

    def test_project_dashboard_api_can_filter_by_decision(self):
        company = CompanyProfile.objects.create(name="小苏科技")
        recommended = TenderProject.objects.create(company=company, name="推荐项目", status=TenderProject.Status.ANALYZED)
        cautious = TenderProject.objects.create(company=company, name="谨慎项目", status=TenderProject.Status.ANALYZED)
        AnalysisReport.objects.create(
            tender_project=recommended,
            decision=AnalysisReport.Decision.RECOMMENDED,
            match_score=88,
        )
        AnalysisReport.objects.create(
            tender_project=cautious,
            decision=AnalysisReport.Decision.CAUTIOUS,
            match_score=72,
        )

        response = self.client.get("/api/projects/?decision=recommended")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["name"] for item in payload["projects"]], ["推荐项目"])

    def test_recent_projects_api_returns_latest_five_analyzed_projects(self):
        company = CompanyProfile.objects.create(name="小苏科技")
        for index in range(6):
            project = TenderProject.objects.create(
                company=company,
                name=f"最近分析项目{index}",
                status=TenderProject.Status.ANALYZED,
            )
            AnalysisReport.objects.create(
                tender_project=project,
                decision=AnalysisReport.Decision.CAUTIOUS,
                match_score=70 + index,
            )

        response = self.client.get("/api/projects/recent/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(len(payload["projects"]), 5)
        self.assertEqual(payload["projects"][0]["name"], "最近分析项目5")
        self.assertEqual(payload["projects"][0]["decision_label"], "谨慎投标")
        self.assertEqual(payload["projects"][0]["match_score"], 75)
        self.assertIsNotNone(payload["projects"][0]["report_id"])

    def test_recent_projects_api_declares_utf8_charset(self):
        response = self.client.get("/api/projects/recent/")

        self.assertIn("charset=utf-8", response["Content-Type"].lower())

    def test_recent_projects_api_returns_html_preview_for_browser_navigation(self):
        company = CompanyProfile.objects.create(name="小苏科技")
        project = TenderProject.objects.create(
            company=company,
            name="智慧园区数字化平台建设项目",
            status=TenderProject.Status.ANALYZED,
        )
        AnalysisReport.objects.create(
            tender_project=project,
            decision=AnalysisReport.Decision.CAUTIOUS,
            match_score=76,
        )

        response = self.client.get(
            "/api/projects/recent/",
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])
        self.assertContains(response, '<meta charset="utf-8">')
        self.assertContains(response, "智慧园区数字化平台建设项目")
        self.assertContains(response, "小苏科技")

    def test_recent_projects_api_still_returns_json_for_fetch_requests(self):
        response = self.client.get("/api/projects/recent/", HTTP_ACCEPT="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response["Content-Type"])
        self.assertEqual(response.json()["ok"], True)

    def test_project_status_api_updates_project_status(self):
        company = CompanyProfile.objects.create(name="小苏科技")
        project = TenderProject.objects.create(
            company=company,
            name="智慧园区数字化平台建设项目",
            status=TenderProject.Status.ANALYZED,
        )

        response = self.client.post(
            f"/api/projects/{project.id}/status/",
            data=json.dumps({"status": TenderProject.Status.RECOMMENDED}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["project"]["status"], TenderProject.Status.RECOMMENDED)
        self.assertEqual(payload["project"]["status_label"], "推荐报名")
        project.refresh_from_db()
        self.assertEqual(project.status, TenderProject.Status.RECOMMENDED)

    def test_project_status_api_creates_status_change_note(self):
        project = TenderProject.objects.create(
            name="智慧园区数字化平台建设项目",
            status=TenderProject.Status.ANALYZED,
        )

        response = self.client.post(
            f"/api/projects/{project.id}/status/",
            data=json.dumps({"status": TenderProject.Status.RECOMMENDED}, ensure_ascii=False),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        detail = self.client.get(f"/api/projects/{project.id}/").json()
        self.assertEqual(detail["notes"][0]["note_type"], "status")
        self.assertIn("已分析", detail["notes"][0]["content"])
        self.assertIn("推荐报名", detail["notes"][0]["content"])

    def test_project_note_api_creates_note_and_project_detail_returns_notes(self):
        project = TenderProject.objects.create(name="智慧园区数字化平台建设项目")

        response = self.client.post(
            f"/api/projects/{project.id}/notes/",
            data=json.dumps(
                {
                    "note_type": "follow_up",
                    "content": "已联系原厂确认授权函。",
                    "operator_name": "投标经理",
                },
                ensure_ascii=False,
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["note"]["content"], "已联系原厂确认授权函。")

        detail = self.client.get(f"/api/projects/{project.id}/").json()
        self.assertEqual(detail["notes"][0]["content"], "已联系原厂确认授权函。")
        self.assertEqual(detail["notes"][0]["operator_name"], "投标经理")

    def test_project_note_api_rejects_empty_content(self):
        project = TenderProject.objects.create(name="智慧园区数字化平台建设项目")

        response = self.client.post(
            f"/api/projects/{project.id}/notes/",
            data=json.dumps({"content": ""}, ensure_ascii=False),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["ok"], False)

    def test_project_status_api_rejects_invalid_status(self):
        project = TenderProject.objects.create(name="智慧园区数字化平台建设项目")

        response = self.client.post(
            f"/api/projects/{project.id}/status/",
            data=json.dumps({"status": "invalid"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["ok"], False)

    def test_project_detail_api_returns_project_workspace_payload(self):
        company = CompanyProfile.objects.create(name="小苏科技")
        project = TenderProject.objects.create(
            company=company,
            name="智慧园区数字化平台建设项目",
            procurement_method="公开招标",
            project_type="软件信息化",
            region="江苏",
            budget_amount=4800000,
            status=TenderProject.Status.RECOMMENDED,
            source_text="招标文件正文",
        )
        report = AnalysisReport.objects.create(
            tender_project=project,
            decision=AnalysisReport.Decision.CAUTIOUS,
            match_score=76,
            summary="项目方向匹配，但需要补充材料。",
            risks=[{"type": "材料风险", "level": "高", "description": "缺少原厂授权函"}],
            missing_materials=["原厂授权函"],
            next_actions=["确认原厂授权", "复核付款条款"],
            raw_report={
                "qualification_match": {"status": "partial", "score": 76, "matched": ["ISO9001"], "missing": ["原厂授权函"]},
                "experience_match": {"score": 80, "summary": "存在类似项目经验", "matched_cases": ["智慧园区平台建设项目"]},
                "material_checklist": [{"category": "商务材料", "name": "投标保证金缴纳凭证", "status": "required"}],
                "agent_trace": [{"agent": "投标决策Agent", "status": "completed"}],
                "review_summary": {"review_level": "需复核", "average_dimension_score": 76},
                "scoring_breakdown": [{"dimension": "资质匹配", "score": 76, "weight": "35%", "comment": "需补材料"}],
                "key_findings": ["缺少原厂授权函"],
            },
        )

        response = self.client.get(f"/api/projects/{project.id}/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["project"]["id"], project.id)
        self.assertEqual(payload["project"]["status_label"], "推荐报名")
        self.assertEqual(payload["report"]["id"], report.id)
        self.assertEqual(payload["report"]["decision_label"], "谨慎投标")
        self.assertEqual(payload["workspace"]["risk_count"], 1)
        self.assertEqual(payload["workspace"]["material_count"], 1)
        self.assertEqual(payload["workspace"]["next_actions"][0], "确认原厂授权")
        self.assertEqual(payload["workspace"]["agent_trace"][0]["agent"], "投标决策Agent")
        self.assertEqual(payload["workspace"]["review_summary"]["review_level"], "需复核")
        self.assertEqual(payload["workspace"]["scoring_breakdown"][0]["dimension"], "资质匹配")
        self.assertEqual(payload["workspace"]["key_findings"][0], "缺少原厂授权函")

    def test_project_detail_api_returns_404_for_missing_project(self):
        response = self.client.get("/api/projects/99999/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["ok"], False)

    def test_project_detail_api_enriches_legacy_workspace_sections(self):
        company = CompanyProfile.objects.create(name="历史项目企业")
        project = TenderProject.objects.create(company=company, name="历史项目")
        AnalysisReport.objects.create(
            tender_project=project,
            decision=AnalysisReport.Decision.RECOMMENDED,
            match_score=88,
            risks=[{"type": "材料风险", "level": "中", "description": "材料待复核"}],
            missing_materials=[],
            raw_report={},
        )

        response = self.client.get(f"/api/projects/{project.id}/")

        self.assertEqual(response.status_code, 200)
        workspace = response.json()["workspace"]
        self.assertEqual(workspace["review_summary"]["review_level"], "可推进")
        self.assertEqual(workspace["review_summary"]["material_status"], "材料齐备")
        self.assertEqual(len(workspace["scoring_breakdown"]), 4)
        self.assertIn("推荐投标", workspace["key_findings"][0])


class TenderReferenceApiTests(TestCase):
    def test_reference_tenders_api_returns_seedable_reference_rows(self):
        TenderReference.objects.create(
            title="电子政务云平台扩容项目参考标书",
            project_type="云平台建设",
            industry="政务信息化",
            region="上海",
            issuing_organization="某市大数据中心",
            summary="适合参考评分办法和运维服务要求。",
            reference_points="重点关注等级保护、运维SLA、验收阶段。",
            source_text="第一章 招标公告\n第二章 投标须知",
            tags="云平台、政务、运维",
            is_featured=True,
        )

        response = self.client.get("/api/reference-tenders/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        references_by_title = {item["title"]: item for item in payload["references"]}
        self.assertIn("电子政务云平台扩容项目参考标书", references_by_title)
        self.assertEqual(references_by_title["电子政务云平台扩容项目参考标书"]["tags"], ["云平台", "政务", "运维"])

    def test_reference_tenders_api_can_filter_by_project_type(self):
        TenderReference.objects.create(title="A", project_type="软件信息化")
        TenderReference.objects.create(title="B", project_type="弱电集成")

        response = self.client.get("/api/reference-tenders/?project_type=软件信息化")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("A", [item["title"] for item in payload["references"]])
        self.assertNotIn("B", [item["title"] for item in payload["references"]])
