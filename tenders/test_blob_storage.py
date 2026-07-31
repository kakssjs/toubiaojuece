import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from tenders.models import AnalysisReport, CompanyProfile, TenderDocument, TenderProject
from tenders.services.blob_storage import is_blob_path, is_client_blob_path, persist_pdf, read_private_blob


class BlobStorageServiceTests(SimpleTestCase):
    def test_client_blob_paths_are_recognized(self):
        pathname = 'client-tender-documents/123/sample-random.pdf'
        self.assertTrue(is_client_blob_path(pathname))
        self.assertTrue(is_blob_path(pathname))

    def test_persist_pdf_uploads_to_private_blob(self):
        client = MagicMock()
        client.put.return_value = SimpleNamespace(
            pathname='tender-documents/7/sample-random.pdf',
        )

        with TemporaryDirectory() as directory:
            pdf_path = Path(directory) / 'sample.pdf'
            pdf_path.write_bytes(b'%PDF-1.4 test')
            with (
                patch.dict('os.environ', {'BLOB_READ_WRITE_TOKEN': 'blob-test-token'}, clear=False),
                patch('tenders.services.blob_storage.BlobClient', return_value=client),
            ):
                result = persist_pdf(str(pdf_path), 'sample.pdf', 7)

        self.assertEqual(result['backend'], 'vercel_blob')
        self.assertTrue(result['persistent'])
        self.assertEqual(result['pathname'], 'tender-documents/7/sample-random.pdf')
        self.assertEqual(client.put.call_args.kwargs['access'], 'private')
        self.assertEqual(client.put.call_args.kwargs['content_type'], 'application/pdf')
        client.close.assert_called_once()

    def test_read_private_blob_returns_content(self):
        client = MagicMock()
        client.get.return_value = SimpleNamespace(content=b'%PDF stored')
        with (
            patch.dict('os.environ', {'BLOB_READ_WRITE_TOKEN': 'blob-test-token'}, clear=False),
            patch('tenders.services.blob_storage.BlobClient', return_value=client),
        ):
            content = read_private_blob('tender-documents/7/sample.pdf')

        self.assertEqual(content, b'%PDF stored')
        self.assertEqual(client.get.call_args.kwargs['access'], 'private')


class DocumentDownloadTests(TestCase):
    def setUp(self):
        company = CompanyProfile.objects.create(name='测试企业')
        project = TenderProject.objects.create(company=company, name='测试项目')
        self.document = TenderDocument.objects.create(
            tender_project=project,
            file='tender-documents/7/private.pdf',
            original_name='private.pdf',
            file_size=12,
        )

    def test_download_requires_login(self):
        response = self.client.get(f'/api/documents/{self.document.id}/download/')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['ok'], False)

    def test_staff_can_download_private_blob(self):
        user = get_user_model().objects.create_user(
            username='staff',
            password='test-password',
            is_staff=True,
        )
        self.client.force_login(user)

        with patch('tenders.views.read_private_blob', return_value=b'%PDF private'):
            response = self.client.get(f'/api/documents/{self.document.id}/download/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF private')
        self.assertIn('attachment', response.headers['Content-Disposition'])


class ClientBlobAnalysisTests(TestCase):
    def setUp(self):
        self.company = CompanyProfile.objects.create(name='大文件测试企业')
        self.user = get_user_model().objects.create_user(
            username='blob-user',
            password='test-password',
        )
        self.client.force_login(self.user)

    def test_rejects_blob_outside_client_upload_prefix(self):
        response = self.client.post(
            '/api/agent/analyze-blob/',
            data=json.dumps({
                'company_id': self.company.id,
                'pathname': 'other/private.pdf',
                'original_name': 'private.pdf',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['ok'], False)

    def test_analyzes_a_private_client_uploaded_pdf(self):
        report = {
            'project_name': '大文件云端分析项目',
            'project_type': '信息化',
            'procurement_method': '公开招标',
            'budget_amount': 5000000,
            'decision': '推荐投标',
            'decision_reason': '企业能力匹配。',
            'match_score': 88,
            'risks': [],
            'next_actions': ['准备投标材料'],
            'qualification_match': {'missing': []},
        }
        extraction = {
            'text': '这是一份用于测试的大型招标文件正文。',
            'method': 'local_text',
            'character_count': 18,
            'used_vision': False,
            'warning': '',
        }

        with (
            patch('tenders.views.read_private_blob', return_value=b'%PDF-1.7 test data'),
            patch('tenders.views.extract_pdf_content', return_value=extraction),
            patch('tenders.views.TenderAnalysisAgent.analyze', return_value=report),
        ):
            response = self.client.post(
                '/api/agent/analyze-blob/',
                data=json.dumps({
                    'company_id': self.company.id,
                    'pathname': 'client-tender-documents/123/sample-random.pdf',
                    'original_name': '大型招标文件.pdf',
                }),
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['storage']['backend'], 'vercel_blob')
        document = TenderDocument.objects.get(id=payload['document_id'])
        self.assertEqual(document.file.name, 'client-tender-documents/123/sample-random.pdf')
        self.assertEqual(document.parse_status, TenderDocument.ParseStatus.PARSED)
        self.assertTrue(AnalysisReport.objects.filter(id=payload['report_id']).exists())
