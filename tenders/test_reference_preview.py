from django.test import TestCase


class TenderReferencePreviewTests(TestCase):
    def test_reference_tenders_api_returns_html_preview_for_browser_navigation(self):
        response = self.client.get(
            "/api/reference-tenders/",
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])
        self.assertContains(response, '<meta charset="utf-8">')
        self.assertContains(response, "参考标书库")
