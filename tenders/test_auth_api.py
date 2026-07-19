import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from tenders.models import CompanyProfile, UserSecurityProfile


class AuthenticationApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username='upload-user',
            password='strong-test-password',
        )

    def test_api_root_reports_backend_status(self):
        response = self.client.get('/api/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertContains(response, '策标后端服务')
        self.assertContains(response, '服务运行正常')
        self.assertContains(response, '/admin/')

    def test_json_responses_render_chinese_without_unicode_escape_sequences(self):
        response = self.client.post(
            '/api/auth/login/',
            data='{}',
            content_type='application/json',
        )

        self.assertIn('账号或密码错误'.encode('utf-8'), response.content)
        self.assertNotIn(b'\\u8d26', response.content)

    def test_status_issues_csrf_token_without_exposing_session_data(self):
        response = self.client.get('/api/auth/status/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['authenticated'])
        self.assertTrue(response.json()['csrf_token'])

    def test_login_and_logout_update_session(self):
        csrf_client = Client(enforce_csrf_checks=True)
        status = csrf_client.get('/api/auth/status/').json()
        login_response = csrf_client.post(
            '/api/auth/login/',
            data=json.dumps({
                'username': 'upload-user',
                'password': 'strong-test-password',
            }),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=status['csrf_token'],
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.json()['authenticated'])
        self.assertTrue(csrf_client.get('/api/auth/status/').json()['authenticated'])

        logout_response = csrf_client.post(
            '/api/auth/logout/',
            HTTP_X_CSRFTOKEN=login_response.json()['csrf_token'],
        )
        self.assertEqual(logout_response.status_code, 200)
        self.assertFalse(csrf_client.get('/api/auth/status/').json()['authenticated'])

    def test_invalid_credentials_are_rejected(self):
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({'username': 'upload-user', 'password': 'wrong'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()['ok'])

    def test_registration_creates_company_account_and_logs_user_in(self):
        csrf_client = Client(enforce_csrf_checks=True)
        token = csrf_client.get('/api/auth/status/').json()['csrf_token']
        response = csrf_client.post(
            '/api/auth/register/',
            data=json.dumps({
                'username': 'new-bid-user',
                'display_name': '新用户',
                'email': 'new-bid-user@example.com',
                'company_name': '新用户测试企业',
                'password': 'Strong-password-2026!',
                'confirm_password': 'Strong-password-2026!',
                'accepted_terms': True,
            }),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username='new-bid-user')
        self.assertEqual(user.first_name, '新用户')
        self.assertTrue(user.company_profiles.filter(name='新用户测试企业').exists())
        self.assertFalse(user.security_profile.must_change_password)
        self.assertTrue(csrf_client.get('/api/auth/status/').json()['authenticated'])

    def test_registration_rejects_duplicate_email_and_missing_terms(self):
        self.user.email = 'used@example.com'
        self.user.save(update_fields=['email'])
        payload = {
            'username': 'another-user',
            'display_name': 'Another User',
            'email': 'used@example.com',
            'company_name': 'Another Company',
            'password': 'Strong-password-2026!',
            'confirm_password': 'Strong-password-2026!',
            'accepted_terms': False,
        }
        missing_terms = self.client.post('/api/auth/register/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(missing_terms.status_code, 400)

        payload['accepted_terms'] = True
        duplicate_email = self.client.post('/api/auth/register/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(duplicate_email.status_code, 409)

    def test_repeated_invalid_logins_are_rate_limited(self):
        for _ in range(5):
            response = self.client.post(
                '/api/auth/login/',
                data=json.dumps({'username': 'upload-user', 'password': 'wrong'}),
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 401)

        limited = self.client.post(
            '/api/auth/login/',
            data=json.dumps({'username': 'upload-user', 'password': 'wrong'}),
            content_type='application/json',
        )
        self.assertEqual(limited.status_code, 429)

    def test_private_write_api_rejects_missing_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        response = csrf_client.post(
            '/api/agent/analyze/',
            data=json.dumps({'tender_text': '测试招标文本'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_password_change_requires_authentication(self):
        response = self.client.post(
            '/api/auth/change-password/',
            data=json.dumps({
                'current_password': 'strong-test-password',
                'new_password': 'Updated-strong-password-2026',
                'confirm_password': 'Updated-strong-password-2026',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_required_password_change_blocks_business_apis_until_completed(self):
        UserSecurityProfile.objects.create(user=self.user, must_change_password=True)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        status = csrf_client.get('/api/auth/status/').json()

        self.assertTrue(status['must_change_password'])
        self.assertEqual(csrf_client.get('/api/projects/').status_code, 403)

        wrong_password = csrf_client.post(
            '/api/auth/change-password/',
            data=json.dumps({
                'current_password': 'wrong-password',
                'new_password': 'Updated-strong-password-2026',
                'confirm_password': 'Updated-strong-password-2026',
            }),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=status['csrf_token'],
        )
        self.assertEqual(wrong_password.status_code, 400)

        changed = csrf_client.post(
            '/api/auth/change-password/',
            data=json.dumps({
                'current_password': 'strong-test-password',
                'new_password': 'Updated-strong-password-2026',
                'confirm_password': 'Updated-strong-password-2026',
            }),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=status['csrf_token'],
        )
        self.assertEqual(changed.status_code, 200)
        self.assertFalse(changed.json()['must_change_password'])
        self.assertTrue(csrf_client.get('/api/auth/status/').json()['authenticated'])
        self.assertNotEqual(csrf_client.get('/api/projects/').status_code, 403)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Updated-strong-password-2026'))


class UploadAuthorizationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username='rate-user',
            password='test-password',
        )
        self.company = CompanyProfile.objects.create(name='授权测试企业')

    def test_requires_authenticated_session(self):
        response = self.client.get(
            '/api/auth/upload-authorize/',
            {'company_id': self.company.id},
        )
        self.assertEqual(response.status_code, 401)

    def test_limits_upload_authorizations_per_user(self):
        self.client.force_login(self.user)
        for _ in range(10):
            response = self.client.get(
                '/api/auth/upload-authorize/',
                {'company_id': self.company.id},
            )
            self.assertEqual(response.status_code, 200)

        limited_response = self.client.get(
            '/api/auth/upload-authorize/',
            {'company_id': self.company.id},
        )
        self.assertEqual(limited_response.status_code, 429)
