from django.test import TestCase


class SecurityHeadersTests(TestCase):
    def test_api_responses_include_browser_security_headers(self):
        response = self.client.get('/api/auth/status/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')
