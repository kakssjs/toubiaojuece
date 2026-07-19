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
        scoring_breakdown = self._build_scoring_breakdown(qualification_match, experience_match, risks, classification)
        review_summary = self._build_review_summary(decision, material_checklist, risks, scoring_breakdown)

        return {
            "project_name": extracted["project_name"],
            "procurement_method": classification["procurement_method"],
            "project_type": classification["project_type"],
            "industry_type": classification["industry_type"],
            "budget_amount": extracted["budget_amount"],
            "highest_limit_amount": extracted["highest_limit_amount"],
            "region": extracted["region"],
            "deadline": extracted["deadline"],
            "match_score": decision["match_score"],
            "decision": decision["decision"],
            "decision_reason": decision["decision_reason"],
            "qualification_match": qualification_match,
            "experience_match": experience_match,
            "risks": risks,
            "material_checklist": material_checklist,
            "scoring_breakdown": scoring_breakdown,
            "review_summary": review_summary,
            "key_findings": self._build_key_findings(qualification_match, experience_match, risks),
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

        budget_amount = self._extract_amount(text, ("项目预算", "预算金额", "采购预算", "预算"))
        highest_limit_amount = self._extract_amount(text, ("最高限价", "最高投标限价"))
        if budget_amount is None:
            budget_amount = highest_limit_amount

        region = self._extract_region(text)
        deadline = self._extract_deadline(text)

        return {
            "project_name": project_name,
            "budget_amount": budget_amount,
            "highest_limit_amount": highest_limit_amount,
            "region": region,
            "deadline": deadline,
        }

    def _extract_amount(self, text, labels):
        label_pattern = "|".join(re.escape(label) for label in labels)
        match = re.search(
            rf"(?:{label_pattern})\s*(?:为|是)?\s*[:：]?\s*(?:人民币\s*)?"
            rf"([0-9][0-9,，]*(?:\.[0-9]+)?)\s*(亿元|亿|万元|万|元)",
            text,
        )
        if not match:
            return None
        amount = float(match.group(1).replace(",", "").replace("，", ""))
        multiplier = {
            "元": 1,
            "万": 10_000,
            "万元": 10_000,
            "亿": 100_000_000,
            "亿元": 100_000_000,
        }[match.group(2)]
        return int(amount * multiplier)

    def _extract_region(self, text):
        match = re.search(
            r"(?:建设地点|项目地点|实施地点|服务地点|项目地区|所在地区)"
            r"\s*(?:为|是)?\s*[:：]?\s*([^\s，,。；;]{2,40})",
            text,
        )
        if not match:
            return None
        location = match.group(1).strip("：:")
        province_names = (
            "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
            "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东",
            "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾", "内蒙古",
            "广西", "西藏", "宁夏", "新疆", "香港", "澳门",
        )
        return next((province for province in province_names if province in location), location)

    def _extract_deadline(self, text):
        label = r"(?:投标截止时间|响应文件提交截止时间|报名截止时间|截止时间)"
        chinese_match = re.search(
            label + r"\s*(?:为|是)?\s*[:：]?\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
            r"(?:\s*(\d{1,2})\s*[:：]\s*(\d{2}))?",
            text,
        )
        if chinese_match:
            year, month, day, hour, minute = chinese_match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d} {int(hour or 0):02d}:{int(minute or 0):02d}"

        numeric_match = re.search(
            label + r"\s*(?:为|是)?\s*[:：]?\s*(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})"
            r"(?:\s*(\d{1,2})\s*[:：]\s*(\d{2}))?",
            text,
        )
        if numeric_match:
            year, month, day, hour, minute = numeric_match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d} {int(hour or 0):02d}:{int(minute or 0):02d}"
        return None

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
        owned = list(company_profile.get("qualifications", []))

        matched = [item for item in required if any(self._qualifications_equivalent(item, value) for value in owned)]
        missing = [item for item in required if item not in owned]
        missing = [item for item in missing if item not in matched]

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
        compact_text = re.sub(r"\s+", "", text)
        known_qualifications = [
            "CMMI三级认证",
            "CMMI认证",
            "ISO9001质量管理体系认证",
            "信息安全管理体系认证",
            "ISO27001信息安全管理体系认证",
            "软件企业认证",
            "原厂授权函",
            "电子与智能化工程专业承包二级",
        ]
        return [item for item in known_qualifications if item in compact_text]

    def _qualifications_equivalent(self, required, owned):
        required_key = re.sub(r"[\s认证证书能力软件]", "", str(required)).lower()
        owned_key = re.sub(r"[\s认证证书能力软件]", "", str(owned)).lower()
        if required_key in owned_key or owned_key in required_key:
            return True
        if required.startswith("CMMI三级") and owned.startswith("CMMI三级"):
            return True
        if "ISO9001" in required.upper() and "ISO9001" in owned.upper():
            return True
        if ("信息安全管理体系" in required or "ISO27001" in required.upper()) and (
            "信息安全管理体系" in owned or "ISO27001" in owned.upper()
        ):
            return True
        return False

    def _match_experiences(self, text, company_profile):
        experiences = company_profile.get("project_experiences", [])
        business_scope = company_profile.get("business_scope", [])
        matched_cases = []

        for case in experiences:
            if any(keyword in text for keyword in self._experience_keywords(case)):
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

    def _experience_keywords(self, value):
        text = str(value or "")
        domain_keywords = (
            "智慧园区", "数字化平台", "数据中台", "数据驾驶舱", "智能客服",
            "知识库", "政务平台", "系统集成", "物联网", "云平台", "网络安全",
        )
        matches = [keyword for keyword in domain_keywords if keyword in text]
        return matches or self._split_keywords(text)

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

        default_items = [
            {"category": "主体材料", "name": "营业执照及法定代表人授权书", "status": "required"},
            {"category": "商务材料", "name": "报价明细表与服务承诺函", "status": "required"},
            {"category": "技术材料", "name": "技术/实施方案响应文件", "status": "required"},
        ]
        existing_names = {item["name"] for item in checklist}
        for item in default_items:
            if item["name"] not in existing_names:
                checklist.append(item)

        return checklist

    def _build_scoring_breakdown(self, qualification_match, experience_match, risks, classification):
        risk_score = max(0, 100 - sum(24 if risk["level"] == "高" else 14 if risk["level"] == "中" else 6 for risk in risks))
        technical_score = 82 if classification["project_type"] in {"软件信息化", "服务采购"} else 72
        business_score = round((qualification_match["score"] * 0.65) + (experience_match["score"] * 0.35))
        return [
            {
                "dimension": "资质匹配",
                "score": qualification_match["score"],
                "weight": "35%",
                "comment": "根据企业资质证书与招标资格要求匹配情况计算。",
            },
            {
                "dimension": "业绩支撑",
                "score": experience_match["score"],
                "weight": "25%",
                "comment": experience_match["summary"],
            },
            {
                "dimension": "风险可控",
                "score": risk_score,
                "weight": "25%",
                "comment": "根据高、中、低风险数量和影响程度扣分。",
            },
            {
                "dimension": "技术响应",
                "score": technical_score,
                "weight": "15%",
                "comment": f"项目类型识别为{classification['project_type']}，按常规响应难度估算。",
            },
            {
                "dimension": "商务完整性",
                "score": business_score,
                "weight": "参考",
                "comment": "综合资质和业绩基础，提示商务响应准备完整度。",
            },
        ]

    def _build_review_summary(self, decision, material_checklist, risks, scoring_breakdown):
        missing_count = sum(1 for item in material_checklist if item.get("status") == "missing")
        required_count = len(material_checklist)
        high_risk_count = sum(1 for risk in risks if risk["level"] == "高")
        average_dimension_score = round(sum(item["score"] for item in scoring_breakdown[:4]) / 4)
        if missing_count == 0:
            material_status = "材料基础较完整"
        elif missing_count <= 2:
            material_status = "存在少量材料缺口"
        else:
            material_status = "材料缺口较多"

        return {
            "conclusion": decision["decision_reason"],
            "material_status": material_status,
            "material_required_count": required_count,
            "material_missing_count": missing_count,
            "high_risk_count": high_risk_count,
            "average_dimension_score": average_dimension_score,
            "review_level": "可推进" if decision["decision"] == "推荐投标" else "需复核" if decision["decision"] == "谨慎投标" else "暂缓",
        }

    def _build_key_findings(self, qualification_match, experience_match, risks):
        findings = []
        if qualification_match["matched"]:
            findings.append(f"已匹配资质：{'、'.join(qualification_match['matched'][:3])}")
        if qualification_match["missing"]:
            findings.append(f"待补材料：{'、'.join(qualification_match['missing'][:3])}")
        findings.append(experience_match["summary"])
        high_risks = [risk["type"] for risk in risks if risk["level"] == "高"]
        if high_risks:
            findings.append(f"高风险项：{'、'.join(high_risks[:3])}")
        elif risks:
            findings.append("未发现必须立即中止投标的高风险项。")
        return findings
