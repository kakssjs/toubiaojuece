import json
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from tenders.models import AnalysisReport, ProjectTask, TenderProject
from tenders.services.project_tasks import sync_report_tasks


class ProjectTaskTests(TestCase):
    def setUp(self):
        self.project = TenderProject.objects.create(
            name='智慧园区数字化平台建设项目',
            deadline=timezone.make_aware(datetime(2026, 8, 20, 9, 30)),
        )
        self.report = AnalysisReport.objects.create(
            tender_project=self.project,
            decision=AnalysisReport.Decision.CAUTIOUS,
            match_score=72,
            next_actions=['确认保证金缴纳方式、金额和截止时间', '补充原厂授权函'],
            missing_materials=['原厂授权函'],
        )

    def test_sync_report_tasks_creates_deadline_and_deduplicated_reminders(self):
        first = sync_report_tasks(self.report)
        second = sync_report_tasks(self.report)

        self.assertEqual(len(first), 4)
        self.assertEqual(len(second), 4)
        self.assertEqual(ProjectTask.objects.count(), 4)
        self.assertTrue(ProjectTask.objects.filter(category=ProjectTask.Category.GUARANTEE).exists())
        self.assertTrue(ProjectTask.objects.filter(category=ProjectTask.Category.DEADLINE).exists())
        self.assertTrue(all(task.due_at < self.project.deadline for task in first))
        self.assertTrue(all(task.remind_at <= task.due_at for task in first))

    def test_project_detail_returns_generated_tasks(self):
        response = self.client.get(f'/api/projects/{self.project.id}/')

        self.assertEqual(response.status_code, 200)
        tasks = response.json()['tasks']
        self.assertEqual(len(tasks), 4)
        self.assertEqual(tasks[0]['status_label'], '待处理')
        self.assertIn(tasks[0]['reminder_state'], {'pending', 'due_soon', 'overdue'})

    def test_sync_preserves_custom_assignee_and_reminder(self):
        task = sync_report_tasks(self.report)[0]
        custom_reminder = timezone.now() + timedelta(days=5)
        task.assignee_name = '张经理'
        task.remind_at = custom_reminder
        task.save(update_fields=['assignee_name', 'remind_at'])

        synced = sync_report_tasks(self.report)[0]

        self.assertEqual(synced.assignee_name, '张经理')
        self.assertEqual(synced.remind_at, custom_reminder)

    def test_task_status_api_marks_task_completed_and_reopens_it(self):
        task = sync_report_tasks(self.report)[0]

        response = self.client.post(
            f'/api/project-tasks/{task.id}/status/',
            data=json.dumps({'status': 'completed'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['task']['reminder_state'], 'completed')
        task.refresh_from_db()
        self.assertIsNotNone(task.completed_at)

        response = self.client.post(
            f'/api/project-tasks/{task.id}/status/',
            data=json.dumps({'status': 'pending'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertIsNone(task.completed_at)

    def test_task_settings_and_in_app_notification_flow(self):
        task = sync_report_tasks(self.report)[0]
        reminder = timezone.now() - timedelta(minutes=1)

        response = self.client.post(
            f'/api/project-tasks/{task.id}/',
            data=json.dumps({'assignee_name': '', 'remind_at': reminder.isoformat()}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['task']['assignee_name'], '')

        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['unread_count'], 1)
        self.assertEqual(payload['notifications'][0]['id'], task.id)
        self.assertEqual(payload['channels'], {'in_app': True, 'email': False, 'wecom': False})

        response = self.client.post(f'/api/notifications/{task.id}/read/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['task']['reminder_unread'], False)
        self.assertEqual(self.client.get('/api/notifications/').json()['unread_count'], 0)
