import hashlib
from datetime import timedelta

from django.utils import timezone

from tenders.models import ProjectTask


def sync_report_tasks(report):
    project = report.tender_project
    task_specs = []

    for action in report.next_actions or []:
        title = str(action or '').strip()
        if title:
            category = _category_for_title(title)
            task_specs.append((title, category, _due_at(project.deadline, category)))

    for material in report.missing_materials or []:
        material_name = str(material or '').strip()
        if material_name:
            task_specs.append(
                (f'补齐材料：{material_name}', ProjectTask.Category.MATERIAL, _due_at(project.deadline, ProjectTask.Category.MATERIAL))
            )

    if project.deadline:
        task_specs.append(
            ('确认投标文件已在截止时间前完成递交', ProjectTask.Category.DEADLINE, _due_at(project.deadline, ProjectTask.Category.DEADLINE))
        )

    tasks = []
    seen = set()
    for title, category, due_at in task_specs:
        normalized = ''.join(title.lower().split())
        dedupe_key = f'{category}:{normalized}'
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        source_key = hashlib.sha256(dedupe_key.encode('utf-8')).hexdigest()[:40]
        task, created = ProjectTask.objects.get_or_create(
            tender_project=project,
            source_key=source_key,
            defaults={
                'analysis_report': report,
                'title': title,
                'category': category,
                'due_at': due_at,
                'remind_at': _remind_at(due_at),
                'is_auto_generated': True,
            },
        )
        if not created:
            task.analysis_report = report
            task.title = title
            task.category = category
            task.due_at = due_at
            update_fields = ['analysis_report', 'title', 'category', 'due_at']
            if task.remind_at is None:
                task.remind_at = _remind_at(due_at)
                update_fields.append('remind_at')
            task.save(update_fields=[*update_fields, 'updated_at'])
        tasks.append(task)
    return tasks


def _category_for_title(title):
    if '保证金' in title:
        return ProjectTask.Category.GUARANTEE
    if any(keyword in title for keyword in ('材料', '资质', '授权', '证书', '证明')):
        return ProjectTask.Category.MATERIAL
    if any(keyword in title for keyword in ('截止', '报名', '递交')):
        return ProjectTask.Category.DEADLINE
    return ProjectTask.Category.ACTION


def _due_at(deadline, category):
    if not deadline:
        return None
    offsets = {
        ProjectTask.Category.MATERIAL: timedelta(days=3),
        ProjectTask.Category.GUARANTEE: timedelta(days=2),
        ProjectTask.Category.DEADLINE: timedelta(hours=6),
        ProjectTask.Category.ACTION: timedelta(days=2),
    }
    due_at = deadline - offsets[category]
    return max(due_at, timezone.now())


def _remind_at(due_at):
    if not due_at:
        return None
    return max(due_at - timedelta(days=1), timezone.now())
