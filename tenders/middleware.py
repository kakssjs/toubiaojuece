from django.http import JsonResponse

from .models import UserSecurityProfile


class PasswordChangeRequiredMiddleware:
    allowed_api_paths = {
        '/api/auth/status/',
        '/api/auth/login/',
        '/api/auth/logout/',
        '/api/auth/change-password/',
        '/api/system/status/',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        password_change_required = (
            request.user.is_authenticated
            and UserSecurityProfile.objects.filter(
                user=request.user,
                must_change_password=True,
            ).exists()
        )

        if (
            request.path.startswith('/api/')
            and request.path not in self.allowed_api_paths
            and password_change_required
        ):
            return JsonResponse(
                {'ok': False, 'error': '请先修改初始密码。', 'password_change_required': True},
                status=403,
                content_type='application/json; charset=utf-8',
            )
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """Add browser protections that are safe for the SPA and Django admin."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
        response.setdefault('Cross-Origin-Resource-Policy', 'same-origin')
        return response
