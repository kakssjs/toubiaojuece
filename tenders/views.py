import json
from html import escape
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.views.static import serve
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .agents import TenderAnalysisAgent
from .models import (
    AnalysisReport,
    CompanyProfile,
    Contract,
    ProjectExperience,
    ProjectNote,
    Qualification,
    TenderDocument,
    TenderProject,
    TenderReference,
)
from .services.pdf_parser import extract_pdf_text
from .services.report_qa import answer_report_question
from .services.report_exporter import build_report_docx, build_report_pdf


JSON_UTF8_CONTENT_TYPE = 'application/json; charset=utf-8'


def utf8_json(data, **kwargs):
    kwargs.setdefault('content_type', JSON_UTF8_CONTENT_TYPE)
    return JsonResponse(data, **kwargs)


def frontend_app(request, *args, **kwargs):
    index_path = Path(settings.BASE_DIR) / 'static' / 'frontend' / 'index.html'
    if not index_path.exists():
        raise Http404('Vue frontend has not been built yet.')

    return FileResponse(index_path.open('rb'), content_type='text/html')


def frontend_static(request, path):
    return serve(request, path, document_root=Path(settings.BASE_DIR) / 'static' / 'frontend')


@csrf_exempt
@require_POST
def analyze_tender_agent(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    tender_text = str(payload.get('tender_text') or '').strip()
    if not tender_text:
        return utf8_json({'ok': False, 'error': 'tender_text 不能为空。'}, status=400)

    company = None
    company_id = payload.get('company_id')
    if company_id:
        try:
            company = CompanyProfile.objects.prefetch_related('qualifications', 'experiences').get(id=company_id)
        except CompanyProfile.DoesNotExist:
            return utf8_json({'ok': False, 'error': '企业档案不存在。'}, status=404)

    company_profile = _company_profile_for_agent(company) if company else payload.get('company_profile') or {}
    if not isinstance(company_profile, dict):
        return utf8_json({'ok': False, 'error': 'company_profile 必须是对象。'}, status=400)

    report = TenderAnalysisAgent().analyze(
        tender_text=tender_text,
        company_profile=company_profile,
    )

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
    companies = CompanyProfile.objects.order_by('name').values('id', 'name', 'main_business', 'service_regions')
    return utf8_json(
        {
            'ok': True,
            'companies': list(companies),
        },
        json_dumps_params={'ensure_ascii': False},
    )


@csrf_exempt
def company_profile_detail(request):
    if request.method == 'GET':
        company = CompanyProfile.objects.prefetch_related('qualifications', 'experiences').order_by('name').first()
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
        company = CompanyProfile.objects.filter(id=company_id).first()
        if company is None:
            return utf8_json({'ok': False, 'error': '企业档案不存在。'}, status=404)
    else:
        company = CompanyProfile.objects.order_by('name').first()

    if company is None:
        company = CompanyProfile()

    company.name = name
    company.main_business = str(payload.get('main_business') or '').strip()
    company.service_regions = str(payload.get('service_regions') or '').strip()
    company.max_project_amount = payload.get('max_project_amount') or None
    company.forbidden_conditions = str(payload.get('forbidden_conditions') or '').strip()
    company.save()

    _replace_company_qualifications(company, payload.get('qualifications') or [])
    _replace_company_experiences(company, payload.get('experiences') or [])

    company = CompanyProfile.objects.prefetch_related('qualifications', 'experiences').get(id=company.id)
    return utf8_json(
        {
            'ok': True,
            'company': _serialize_company_profile(company),
        },
        json_dumps_params={'ensure_ascii': False},
    )


def project_dashboard(request):
    projects = TenderProject.objects.select_related('company').prefetch_related('analysis_report').order_by('-created_at')
    decision = request.GET.get('decision')
    if decision:
        projects = projects.filter(analysis_report__decision=decision)

    rows = [_serialize_project_row(project) for project in projects]
    summary_source = TenderProject.objects.select_related('analysis_report').all()
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
    projects = (
        TenderProject.objects.select_related('company', 'analysis_report')
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
    contracts = [_serialize_contract(item) for item in Contract.objects.all()]
    return HttpResponse(_contracts_page_html(contracts), content_type='text/html; charset=utf-8')


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def contracts_collection(request):
    if request.method == 'GET':
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


@csrf_exempt
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


def project_detail(request, project_id):
    try:
        project = (
            TenderProject.objects.select_related('company')
            .prefetch_related('analysis_report', 'notes')
            .get(id=project_id)
        )
    except TenderProject.DoesNotExist:
        return utf8_json({'ok': False, 'error': '项目不存在。'}, status=404)

    report = getattr(project, 'analysis_report', None)
    raw_report = report.raw_report if report else {}

    return utf8_json(
        {
            'ok': True,
            'project': _serialize_project_row(project),
            'report': _serialize_project_report(report),
            'notes': [_serialize_project_note(note) for note in project.notes.all()],
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
            },
        },
        json_dumps_params={'ensure_ascii': False},
    )


@csrf_exempt
@require_POST
def update_project_status(request, project_id):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    status = str(payload.get('status') or '').strip()
    valid_statuses = {value for value, _ in TenderProject.Status.choices}
    if status not in valid_statuses:
        return utf8_json({'ok': False, 'error': '项目状态不合法。'}, status=400)

    try:
        project = TenderProject.objects.select_related('company').prefetch_related('analysis_report').get(id=project_id)
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
    project = TenderProject.objects.select_related('company').prefetch_related('analysis_report').get(id=project.id)

    return utf8_json(
        {
            'ok': True,
            'project': _serialize_project_row(project),
        },
        json_dumps_params={'ensure_ascii': False},
    )


@csrf_exempt
@require_POST
def create_project_note(request, project_id):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    try:
        project = TenderProject.objects.get(id=project_id)
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


def report_detail(request, report_id):
    try:
        report = AnalysisReport.objects.select_related('tender_project', 'tender_project__company').get(id=report_id)
    except AnalysisReport.DoesNotExist:
        return utf8_json({'ok': False, 'error': '分析报告不存在。'}, status=404)

    project = report.tender_project
    company = project.company
    raw_report = report.raw_report or {}

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
            },
        },
        json_dumps_params={'ensure_ascii': False},
    )


@csrf_exempt
@require_POST
def ask_report_question(request, report_id):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return utf8_json({'ok': False, 'error': '请求体必须是有效的 JSON。'}, status=400)

    question = str(payload.get('question') or '').strip()
    if not question:
        return utf8_json({'ok': False, 'error': '问题不能为空。'}, status=400)

    report = _get_report_or_none(report_id)
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
    report = _get_report_or_none(report_id)
    if report is None:
        return utf8_json({'ok': False, 'error': '分析报告不存在。'}, status=404)

    content = build_report_pdf(report)
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="tender-report-{report.id}.pdf"'
    return response


def export_report_word(request, report_id):
    report = _get_report_or_none(report_id)
    if report is None:
        return utf8_json({'ok': False, 'error': '分析报告不存在。'}, status=404)

    content = build_report_docx(report)
    response = HttpResponse(
        content,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    response['Content-Disposition'] = f'attachment; filename="tender-report-{report.id}.docx"'
    return response


def _get_report_or_none(report_id):
    try:
        return AnalysisReport.objects.select_related('tender_project', 'tender_project__company').get(id=report_id)
    except AnalysisReport.DoesNotExist:
        return None


@csrf_exempt
@require_POST
def analyze_tender_pdf_agent(request):
    company_id = request.POST.get('company_id')
    if not company_id:
        return utf8_json({'ok': False, 'error': 'company_id 不能为空。'}, status=400)

    try:
        company = CompanyProfile.objects.prefetch_related('qualifications', 'experiences').get(id=company_id)
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
    document = TenderDocument.objects.create(
        tender_project=project,
        file=pdf_file,
        original_name=pdf_file.name,
        file_size=pdf_file.size,
    )

    try:
        extracted_text = extract_pdf_text(document.file.path)
        if not extracted_text:
            raise ValueError('未能从 PDF 中提取到文本。')

        document.extracted_text = extracted_text
        document.parse_status = TenderDocument.ParseStatus.PARSED
        document.save(update_fields=['extracted_text', 'parse_status', 'updated_at'])

        company_profile = _company_profile_for_agent(company)
        report = TenderAnalysisAgent().analyze(
            tender_text=extracted_text,
            company_profile=company_profile,
        )
        project.name = report.get('project_name') or project.name
        project.procurement_method = report.get('procurement_method') or ''
        project.project_type = report.get('project_type') or ''
        project.budget_amount = report.get('budget_amount')
        project.source_text = extracted_text
        project.status = TenderProject.Status.ANALYZED
        project.save(
            update_fields=[
                'name',
                'procurement_method',
                'project_type',
                'budget_amount',
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
        },
        json_dumps_params={'ensure_ascii': False},
    )


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
    report = getattr(project, 'analysis_report', None)
    return {
        'id': project.id,
        'name': project.name,
        'company_name': project.company.name if project.company else '-',
        'procurement_method': project.procurement_method,
        'project_type': project.project_type,
        'region': project.region,
        'budget_amount': float(project.budget_amount) if project.budget_amount is not None else None,
        'status': project.status,
        'status_label': project.get_status_display(),
        'created_at': project.created_at.isoformat(),
        'report_id': report.id if report else None,
        'decision': report.decision if report else '',
        'decision_label': report.get_decision_display() if report else '待分析',
        'match_score': report.match_score if report else None,
        'risk_level': _project_risk_level(project),
        'summary': report.summary if report else '',
    }


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
    :root {{ color-scheme: light; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #eef1f6; color: #16202f; font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; }}
    .shell {{ width: min(1320px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 42px; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 20px; }}
    h1 {{ margin: 0; font-size: 30px; }}
    .lead {{ margin: 8px 0 0; color: #5a6678; line-height: 1.7; }}
    .back-link {{ color: #9a7335; font-weight: 700; }}
    .layout {{ display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 18px; align-items: start; }}
    .panel {{ background: rgba(255,255,255,0.92); border: 1px solid #d9e0ea; border-radius: 12px; box-shadow: 0 14px 30px rgba(18,23,34,0.06); }}
    .list-panel {{ padding: 14px; position: sticky; top: 18px; }}
    .form-panel {{ padding: 20px; }}
    .list-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }}
    .list-head strong {{ font-size: 16px; }}
    .list {{ display: grid; gap: 10px; max-height: calc(100vh - 180px); overflow: auto; }}
    .contract-item {{ width: 100%; text-align: left; padding: 14px; border: 1px solid #d8dee8; border-radius: 10px; background: #fff; cursor: pointer; }}
    .contract-item.active {{ border-color: #b08a43; box-shadow: 0 0 0 2px rgba(176,138,67,0.14); }}
    .contract-item strong, .contract-item span {{ display: block; }}
    .contract-item strong {{ font-size: 14px; line-height: 1.5; }}
    .contract-item span {{ margin-top: 6px; color: #697385; font-size: 12px; line-height: 1.5; }}
    .empty {{ padding: 16px; border: 1px dashed #ccd4df; border-radius: 10px; color: #697385; background: #fafbfd; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }}
    .button-primary, .button-secondary, .button-danger {{ min-height: 42px; border-radius: 8px; padding: 0 16px; font-size: 14px; font-weight: 700; cursor: pointer; }}
    .button-primary {{ border: 0; color: #fff; background: #111722; }}
    .button-secondary {{ border: 1px solid #cfd6e0; background: #fff; color: #1a2230; }}
    .button-danger {{ border: 1px solid #e0c2c2; background: #fff7f7; color: #a23d3d; }}
    .status {{ min-height: 24px; margin-bottom: 12px; color: #5a6678; }}
    .status.error {{ color: #b13e3e; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .field {{ display: grid; gap: 8px; }}
    .field.full {{ grid-column: 1 / -1; }}
    label {{ font-size: 13px; font-weight: 700; color: #364152; }}
    input, textarea {{ width: 100%; border: 1px solid #cfd6e0; border-radius: 8px; padding: 12px 13px; font: inherit; color: inherit; background: #fff; }}
    textarea {{ min-height: 120px; resize: vertical; line-height: 1.7; }}
    .meta {{ margin-top: 16px; color: #6d7685; font-size: 12px; }}
    @media (max-width: 980px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .list-panel {{ position: static; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="topbar">
      <div>
        <h1>合同库</h1>
        <p class="lead">管理合同/标书参考资料，支持新增、编辑、删除，并沉淀风险、评分规则与材料清单。</p>
      </div>
      <a class="back-link" href="/">返回首页</a>
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


def _split_profile_text(value):
    return [item.strip() for item in str(value or '').replace('\n', '、').replace(',', '、').replace('，', '、').split('、') if item.strip()]


def _save_agent_report(tender_text, company, report):
    project = TenderProject.objects.create(
        company=company,
        name=report.get('project_name') or '未命名招标项目',
        procurement_method=report.get('procurement_method') or '',
        project_type=report.get('project_type') or '',
        budget_amount=report.get('budget_amount'),
        source_text=tender_text,
        status=TenderProject.Status.ANALYZED,
    )
    analysis_report = _create_analysis_report(project=project, report=report)
    return project, analysis_report


def _create_analysis_report(project, report):
    return AnalysisReport.objects.create(
        tender_project=project,
        decision=_map_decision(report.get('decision')),
        match_score=report.get('match_score') or 0,
        summary=report.get('decision_reason') or '',
        risks=report.get('risks') or [],
        missing_materials=report.get('qualification_match', {}).get('missing', []),
        next_actions=report.get('next_actions') or [],
        raw_report=report,
    )


def _map_decision(decision):
    mapping = {
        '推荐投标': AnalysisReport.Decision.RECOMMENDED,
        '谨慎投标': AnalysisReport.Decision.CAUTIOUS,
        '不建议投标': AnalysisReport.Decision.NOT_RECOMMENDED,
        '人工复核': AnalysisReport.Decision.NEEDS_REVIEW,
    }
    return mapping.get(decision, AnalysisReport.Decision.NEEDS_REVIEW)

