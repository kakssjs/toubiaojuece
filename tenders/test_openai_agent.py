import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from tenders.agents import TenderAnalysisAgent


class OpenAIHybridAgentTests(SimpleTestCase):
    def test_agent_falls_back_without_openai_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "", "OPENAI_ANALYSIS_ENABLED": "1"}, clear=False):
            report = TenderAnalysisAgent().analyze(
                tender_text="智慧园区数字化平台建设项目，公开招标，预算金额480万元。",
                company_profile={"qualifications": [], "project_experiences": []},
            )

        self.assertEqual(report["analysis_engine"], "rule_based")
        self.assertIn("match_score", report)

    def test_agent_merges_openai_structured_report_when_configured(self):
        openai_payload = {
            "output": [
                {
                    "content": [
                        {
                            "text": json.dumps(
                                {
                                    "project_name": "智慧园区数字化平台建设项目",
                                    "procurement_method": "公开招标",
                                    "project_type": "软件信息化",
                                    "industry_type": "信息化服务",
                                    "budget_amount": 4800000,
                                    "deadline": "2026年7月20日09:30",
                                    "match_score": 91,
                                    "decision": "推荐投标",
                                    "decision_reason": "资质和业绩匹配度高，可进入投标准备。",
                                    "qualification_match": {
                                        "status": "matched",
                                        "score": 92,
                                        "required": ["ISO9001质量管理体系认证"],
                                        "matched": ["ISO9001质量管理体系认证"],
                                        "missing": [],
                                    },
                                    "experience_match": {
                                        "score": 88,
                                        "matched_cases": ["智慧园区平台建设项目"],
                                        "summary": "存在可支撑评分的同类案例。",
                                    },
                                    "risks": [
                                        {
                                            "type": "商务风险",
                                            "level": "低",
                                            "description": "需确认保证金缴纳时间。",
                                            "source": "商务条款",
                                        }
                                    ],
                                    "material_checklist": [
                                        {"category": "主体材料", "name": "营业执照", "status": "required"}
                                    ],
                                    "scoring_breakdown": [
                                        {
                                            "dimension": "资质匹配",
                                            "score": 92,
                                            "weight": "35%",
                                            "comment": "资质匹配。",
                                        }
                                    ],
                                    "review_summary": {
                                        "conclusion": "建议推进。",
                                        "material_status": "材料基础较完整",
                                        "material_required_count": 1,
                                        "material_missing_count": 0,
                                        "high_risk_count": 0,
                                        "average_dimension_score": 90,
                                        "review_level": "可推进",
                                    },
                                    "key_findings": ["资质匹配度高"],
                                    "next_actions": ["进入投标报名流程"],
                                },
                                ensure_ascii=False,
                            )
                        }
                    ]
                }
            ]
        }
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(openai_payload).encode("utf-8")

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test", "OPENAI_ANALYSIS_ENABLED": "1"}, clear=False):
            with patch("urllib.request.urlopen", return_value=response):
                report = TenderAnalysisAgent().analyze(
                    tender_text="智慧园区数字化平台建设项目，公开招标，预算金额480万元。",
                    company_profile={
                        "qualifications": ["ISO9001质量管理体系认证"],
                        "project_experiences": ["智慧园区平台建设项目"],
                    },
                )

        self.assertEqual(report["analysis_engine"], "openai")
        self.assertEqual(report["match_score"], 91)
        self.assertEqual(report["review_summary"]["review_level"], "可推进")
        self.assertEqual(report["agent_trace"][-1]["agent"], "OpenAI深度审查Agent")
