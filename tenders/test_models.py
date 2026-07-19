from django.contrib import admin
from django.test import TestCase

from tenders import models


class TenderDomainModelTests(TestCase):
    def test_company_profile_can_hold_qualifications_and_experiences(self):
        company = models.CompanyProfile.objects.create(
            name="小苏科技",
            main_business="软件开发、系统集成、智慧园区",
            service_regions="全国",
            max_project_amount=10000000,
            forbidden_conditions="付款周期超过12个月",
        )

        qualification = models.Qualification.objects.create(
            company=company,
            name="ISO9001质量管理体系认证",
            certificate_no="ISO-2026-001",
            issuer="认证机构",
        )
        experience = models.ProjectExperience.objects.create(
            company=company,
            name="智慧园区平台建设项目",
            industry="软件信息化",
            amount=4800000,
            client_name="某园区管委会",
        )

        self.assertEqual(str(company), "小苏科技")
        self.assertEqual(company.qualifications.first(), qualification)
        self.assertEqual(company.experiences.first(), experience)

    def test_tender_project_can_store_analysis_report(self):
        company = models.CompanyProfile.objects.create(name="小苏科技")
        project = models.TenderProject.objects.create(
            company=company,
            name="智慧园区数字化平台建设项目",
            procurement_method="公开招标",
            project_type="软件信息化",
            budget_amount=4800000,
            status=models.TenderProject.Status.ANALYZED,
        )
        report = models.AnalysisReport.objects.create(
            tender_project=project,
            decision=models.AnalysisReport.Decision.CAUTIOUS,
            match_score=76,
            summary="项目方向匹配，但需要补充原厂授权。",
            risks=[{"type": "材料风险", "level": "高"}],
            missing_materials=["原厂授权函"],
            next_actions=["确认原厂授权"],
        )

        self.assertEqual(str(project), "智慧园区数字化平台建设项目")
        self.assertEqual(project.analysis_report, report)
        self.assertEqual(report.risks[0]["type"], "材料风险")

    def test_tender_reference_can_store_reference_text(self):
        reference = models.TenderReference.objects.create(
            title="智慧园区数字化平台采购参考标书",
            project_type="软件信息化",
            industry="园区数字化",
            region="江苏",
            issuing_organization="某高新区管委会",
            summary="用于参考功能清单、评分项和交付边界。",
            reference_points="重点关注资质要求、驻场要求、付款节点。",
            source_text="第一章 招标公告\n第二章 投标人须知\n第三章 技术规范书",
            tags="数字平台、园区、软件实施",
        )

        self.assertEqual(str(reference), "智慧园区数字化平台采购参考标书")
        self.assertIn("技术规范书", reference.source_text)


class TenderAdminRegistrationTests(TestCase):
    def test_domain_models_are_registered_in_admin(self):
        registered_models = admin.site._registry

        self.assertIn(models.CompanyProfile, registered_models)
        self.assertIn(models.Qualification, registered_models)
        self.assertIn(models.ProjectExperience, registered_models)
        self.assertIn(models.TenderProject, registered_models)
        self.assertIn(models.AnalysisReport, registered_models)
        self.assertIn(models.TenderReference, registered_models)


class CompanyApiTests(TestCase):
    def test_companies_api_returns_company_options(self):
        company = models.CompanyProfile.objects.create(
            name="小苏科技",
            main_business="软件开发、系统集成",
            service_regions="全国",
        )

        response = self.client.get('/api/companies/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["companies"][0]["id"], company.id)
        self.assertEqual(payload["companies"][0]["name"], "小苏科技")
