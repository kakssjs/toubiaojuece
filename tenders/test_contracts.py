import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from tenders.models import Contract


class ContractApiTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username='contract-admin',
            password='Contract-admin-2026',
            is_staff=True,
        )
        self.client.force_login(self.staff)

    def test_contracts_api_returns_seeded_rows(self):
        response = self.client.get('/api/contracts/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['ok'], True)
        self.assertGreaterEqual(len(payload['contracts']), 2)

    def test_contracts_api_can_create_contract(self):
        response = self.client.post(
            '/api/contracts/',
            data=json.dumps(
                {
                    'basic_info': '测试合同',
                    'tender_content': '测试标书内容',
                    'reference_points': '测试参考要点',
                    'scoring_rules': '测试评分规则',
                    'risk_tags': '测试风险',
                    'material_checklist': '测试材料',
                    'source_maintenance_info': '测试来源',
                },
                ensure_ascii=False,
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload['ok'], True)
        self.assertEqual(payload['contract']['basic_info'], '测试合同')

    def test_contracts_api_can_update_and_delete_contract(self):
        contract = Contract.objects.create(basic_info='初始合同')

        update = self.client.put(
            f'/api/contracts/{contract.id}/',
            data=json.dumps(
                {
                    'basic_info': '更新后的合同',
                    'tender_content': '更新内容',
                    'reference_points': '',
                    'scoring_rules': '',
                    'risk_tags': '',
                    'material_checklist': '',
                    'source_maintenance_info': '',
                },
                ensure_ascii=False,
            ),
            content_type='application/json',
        )

        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()['contract']['basic_info'], '更新后的合同')

        delete = self.client.delete(f'/api/contracts/{contract.id}/')
        self.assertEqual(delete.status_code, 200)
        self.assertFalse(Contract.objects.filter(id=contract.id).exists())

    def test_contract_write_requires_staff_account(self):
        regular_user = get_user_model().objects.create_user(
            username='contract-viewer',
            password='Contract-viewer-2026',
        )
        self.client.force_login(regular_user)

        response = self.client.post(
            '/api/contracts/',
            data=json.dumps({'basic_info': '无权创建的合同'}, ensure_ascii=False),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Contract.objects.filter(basic_info='无权创建的合同').exists())

    def test_contract_write_requires_authentication(self):
        self.client.logout()

        response = self.client.post(
            '/api/contracts/',
            data=json.dumps({'basic_info': '匿名创建的合同'}, ensure_ascii=False),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Contract.objects.filter(basic_info='匿名创建的合同').exists())


class ContractPageTests(TestCase):
    def test_contracts_page_renders_html(self):
        response = self.client.get('/contracts/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
        self.assertContains(response, '<meta charset="utf-8">')
        self.assertContains(response, '合同库')
