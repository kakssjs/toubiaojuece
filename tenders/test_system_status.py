from unittest.mock import patch

from django.test import TestCase

from tenders.models import CompanyProfile, Contract, TenderProject


class SystemStatusApiTests(TestCase):
    def test_status_does_not_expose_openai_key(self):
        CompanyProfile.objects.create(name='测试企业')
        TenderProject.objects.create(name='测试项目')
        Contract.objects.create(basic_info='测试标书')

        with patch.dict(
            'os.environ',
            {
                'OPENAI_API_KEY': 'sk-test-secret-that-must-never-be-returned',
                'OPENAI_ANALYSIS_ENABLED': '1',
                'OPENAI_ANALYSIS_MODEL': 'gpt-5.6',
                'AGNES_API_KEY': '',
            },
            clear=False,
        ):
            response = self.client.get('/api/system/status/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['analysis']['mode'], 'user_selected')
        self.assertEqual(payload['analysis']['default_mode'], 'rule_based')
        self.assertEqual(payload['analysis']['available_modes'], ['rule_based', 'openai'])
        self.assertTrue(payload['analysis']['openai_configured'])
        self.assertTrue(payload['analysis']['fallback_enabled'])
        self.assertEqual(payload['analysis']['model'], 'gpt-5.6')
        self.assertEqual(payload['data']['companies'], 1)
        self.assertEqual(payload['data']['projects'], 1)
        self.assertEqual(payload['data']['contracts'], Contract.objects.count())
        self.assertNotIn('sk-test-secret', response.content.decode('utf-8'))

    def test_status_reports_rule_mode_when_openai_is_disabled(self):
        with patch.dict(
            'os.environ',
            {'OPENAI_API_KEY': '', 'OPENAI_ANALYSIS_ENABLED': '0', 'AGNES_API_KEY': ''},
            clear=False,
        ):
            response = self.client.get('/api/system/status/')

        payload = response.json()
        self.assertEqual(payload['analysis']['mode'], 'user_selected')
        self.assertEqual(payload['analysis']['default_mode'], 'rule_based')
        self.assertEqual(payload['analysis']['available_modes'], ['rule_based'])
        self.assertFalse(payload['analysis']['openai_configured'])
        self.assertFalse(payload['analysis']['openai_enabled'])

    def test_status_reports_agnes_as_user_selectable_when_configured(self):
        with patch.dict(
            'os.environ',
            {
                'OPENAI_API_KEY': '',
                'AGNES_API_KEY': 'agnes-test-key',
                'AGNES_ANALYSIS_ENABLED': '1',
                'AGNES_ANALYSIS_MODEL': 'agnes-2.0-flash',
            },
            clear=False,
        ):
            response = self.client.get('/api/system/status/')

        analysis = response.json()['analysis']
        self.assertEqual(analysis['available_modes'], ['rule_based', 'agnes'])
        self.assertTrue(analysis['agnes_configured'])
        self.assertTrue(analysis['agnes_enabled'])
        self.assertEqual(analysis['agnes_model'], 'agnes-2.0-flash')
