import re


class TenderAnalysisAgent:
    """Local rule-based MVP for tender analysis.

    This class keeps the same orchestration shape expected from an LLM-powered
    agent, while remaining deterministic and runnable without external keys.
    """

    def analyze(self, tender_text, company_profile=None):
        company_profile = company_profile or {}
        text = self._normalize_text(tender_text)

        extracted = self._extract_information(text)
        classification = self._classify_tender(text)
        qualification_match = self._match_qualifications(text, company_profile)
        experience_match = self._match_experiences(text, company_profile)
        risks = self._identify_risks(text, qualification_match, company_profile)
        decision = self._make_decision(qualification_match, experience_match, risks, classification)
        material_checklist = self._build_material_checklist(text, qualification_match)

        return {
            "project_name": extracted["project_name"],
            "procurement_method": classification["procurement_method"],
            "project_type": classification["project_type"],
            "industry_type": classification["industry_type"],
            "budget_amount": extracted["budget_amount"],
            "deadline": extracted["deadline"],
            "match_score": decision["match_score"],
            "decision": decision["decision"],
            "decision_reason": decision["decision_reason"],
            "qualification_match": qualification_match,
            "experience_match": experience_match,
            "risks": risks,
            "material_checklist": material_checklist,
            "next_actions": decision["next_actions"],
            "agent_trace": [
                {"agent": "信息抽取Agent", "status": "completed"},
                {"agent": "招标分类Agent", "status": "completed"},
                {"agent": "资质匹配Agent", "status": "completed"},
                {"agent": "业绩匹配Agent", "status": "completed"},
                {"agent": "风险识别Agent", "status": "completed"},
                {"agent": "投标决策Agent", "status": "completed"},
            ],
        }

    def _normalize_text(self, tender_text):
        return re.sub(r"\s+", " ", str(tender_text or "")).strip()

    def _extract_information(self, text):
        project_name = None
        project_match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9（）()·\-]+项目)", text)
        if project_match:
            project_name = project_match.group(1)

        budget_amount = None
        budget_match = re.search(r"(?:预算金额|最高限价|预算)[^\d]*(\d+(?:\.\d+)?)\s*(万元|万|元)", text)
        if budget_match:
            amount = float(budget_match.group(1))
            unit = budget_match.group(2)
            budget_amount = int(amount * 10000) if unit in {"万元", "万"} else int(amount)

        deadline = None
        deadline_match = re.search(r"(?:投标截止时间|截止时间)[^0-9]*(\d{4}年\d{1,2}月\d{1,2}日\s*\d{1,2}[:：]\d{2})", text)
        if deadline_match:
            deadline = deadline_match.group(1).replace(" ", "")

        return {
            "project_name": project_name,
            "budget_amount": budget_amount,
            "deadline": deadline,
        }

    def _classify_tender(self, text):
        procurement_method = "未识别"
        if "公开招标" in text:
            procurement_method = "公开招标"
        elif "竞争性磋商" in text:
            procurement_method = "竞争性磋商"
        elif "邀请招标" in text:
            procurement_method = "邀请招标"
        elif "询价" in text:
            procurement_method = "询价采购"

        if any(keyword in text for keyword in ["软件", "系统集成", "数字化", "平台", "信息化"]):
            project_type = "软件信息化"
            industry_type = "信息化服务"
        elif any(keyword in text for keyword in ["施工", "工程", "建设工程"]):
            project_type = "工程建设"
            industry_type = "工程"
        elif any(keyword in text for keyword in ["设备", "货物", "采购设备"]):
            project_type = "货物采购"
            industry_type = "货物"
        else:
            project_type = "服务采购"
            industry_type = "综合服务"

        return {
            "procurement_method": procurement_method,
            "project_type": project_type,
            "industry_type": industry_type,
        }

    def _match_qualifications(self, text, company_profile):
        required = self._find_required_qualifications(text)
        owned = set(company_profile.get("qualifications", []))

        matched = [item for item in required if item in owned]
        missing = [item for item in required if item not in owned]

        if not required:
            status = "unknown"
            score = 60
        elif missing:
            status = "partial"
            score = round(len(matched) / len(required) * 100)
        else:
            status = "matched"
            score = 100

        return {
            "status": status,
            "score": score,
            "required": required,
            "matched": matched,
            "missing": missing,
        }

    def _find_required_qualifications(self, text):
        known_qualifications = [
            "CMMI三级认证",
            "CMMI认证",
            "ISO9001质量管理体系认证",
            "软件企业认证",
            "原厂授权函",
            "电子与智能化工程专业承包二级",
        ]
        return [item for item in known_qualifications if item in text]

    def _match_experiences(self, text, company_profile):
        experiences = company_profile.get("project_experiences", [])
        business_scope = company_profile.get("business_scope", [])
        matched_cases = []

        for case in experiences:
            if any(keyword in text for keyword in self._split_keywords(case)):
                matched_cases.append(case)

        if not matched_cases:
            for scope in business_scope:
                if scope in text:
                    matched_cases.extend(experiences[:1])
                    break

        score = 80 if matched_cases else 45
        return {
            "score": score,
            "matched_cases": matched_cases,
            "summary": "存在类似项目经验" if matched_cases else "未识别到明确类似项目经验",
        }

    def _split_keywords(self, value):
        return [part for part in re.split(r"[\s、,，\-]+", str(value)) if len(part) >= 2]

    def _identify_risks(self, text, qualification_match, company_profile):
        risks = []

        for item in qualification_match["missing"]:
            risks.append(
                {
                    "type": "资质材料风险",
                    "level": "高" if item in {"原厂授权函", "CMMI三级认证"} else "中",
                    "description": f"招标文件要求提供{item}，企业档案中暂未匹配。",
                    "source": "资格要求",
                }
            )

        if any(keyword in text for keyword in ["保证金", "投标保证金"]):
            risks.append(
                {
                    "type": "保证金风险",
                    "level": "低",
                    "description": "文件包含投标保证金要求，需在截止时间前完成缴纳和凭证准备。",
                    "source": "商务条款",
                }
            )

        if any(keyword in text for keyword in ["质保期满", "验收合格后", "分阶段付款"]):
            risks.append(
                {
                    "type": "付款风险",
                    "level": "中",
                    "description": "付款条件存在验收后或质保期后支付安排，需评估现金流压力。",
                    "source": "付款条件",
                }
            )

        forbidden_conditions = company_profile.get("forbidden_conditions", [])
        for condition in forbidden_conditions:
            if condition and condition in text:
                risks.append(
                    {
                        "type": "禁投条件风险",
                        "level": "高",
                        "description": f"触发企业禁投条件：{condition}。",
                        "source": "企业能力档案",
                    }
                )

        return risks

    def _make_decision(self, qualification_match, experience_match, risks, classification):
        risk_penalty = sum(18 if risk["level"] == "高" else 10 if risk["level"] == "中" else 4 for risk in risks)
        base_score = round(qualification_match["score"] * 0.45 + experience_match["score"] * 0.3 + 20)
        if classification["project_type"] == "软件信息化":
            base_score += 5
        match_score = max(0, min(100, base_score - risk_penalty))

        high_risk_count = sum(1 for risk in risks if risk["level"] == "高")
        if match_score >= 80 and high_risk_count == 0:
            decision = "推荐投标"
        elif match_score >= 55:
            decision = "谨慎投标"
        else:
            decision = "不建议投标"

        next_actions = []
        for item in qualification_match["missing"]:
            next_actions.append(f"补充或确认{item}是否为强制要求")
        if any(risk["type"] == "付款风险" for risk in risks):
            next_actions.append("复核付款条件对现金流和履约周期的影响")
        if any(risk["type"] == "保证金风险" for risk in risks):
            next_actions.append("确认保证金缴纳方式、金额和截止时间")
        if not next_actions:
            next_actions.append("进入投标报名和标书准备流程")

        return {
            "decision": decision,
            "match_score": match_score,
            "decision_reason": self._decision_reason(decision, qualification_match, experience_match, risks),
            "next_actions": next_actions,
        }

    def _decision_reason(self, decision, qualification_match, experience_match, risks):
        missing_count = len(qualification_match["missing"])
        risk_count = len(risks)
        if decision == "推荐投标":
            return "企业资质与业绩匹配度较高，未识别到影响投标的高风险事项。"
        if decision == "谨慎投标":
            return f"项目方向具备匹配基础，但存在{missing_count}项资质或材料缺口、{risk_count}项风险，建议复核后再决策。"
        return f"当前匹配度较低或风险较高，存在{missing_count}项关键缺口，建议暂缓投标。"

    def _build_material_checklist(self, text, qualification_match):
        checklist = [
            {"category": "资格材料", "name": item, "status": "missing"}
            for item in qualification_match["missing"]
        ]

        if "类似项目业绩" in text:
            checklist.append({"category": "业绩材料", "name": "近三年类似项目合同或验收证明", "status": "required"})
        if "保证金" in text:
            checklist.append({"category": "商务材料", "name": "投标保证金缴纳凭证", "status": "required"})
        if "评分标准" in text:
            checklist.append({"category": "技术材料", "name": "技术方案与评分响应表", "status": "required"})

        return checklist
