def answer_report_question(report, question):
    normalized_question = _normalize_question(question)
    raw_report = report.raw_report or {}

    if _matches(normalized_question, ['能投', '是否能投', '能不能投', '建议投', '值得投', '投吗']):
        return _decision_answer(report)

    if _matches(normalized_question, ['材料', '缺失', '补充', '清单', '资质']):
        return _material_answer(report, raw_report)

    if _matches(normalized_question, ['风险', '废标', '高风险', '注意']):
        return _risk_answer(report)

    if _matches(normalized_question, ['下一步', '怎么做', '动作', '跟进']):
        return _next_action_answer(report)

    if _matches(normalized_question, ['业绩', '案例', '经验']):
        return _experience_answer(raw_report)

    return _fallback_answer(report, raw_report)


def _decision_answer(report):
    answer = (
        f'当前 AI 建议为「{report.get_decision_display()}」，综合匹配评分为 {report.match_score} 分。'
        f'{report.summary or "系统暂未生成更详细的决策摘要。"}'
    )
    references = ['AI投标建议', '综合匹配评分', '报告摘要']
    if report.risks:
        answer += f' 报告同时识别到 {len(report.risks)} 项风险，建议在投标决策前完成复核。'
        references.append('风险清单')
    return _payload(answer, references)


def _material_answer(report, raw_report):
    missing_materials = [str(item) for item in report.missing_materials or [] if str(item).strip()]
    checklist = raw_report.get('material_checklist', [])
    checklist_names = [
        f"{item.get('category', '材料')}：{item.get('name')}"
        for item in checklist
        if isinstance(item, dict) and item.get('name')
    ]
    pieces = []
    if missing_materials:
        pieces.append('当前缺失或需要重点补充的材料包括：' + '、'.join(missing_materials) + '。')
    if checklist_names:
        pieces.append('报告材料清单中还包含：' + '、'.join(checklist_names) + '。')
    if not pieces:
        pieces.append('当前报告暂未识别到明确缺失材料，但仍建议人工复核资格证明、商务响应和签章格式。')
    return _payload(''.join(pieces), ['缺失材料', '材料清单', '资质匹配'])


def _risk_answer(report):
    risks = report.risks or []
    if not risks:
        return _payload('当前报告暂未识别到明确风险项，但仍建议复核废标条款、付款条件、截止时间和保证金要求。', ['风险清单'])

    descriptions = []
    for risk in risks:
        if not isinstance(risk, dict):
            continue
        risk_type = risk.get('type') or '风险项'
        level = risk.get('level') or '待复核'
        description = risk.get('description') or ''
        descriptions.append(f'{risk_type}（{level}）：{description}')

    return _payload('当前需要关注的风险包括：' + '；'.join(descriptions) + '。', ['风险清单'])


def _next_action_answer(report):
    actions = [str(item) for item in report.next_actions or [] if str(item).strip()]
    if not actions:
        return _payload('当前报告暂未生成下一步动作，建议先复核资质缺口、风险条款和投标截止时间。', ['下一步动作'])
    return _payload('建议优先推进：' + '；'.join(actions) + '。', ['下一步动作'])


def _experience_answer(raw_report):
    experience_match = raw_report.get('experience_match', {})
    if not isinstance(experience_match, dict):
        experience_match = {}
    summary = experience_match.get('summary') or '当前报告暂未生成业绩匹配摘要。'
    cases = [str(item) for item in experience_match.get('matched_cases', []) if str(item).strip()]
    answer = summary
    if cases:
        answer += ' 可参考的匹配案例包括：' + '、'.join(cases) + '。'
    return _payload(answer, ['业绩匹配'])


def _fallback_answer(report, raw_report):
    qualification_match = raw_report.get('qualification_match', {})
    if not isinstance(qualification_match, dict):
        qualification_match = {}
    answer = (
        f'我可以基于当前报告回答投标建议、缺失材料、风险清单、业绩匹配和下一步动作。'
        f'本项目当前建议为「{report.get_decision_display()}」，匹配评分为 {report.match_score} 分。'
    )
    if qualification_match.get('status'):
        answer += f" 资质匹配状态为 {qualification_match.get('status')}。"
    return _payload(answer, ['报告摘要', '资质匹配', '风险清单'])


def _payload(answer, references):
    return {
        'answer': answer,
        'references': references,
    }


def _normalize_question(question):
    return str(question or '').strip().lower().replace('？', '?')


def _matches(question, keywords):
    return any(keyword.lower() in question for keyword in keywords)
