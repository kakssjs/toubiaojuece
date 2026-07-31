import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from tenders.models import Contract


class ContractCreateApiTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username='contract-create-admin',
            password='Contract-create-2026',
            is_staff=True,
        )
        self.client.force_login(self.staff)

    def test_vue_frontend_can_create_contract_with_json(self):
        response = self.client.post(
            '/api/contracts/',
            data=json.dumps(
                {
                    'basic_info': '项目名称：智慧园区数字化平台建设项目\n预算：480万元',
                    'tender_content': '建设统一门户、数据中台、移动端应用和运维管理模块。',
                    'reference_points': '重点参考资格要求、服务周期、验收节点和付款比例。',
                    'scoring_rules': '技术方案40分，项目团队20分，类似业绩20分，报价20分。',
                    'risk_tags': '原厂授权风险；交付周期风险；付款周期风险',
                    'material_checklist': '营业执照；资质证书；项目经理证书；类似业绩合同；授权函',
                    'source_maintenance_info': '来源：人工录入；维护人：投标经理；更新时间：2026-06-28',
                },
                ensure_ascii=False,
            ),
            content_type='application/json',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload['ok'], True)
        self.assertEqual(payload['contract']['basic_info'], '项目名称：智慧园区数字化平台建设项目\n预算：480万元')
        self.assertTrue(Contract.objects.filter(basic_info__contains='智慧园区').exists())

    def test_contract_create_api_rejects_empty_payload(self):
        existing_count = Contract.objects.count()

        response = self.client.post(
            '/api/contracts/',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['ok'], False)
        self.assertEqual(Contract.objects.count(), existing_count)
