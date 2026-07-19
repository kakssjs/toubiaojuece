from django.core.management import call_command
from django.test import TestCase, override_settings

from tenders.models import AnalysisReport, CompanyProfile, Contract, TenderProject, TenderReference
from tenders import views


class SeedWorkspaceDemoCommandTests(TestCase):
    def test_seed_workspace_demo_creates_complete_business_data(self):
        call_command("seed_workspace_demo", verbosity=0)

        self.assertGreaterEqual(CompanyProfile.objects.count(), 3)
        self.assertGreaterEqual(TenderProject.objects.count(), 10)
        self.assertEqual(AnalysisReport.objects.count(), TenderProject.objects.count())
        self.assertGreaterEqual(Contract.objects.count(), 15)
        self.assertGreaterEqual(TenderReference.objects.count(), 10)

        response = self.client.get("/api/projects/")
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertGreaterEqual(payload["summary"]["total"], 10)
        self.assertTrue(payload["projects"][0]["company_name"])

    def test_seed_workspace_demo_is_idempotent(self):
        call_command("seed_workspace_demo", verbosity=0)
        counts = (
            CompanyProfile.objects.count(),
            TenderProject.objects.count(),
            AnalysisReport.objects.count(),
            TenderReference.objects.count(),
        )

        call_command("seed_workspace_demo", verbosity=0)

        self.assertEqual(
            counts,
            (
                CompanyProfile.objects.count(),
                TenderProject.objects.count(),
                AnalysisReport.objects.count(),
                TenderReference.objects.count(),
            ),
        )

    @override_settings(AUTO_SEED_DEMO_DATA=True)
    def test_project_api_auto_seeds_when_enabled(self):
        views._DEMO_DATA_ENSURED = False

        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertGreaterEqual(payload["summary"]["total"], 10)
        self.assertGreaterEqual(CompanyProfile.objects.count(), 3)
        self.assertGreaterEqual(TenderReference.objects.count(), 10)
