const DECISION_PRIORITY = {
  recommended: 3,
  cautious: 2,
  not_recommended: 1,
  needs_review: 0,
  '': 0,
}

const RISK_PRIORITY = {
  高: 3,
  中: 2,
  低: 1,
  '-': 0,
}

export function rankWorkspaceProjects(projects) {
  return [...projects].sort((left, right) => {
    const decisionGap =
      (DECISION_PRIORITY[right.decision] || 0) - (DECISION_PRIORITY[left.decision] || 0)
    if (decisionGap !== 0) {
      return decisionGap
    }

    const scoreGap = Number(right.match_score || 0) - Number(left.match_score || 0)
    if (scoreGap !== 0) {
      return scoreGap
    }

    const riskGap = (RISK_PRIORITY[left.risk_level] || 0) - (RISK_PRIORITY[right.risk_level] || 0)
    if (riskGap !== 0) {
      return riskGap
    }

    return new Date(right.created_at || 0).getTime() - new Date(left.created_at || 0).getTime()
  })
}

export function buildWorkspaceMetrics(projects) {
  const total = projects.length
  const recommended = projects.filter((project) => project.decision === 'recommended').length
  const highRisk = projects.filter((project) => project.risk_level === '高').length
  const averageScore = total
    ? Math.round(
        projects.reduce((sum, project) => sum + Number(project.match_score || 0), 0) / total,
      )
    : 0

  return [
    {
      label: '待评估机会',
      value: String(total),
      hint: `${recommended} 个项目值得优先关注`,
    },
    {
      label: '推荐投标',
      value: String(recommended),
      hint: highRisk ? `${highRisk} 个项目需要同步看风险` : '当前推荐项目风险可控',
    },
    {
      label: '高风险项目',
      value: String(highRisk),
      hint: highRisk ? '建议优先复核高风险条款' : '暂无高风险项目',
    },
    {
      label: '平均匹配度',
      value: String(averageScore),
      hint: total ? '基于当前项目池动态计算' : '暂无可计算数据',
    },
  ]
}

export function buildRiskReminders(projects) {
  const highRiskProjects = projects.filter((project) => project.risk_level === '高')
  const recommendedProjects = projects.filter((project) => project.decision === 'recommended')

  const reminders = []

  if (highRiskProjects.length) {
    reminders.push({
      level: 'high',
      title: `高风险项目 ${highRiskProjects.length} 个`,
      description: '建议优先复核废标条款、付款条件和缺失材料。',
    })
  }

  if (recommendedProjects.length) {
    reminders.push({
      level: 'medium',
      title: `推荐项目 ${recommendedProjects.length} 个待跟进`,
      description: '建议尽快进入项目详情确认下一步动作和负责人。',
    })
  }

  return reminders
}
