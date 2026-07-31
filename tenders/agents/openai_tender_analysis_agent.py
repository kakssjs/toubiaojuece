import json
import os
import urllib.error
import urllib.request

from .tender_analysis_agent import TenderAnalysisAgent as RuleBasedTenderAnalysisAgent
from tenders.services.openai_config import openai_responses_url


class HybridTenderAnalysisAgent:
    """Use OpenAI for richer bid review when configured, with a local fallback."""

    def __init__(self, fallback_agent=None):
        self.fallback_agent = fallback_agent or RuleBasedTenderAnalysisAgent()

    def analyze(self, tender_text, company_profile=None):
        fallback_report = self.fallback_agent.analyze(tender_text=tender_text, company_profile=company_profile)
        if not self._enabled():
            fallback_report["analysis_engine"] = "rule_based"
            return fallback_report

        try:
            ai_report = self._call_openai(tender_text, company_profile or {}, fallback_report)
        except Exception as exc:
            fallback_report["analysis_engine"] = "rule_based_fallback"
            fallback_report["analysis_warning"] = f"OpenAI分析暂不可用，已使用规则版结果：{exc}"
            return fallback_report

        merged = self._merge_reports(fallback_report, ai_report)
        merged["analysis_engine"] = "openai"
        return merged

    def _enabled(self):
        return bool(os.getenv("OPENAI_API_KEY", "").strip()) and os.getenv("OPENAI_ANALYSIS_ENABLED", "1").strip() not in {
            "0",
            "false",
            "False",
            "no",
        }

    def _call_openai(self, tender_text, company_profile, fallback_report):
        payload = {
            "model": os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-5.6"),
            "reasoning": {"effort": os.getenv("OPENAI_ANALYSIS_REASONING_EFFORT", "low")},
            "input": [
                {
                    "role": "developer",
                    "content": self._developer_prompt(),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "company_profile": company_profile,
                            "fallback_report": fallback_report,
                            "tender_text": str(tender_text or "")[: int(os.getenv("OPENAI_ANALYSIS_TEXT_LIMIT", "18000"))],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "tender_review_report",
                    "strict": True,
                    "schema": self._schema(),
                }
            },
        }

        request = urllib.request.Request(
            openai_responses_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '').strip()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        timeout = int(os.getenv("OPENAI_ANALYSIS_TIMEOUT", "45"))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:300]
            raise RuntimeError(f"OpenAI请求失败({exc.code}) {detail}") from exc
        return json.loads(self._extract_output_text(response_payload))

    def _developer_prompt(self):
        return (
            "你是企业投标审查专家。请基于招标文本、企业档案和规则版初稿，输出严格 JSON。"
            "不要编造不存在的证书、业绩或金额；不确定时写“需人工复核”。"
            "风险要具体到条款/材料/商务影响；下一步动作要能直接交给投标经理执行。"
            "所有字段必须使用中文。"
        )

    def _schema(self):
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "project_name",
                "procurement_method",
                "project_type",
                "industry_type",
                "budget_amount",
                "deadline",
                "match_score",
                "decision",
                "decision_reason",
                "qualification_match",
                "experience_match",
                "risks",
                "material_checklist",
                "scoring_breakdown",
                "review_summary",
                "key_findings",
                "next_actions",
            ],
            "properties": {
                "project_name": {"type": ["string", "null"]},
                "procurement_method": {"type": "string"},
                "project_type": {"type": "string"},
                "industry_type": {"type": "string"},
                "budget_amount": {"type": ["number", "null"]},
                "deadline": {"type": ["string", "null"]},
                "match_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "decision": {"type": "string", "enum": ["推荐投标", "谨慎投标", "不建议投标", "人工复核"]},
                "decision_reason": {"type": "string"},
                "qualification_match": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["status", "score", "required", "matched", "missing"],
                    "properties": {
                        "status": {"type": "string"},
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "required": {"type": "array", "items": {"type": "string"}},
                        "matched": {"type": "array", "items": {"type": "string"}},
                        "missing": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "experience_match": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["score", "matched_cases", "summary"],
                    "properties": {
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "matched_cases": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"},
                    },
                },
                "risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["type", "level", "description", "source"],
                        "properties": {
                            "type": {"type": "string"},
                            "level": {"type": "string", "enum": ["高", "中", "低"]},
                            "description": {"type": "string"},
                            "source": {"type": "string"},
                        },
                    },
                },
                "material_checklist": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["category", "name", "status"],
                        "properties": {
                            "category": {"type": "string"},
                            "name": {"type": "string"},
                            "status": {"type": "string", "enum": ["missing", "required", "ready"]},
                        },
                    },
                },
                "scoring_breakdown": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["dimension", "score", "weight", "comment"],
                        "properties": {
                            "dimension": {"type": "string"},
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "weight": {"type": "string"},
                            "comment": {"type": "string"},
                        },
                    },
                },
                "review_summary": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "conclusion",
                        "material_status",
                        "material_required_count",
                        "material_missing_count",
                        "high_risk_count",
                        "average_dimension_score",
                        "review_level",
                    ],
                    "properties": {
                        "conclusion": {"type": "string"},
                        "material_status": {"type": "string"},
                        "material_required_count": {"type": "integer", "minimum": 0},
                        "material_missing_count": {"type": "integer", "minimum": 0},
                        "high_risk_count": {"type": "integer", "minimum": 0},
                        "average_dimension_score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "review_level": {"type": "string"},
                    },
                },
                "key_findings": {"type": "array", "items": {"type": "string"}},
                "next_actions": {"type": "array", "items": {"type": "string"}},
            },
        }

    def _extract_output_text(self, payload):
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]

        chunks = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if isinstance(content.get("text"), str):
                    chunks.append(content["text"])
        if not chunks:
            raise RuntimeError("OpenAI响应中没有可解析文本")
        return "".join(chunks)

    def _merge_reports(self, fallback, ai_report):
        merged = dict(fallback)
        for key, value in ai_report.items():
            if value not in (None, "", [], {}):
                merged[key] = value
        merged["agent_trace"] = [
            *fallback.get("agent_trace", []),
            {"agent": "OpenAI深度审查Agent", "status": "completed"},
        ]
        return merged
