import json
import os
import urllib.error
import urllib.request

from .openai_tender_analysis_agent import HybridTenderAnalysisAgent
from .tender_analysis_agent import TenderAnalysisAgent as RuleBasedTenderAnalysisAgent
from tenders.services.openai_config import validated_https_api_base


class AgnesTenderAnalysisAgent(HybridTenderAnalysisAgent):
    """Use Agnes AI chat completions with the deterministic report as fallback."""

    def __init__(self, fallback_agent=None):
        super().__init__(fallback_agent=fallback_agent or RuleBasedTenderAnalysisAgent())

    def analyze(self, tender_text, company_profile=None):
        fallback_report = self.fallback_agent.analyze(
            tender_text=tender_text,
            company_profile=company_profile,
        )
        if not self._enabled():
            fallback_report['analysis_engine'] = 'rule_based'
            return fallback_report

        try:
            agnes_report = self._call_agnes(
                tender_text,
                company_profile or {},
                fallback_report,
            )
        except Exception as exc:
            fallback_report['analysis_engine'] = 'rule_based_agnes_fallback'
            fallback_report['analysis_warning'] = f'Agnes AI 分析暂不可用，已使用规则版结果：{exc}'
            return fallback_report

        merged = self._merge_reports(fallback_report, agnes_report)
        merged['agent_trace'][-1] = {'agent': 'Agnes AI深度审查Agent', 'status': 'completed'}
        merged['analysis_engine'] = 'agnes'
        return merged

    def _enabled(self):
        return bool(os.getenv('AGNES_API_KEY', '').strip()) and os.getenv(
            'AGNES_ANALYSIS_ENABLED',
            '1',
        ).strip().lower() not in {'0', 'false', 'no'}

    def _call_agnes(self, tender_text, company_profile, fallback_report):
        payload = {
            'model': os.getenv('AGNES_ANALYSIS_MODEL', 'agnes-2.0-flash'),
            'messages': [
                {'role': 'system', 'content': self._developer_prompt()},
                {
                    'role': 'user',
                    'content': json.dumps(
                        {
                            'company_profile': company_profile,
                            'fallback_report': fallback_report,
                            'tender_text': str(tender_text or '')[
                                : int(os.getenv('AGNES_ANALYSIS_TEXT_LIMIT', '18000'))
                            ],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            'response_format': {'type': 'json_object'},
            'temperature': 0.2,
        }
        base_url = validated_https_api_base(
            os.getenv('AGNES_API_BASE', 'https://apihub.agnes-ai.com/v1'),
            'AGNES_API_BASE',
        )
        request = urllib.request.Request(
            f'{base_url}/chat/completions',
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={
                'Authorization': f"Bearer {os.getenv('AGNES_API_KEY', '').strip()}",
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        timeout = int(os.getenv('AGNES_ANALYSIS_TIMEOUT', '60'))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - URL validated as HTTPS
                response_payload = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='ignore')[:300]
            raise RuntimeError(f'Agnes AI 请求失败({exc.code}) {detail}') from exc

        try:
            content = response_payload['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError('Agnes AI 响应中没有可解析文本') from exc
        return json.loads(self._strip_json_fence(content))

    def _strip_json_fence(self, content):
        text = str(content or '').strip()
        if text.startswith('```'):
            lines = text.splitlines()
            if lines and lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines).strip()
        return text
