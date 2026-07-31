from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from tenders.models import AnalysisReport, CompanyProfile, TenderProject


@override_settings(DATA_ACCESS_CONTROL_ENABLED=True, AUTO_SEED_DEMO_DATA=False)
class CompanyDataAccessTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.user_a = users.objects.create_user(username='tenant-a', password='password-a')
        self.user_b = users.objects.create_user(username='tenant-b', password='password-b')
        self.staff = users.objects.create_user(username='tenant-admin', password='password-admin', is_staff=True)

        self.company_a = CompanyProfile.objects.create(owner=self.user_a, name='甲方科技')
        self.company_b = CompanyProfile.objects.create(owner=self.user_b, name='乙方科技')
        self.project_a = TenderProject.objects.create(company=self.company_a, name='甲方项目')
        self.project_b = TenderProject.objects.create(company=self.company_b, name='乙方项目')
        self.report_a = AnalysisReport.objects.create(
            tender_project=self.project_a,
            decision=AnalysisReport.Decision.RECOMMENDED,
            match_score=88,
        )
        self.report_b = AnalysisReport.objects.create(
            tender_project=self.project_b,
            decision=AnalysisReport.Decision.CAUTIOUS,
            match_score=66,
        )

    def test_anonymous_workspace_requests_are_rejected(self):
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, 401)

    def test_regular_user_only_sees_owned_company_and_projects(self):
        self.client.force_login(self.user_a)

        companies = self.client.get('/api/companies/').json()['companies']
        projects = self.client.get('/api/projects/').json()['projects']

        self.assertEqual([item['id'] for item in companies], [self.company_a.id])
        self.assertEqual([item['id'] for item in projects], [self.project_a.id])

    def test_regular_user_cannot_read_another_users_project_or_report(self):
        self.client.force_login(self.user_a)

        project_response = self.client.get(f'/api/projects/{self.project_b.id}/')
        report_response = self.client.get(f'/api/reports/{self.report_b.id}/')

        self.assertEqual(project_response.status_code, 404)
        self.assertEqual(report_response.status_code, 404)

    def test_regular_user_can_read_owned_report(self):
        self.client.force_login(self.user_a)
        response = self.client.get(f'/api/reports/{self.report_a.id}/')
        self.assertEqual(response.status_code, 200)

    def test_staff_user_can_see_all_companies_and_projects(self):
        self.client.force_login(self.staff)

        companies = self.client.get('/api/companies/').json()['companies']
        projects = self.client.get('/api/projects/').json()['projects']

        self.assertEqual({item['id'] for item in companies}, {self.company_a.id, self.company_b.id})
        self.assertEqual({item['id'] for item in projects}, {self.project_a.id, self.project_b.id})
