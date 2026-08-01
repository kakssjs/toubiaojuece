from django.core.management import call_command
from django.test import TestCase

from tenders.models import Contract, TenderReference
from tenders.views import _find_similar_reference_tenders


class ReferenceLibraryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_reference_templates", verbosity=0)

    def test_catalogue_contains_requested_number_of_viewable_templates(self):
        self.assertEqual(TenderReference.objects.count(), 57)
        self.assertEqual(Contract.objects.count(), 58)

        response = self.client.get("/api/reference-tenders/", HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="reference-', count=57)

        contract_response = self.client.get("/api/contracts/")
        self.assertEqual(contract_response.status_code, 200)
        self.assertEqual(len(contract_response.json()["contracts"]), 58)

    def test_local_retrieval_matches_relevant_industry_templates(self):
        matches = _find_similar_reference_tenders(
            "本项目建设医院电子病历、PACS影像云和医疗数据互联互通平台。"
        )

        self.assertTrue(matches)
        self.assertTrue(any(item["industry"] == "智慧医疗" for item in matches))
        self.assertTrue(all(item["reference_points"] for item in matches))

    def test_seed_command_is_idempotent(self):
        call_command("seed_reference_templates", verbosity=0)
        self.assertEqual(TenderReference.objects.count(), 57)
        self.assertEqual(Contract.objects.count(), 58)
