import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildWorkspaceMetrics,
  buildRiskReminders,
  rankWorkspaceProjects,
} from './dashboard-data.js'

const projects = [
  {
    id: 1,
    name: '智慧园区综合运维平台',
    decision: 'recommended',
    decision_label: '推荐投标',
    match_score: 92,
    risk_level: '低',
    status: 'analyzed',
    status_label: '已分析',
    project_type: '软件信息化',
    company_name: '小苏科技',
    budget_amount: 4800000,
    created_at: '2026-06-26T09:00:00',
    report_id: 11,
  },
  {
    id: 2,
    name: '政务数据治理服务采购',
    decision: 'cautious',
    decision_label: '谨慎投标',
    match_score: 78,
    risk_level: '高',
    status: 'pending',
    status_label: '待分析',
    project_type: '数据服务',
    company_name: '小苏科技',
    budget_amount: 2200000,
    created_at: '2026-06-27T10:00:00',
    report_id: 12,
  },
  {
    id: 3,
    name: '企业门户升级项目',
    decision: 'recommended',
    decision_label: '推荐投标',
    match_score: 88,
    risk_level: '中',
    status: 'analyzed',
    status_label: '已分析',
    project_type: '软件开发',
    company_name: '小苏科技',
    budget_amount: 960000,
    created_at: '2026-06-25T08:00:00',
    report_id: 13,
  },
]

test('rankWorkspaceProjects puts recommended and higher scores first', () => {
  const ranked = rankWorkspaceProjects(projects)

  assert.equal(ranked[0].id, 1)
  assert.equal(ranked[1].id, 3)
  assert.equal(ranked[2].id, 2)
})

test('buildWorkspaceMetrics summarizes project counts and average score', () => {
  const metrics = buildWorkspaceMetrics(projects)

  assert.deepEqual(metrics.map((item) => item.value), ['3', '2', '1', '86'])
  assert.equal(metrics[0].label, '待评估机会')
  assert.equal(metrics[1].label, '推荐投标')
  assert.equal(metrics[2].label, '高风险项目')
  assert.equal(metrics[3].label, '平均匹配度')
})

test('buildRiskReminders keeps only actionable alerts', () => {
  const reminders = buildRiskReminders(projects)

  assert.equal(reminders.length, 2)
  assert.match(reminders[0].title, /高风险项目/)
  assert.match(reminders[1].title, /待跟进/)
})
