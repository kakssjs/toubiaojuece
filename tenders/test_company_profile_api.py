import json

from django.test import TestCase

from tenders.models import CompanyProfile, ProjectExperience, Qualification


class CompanyProfileApiTests(TestCase):
    def test_company_profile_api_returns_first_company_with_capabilities(self):
        company = CompanyProfile.objects.create(
            name="小苏科技",
            main_business="软件开发、系统集成",
            service_regions="江苏、上海",
            max_project_amount=5000000,
            forbidden_conditions="垫资周期超过12个月",
        )
        Qualification.objects.create(company=company, name="ISO9001", certificate_no="ISO-001")
        ProjectExperience.objects.create(company=company, name="智慧园区平台建设项目", industry="软件信息化", amount=3200000)

        response = self.client.get("/api/company-profile/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["company"]["name"], "小苏科技")
        self.assertEqual(payload["company"]["qualifications"][0]["name"], "ISO9001")
        self.assertEqual(payload["company"]["experiences"][0]["name"], "智慧园区平台建设项目")

    def test_company_profile_api_prefers_xiaosu_as_default_company(self):
        CompanyProfile.objects.create(name="云衡数据科技有限公司")
        CompanyProfile.objects.create(name="小苏科技有限公司")

        response = self.client.get("/api/company-profile/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["company"]["name"], "小苏科技有限公司")

    def test_company_profile_api_saves_company_capabilities(self):
        payload = {
            "name": "小苏科技",
            "main_business": "AI应用开发、政企信息化系统集成",
            "service_regions": "全国、江苏、上海",
            "max_project_amount": "8000000",
            "forbidden_conditions": "不接受纯垫资项目",
            "qualifications": [
                {
                    "name": "ISO9001质量管理体系认证",
                    "certificate_no": "ISO-2026-001",
                    "issuer": "认证机构",
                    "valid_until": "2028-12-31",
                }
            ],
            "experiences": [
                {
                    "name": "智慧园区数字化平台",
                    "industry": "软件信息化",
                    "amount": "3600000",
                    "client_name": "某产业园",
                    "completed_at": "2025-08-20",
                    "description": "建设园区管理、数据看板和移动端服务。",
                }
            ],
        }

        response = self.client.post(
            "/api/company-profile/",
            data=json.dumps(payload, ensure_ascii=False),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["ok"], True)
        company = CompanyProfile.objects.get(name="小苏科技")
        self.assertEqual(company.main_business, "AI应用开发、政企信息化系统集成")
        self.assertEqual(company.qualifications.count(), 1)
        self.assertEqual(company.experiences.count(), 1)
        self.assertEqual(company.qualifications.first().valid_until.isoformat(), "2028-12-31")
        self.assertEqual(company.experiences.first().amount, 3600000)

    def test_company_profile_api_rejects_missing_company_name(self):
        response = self.client.post(
            "/api/company-profile/",
            data=json.dumps({"name": ""}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["ok"], False)
