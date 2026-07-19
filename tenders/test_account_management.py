import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from tenders.models import CompanyProfile, UserSecurityProfile


class StaffAccountManagementTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.staff = users.objects.create_user(
            username='account-admin',
            password='Admin-password-2026',
            is_staff=True,
        )
        self.regular = users.objects.create_user(
            username='regular-user',
            password='Regular-password-2026',
        )
        self.superuser = users.objects.create_superuser(
            username='root-user',
            password='Root-password-2026',
        )
        self.staff_peer = users.objects.create_user(
            username='staff-peer',
            password='Peer-password-2026',
            is_staff=True,
        )
        self.company = CompanyProfile.objects.create(name='账号分配测试企业')

    def post_action(self, payload):
        return self.client.post(
            '/api/admin/accounts/',
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_requires_login_and_staff_permission(self):
        self.assertEqual(self.client.get('/api/admin/accounts/').status_code, 401)
        self.client.force_login(self.regular)
        self.assertEqual(self.client.get('/api/admin/accounts/').status_code, 403)

    def test_staff_can_create_regular_user(self):
        self.client.force_login(self.staff)
        response = self.post_action({
            'action': 'create_user',
            'username': 'new-company-user',
            'display_name': '新企业用户',
            'email': 'new-user@example.com',
            'password': 'Strong-password-2026',
        })

        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(username='new-company-user')
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('Strong-password-2026'))
        self.assertTrue(user.security_profile.must_change_password)

    def test_staff_can_assign_company_owner(self):
        self.client.force_login(self.staff)
        response = self.post_action({
            'action': 'assign_company',
            'company_id': self.company.id,
            'user_id': self.regular.id,
        })

        self.assertEqual(response.status_code, 200)
        self.company.refresh_from_db()
        self.assertEqual(self.company.owner, self.regular)

    def test_staff_can_reset_regular_password_but_not_superuser_password(self):
        self.client.force_login(self.staff)
        regular_response = self.post_action({
            'action': 'reset_password',
            'user_id': self.regular.id,
            'password': 'Updated-password-2026',
        })
        protected_response = self.post_action({
            'action': 'reset_password',
            'user_id': self.superuser.id,
            'password': 'Changed-root-password-2026',
        })
        peer_response = self.post_action({
            'action': 'reset_password',
            'user_id': self.staff_peer.id,
            'password': 'Changed-peer-password-2026',
        })

        self.assertEqual(regular_response.status_code, 200)
        self.assertEqual(protected_response.status_code, 404)
        self.assertEqual(peer_response.status_code, 404)
        self.regular.refresh_from_db()
        self.superuser.refresh_from_db()
        self.staff_peer.refresh_from_db()
        self.assertTrue(self.regular.check_password('Updated-password-2026'))
        self.assertTrue(UserSecurityProfile.objects.get(user=self.regular).must_change_password)
        self.assertTrue(self.superuser.check_password('Root-password-2026'))
        self.assertTrue(self.staff_peer.check_password('Peer-password-2026'))
