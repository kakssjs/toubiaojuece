from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from pypdf import PdfWriter

from tenders.models import AnalysisReport, CompanyProfile, ProjectExperience, Qualification, TenderDocument, TenderProject


def make_sample_pdf(text):
    buffer = BytesIO()
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    page.compress_content_streams()
    writer.add_metadata({"/Title": text})
    writer.write(buffer)
    buffer.seek(0)
    return buffer.getvalue()


@override_settings(MEDIA_ROOT='D:/2/tmp-test-media')
class TenderPdfAnalysisApiTests(TestCase):
    def test_analyze_pdf_api_extracts_and_saves_document_project_and_report(self):
        company = CompanyProfile.objects.create(
            name="小苏科技",
            main_business="软件开发、系统集成、智慧园区",
            service_regions="全国",
            max_project_amount=10000000,
        )
        Qualification.objects.create(company=company, name="ISO9001质量管理体系认证")
        ProjectExperience.objects.create(company=company, name="智慧园区平台建设项目", industry="软件信息化")

        pdf_file = SimpleUploadedFile(
            "sample-tender.pdf",
            make_sample_pdf("sample tender"),
            content_type="application/pdf",
        )

        response = self.client.post(
            "/api/agent/analyze-pdf/",
            data={
                "company_id": company.id,
                "pdf_file": pdf_file,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["ok"], True)
        self.assertIsNotNone(payload["project_id"])
        self.assertIsNotNone(payload["document_id"])
        self.assertIsNotNone(payload["report_id"])

        project = TenderProject.objects.get(id=payload["project_id"])
        document = TenderDocument.objects.get(id=payload["document_id"])
        report = AnalysisReport.objects.get(id=payload["report_id"])

        self.assertEqual(project.company, company)
        self.assertEqual(document.tender_project, project)
        self.assertEqual(document.parse_status, TenderDocument.ParseStatus.PARSED)
        self.assertTrue(document.extracted_text)
        self.assertEqual(report.tender_project, project)

    def test_analyze_pdf_api_requires_pdf_file(self):
        company = CompanyProfile.objects.create(name="小苏科技")

        response = self.client.post(
            "/api/agent/analyze-pdf/",
            data={"company_id": company.id},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["ok"], False)
