import json
from html import escape
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .agents import TenderAnalysisAgent
from .models import AnalysisReport, CompanyProfile, ProjectExperience, ProjectNote, Qualification, TenderDocument, TenderProject
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

