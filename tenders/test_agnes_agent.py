import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from tenders.agents import AgnesTenderAnalysisAgent


class AgnesTenderAnalysisAgentTests(SimpleTestCase):
    def test_agent_uses_rules_without_agnes_key(self):
        with patch.dict('os.environ', {'AGNES_API_KEY': ''}, clear=False):
            report = AgnesTenderAnalysisAgent().analyze(
                tender_text='政务数据平台运维项目，公开招标。',
                company_profile={},
            )

        self.assertEqual(report['analysis_engine'], 'rule_based')
        self.assertIn('match_score', report)

    def test_agent_calls_agnes_chat_completions_when_configured(self):
        agnes_report = {
            'project_name': '政务数据平台运维项目',
            'match_score': 86,
            'decision': '推荐投标',
            'decision_reason': '企业能力与项目要求匹配。',
            'risks': [],
            'next_actions': ['确认报名时间'],
        }
        response_payload = {
            'choices': [
                {'message': {'content': json.dumps(agnes_report, ensure_ascii=False)}}
            ]
        }
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            response_payload,
            ensure_ascii=False,
        ).encode('utf-8')

        with patch.dict(
            'os.environ',
            {
                'AGNES_API_KEY': 'agnes-test-key',
                'AGNES_ANALYSIS_ENABLED': '1',
                'AGNES_ANALYSIS_MODEL': 'agnes-2.0-flash',
            },
            clear=False,
        ):
            with patch('urllib.request.urlopen', return_value=response) as urlopen:
                report = AgnesTenderAnalysisAgent().analyze(
                    tender_text='政务数据平台运维项目，公开招标。',
                    company_profile={},
                )

        request = urlopen.call_args.args[0]
        request_payload = json.loads(request.data.decode('utf-8'))
        self.assertEqual(request.full_url, 'https://apihub.agnes-ai.com/v1/chat/completions')
        self.assertEqual(request.headers['Authorization'], 'Bearer agnes-test-key')
        self.assertEqual(request_payload['model'], 'agnes-2.0-flash')
        self.assertEqual(report['analysis_engine'], 'agnes')
        self.assertEqual(report['match_score'], 86)
        self.assertEqual(report['agent_trace'][-1]['agent'], 'Agnes AI深度审查Agent')
