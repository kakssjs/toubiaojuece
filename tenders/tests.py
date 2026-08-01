import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import CompanyProfile


class FrontendRoutesTests(TestCase):
    def test_top_navigation_root_pages_return_vue_app(self):
        for path in ['/', '/product/', '/solutions/', '/process/', '/scenes/', '/agent/']:
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<div id="app"></div>', html=True)


@override_settings(DATA_ACCESS_CONTROL_ENABLED=True)
class SecurityRegressionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user('tenant-a', password='A-strong-test-password-2026')
        self.other_user = user_model.objects.create_user('tenant-b', password='B-strong-test-password-2026')
        self.company = CompanyProfile.objects.create(owner=self.user, name='租户甲')
        self.other_company = CompanyProfile.objects.create(owner=self.other_user, name='租户乙')

    def test_security_headers_are_added(self):
        response = self.client.get('/api/auth/status/')
        self.assertEqual(response.headers['Permissions-Policy'], 'camera=(), microphone=(), geolocation=()')
        self.assertEqual(response.headers['X-Permitted-Cross-Domain-Policies'], 'none')

    def test_anonymous_system_status_hides_internal_details(self):
        payload = self.client.get('/api/system/status/').json()
        self.assertNotIn('data', payload)
        self.assertNotIn('ownership', payload)
        self.assertNotIn('model', payload['analysis'])

    def test_blob_path_must_match_selected_company(self):
        self.client.force_login(self.user)
        response = self.client.post(
            '/api/agent/analyze-blob/',
            data=json.dumps({
                'company_id': self.company.id,
                'analysis_mode': 'rule_based',
                'pathname': f'client-tender-documents/company-{self.other_company.id}/secret.pdf',
                'original_name': 'secret.pdf',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], '云端 PDF 路径无效。')

    def test_uploaded_pdf_is_validated_by_magic_bytes(self):
        self.client.force_login(self.user)
        fake_pdf = SimpleUploadedFile('fake.pdf', b'not-a-pdf', content_type='application/pdf')
        response = self.client.post('/api/agent/analyze-pdf/', {
            'company_id': self.company.id,
            'analysis_mode': 'rule_based',
            'pdf_file': fake_pdf,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], '文件内容不是有效的 PDF。')
