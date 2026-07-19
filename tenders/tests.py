from django.test import TestCase


class FrontendRoutesTests(TestCase):
    def test_top_navigation_root_pages_return_vue_app(self):
        for path in ['/', '/product/', '/solutions/', '/process/', '/scenes/', '/agent/']:
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<div id="app"></div>', html=True)

# Create your tests here.
