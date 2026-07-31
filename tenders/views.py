import json
import os
import tempfile
import hashlib
import re
from html import escape
from io import BytesIO
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, transaction
from django.db.models import Q
from django.middleware.csrf import get_token
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.utils import timezone
from django.views.static import serve
from django.views.decorators.http import require_http_methods, require_POST

from .agents import AgnesTenderAnalysisAgent, RuleBasedTenderAnalysisAgent, TenderAnalysisAgent
from .models import (
    AnalysisReport,
    CompanyProfile,
    Contract,
    ProjectExperience,
    ProjectNote,
    ProjectTask,
    Qualification,
    TenderDocument,
    TenderProject,
    TenderReference,
    UserSecurityProfile,
)
from .services.pdf_parser import extract_pdf_content
from .services.blob_storage import (
    is_blob_path,
    is_client_blob_path,
    persist_pdf,
    read_private_blob,
)
from .services.report_qa import answer_report_question
from .services.report_exporter import build_report_docx, build_report_pdf
from .services.project_tasks import sync_report_tasks


_PROJECT_TASK_SCHEMA_READY = False


JSON_UTF8_CONTENT_TYPE = 'application/json; charset=utf-8'
_DEMO_DATA_ENSURED = False
ANALYSIS_MODES = {'rule_based', 'openai', 'agnes'}


def utf8_json(data, **kwargs):
    kwargs.setdefault('content_type', JSON_UTF8_CONTENT_TYPE)
    kwargs.setdefault('json_dumps_params', {'ensure_ascii': False})
    return JsonResponse(data, **kwargs)


@require_http_methods(['GET'])
def api_root(request):
    return HttpResponse(
        '''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>策标后端服务</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; color: #172033; background: #f4f7fb; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }
    main { width: min(720px, calc(100% - 32px)); margin: 10vh auto; padding: 42px; border: 1px solid #dce4ef; border-radius: 16px; background: #fff; box-shadow: 0 24px 70px rgba(25, 50, 84, .12); }
    .status { display: inline-flex; align-items: center; min-height: 30px; padding: 0 12px; color: #087556; border: 1px solid #b9dfd2; border-radius: 999px; background: #eaf7f2; font-size: 13px; font-weight: 700; }
    h1 { margin: 22px 0 10px; font-size: clamp(30px, 5vw, 44px); }
    p { margin: 0; color: #657083; line-height: 1.8; }
    nav { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 32px; }
    a { min-height: 48px; display: inline-flex; align-items: center; justify-content: center; padding: 0 18px; color: #fff; border-radius: 7px; background: #0b57d0; font-weight: 700; text-decoration: none; }
    a.secondary { color: #0b57d0; border: 1px solid #a9c5f0; background: #f5f9ff; }
    small { display: block; margin-top: 30px; color: #929aaa; }
    @media (max-width: 560px) { main { margin: 0; width: 100%; min-height: 100vh; padding: 40px 22px; border: 0; border-radius: 0; } nav { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main>
    <span class="status">服务运行正常</span>
    <h1>策标后端服务</h1>
    <p>后端接口与生产数据库连接正常。管理人员可以进入后台维护账号、企业档案、项目和分析报告。</p>
    <nav>
      <a href="/admin/">进入管理后台</a>
      <a class="secondary" href="/api/system/status/">查看接口状态</a>
    </nav>
    <small>Production API · cebiao.space</small>
  </main>
</body>
</html>''',
        content_type='text/html; charset=utf-8',
    )


def _resolve_analysis_mode(value):
    mode = str(value or 'rule_based').strip().lower()
    return mode if mode in ANALYSIS_MODES else None


def _analyze_tender(tender_text, company_profile, analysis_mode):
    agents = {
        'rule_based': RuleBasedTenderAnalysisAgent,
        'openai': TenderAnalysisAgent,
        'agnes': AgnesTenderAnalysisAgent,
    }
    agent = agents[analysis_mode]()
    report = agent.analyze(tender_text=tender_text, company_profile=company_profile)
    report.setdefault('analysis_engine', 'rule_based')
    return report


def _password_change_required(user):
    if not user.is_authenticated:
        return False
    return UserSecurityProfile.objects.filter(user=user, must_change_password=True).exists()




def auth_status(request):
    user = request.user
    return utf8_json({
        'ok': True,
        'authenticated': user.is_authenticated,
        'username': user.get_username() if user.is_authenticated else '',
        'is_staff': bool(user.is_staff) if user.is_authenticated else False,
        'must_change_password': _password_change_required(user),
        'csrf_token': get_token(request),
    })


@require_POST
def auth_login_api(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    username = str(payload.get('username') or '').strip()
    password = str(payload.get('password') or '')
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    client_ip = forwarded_for.split(',')[0].strip() or request.META.get('REMOTE_ADDR', 'unknown')
    login_identity = f'{username.casefold()}:{client_ip}'
    rate_key = f'login-failures:{hashlib.sha256(login_identity.encode("utf-8")).hexdigest()}'
    failure_count = int(cache.get(rate_key, 0) or 0)
    if failure_count >= 5:
        return utf8_json({'ok': False, 'error': '登录尝试过多，请 10 分钟后重试。'}, status=429)

    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        cache.set(rate_key, failure_count + 1, timeout=600)
        return utf8_json({'ok': False, 'error': '账号或密码错误。'}, status=401)

    cache.delete(rate_key)
    auth_login(request, user)
    return utf8_json({
        'ok': True,
        'authenticated': True,
        'username': user.get_username(),
        'is_staff': bool(user.is_staff),
        'must_change_password': _password_change_required(user),
        'csrf_token': get_token(request),
    })


@require_POST
def auth_register_api(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    username = str(payload.get('username') or '').strip()
    display_name = str(payload.get('display_name') or '').strip()
    email = str(payload.get('email') or '').strip()
    company_name = str(payload.get('company_name') or '').strip()
    password = str(payload.get('password') or '')
    confirm_password = str(payload.get('confirm_password') or '')
    accepted_terms = payload.get('accepted_terms') is True

    forwarded_for = request.headers.get('X-Forwarded-For', '')
    client_ip = forwarded_for.split(',')[0].strip() or request.META.get('REMOTE_ADDR', 'unknown')
    rate_key = f'registration-attempts:{hashlib.sha256(client_ip.encode("utf-8")).hexdigest()}'
    attempt_count = int(cache.get(rate_key, 0) or 0)
    if attempt_count >= 5:
        return utf8_json({'ok': False, 'error': '注册操作过于频繁，请 1 小时后重试。'}, status=429)
    cache.set(rate_key, attempt_count + 1, timeout=3600)

    if not re.fullmatch(r'[\w.@+-]{3,30}', username, flags=re.UNICODE):
        return utf8_json({'ok': False, 'error': '账号需为 3-30 位，可使用中文、字母、数字及 _ . @ + -。'}, status=400)
    if not display_name or len(display_name) > 30:
        return utf8_json({'ok': False, 'error': '请填写不超过 30 个字符的联系人姓名。'}, status=400)
    if not email:
        return utf8_json({'ok': False, 'error': '请填写工作邮箱。'}, status=400)
    if not company_name or len(company_name) > 120:
        return utf8_json({'ok': False, 'error': '请填写不超过 120 个字符的企业名称。'}, status=400)
    if password != confirm_password:
        return utf8_json({'ok': False, 'error': '两次输入的密码不一致。'}, status=400)
    if not accepted_terms:
        return utf8_json({'ok': False, 'error': '请阅读并同意服务协议和隐私政策。'}, status=400)

    user_model = get_user_model()
    if user_model.objects.filter(username__iexact=username).exists():
        return utf8_json({'ok': False, 'error': '该账号已被注册。'}, status=409)
    if user_model.objects.filter(email__iexact=email).exists():
        return utf8_json({'ok': False, 'error': '该邮箱已被注册。'}, status=409)

    candidate = user_model(username=username, email=email, first_name=display_name)
    try:
        candidate.full_clean(exclude=['password'])
        validate_password(password, user=candidate)
    except ValidationError as exc:
        return utf8_json({'ok': False, 'error': '；'.join(exc.messages)}, status=400)

    with transaction.atomic():
        candidate.set_password(password)
        candidate.save()
        UserSecurityProfile.objects.create(
            user=candidate,
            must_change_password=False,
            password_changed_at=timezone.now(),
        )
        CompanyProfile.objects.create(owner=candidate, name=company_name)

    cache.delete(rate_key)
    auth_login(request, candidate)
    return utf8_json({
        'ok': True,
        'authenticated': True,
        'username': candidate.get_username(),
        'is_staff': False,
        'must_change_password': False,
        'csrf_token': get_token(request),
    }, status=201)


@require_POST
def auth_logout_api(request):
    auth_logout(request)
    return utf8_json({'ok': True, 'authenticated': False, 'csrf_token': get_token(request)})


@require_POST
def auth_change_password_api(request):
    if not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录。'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    current_password = str(payload.get('current_password') or '')
    new_password = str(payload.get('new_password') or '')
    confirm_password = str(payload.get('confirm_password') or '')
    if not request.user.check_password(current_password):
        return utf8_json({'ok': False, 'error': '当前密码不正确。'}, status=400)
    if new_password != confirm_password:
        return utf8_json({'ok': False, 'error': '两次输入的新密码不一致。'}, status=400)
    if current_password == new_password:
        return utf8_json({'ok': False, 'error': '新密码不能与当前密码相同。'}, status=400)

    try:
        validate_password(new_password, user=request.user)
    except ValidationError as exc:
        return utf8_json({'ok': False, 'error': '；'.join(exc.messages)}, status=400)

    request.user.set_password(new_password)
    request.user.save(update_fields=['password'])
    update_session_auth_hash(request, request.user)
    security_profile, _ = UserSecurityProfile.objects.get_or_create(user=request.user)
    security_profile.must_change_password = False
    security_profile.password_changed_at = timezone.now()
    security_profile.save(update_fields=['must_change_password', 'password_changed_at', 'updated_at'])
    return utf8_json({
        'ok': True,
        'authenticated': True,
        'username': request.user.get_username(),
        'is_staff': bool(request.user.is_staff),
        'must_change_password': False,
        'csrf_token': get_token(request),
    })


def authorize_blob_upload(request):
    if not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录。'}, status=401)

    company_id = request.GET.get('company_id')
    if not company_id or not _companies_for_request(request).filter(id=company_id).exists():
        return utf8_json({'ok': False, 'error': '企业档案不存在。'}, status=404)

    cache_key = f'blob-upload-authorizations:{request.user.pk}'
    if cache.add(cache_key, 1, timeout=600):
        authorization_count = 1
    else:
        try:
            authorization_count = cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=600)
            authorization_count = 1
    if authorization_count > 10:
        return utf8_json({'ok': False, 'error': '上传过于频繁，请 10 分钟后重试。'}, status=429)

    return utf8_json({'ok': True, 'username': request.user.get_username()})


@require_http_methods(['GET', 'POST'])
def staff_account_management(request):
    if not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录。'}, status=401)
    if not request.user.is_staff:
        return utf8_json({'ok': False, 'error': '仅管理员可以管理账号。'}, status=403)

    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

        action = str(payload.get('action') or '').strip()
        user_model = get_user_model()
        if action == 'create_user':
            username = str(payload.get('username') or '').strip()
            password = str(payload.get('password') or '')
            email = str(payload.get('email') or '').strip()
            display_name = str(payload.get('display_name') or '').strip()
            if not username:
                return utf8_json({'ok': False, 'error': '账号不能为空。'}, status=400)
            if user_model.objects.filter(username__iexact=username).exists():
                return utf8_json({'ok': False, 'error': '该账号已存在。'}, status=409)

            candidate = user_model(username=username, email=email, first_name=display_name)
            try:
                candidate.full_clean(exclude=['password'])
                validate_password(password, user=candidate)
            except ValidationError as exc:
                return utf8_json({'ok': False, 'error': '；'.join(exc.messages)}, status=400)
            candidate.set_password(password)
            candidate.save()
            UserSecurityProfile.objects.update_or_create(
                user=candidate,
                defaults={'must_change_password': True},
            )
        elif action == 'reset_password':
            user = user_model.objects.filter(
                id=payload.get('user_id'),
                is_staff=False,
                is_superuser=False,
            ).first()
            if user is None:
                return utf8_json({'ok': False, 'error': '普通用户不存在。'}, status=404)
            password = str(payload.get('password') or '')
            try:
                validate_password(password, user=user)
            except ValidationError as exc:
                return utf8_json({'ok': False, 'error': '；'.join(exc.messages)}, status=400)
            user.set_password(password)
            user.save(update_fields=['password'])
            UserSecurityProfile.objects.update_or_create(
                user=user,
                defaults={'must_change_password': True, 'password_changed_at': None},
            )
        elif action == 'assign_company':
            company = CompanyProfile.objects.filter(id=payload.get('company_id')).first()
            if company is None:
                return utf8_json({'ok': False, 'error': '企业档案不存在。'}, status=404)
            user_id = payload.get('user_id')
            owner = None
            if user_id:
                owner = user_model.objects.filter(id=user_id, is_active=True).first()
                if owner is None:
                    return utf8_json({'ok': False, 'error': '目标账号不存在或已停用。'}, status=404)
            company.owner = owner
            company.save(update_fields=['owner', 'updated_at'])
        else:
            return utf8_json({'ok': False, 'error': '不支持的管理操作。'}, status=400)

    user_model = get_user_model()
    users = [
        {
            'id': user.id,
            'username': user.get_username(),
            'display_name': user.first_name,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'must_change_password': _password_change_required(user),
        }
        for user in user_model.objects.order_by('username')
    ]
    companies = [
        {
            'id': company.id,
            'name': company.name,
            'owner_id': company.owner_id,
            'owner_username': company.owner.get_username() if company.owner else '',
        }
        for company in CompanyProfile.objects.select_related('owner').order_by('name')
    ]
    return utf8_json({'ok': True, 'users': users, 'companies': companies})


def _access_control_enabled():
    return bool(getattr(settings, 'DATA_ACCESS_CONTROL_ENABLED', False))


def _authentication_error(request):
    if _access_control_enabled() and not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录。'}, status=401)
    return None


def _companies_for_request(request):
    queryset = CompanyProfile.objects.all()
    if not _access_control_enabled() or (request.user.is_authenticated and request.user.is_staff):
        return queryset
    if request.user.is_authenticated:
        return queryset.filter(owner=request.user)
    return queryset.none()


def _projects_for_request(request):
    queryset = TenderProject.objects.all()
    if not _access_control_enabled() or (request.user.is_authenticated and request.user.is_staff):
        return queryset
    if request.user.is_authenticated:
        return queryset.filter(company__owner=request.user)
    return queryset.none()


def _reports_for_request(request):
    queryset = AnalysisReport.objects.all()
    if not _access_control_enabled() or (request.user.is_authenticated and request.user.is_staff):
        return queryset
    if request.user.is_authenticated:
        return queryset.filter(tender_project__company__owner=request.user)
    return queryset.none()


def _ensure_demo_data_available():
    global _DEMO_DATA_ENSURED
    if _DEMO_DATA_ENSURED or not getattr(settings, 'AUTO_SEED_DEMO_DATA', False):
        return

    has_enough_data = (
        CompanyProfile.objects.count() >= 3
        and TenderProject.objects.count() >= 10
        and AnalysisReport.objects.count() >= 10
        and Contract.objects.count() >= 15
        and TenderReference.objects.count() >= 10
    )
    if not has_enough_data:
        call_command('seed_workspace_demo', verbosity=0)
    _DEMO_DATA_ENSURED = True


def frontend_app(request, *args, **kwargs):
    index_path = Path(settings.BASE_DIR) / 'static' / 'frontend' / 'index.html'
    if not index_path.exists():
        raise Http404('Vue frontend has not been built yet.')

    return FileResponse(index_path.open('rb'), content_type='text/html')


def frontend_static(request, path):
    return serve(request, path, document_root=Path(settings.BASE_DIR) / 'static' / 'frontend')


def download_tender_document(request, document_id):
    if not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录。'}, status=401)
    try:
        documents = TenderDocument.objects.select_related('tender_project__company')
        if not request.user.is_staff:
            documents = documents.filter(tender_project__company__owner=request.user)
        document = documents.get(id=document_id)
    except TenderDocument.DoesNotExist as exc:
        raise Http404('招标文件不存在。') from exc

    if is_blob_path(document.file.name):
        try:
            content = read_private_blob(document.file.name)
        except FileNotFoundError as exc:
            raise Http404(str(exc)) from exc
        return FileResponse(
            BytesIO(content),
            as_attachment=True,
            filename=document.original_name,
            content_type='application/pdf',
        )

    try:
        return FileResponse(
            document.file.open('rb'),
            as_attachment=True,
            filename=document.original_name,
            content_type='application/pdf',
        )
    except (FileNotFoundError, OSError) as exc:
        raise Http404('原始文件已不在当前服务器中。') from exc


def system_status(request):
    openai_configured = bool(os.getenv('OPENAI_API_KEY', '').strip())
    analysis_enabled = os.getenv('OPENAI_ANALYSIS_ENABLED', '1').strip().lower() not in {
        '0',
        'false',
        'no',
    }
    openai_enabled = openai_configured and analysis_enabled
    agnes_configured = bool(os.getenv('AGNES_API_KEY', '').strip())
    agnes_analysis_enabled = os.getenv('AGNES_ANALYSIS_ENABLED', '1').strip().lower() not in {
        '0',
        'false',
        'no',
    }
    agnes_enabled = agnes_configured and agnes_analysis_enabled
    available_modes = ['rule_based']
    if openai_enabled:
        available_modes.append('openai')
    if agnes_enabled:
        available_modes.append('agnes')
    assigned_company_count = CompanyProfile.objects.filter(owner__isnull=False).count()
    total_company_count = CompanyProfile.objects.count()

    return utf8_json(
        {
            'ok': True,
            'analysis': {
                'mode': 'user_selected',
                'default_mode': 'rule_based',
                'available_modes': available_modes,
                'openai_configured': openai_configured,
                'openai_enabled': openai_enabled,
                'model': os.getenv('OPENAI_ANALYSIS_MODEL', 'gpt-5.6'),
                'agnes_configured': agnes_configured,
                'agnes_enabled': agnes_enabled,
                'agnes_model': os.getenv('AGNES_ANALYSIS_MODEL', 'agnes-2.0-flash'),
                'fallback_enabled': True,
            },
            'ownership': {
                'assigned_companies': assigned_company_count,
                'unassigned_companies': max(total_company_count - assigned_company_count, 0),
            },
            'data': {
                'companies': CompanyProfile.objects.count(),
                'projects': TenderProject.objects.count(),
                'reports': AnalysisReport.objects.count(),
                'contracts': Contract.objects.count(),
                'reference_tenders': TenderReference.objects.count(),
            },
        },
        json_dumps_params={'ensure_ascii': False},
    )


@require_POST
def analyze_tender_agent(request):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    tender_text = str(payload.get('tender_text') or '').strip()
    if not tender_text:
        return utf8_json({'ok': False, 'error': 'tender_text 不能为空。'}, status=400)

    analysis_mode = _resolve_analysis_mode(payload.get('analysis_mode'))
    if analysis_mode is None:
        return utf8_json({'ok': False, 'error': 'analysis_mode 仅支持 rule_based、openai 或 agnes。'}, status=400)

    company = None
    company_id = payload.get('company_id')
    if company_id:
        try:
            company = _companies_for_request(request).prefetch_related('qualifications', 'experiences').get(id=company_id)
        except CompanyProfile.DoesNotExist:
            return utf8_json({'ok': False, 'error': '企业档案不存在。'}, status=404)

    company_profile = _company_profile_for_agent(company) if company else payload.get('company_profile') or {}
    if not isinstance(company_profile, dict):
        return utf8_json({'ok': False, 'error': 'company_profile 必须是对象。'}, status=400)

    report = _analyze_tender(tender_text, company_profile, analysis_mode)

    response_payload = {'ok': True, 'report': report}
    if payload.get('save'):
        project, analysis_report = _save_agent_report(
            tender_text=tender_text,
            company=company,
            report=report,
        )
        response_payload.update(
            {
                'project_id': project.id,
                'report_id': analysis_report.id,
            }
        )

    return utf8_json(response_payload, json_dumps_params={'ensure_ascii': False})


def list_companies(request):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    _ensure_demo_data_available()
    companies = sorted(
        _companies_for_request(request).values('id', 'name', 'main_business', 'service_regions'),
        key=lambda item: (0 if '小苏' in item['name'] else 1, item['name']),
    )
    return utf8_json(
        {
            'ok': True,
            'companies': companies,
        },
        json_dumps_params={'ensure_ascii': False},
    )


def company_profile_detail(request):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    if request.method == 'GET':
        _ensure_demo_data_available()
        company = _default_company_queryset(request).first()
        return utf8_json(
            {
                'ok': True,
                'company': _serialize_company_profile(company) if company else None,
            },
            json_dumps_params={'ensure_ascii': False},
        )

    if request.method != 'POST':
        return utf8_json({'ok': False, 'error': '仅支持 GET 或 POST 请求。'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    name = str(payload.get('name') or '').strip()
    if not name:
        return utf8_json({'ok': False, 'error': '企业名称不能为空。'}, status=400)

    company_id = payload.get('id')
    if company_id:
        company = _companies_for_request(request).filter(id=company_id).first()
        if company is None:
            return utf8_json({'ok': False, 'error': '企业档案不存在。'}, status=404)
    else:
        company = _default_company_queryset(request).first()

    if company is None:
        company = CompanyProfile(owner=request.user if request.user.is_authenticated else None)

    company.name = name
    company.main_business = str(payload.get('main_business') or '').strip()
    company.service_regions = str(payload.get('service_regions') or '').strip()
    company.max_project_amount = payload.get('max_project_amount') or None
    company.forbidden_conditions = str(payload.get('forbidden_conditions') or '').strip()
    company.save()

    _replace_company_qualifications(company, payload.get('qualifications') or [])
    _replace_company_experiences(company, payload.get('experiences') or [])

    company = _companies_for_request(request).prefetch_related('qualifications', 'experiences').get(id=company.id)
    return utf8_json(
        {
            'ok': True,
            'company': _serialize_company_profile(company),
        },
        json_dumps_params={'ensure_ascii': False},
    )


def _default_company_queryset(request):
    queryset = _companies_for_request(request).prefetch_related('qualifications', 'experiences')
    preferred = queryset.filter(name__contains='小苏')
    if preferred.exists():
        return preferred.order_by('name')
    return queryset.order_by('name')


def project_dashboard(request):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    _ensure_project_task_schema()
    _ensure_demo_data_available()
    projects = _projects_for_request(request).select_related('company').prefetch_related('analysis_report', 'tasks').order_by('-created_at')
    decision = request.GET.get('decision')
    if decision:
        projects = projects.filter(analysis_report__decision=decision)

    rows = [_serialize_project_row(project) for project in projects]
    summary_source = _projects_for_request(request).select_related('analysis_report')
    summary = {
        'total': summary_source.count(),
        'recommended': summary_source.filter(analysis_report__decision=AnalysisReport.Decision.RECOMMENDED).count(),
        'cautious': summary_source.filter(analysis_report__decision=AnalysisReport.Decision.CAUTIOUS).count(),
        'not_recommended': summary_source.filter(analysis_report__decision=AnalysisReport.Decision.NOT_RECOMMENDED).count(),
        'high_risk': sum(1 for project in summary_source if _project_risk_level(project) == '高'),
    }

    return utf8_json(
        {
            'ok': True,
            'summary': summary,
            'projects': rows,
        },
        json_dumps_params={'ensure_ascii': False},
    )


def recent_projects(request):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    _ensure_project_task_schema()
    _ensure_demo_data_available()
    projects = (
        _projects_for_request(request).select_related('company', 'analysis_report')
        .filter(analysis_report__isnull=False)
        .order_by('-created_at')[:5]
    )
    rows = [_serialize_project_row(project) for project in projects]

    if _prefers_html(request):
        return HttpResponse(_recent_projects_html(rows), content_type='text/html; charset=utf-8')

    return utf8_json(
        {
            'ok': True,
            'projects': rows,
        },
        json_dumps_params={'ensure_ascii': False},
    )


def list_reference_tenders(request):
    _ensure_demo_data_available()
    references = TenderReference.objects.all()
    project_type = str(request.GET.get('project_type') or '').strip()
    industry = str(request.GET.get('industry') or '').strip()
    region = str(request.GET.get('region') or '').strip()

    if project_type:
        references = references.filter(project_type=project_type)
    if industry:
        references = references.filter(industry=industry)
    if region:
        references = references.filter(region=region)

    rows = [_serialize_reference_tender(item) for item in references]

    if _prefers_html(request):
        return HttpResponse(_reference_tenders_html(rows), content_type='text/html; charset=utf-8')

    return utf8_json(
        {
            'ok': True,
            'references': rows,
        },
        json_dumps_params={'ensure_ascii': False},
    )


def contracts_page(request):
    _ensure_demo_data_available()
    contracts = [_serialize_contract(item) for item in Contract.objects.all()]
    return HttpResponse(_contracts_page_html(contracts), content_type='text/html; charset=utf-8')


@require_http_methods(['GET', 'POST'])
def contracts_collection(request):
    if request.method == 'GET':
        _ensure_demo_data_available()
        contracts = [_serialize_contract(item) for item in Contract.objects.all()]
        if _prefers_html(request):
            return HttpResponse(_contracts_page_html(contracts), content_type='text/html; charset=utf-8')
        return utf8_json(
            {
                'ok': True,
                'contracts': contracts,
            },
            json_dumps_params={'ensure_ascii': False},
        )

    if not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录。'}, status=401)
    if not request.user.is_staff:
        return utf8_json({'ok': False, 'error': '仅管理员可以新增合同模板。'}, status=403)

    payload = _load_json_payload(request)
    if isinstance(payload, JsonResponse):
        return payload

    fields = _contract_fields_from_payload(payload)
    validation_error = _validate_contract_fields(fields)
    if validation_error:
        return validation_error

    contract = Contract.objects.create(**fields)
    return utf8_json(
        {
            'ok': True,
            'contract': _serialize_contract(contract),
        },
        status=201,
        json_dumps_params={'ensure_ascii': False},
    )


@require_http_methods(['GET', 'PUT', 'DELETE'])
def contract_detail_api(request, contract_id):
    try:
        contract = Contract.objects.get(id=contract_id)
    except Contract.DoesNotExist:
        return utf8_json({'ok': False, 'error': '合同记录不存在。'}, status=404)

    if request.method == 'GET':
        return utf8_json(
            {
                'ok': True,
                'contract': _serialize_contract(contract),
            },
            json_dumps_params={'ensure_ascii': False},
        )

    if not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录。'}, status=401)
    if not request.user.is_staff:
        return utf8_json({'ok': False, 'error': '仅管理员可以修改合同模板。'}, status=403)

    if request.method == 'DELETE':
        contract.delete()
        return utf8_json({'ok': True}, json_dumps_params={'ensure_ascii': False})

    payload = _load_json_payload(request)
    if isinstance(payload, JsonResponse):
        return payload

    fields = _contract_fields_from_payload(payload)
    validation_error = _validate_contract_fields(fields)
    if validation_error:
        return validation_error

    for field, value in fields.items():
        setattr(contract, field, value)
    contract.save()
    return utf8_json(
        {
            'ok': True,
            'contract': _serialize_contract(contract),
        },
        json_dumps_params={'ensure_ascii': False},
    )


def _safe_score(value, fallback=0):
    try:
        return max(0, min(100, round(float(value))))
    except (TypeError, ValueError):
        return max(0, min(100, round(float(fallback or 0))))


def _risk_level_key(level):
    value = str(level or '').strip()
    if '高' in value:
        return 'high'
    if '中' in value:
        return 'medium'
    return 'low'


def _build_report_sections(report):
    """Fill presentation-only sections for reports created before richer analysis fields existed."""
    raw_report = report.raw_report or {}
    risks = report.risks or []
    missing_materials = report.missing_materials or []
    material_checklist = raw_report.get('material_checklist') or []
    qualification_match = raw_report.get('qualification_match') or {}
    experience_match = raw_report.get('experience_match') or {}

    risk_counts = {'high': 0, 'medium': 0, 'low': 0}
    for risk in risks:
        risk_counts[_risk_level_key(risk.get('level'))] += 1

    review_summary = dict(raw_report.get('review_summary') or {})
    review_levels = {
        AnalysisReport.Decision.RECOMMENDED: '可推进',
        AnalysisReport.Decision.CAUTIOUS: '需复核',
        AnalysisReport.Decision.NOT_RECOMMENDED: '建议暂停',
        AnalysisReport.Decision.NEEDS_REVIEW: '人工复核',
    }
    missing_count = len(missing_materials)
    material_status = '材料齐备'
    if missing_count > 2:
        material_status = '多项材料待补'
    elif missing_count:
        material_status = '少量材料待补'

    scoring_breakdown = raw_report.get('scoring_breakdown') or []
    if not scoring_breakdown:
        qualification_score = _safe_score(qualification_match.get('score'), report.match_score)
        experience_score = _safe_score(experience_match.get('score'), report.match_score)
        risk_score = max(
            0,
            100 - (risk_counts['high'] * 20) - (risk_counts['medium'] * 8) - (risk_counts['low'] * 2),
        )
        scoring_breakdown = [
            {
                'dimension': '资质匹配',
                'score': qualification_score,
                'weight': '35%',
                'comment': '根据历史报告中保存的资质匹配结果补全。',
            },
            {
                'dimension': '业绩支撑',
                'score': experience_score,
                'weight': '25%',
                'comment': '根据历史报告中保存的类似业绩结果补全。',
            },
            {
                'dimension': '风险可控',
                'score': risk_score,
                'weight': '25%',
                'comment': '根据当前风险等级与数量估算，用于历史报告展示。',
            },
            {
                'dimension': '综合决策',
                'score': _safe_score(report.match_score),
                'weight': '15%',
                'comment': '沿用历史报告的综合匹配评分。',
            },
        ]

    valid_scores = [
        _safe_score(item.get('score'))
        for item in scoring_breakdown
        if item.get('score') is not None
    ]
    review_summary.setdefault('review_level', review_levels.get(report.decision, '待复核'))
    review_summary.setdefault('material_status', material_status)
    review_summary.setdefault(
        'average_dimension_score',
        round(sum(valid_scores) / len(valid_scores)) if valid_scores else _safe_score(report.match_score),
    )
    review_summary['high_risk_count'] = risk_counts['high']
    review_summary.setdefault('material_required_count', len(material_checklist))
    review_summary['material_missing_count'] = missing_count

    key_findings = raw_report.get('key_findings') or []
    if not key_findings:
        key_findings = [f'系统建议：{report.get_decision_display()}（综合匹配度 {report.match_score}）']
        if missing_materials:
            key_findings.append(f"待补材料：{'、'.join(str(item) for item in missing_materials[:3])}")
        if risk_counts['high']:
            key_findings.append(f"优先处理 {risk_counts['high']} 项高风险事项")
        elif risks:
            key_findings.append(f"持续跟踪 {len(risks)} 项风险事项")

    return {
        'review_summary': review_summary,
        'scoring_breakdown': scoring_breakdown,
        'key_findings': key_findings,
    }


def project_detail(request, project_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    _ensure_project_task_schema()
    try:
        project = (
            _projects_for_request(request).select_related('company')
            .prefetch_related('analysis_report', 'notes', 'tasks')
            .get(id=project_id)
        )
    except TenderProject.DoesNotExist:
        return utf8_json({'ok': False, 'error': '项目不存在。'}, status=404)

    report = getattr(project, 'analysis_report', None)
    project_tasks = list(project.tasks.all())
    if report:
        project_tasks = sync_report_tasks(report)
    raw_report = report.raw_report if report else {}
    report_sections = _build_report_sections(report) if report else {}
    assignees = {'投标经理'}
    if request.user.is_authenticated:
        assignees.add(request.user.username)
    if project.company and project.company.owner:
        assignees.add(project.company.owner.username)

    return utf8_json(
        {
            'ok': True,
            'project': _serialize_project_row(project),
            'report': _serialize_project_report(report),
            'notes': [_serialize_project_note(note) for note in project.notes.all()],
            'tasks': [_serialize_project_task(task) for task in project_tasks],
            'available_assignees': sorted(assignees),
            'workspace': {
                'risk_count': len(report.risks or []) if report else 0,
                'material_count': len(raw_report.get('material_checklist', [])),
                'next_actions': report.next_actions if report else [],
                'risks': report.risks if report else [],
                'missing_materials': report.missing_materials if report else [],
                'material_checklist': raw_report.get('material_checklist', []),
                'agent_trace': raw_report.get('agent_trace', []),
                'qualification_match': raw_report.get('qualification_match', {}),
                'experience_match': raw_report.get('experience_match', {}),
                'scoring_breakdown': report_sections.get('scoring_breakdown', []),
                'review_summary': report_sections.get('review_summary', {}),
                'key_findings': report_sections.get('key_findings', []),
            },
        },
        json_dumps_params={'ensure_ascii': False},
    )


@require_POST
def update_project_status(request, project_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    status = str(payload.get('status') or '').strip()
    valid_statuses = {value for value, _ in TenderProject.Status.choices}
    if status not in valid_statuses:
        return utf8_json({'ok': False, 'error': '项目状态不合法。'}, status=400)

    try:
        project = _projects_for_request(request).select_related('company').prefetch_related('analysis_report').get(id=project_id)
    except TenderProject.DoesNotExist:
        return utf8_json({'ok': False, 'error': '项目不存在。'}, status=404)

    old_status_label = project.get_status_display()
    project.status = status
    project.save(update_fields=['status', 'updated_at'])
    new_status_label = project.get_status_display()
    if old_status_label != new_status_label:
        ProjectNote.objects.create(
            tender_project=project,
            note_type=ProjectNote.NoteType.STATUS,
            content=f'项目状态从「{old_status_label}」变更为「{new_status_label}」。',
            operator_name=str(payload.get('operator_name') or '系统').strip() or '系统',
        )
    project = _projects_for_request(request).select_related('company').prefetch_related('analysis_report').get(id=project.id)

    return utf8_json(
        {
            'ok': True,
            'project': _serialize_project_row(project),
        },
        json_dumps_params={'ensure_ascii': False},
    )


@require_POST
def create_project_note(request, project_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    try:
        project = _projects_for_request(request).get(id=project_id)
    except TenderProject.DoesNotExist:
        return utf8_json({'ok': False, 'error': '项目不存在。'}, status=404)

    content = str(payload.get('content') or '').strip()
    if not content:
        return utf8_json({'ok': False, 'error': '记录内容不能为空。'}, status=400)

    note_type = str(payload.get('note_type') or ProjectNote.NoteType.FOLLOW_UP).strip()
    valid_note_types = {value for value, _ in ProjectNote.NoteType.choices}
    if note_type not in valid_note_types:
        return utf8_json({'ok': False, 'error': '记录类型不合法。'}, status=400)

    note = ProjectNote.objects.create(
        tender_project=project,
        note_type=note_type,
        content=content,
        operator_name=str(payload.get('operator_name') or '投标经理').strip() or '投标经理',
    )

    return utf8_json(
        {
            'ok': True,
            'note': _serialize_project_note(note),
        },
        json_dumps_params={'ensure_ascii': False},
    )


@require_POST
def update_project_task_status(request, task_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    _ensure_project_task_schema()
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    task = ProjectTask.objects.select_related('tender_project').filter(
        id=task_id,
        tender_project__in=_projects_for_request(request),
    ).first()
    if task is None:
        return utf8_json({'ok': False, 'error': '任务不存在。'}, status=404)

    update_fields = []
    if 'status' in payload:
        status = str(payload.get('status') or '').strip()
        valid_statuses = {value for value, _ in ProjectTask.Status.choices}
        if status not in valid_statuses:
            return utf8_json({'ok': False, 'error': '任务状态不合法。'}, status=400)
        task.status = status
        task.completed_at = timezone.now() if status == ProjectTask.Status.COMPLETED else None
        update_fields.extend(['status', 'completed_at'])

    if 'assignee_name' in payload:
        task.assignee_name = str(payload.get('assignee_name') or '').strip()[:80]
        update_fields.append('assignee_name')

    if 'remind_at' in payload:
        reminder_value = payload.get('remind_at')
        remind_at = _parse_report_deadline(reminder_value) if reminder_value else None
        if reminder_value and remind_at is None:
            return utf8_json({'ok': False, 'error': '提醒时间格式不合法。'}, status=400)
        task.remind_at = remind_at
        task.reminder_read_at = None
        update_fields.extend(['remind_at', 'reminder_read_at'])

    if not update_fields:
        return utf8_json({'ok': False, 'error': '没有需要更新的任务字段。'}, status=400)
    task.save(update_fields=[*dict.fromkeys(update_fields), 'updated_at'])
    return utf8_json({'ok': True, 'task': _serialize_project_task(task)}, json_dumps_params={'ensure_ascii': False})


def list_task_notifications(request):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    _ensure_project_task_schema()
    tasks = ProjectTask.objects.select_related('tender_project').filter(
        tender_project__in=_projects_for_request(request),
        status=ProjectTask.Status.PENDING,
        remind_at__isnull=False,
        remind_at__lte=timezone.now(),
    )
    if not request.user.is_staff:
        tasks = tasks.filter(Q(assignee_name='') | Q(assignee_name=request.user.username))
    tasks = tasks.order_by('remind_at', 'due_at')[:30]
    rows = [_serialize_project_task(task) for task in tasks]
    return utf8_json(
        {
            'ok': True,
            'unread_count': sum(1 for task in tasks if task.reminder_read_at is None),
            'notifications': rows,
            'channels': {'in_app': True, 'email': False, 'wecom': False},
        },
        json_dumps_params={'ensure_ascii': False},
    )


@require_POST
def mark_task_notification_read(request, task_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    _ensure_project_task_schema()
    task = ProjectTask.objects.filter(id=task_id, tender_project__in=_projects_for_request(request)).first()
    if task is None:
        return utf8_json({'ok': False, 'error': '提醒不存在。'}, status=404)
    task.reminder_read_at = timezone.now()
    task.save(update_fields=['reminder_read_at', 'updated_at'])
    return utf8_json({'ok': True, 'task': _serialize_project_task(task)}, json_dumps_params={'ensure_ascii': False})


def report_detail(request, report_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    try:
        report = _reports_for_request(request).select_related('tender_project', 'tender_project__company').get(id=report_id)
    except AnalysisReport.DoesNotExist:
        return utf8_json({'ok': False, 'error': '分析报告不存在。'}, status=404)

    project = report.tender_project
    company = project.company
    raw_report = report.raw_report or {}
    report_sections = _build_report_sections(report)

    return utf8_json(
        {
            'ok': True,
            'report': {
                'id': report.id,
                'decision': report.decision,
                'decision_label': report.get_decision_display(),
                'match_score': report.match_score,
                'summary': report.summary,
                'risks': report.risks,
                'missing_materials': report.missing_materials,
                'next_actions': report.next_actions,
                'raw_report': raw_report,
                'created_at': report.created_at.isoformat(),
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'procurement_method': project.procurement_method,
                    'project_type': project.project_type,
                    'region': project.region,
                    'budget_amount': float(project.budget_amount) if project.budget_amount is not None else None,
                    'deadline': project.deadline.isoformat() if project.deadline else None,
                    'status': project.status,
                    'source_text': project.source_text,
                    'company': {
                        'id': company.id,
                        'name': company.name,
                    } if company else None,
                },
                'agent_trace': raw_report.get('agent_trace', []),
                'qualification_match': raw_report.get('qualification_match', {}),
                'experience_match': raw_report.get('experience_match', {}),
                'material_checklist': raw_report.get('material_checklist', []),
                'scoring_breakdown': report_sections['scoring_breakdown'],
                'review_summary': report_sections['review_summary'],
                'key_findings': report_sections['key_findings'],
            },
        },
        json_dumps_params={'ensure_ascii': False},
    )


@require_POST
def ask_report_question(request, report_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    question = str(payload.get('question') or '').strip()
    if not question:
        return utf8_json({'ok': False, 'error': '问题不能为空。'}, status=400)

    report = _get_report_or_none(request, report_id)
    if report is None:
        return utf8_json({'ok': False, 'error': '分析报告不存在。'}, status=404)

    answer = answer_report_question(report, question)
    return utf8_json(
        {
            'ok': True,
            'question': question,
            'answer': answer['answer'],
            'references': answer['references'],
        },
        json_dumps_params={'ensure_ascii': False},
    )


def export_report_pdf(request, report_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    report = _get_report_or_none(request, report_id)
    if report is None:
        return utf8_json({'ok': False, 'error': '分析报告不存在。'}, status=404)

    content = build_report_pdf(report)
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="tender-report-{report.id}.pdf"'
    return response


def export_report_word(request, report_id):
    auth_error = _authentication_error(request)
    if auth_error:
        return auth_error
    report = _get_report_or_none(request, report_id)
    if report is None:
        return utf8_json({'ok': False, 'error': '分析报告不存在。'}, status=404)

    content = build_report_docx(report)
    response = HttpResponse(
        content,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    response['Content-Disposition'] = f'attachment; filename="tender-report-{report.id}.docx"'
    return response


def _get_report_or_none(request, report_id):
    try:
        return _reports_for_request(request).select_related('tender_project', 'tender_project__company').get(id=report_id)
    except AnalysisReport.DoesNotExist:
        return None


@require_POST
def analyze_tender_pdf_agent(request):
    if not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录后再上传 PDF。'}, status=401)

    company_id = request.POST.get('company_id')
    if not company_id:
        return utf8_json({'ok': False, 'error': 'company_id 不能为空。'}, status=400)
    analysis_mode = _resolve_analysis_mode(request.POST.get('analysis_mode'))
    if analysis_mode is None:
        return utf8_json({'ok': False, 'error': 'analysis_mode 仅支持 rule_based、openai 或 agnes。'}, status=400)

    try:
        company = _companies_for_request(request).prefetch_related('qualifications', 'experiences').get(id=company_id)
    except CompanyProfile.DoesNotExist:
        return utf8_json({'ok': False, 'error': '企业档案不存在。'}, status=404)

    pdf_file = request.FILES.get('pdf_file')
    if not pdf_file:
        return utf8_json({'ok': False, 'error': 'pdf_file 不能为空。'}, status=400)
    if not pdf_file.name.lower().endswith('.pdf'):
        return utf8_json({'ok': False, 'error': '请上传 PDF 文件。'}, status=400)

    project = TenderProject.objects.create(
        company=company,
        name=pdf_file.name.rsplit('.', 1)[0],
        status=TenderProject.Status.ANALYZING,
    )
    try:
        document = TenderDocument.objects.create(
            tender_project=project,
            file=pdf_file,
            original_name=pdf_file.name,
            file_size=pdf_file.size,
        )
    except Exception:
        project.delete()
        return utf8_json(
            {'ok': False, 'error': 'PDF 临时文件保存失败，请稍后重试。'},
            status=500,
        )

    try:
        local_file_path = document.file.path
        extraction = extract_pdf_content(local_file_path, document.original_name)
        extracted_text = extraction['text']
        if not extracted_text:
            raise ValueError('未能从 PDF 中提取到文本。')

        try:
            storage_info = persist_pdf(local_file_path, document.original_name, project.id)
        except Exception as storage_error:
            storage_info = {
                'backend': 'temporary',
                'persistent': False,
                'pathname': document.file.name,
                'warning': f'原始 PDF 永久保存失败：{storage_error}',
            }

        if storage_info['backend'] == 'vercel_blob':
            document.file.name = storage_info['pathname']

        document.extracted_text = extracted_text
        document.parse_status = TenderDocument.ParseStatus.PARSED
        document.error_message = '；'.join(
            item
            for item in [extraction.get('warning', ''), storage_info.get('warning', '')]
            if item
        )
        update_fields = ['extracted_text', 'parse_status', 'error_message', 'updated_at']
        if storage_info['backend'] == 'vercel_blob':
            update_fields.append('file')
        document.save(update_fields=update_fields)
        if storage_info['backend'] == 'vercel_blob':
            try:
                os.remove(local_file_path)
            except OSError:
                pass

        company_profile = _company_profile_for_agent(company)
        report = _analyze_tender(extracted_text, company_profile, analysis_mode)
        project.name = report.get('project_name') or project.name
        project.procurement_method = report.get('procurement_method') or ''
        project.project_type = report.get('project_type') or ''
        project.region = report.get('region') or ''
        project.budget_amount = report.get('budget_amount')
        project.deadline = _parse_report_deadline(report.get('deadline'))
        project.source_text = extracted_text
        project.status = TenderProject.Status.ANALYZED
        project.save(
            update_fields=[
                'name',
                'procurement_method',
                'project_type',
                'region',
                'budget_amount',
                'deadline',
                'source_text',
                'status',
                'updated_at',
            ]
        )

        analysis_report = _create_analysis_report(project=project, report=report)
    except Exception as exc:
        document.parse_status = TenderDocument.ParseStatus.FAILED
        document.error_message = str(exc)
        document.save(update_fields=['parse_status', 'error_message', 'updated_at'])
        project.status = TenderProject.Status.PENDING
        project.save(update_fields=['status', 'updated_at'])
        return utf8_json({'ok': False, 'error': str(exc), 'project_id': project.id, 'document_id': document.id}, status=400)

    return utf8_json(
        {
            'ok': True,
            'project_id': project.id,
            'document_id': document.id,
            'report_id': analysis_report.id,
            'report': report,
            'extraction': {
                'method': extraction['method'],
                'character_count': extraction['character_count'],
                'used_vision': extraction['used_vision'],
                'warning': extraction.get('warning', ''),
            },
            'storage': {
                'backend': storage_info['backend'],
                'persistent': storage_info['persistent'],
                'warning': storage_info.get('warning', ''),
            },
        },
        json_dumps_params={'ensure_ascii': False},
    )


@require_POST
def analyze_tender_blob_agent(request):
    if not request.user.is_authenticated:
        return utf8_json({'ok': False, 'error': '请先登录后再分析云端 PDF。'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    company_id = payload.get('company_id')
    pathname = str(payload.get('pathname') or '').strip()
    original_name = Path(str(payload.get('original_name') or 'document.pdf')).name
    analysis_mode = _resolve_analysis_mode(payload.get('analysis_mode'))
    if not company_id:
        return utf8_json({'ok': False, 'error': 'company_id 不能为空。'}, status=400)
    if analysis_mode is None:
        return utf8_json({'ok': False, 'error': 'analysis_mode 仅支持 rule_based、openai 或 agnes。'}, status=400)
    if not is_client_blob_path(pathname) or not pathname.lower().endswith('.pdf'):
        return utf8_json({'ok': False, 'error': '云端 PDF 路径无效。'}, status=400)
    if not original_name.lower().endswith('.pdf'):
        return utf8_json({'ok': False, 'error': '请上传 PDF 文件。'}, status=400)

    try:
        company = _companies_for_request(request).prefetch_related('qualifications', 'experiences').get(id=company_id)
    except CompanyProfile.DoesNotExist:
        return utf8_json({'ok': False, 'error': '企业档案不存在。'}, status=404)

    try:
        pdf_content = read_private_blob(pathname)
    except (FileNotFoundError, RuntimeError) as exc:
        return utf8_json({'ok': False, 'error': str(exc)}, status=400)

    if len(pdf_content) > 50 * 1024 * 1024:
        return utf8_json({'ok': False, 'error': 'PDF 文件不能超过 50 MB。'}, status=400)
    if not pdf_content.lstrip().startswith(b'%PDF'):
        return utf8_json({'ok': False, 'error': '云端文件不是有效的 PDF。'}, status=400)

    project = TenderProject.objects.create(
        company=company,
        name=original_name.rsplit('.', 1)[0],
        status=TenderProject.Status.ANALYZING,
    )
    document = TenderDocument.objects.create(
        tender_project=project,
        file=pathname,
        original_name=original_name,
        file_size=len(pdf_content),
    )

    temporary_path = ''
    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temporary_file:
            temporary_file.write(pdf_content)
            temporary_path = temporary_file.name

        extraction = extract_pdf_content(temporary_path, original_name)
        extracted_text = extraction['text']
        if not extracted_text:
            raise ValueError('未能从 PDF 中提取到文本。')

        document.extracted_text = extracted_text
        document.parse_status = TenderDocument.ParseStatus.PARSED
        document.error_message = extraction.get('warning', '')
        document.save(update_fields=['extracted_text', 'parse_status', 'error_message', 'updated_at'])

        report = _analyze_tender(
            extracted_text,
            _company_profile_for_agent(company),
            analysis_mode,
        )
        project.name = report.get('project_name') or project.name
        project.procurement_method = report.get('procurement_method') or ''
        project.project_type = report.get('project_type') or ''
        project.region = report.get('region') or ''
        project.budget_amount = report.get('budget_amount')
        project.deadline = _parse_report_deadline(report.get('deadline'))
        project.source_text = extracted_text
        project.status = TenderProject.Status.ANALYZED
        project.save(
            update_fields=[
                'name', 'procurement_method', 'project_type', 'region', 'budget_amount', 'deadline',
                'source_text', 'status', 'updated_at',
            ]
        )
        analysis_report = _create_analysis_report(project=project, report=report)
    except Exception as exc:
        document.parse_status = TenderDocument.ParseStatus.FAILED
        document.error_message = str(exc)
        document.save(update_fields=['parse_status', 'error_message', 'updated_at'])
        project.status = TenderProject.Status.PENDING
        project.save(update_fields=['status', 'updated_at'])
        return utf8_json(
            {'ok': False, 'error': str(exc), 'project_id': project.id, 'document_id': document.id},
            status=400,
        )
    finally:
        if temporary_path:
            try:
                os.remove(temporary_path)
            except OSError:
                pass

    return utf8_json({
        'ok': True,
        'project_id': project.id,
        'document_id': document.id,
        'report_id': analysis_report.id,
        'report': report,
        'extraction': {
            'method': extraction['method'],
            'character_count': extraction['character_count'],
            'used_vision': extraction['used_vision'],
            'warning': extraction.get('warning', ''),
        },
        'storage': {'backend': 'vercel_blob', 'persistent': True, 'warning': ''},
    })


def _company_profile_for_agent(company):
    return {
        'name': company.name,
        'business_scope': _split_profile_text(company.main_business),
        'qualifications': [item.name for item in company.qualifications.all()],
        'project_experiences': [item.name for item in company.experiences.all()],
        'service_regions': _split_profile_text(company.service_regions),
        'max_project_amount': float(company.max_project_amount) if company.max_project_amount is not None else None,
        'forbidden_conditions': _split_profile_text(company.forbidden_conditions),
    }


def _serialize_company_profile(company):
    if company is None:
        return None

    return {
        'id': company.id,
        'name': company.name,
        'main_business': company.main_business,
        'service_regions': company.service_regions,
        'max_project_amount': float(company.max_project_amount) if company.max_project_amount is not None else None,
        'forbidden_conditions': company.forbidden_conditions,
        'qualifications': [
            {
                'id': item.id,
                'name': item.name,
                'certificate_no': item.certificate_no,
                'issuer': item.issuer,
                'valid_until': item.valid_until.isoformat() if item.valid_until else '',
            }
            for item in company.qualifications.all()
        ],
        'experiences': [
            {
                'id': item.id,
                'name': item.name,
                'industry': item.industry,
                'amount': float(item.amount) if item.amount is not None else None,
                'client_name': item.client_name,
                'completed_at': item.completed_at.isoformat() if item.completed_at else '',
                'description': item.description,
            }
            for item in company.experiences.all()
        ],
    }


def _serialize_project_row(project):
    _ensure_project_task_schema()
    report = getattr(project, 'analysis_report', None)
    tasks = list(project.tasks.all()) if hasattr(project, 'tasks') else []
    pending_tasks = [task for task in tasks if task.status == ProjectTask.Status.PENDING]
    overdue_tasks = [task for task in pending_tasks if task.due_at and task.due_at < timezone.now()]
    return {
        'id': project.id,
        'name': project.name,
        'company_name': project.company.name if project.company else '-',
        'procurement_method': project.procurement_method,
        'project_type': project.project_type,
        'region': project.region,
        'budget_amount': float(project.budget_amount) if project.budget_amount is not None else None,
        'deadline': project.deadline.isoformat() if project.deadline else None,
        'status': project.status,
        'status_label': project.get_status_display(),
        'created_at': project.created_at.isoformat(),
        'report_id': report.id if report else None,
        'decision': report.decision if report else '',
        'decision_label': report.get_decision_display() if report else '待分析',
        'match_score': report.match_score if report else None,
        'risk_level': _project_risk_level(project),
        'summary': report.summary if report else '',
        'pending_task_count': len(pending_tasks),
        'overdue_task_count': len(overdue_tasks),
    }


def _serialize_project_task(task):
    now = timezone.now()
    reminder_state = 'completed'
    if task.status == ProjectTask.Status.PENDING:
        if task.due_at and task.due_at < now:
            reminder_state = 'overdue'
        elif task.due_at and task.due_at <= now + timedelta(days=1):
            reminder_state = 'due_soon'
        else:
            reminder_state = 'pending'
    return {
        'id': task.id,
        'title': task.title,
        'category': task.category,
        'category_label': task.get_category_display(),
        'status': task.status,
        'status_label': task.get_status_display(),
        'due_at': task.due_at.isoformat() if task.due_at else None,
        'assignee_name': task.assignee_name,
        'remind_at': task.remind_at.isoformat() if task.remind_at else None,
        'reminder_unread': bool(task.remind_at and task.remind_at <= now and task.reminder_read_at is None and task.status == ProjectTask.Status.PENDING),
        'project_id': task.tender_project_id,
        'project_name': task.tender_project.name if hasattr(task, 'tender_project') else '',
        'reminder_state': reminder_state,
        'is_auto_generated': task.is_auto_generated,
    }


def _ensure_project_task_schema():
    global _PROJECT_TASK_SCHEMA_READY
    if _PROJECT_TASK_SCHEMA_READY:
        return
    table_name = ProjectTask._meta.db_table
    tables = connection.introspection.table_names()
    columns = set()
    if table_name in tables:
        with connection.cursor() as cursor:
            columns = {column.name for column in connection.introspection.get_table_description(cursor, table_name)}
    required_columns = {'assignee_name', 'remind_at', 'reminder_read_at'}
    if table_name not in tables or not required_columns.issubset(columns):
        call_command('migrate', 'tenders', interactive=False, verbosity=0)
    _PROJECT_TASK_SCHEMA_READY = True


def _prefers_html(request):
    accept = request.headers.get('Accept', '')
    return 'text/html' in accept and 'application/json' not in accept.split(',')[0]


def _recent_projects_html(projects):
    rows = []
    for project in projects:
        report_link = f'/reports/{project["report_id"]}/' if project.get('report_id') else ''
        report_anchor = f'<a href="{escape(report_link)}">查看报告</a>' if report_link else '<span>-</span>'
        rows.append(
            '<tr>'
            f'<td>{escape(str(project.get("id", "")))}</td>'
            f'<td>{escape(project.get("name") or "-")}</td>'
            f'<td>{escape(project.get("company_name") or "-")}</td>'
            f'<td>{escape(project.get("project_type") or "-")}</td>'
            f'<td>{escape(project.get("decision_label") or "-")}</td>'
            f'<td>{escape(str(project.get("match_score") if project.get("match_score") is not None else "-"))}</td>'
            f'<td>{escape(project.get("risk_level") or "-")}</td>'
            f'<td>{escape(project.get("status_label") or "-")}</td>'
            f'<td>{report_anchor} <a href="/projects/{escape(str(project.get("id", "")))}/">查看项目</a></td>'
            '</tr>'
        )

    body = ''.join(rows) or '<tr><td colspan="9">暂无最近分析项目。</td></tr>'
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>最近分析项目</title>
  <style>
    body {{ margin: 0; padding: 32px; background: #f6f7f9; color: #151922; font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    p {{ margin: 0 0 22px; color: #5d6675; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d9dde5; }}
    th, td {{ padding: 12px 14px; border-bottom: 1px solid #eceff3; text-align: left; font-size: 14px; }}
    th {{ background: #121722; color: #fff; }}
    a {{ color: #9a7335; font-weight: 700; text-decoration: none; margin-right: 10px; }}
  </style>
</head>
<body>
  <h1>最近分析项目</h1>
  <p>这是浏览器预览页面。程序调用请使用 Accept: application/json 获取 JSON 数据。</p>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>项目名称</th><th>企业</th><th>类型</th><th>AI建议</th><th>评分</th><th>风险</th><th>状态</th><th>操作</th>
      </tr>
    </thead>
    <tbody>{body}</tbody>
  </table>
</body>
</html>'''


def _reference_tenders_html(references):
    rows = []
    for item in references:
        tags = ' / '.join(item.get('tags') or []) or '-'
        source_text = escape(item.get('source_text') or '-').replace('\n', '<br>')
        rows.append(
            '<article class="reference-card">'
            f'<div class="reference-card__top"><h2>{escape(item.get("title") or "-")}</h2><span>{escape(item.get("project_type") or "-")}</span></div>'
            f'<p class="reference-card__meta">{escape(item.get("industry") or "-")} · {escape(item.get("region") or "-")} · {escape(item.get("issuing_organization") or "-")}</p>'
            f'<p><strong>摘要：</strong>{escape(item.get("summary") or "-")}</p>'
            f'<p><strong>参考要点：</strong>{escape(item.get("reference_points") or "-")}</p>'
            f'<p><strong>标签：</strong>{escape(tags)}</p>'
            f'<div class="reference-card__text"><strong>正文片段：</strong><div>{source_text}</div></div>'
            '</article>'
        )

    body = ''.join(rows) or '<p class="empty">暂无参考标书。</p>'
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>参考标书库</title>
  <style>
    body {{ margin: 0; padding: 32px; background: #f3f4f7; color: #1b2330; font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    p.lead {{ margin: 0 0 24px; color: #5b6472; }}
    .reference-grid {{ display: grid; gap: 16px; }}
    .reference-card {{ background: #fff; border: 1px solid #dbe0e8; border-radius: 8px; padding: 18px 20px; box-shadow: 0 8px 24px rgba(18, 23, 34, 0.05); }}
    .reference-card__top {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }}
    .reference-card__top h2 {{ margin: 0; font-size: 20px; }}
    .reference-card__top span {{ color: #8a6230; font-weight: 700; }}
    .reference-card__meta {{ color: #5b6472; }}
    .reference-card p {{ margin: 10px 0; line-height: 1.7; }}
    .reference-card__text {{ margin-top: 14px; padding-top: 14px; border-top: 1px solid #edf0f4; line-height: 1.7; }}
    .empty {{ padding: 24px; background: #fff; border: 1px solid #dbe0e8; border-radius: 8px; }}
  </style>
</head>
<body>
  <h1>参考标书库</h1>
  <p class="lead">浏览器中查看时展示可读预览；程序调用请继续使用 JSON 接口。</p>
  <section class="reference-grid">{body}</section>
</body>
</html>'''


def _contracts_page_html(contracts):
    cards = []
    for item in contracts:
        cards.append(
            '<button class="contract-item" type="button"'
            f' data-contract=\'{escape(json.dumps(item, ensure_ascii=False))}\'>'
            f'<strong>{escape(_contract_title(item))}</strong>'
            f'<span>{escape(_contract_subtitle(item))}</span>'
            '</button>'
        )

    list_html = ''.join(cards) or '<div class="empty">当前还没有合同样本。</div>'
    initial_payload = json.dumps(contracts, ensure_ascii=False).replace('</', '<\\/')
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>合同库</title>
  <style>
    :root {{
      color-scheme: light;
      --canvas: #f6f4ef;
      --surface: rgba(255, 255, 255, 0.78);
      --ink: #111722;
      --muted: #697385;
      --line: #d9dee6;
      --blue: #0b5fe7;
      --blue-soft: #edf4ff;
      --gold: #b48b34;
      --danger: #d9404a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 8% 0%, rgba(11,95,231,0.055), transparent 30%),
        linear-gradient(180deg, #fbfaf7 0%, var(--canvas) 100%);
      color: var(--ink);
      font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
    }}
    button, input, textarea {{ font: inherit; }}
    .site-header {{
      min-height: 76px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 28px;
      padding: 0 max(32px, calc((100vw - 1296px) / 2));
      border-bottom: 1px solid rgba(17,23,34,0.1);
      background: rgba(251,250,247,0.9);
      backdrop-filter: blur(18px);
    }}
    .brand {{ display: inline-flex; align-items: center; gap: 12px; color: var(--ink); text-decoration: none; }}
    .brand img {{ width: 36px; height: 36px; border-radius: 9px; }}
    .brand strong {{ font-size: 22px; letter-spacing: -0.05em; }}
    .site-nav {{ display: flex; align-items: center; gap: 34px; }}
    .site-nav a {{ position: relative; padding: 28px 0 25px; color: #5c6573; font-size: 14px; font-weight: 700; text-decoration: none; }}
    .site-nav a:hover, .site-nav a.active {{ color: var(--blue); }}
    .site-nav a.active::after {{ content: ""; position: absolute; right: 0; bottom: -1px; left: 0; height: 2px; background: var(--blue); }}
    .shell {{ width: min(1296px, calc(100% - 48px)); margin: 0 auto; padding: 54px 0 64px; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 32px; align-items: end; margin-bottom: 30px; padding-bottom: 26px; border-bottom: 1px solid var(--line); }}
    .eyebrow {{ margin: 0 0 12px; color: var(--blue); font-size: 11px; font-weight: 800; letter-spacing: 0.2em; text-transform: uppercase; }}
    h1 {{ margin: 0; font-family: "Songti SC", SimSun, serif; font-size: clamp(38px, 4vw, 58px); line-height: 1.05; letter-spacing: -0.07em; }}
    .lead {{ max-width: 760px; margin: 14px 0 0; color: var(--muted); line-height: 1.8; }}
    .back-link {{ color: var(--blue); font-size: 14px; font-weight: 800; text-decoration: none; white-space: nowrap; }}
    .layout {{ display: grid; grid-template-columns: 324px minmax(0, 1fr); gap: 20px; align-items: start; }}
    .panel {{ background: var(--surface); border: 1px solid var(--line); border-radius: 4px; box-shadow: 0 20px 48px rgba(39,53,75,0.055); backdrop-filter: blur(16px); }}
    .list-panel {{ padding: 18px; position: sticky; top: 18px; }}
    .form-panel {{ padding: 24px; }}
    .list-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--line); }}
    .list-head strong {{ font-family: "Songti SC", SimSun, serif; font-size: 20px; }}
    .list {{ display: grid; gap: 8px; max-height: calc(100vh - 184px); overflow: auto; padding-right: 3px; }}
    .contract-item {{ width: 100%; text-align: left; padding: 15px 14px; border: 1px solid transparent; border-radius: 3px; background: rgba(255,255,255,0.58); cursor: pointer; transition: 160ms ease; }}
    .contract-item:hover {{ border-color: #c8d3e4; transform: translateY(-1px); }}
    .contract-item.active {{ border-color: rgba(11,95,231,0.5); background: var(--blue-soft); box-shadow: inset 3px 0 0 var(--blue); }}
    .contract-item strong, .contract-item span {{ display: block; }}
    .contract-item strong {{ font-size: 14px; line-height: 1.55; }}
    .contract-item span {{ margin-top: 7px; color: var(--muted); font-size: 12px; line-height: 1.55; }}
    .empty {{ padding: 18px; border: 1px dashed #c9d1dd; border-radius: 3px; color: var(--muted); background: rgba(255,255,255,0.48); }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; }}
    .button-primary, .button-secondary, .button-danger {{ min-height: 42px; border-radius: 3px; padding: 0 18px; font-size: 14px; font-weight: 800; cursor: pointer; transition: 160ms ease; }}
    .button-primary {{ border: 1px solid var(--blue); color: #fff; background: var(--blue); }}
    .button-secondary {{ border: 1px solid #cbd3df; background: rgba(255,255,255,0.82); color: var(--ink); }}
    .button-danger {{ border: 1px solid rgba(217,64,74,0.3); background: #fff7f6; color: var(--danger); }}
    .button-primary:hover, .button-secondary:hover, .button-danger:hover {{ transform: translateY(-1px); box-shadow: 0 10px 24px rgba(39,53,75,0.1); }}
    .status {{ min-height: 38px; margin-bottom: 18px; padding: 10px 12px; border-left: 3px solid var(--gold); color: #596475; background: rgba(255,249,232,0.7); font-size: 13px; }}
    .status.error {{ border-left-color: var(--danger); color: #b13e3e; background: #fff6f6; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
    .field {{ display: grid; gap: 8px; }}
    .field.full {{ grid-column: 1 / -1; }}
    label {{ font-size: 13px; font-weight: 800; color: #354052; }}
    input, textarea {{ width: 100%; border: 1px solid #cfd6e0; border-radius: 3px; padding: 12px 13px; color: inherit; background: rgba(255,255,255,0.88); outline: none; transition: 160ms ease; }}
    input:focus, textarea:focus {{ border-color: var(--blue); box-shadow: 0 0 0 3px rgba(11,95,231,0.1); background: #fff; }}
    textarea {{ min-height: 120px; resize: vertical; line-height: 1.75; }}
    .meta {{ margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; }}
    @media (max-width: 980px) {{
      .site-header {{ padding: 0 24px; }}
      .site-nav {{ display: none; }}
      .shell {{ width: min(100% - 28px, 760px); padding-top: 34px; }}
      .topbar {{ align-items: start; }}
      .layout {{ grid-template-columns: 1fr; }}
      .list-panel {{ position: static; }}
      .list {{ max-height: 360px; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 640px) {{
      .site-header {{ min-height: 64px; padding: 0 16px; }}
      .brand img {{ width: 32px; height: 32px; }}
      .shell {{ width: calc(100% - 20px); padding: 26px 0 40px; }}
      .topbar {{ display: grid; grid-template-columns: minmax(0, 1fr); gap: 18px; }}
      .topbar > div {{ min-width: 0; }}
      .lead {{ overflow-wrap: anywhere; }}
      h1 {{ font-size: 38px; }}
      .form-panel {{ padding: 16px; }}
      .field.full {{ grid-column: auto; }}
    }}
  </style>
</head>
<body>
  <header class="site-header">
    <a class="brand" href="/" aria-label="策标首页">
      <img src="/static/frontend/brand-mark-color.png" alt="">
      <strong>策标</strong>
    </a>
    <nav class="site-nav" aria-label="网站导航">
      <a href="/">首页</a>
      <a href="/product/">产品功能</a>
      <a href="/solutions/">解决方案</a>
      <a href="/process/">AI分析流程</a>
      <a href="/scenes/">应用场景</a>
      <a class="active" href="/contracts/">合同库</a>
    </nav>
  </header>
  <div class="shell">
    <div class="topbar">
      <div>
        <p class="eyebrow">REFERENCE LIBRARY</p>
        <h1>合同库</h1>
        <p class="lead">管理合同/标书参考资料，支持新增、编辑、删除，并沉淀风险、评分规则与材料清单。</p>
      </div>
      <a class="back-link" href="/">返回工作台 →</a>
    </div>
    <div class="layout">
      <aside class="panel list-panel">
        <div class="list-head">
          <strong>样本列表</strong>
          <button class="button-secondary" id="newContract" type="button">新建</button>
        </div>
        <div class="list" id="contractList">{list_html}</div>
      </aside>
      <section class="panel form-panel">
        <div class="toolbar">
          <button class="button-primary" id="saveButton" type="button">保存</button>
          <button class="button-secondary" id="resetButton" type="button">重置</button>
          <button class="button-danger" id="deleteButton" type="button">删除</button>
        </div>
        <div class="status" id="statusText">已加载 {len(contracts)} 条合同样本。</div>
        <div class="grid">
          <div class="field full">
            <label for="basic_info">基础信息</label>
            <textarea id="basic_info"></textarea>
          </div>
          <div class="field full">
            <label for="tender_content">标书内容</label>
            <textarea id="tender_content"></textarea>
          </div>
          <div class="field full">
            <label for="reference_points">参考要点</label>
            <textarea id="reference_points"></textarea>
          </div>
          <div class="field full">
            <label for="scoring_rules">评分规则</label>
            <textarea id="scoring_rules"></textarea>
          </div>
          <div class="field">
            <label for="risk_tags">风险标签</label>
            <textarea id="risk_tags"></textarea>
          </div>
          <div class="field">
            <label for="material_checklist">材料清单</label>
            <textarea id="material_checklist"></textarea>
          </div>
          <div class="field full">
            <label for="source_maintenance_info">来源与维护信息</label>
            <textarea id="source_maintenance_info"></textarea>
          </div>
        </div>
        <div class="meta" id="metaText">当前为新建模式。</div>
      </section>
    </div>
  </div>
  <script id="initial-contracts" type="application/json">{initial_payload}</script>
  <script>
    const initialContracts = JSON.parse(document.getElementById('initial-contracts').textContent);
    const fields = [
      'basic_info',
      'tender_content',
      'reference_points',
      'scoring_rules',
      'risk_tags',
      'material_checklist',
      'source_maintenance_info',
    ];
    const formEls = Object.fromEntries(fields.map((name) => [name, document.getElementById(name)]));
    const listEl = document.getElementById('contractList');
    const statusEl = document.getElementById('statusText');
    const metaEl = document.getElementById('metaText');
    let contracts = initialContracts;
    let currentId = null;

    function emptyContract() {{
      return Object.fromEntries(fields.map((name) => [name, '']));
    }}

    function contractTitle(item) {{
      return (item.basic_info || '未命名合同').split('\\n')[0].trim() || '未命名合同';
    }}

    function contractSubtitle(item) {{
      const parts = [];
      if (item.risk_tags) parts.push(item.risk_tags.split('\\n')[0].trim());
      if (item.source_maintenance_info) parts.push(item.source_maintenance_info.split('\\n')[0].trim());
      return parts.filter(Boolean).join(' · ') || '点击查看详情';
    }}

    function renderList() {{
      if (!contracts.length) {{
        listEl.innerHTML = '<div class="empty">当前还没有合同样本。</div>';
        return;
      }}
      listEl.innerHTML = contracts.map((item) => `
        <button class="contract-item ${'{'}item.id === currentId ? 'active' : ''{'}'}" type="button" data-id="${'{'}item.id{'}'}">
          <strong>${'{'}escapeHtml(contractTitle(item)){'}'}</strong>
          <span>${'{'}escapeHtml(contractSubtitle(item)){'}'}</span>
        </button>
      `).join('');
    }}

    function fillForm(contract) {{
      const source = contract || emptyContract();
      fields.forEach((name) => {{
        formEls[name].value = source[name] || '';
      }});
      currentId = contract ? contract.id : null;
      metaEl.textContent = currentId ? `当前编辑 ID: ${'{'}currentId{'}'}` : '当前为新建模式。';
      renderList();
    }}

    function getPayload() {{
      const payload = {{}};
      fields.forEach((name) => {{
        payload[name] = formEls[name].value.trim();
      }});
      return payload;
    }}

    function setStatus(message, isError = false) {{
      statusEl.textContent = message;
      statusEl.className = isError ? 'status error' : 'status';
    }}

    function escapeHtml(value) {{
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }}

    async function reloadContracts(selectId = currentId) {{
      const response = await fetch('/api/contracts/');
      const payload = await response.json();
      contracts = payload.contracts || [];
      if (selectId) {{
        const current = contracts.find((item) => item.id === selectId);
        if (current) {{
          fillForm(current);
          return;
        }}
      }}
      fillForm(contracts[0] || null);
    }}

    listEl.addEventListener('click', (event) => {{
      const trigger = event.target.closest('.contract-item');
      if (!trigger) return;
      const id = Number(trigger.dataset.id);
      const target = contracts.find((item) => item.id === id);
      fillForm(target || null);
      setStatus(`已切换到合同 ${'{'}id{'}'}。`);
    }});

    document.getElementById('newContract').addEventListener('click', () => {{
      fillForm(null);
      setStatus('已切换到新建模式。');
    }});

    document.getElementById('resetButton').addEventListener('click', () => {{
      const current = contracts.find((item) => item.id === currentId);
      fillForm(current || null);
      setStatus('表单已重置。');
    }});

    document.getElementById('saveButton').addEventListener('click', async () => {{
      const payload = getPayload();
      const method = currentId ? 'PUT' : 'POST';
      const url = currentId ? `/api/contracts/${'{'}currentId{'}'}/` : '/api/contracts/';
      const response = await fetch(url, {{
        method,
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload),
      }});
      const result = await response.json();
      if (!response.ok || !result.ok) {{
        setStatus(result.error || '保存失败。', true);
        return;
      }}
      const saved = result.contract;
      setStatus(currentId ? `合同 ${'{'}saved.id{'}'} 已更新。` : `合同 ${'{'}saved.id{'}'} 已创建。`);
      await reloadContracts(saved.id);
    }});

    document.getElementById('deleteButton').addEventListener('click', async () => {{
      if (!currentId) {{
        setStatus('当前是新建模式，没有可删除的记录。', true);
        return;
      }}
      if (!window.confirm(`确认删除合同 ${'{'}currentId{'}'} 吗？`)) return;
      const response = await fetch(`/api/contracts/${'{'}currentId{'}'}/`, {{ method: 'DELETE' }});
      const result = await response.json();
      if (!response.ok || !result.ok) {{
        setStatus(result.error || '删除失败。', true);
        return;
      }}
      setStatus(`合同 ${'{'}currentId{'}'} 已删除。`);
      currentId = null;
      await reloadContracts();
    }});

    fillForm(contracts[0] || null);
  </script>
</body>
</html>'''


def _serialize_project_report(report):
    if report is None:
        return None

    return {
        'id': report.id,
        'decision': report.decision,
        'decision_label': report.get_decision_display(),
        'match_score': report.match_score,
        'summary': report.summary,
        'created_at': report.created_at.isoformat(),
    }


def _serialize_project_note(note):
    return {
        'id': note.id,
        'note_type': note.note_type,
        'note_type_label': note.get_note_type_display(),
        'content': note.content,
        'operator_name': note.operator_name,
        'created_at': note.created_at.isoformat(),
    }


def _serialize_reference_tender(item):
    return {
        'id': item.id,
        'title': item.title,
        'project_type': item.project_type,
        'industry': item.industry,
        'region': item.region,
        'issuing_organization': item.issuing_organization,
        'budget_amount': float(item.budget_amount) if item.budget_amount is not None else None,
        'published_at': item.published_at.isoformat() if item.published_at else '',
        'summary': item.summary,
        'reference_points': item.reference_points,
        'source_text': item.source_text,
        'tags': _split_profile_text(item.tags),
        'is_featured': item.is_featured,
        'updated_at': item.updated_at.isoformat(),
    }


def _serialize_contract(item):
    return {
        'id': item.id,
        'basic_info': item.basic_info,
        'tender_content': item.tender_content,
        'reference_points': item.reference_points,
        'scoring_rules': item.scoring_rules,
        'risk_tags': item.risk_tags,
        'material_checklist': item.material_checklist,
        'source_maintenance_info': item.source_maintenance_info,
    }


def _contract_title(item):
    first_line = str(item.get('basic_info') or '').split('\n')[0].strip()
    return first_line or '未命名合同'


def _contract_subtitle(item):
    parts = []
    risk = str(item.get('risk_tags') or '').split('\n')[0].strip()
    source = str(item.get('source_maintenance_info') or '').split('\n')[0].strip()
    if risk:
        parts.append(risk)
    if source:
        parts.append(source)
    return ' · '.join(parts) or '点击查看详情'


def _load_json_payload(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)


def _contract_fields_from_payload(payload):
    return {
        'basic_info': str(payload.get('basic_info') or '').strip(),
        'tender_content': str(payload.get('tender_content') or '').strip(),
        'reference_points': str(payload.get('reference_points') or '').strip(),
        'scoring_rules': str(payload.get('scoring_rules') or '').strip(),
        'risk_tags': str(payload.get('risk_tags') or '').strip(),
        'material_checklist': str(payload.get('material_checklist') or '').strip(),
        'source_maintenance_info': str(payload.get('source_maintenance_info') or '').strip(),
    }


def _validate_contract_fields(fields):
    if not any(fields.values()):
        return utf8_json({'ok': False, 'error': '请至少填写一项合同/标书内容。'}, status=400)
    return None


def _project_risk_level(project):
    report = getattr(project, 'analysis_report', None)
    if not report:
        return '-'

    priority = {'高': 3, '中': 2, '低': 1}
    risks = report.risks or []
    if not risks:
        return '低'

    return max((str(risk.get('level') or '低') for risk in risks), key=lambda level: priority.get(level, 0))


def _replace_company_qualifications(company, qualifications):
    company.qualifications.all().delete()
    for item in qualifications:
        name = str(item.get('name') or '').strip()
        if not name:
            continue
        Qualification.objects.create(
            company=company,
            name=name,
            certificate_no=str(item.get('certificate_no') or '').strip(),
            issuer=str(item.get('issuer') or '').strip(),
            valid_until=_parse_date(item.get('valid_until')),
        )


def _replace_company_experiences(company, experiences):
    company.experiences.all().delete()
    for item in experiences:
        name = str(item.get('name') or '').strip()
        if not name:
            continue
        ProjectExperience.objects.create(
            company=company,
            name=name,
            industry=str(item.get('industry') or '').strip(),
            amount=item.get('amount') or None,
            client_name=str(item.get('client_name') or '').strip(),
            completed_at=_parse_date(item.get('completed_at')),
            description=str(item.get('description') or '').strip(),
        )


def _parse_date(value):
    value = str(value or '').strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _parse_report_deadline(value):
    value = str(value or '').strip()
    if not value:
        return None

    normalized = value.replace('：', ':')
    try:
        parsed = datetime.fromisoformat(normalized.replace('Z', '+00:00'))
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed
    except ValueError:
        pass
    formats = (
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M',
        '%Y年%m月%d日%H:%M',
        '%Y年%m月%d日',
    )
    for date_format in formats:
        candidate = normalized.replace(' ', '') if '年' in date_format else normalized
        try:
            parsed = datetime.strptime(candidate, date_format)
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        except ValueError:
            continue
    return None


def _split_profile_text(value):
    return [item.strip() for item in str(value or '').replace('\n', '、').replace(',', '、').replace('，', '、').split('、') if item.strip()]


def _save_agent_report(tender_text, company, report):
    project = TenderProject.objects.create(
        company=company,
        name=report.get('project_name') or '未命名招标项目',
        procurement_method=report.get('procurement_method') or '',
        project_type=report.get('project_type') or '',
        region=report.get('region') or '',
        budget_amount=report.get('budget_amount'),
        deadline=_parse_report_deadline(report.get('deadline')),
        source_text=tender_text,
        status=TenderProject.Status.ANALYZED,
    )
    analysis_report = _create_analysis_report(project=project, report=report)
    return project, analysis_report


def _create_analysis_report(project, report):
    _ensure_project_task_schema()
    analysis_report = AnalysisReport.objects.create(
        tender_project=project,
        decision=_map_decision(report.get('decision')),
        match_score=report.get('match_score') or 0,
        summary=report.get('decision_reason') or '',
        risks=report.get('risks') or [],
        missing_materials=report.get('qualification_match', {}).get('missing', []),
        next_actions=report.get('next_actions') or [],
        raw_report=report,
    )
    sync_report_tasks(analysis_report)
    return analysis_report


def _map_decision(decision):
    mapping = {
        '推荐投标': AnalysisReport.Decision.RECOMMENDED,
        '谨慎投标': AnalysisReport.Decision.CAUTIOUS,
        '不建议投标': AnalysisReport.Decision.NOT_RECOMMENDED,
        '人工复核': AnalysisReport.Decision.NEEDS_REVIEW,
    }
    return mapping.get(decision, AnalysisReport.Decision.NEEDS_REVIEW)
