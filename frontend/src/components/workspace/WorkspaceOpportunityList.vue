<template>
  <section class="workspace-panel workspace-panel-priority">
    <div class="workspace-panel-head">
      <div>
        <h2>今日投标优先级建议</h2>
        <p>综合评分 = 中标概率 × 金额权重 × 战略匹配度</p>
      </div>
      <a class="table-link" href="/projects/">查看全部机会池 <ArrowRightIcon /></a>
    </div>

    <div v-if="projects.length" class="workspace-opportunity-table">
      <div class="workspace-opportunity-head" aria-hidden="true">
        <span>#</span><span>项目名称</span><span>项目类型</span><span>预算金额</span><span>综合评分</span><span>风险等级</span><span>推荐建议</span><span>下一步行动</span>
      </div>
      <a
        v-for="(project, index) in projects.slice(0, 6)"
        :key="project.id"
        class="workspace-opportunity-row"
        :href="`/projects/${project.id}/`"
      >
        <strong class="workspace-rank">{{ index + 1 }}</strong>
        <span class="workspace-opportunity-main">
          <strong>{{ project.name }}</strong>
          <small>{{ project.company_name || '采购单位待确认' }}</small>
        </span>
        <span>{{ project.project_type || '信息化项目' }}</span>
        <span>{{ formatBudget(project.budget_amount) }}</span>
        <strong class="workspace-score">{{ project.match_score ?? '—' }}</strong>
        <span :class="riskClass(project.risk_level)">{{ normalizedRisk(project.risk_level) }}</span>
        <b :class="decisionClass(project.decision)">{{ project.decision_label || '待评估' }}</b>
        <span class="workspace-next-action">{{ nextAction(project) }} <ChevronRightIcon /></span>
      </a>
    </div>
    <div v-else class="workspace-empty">
      暂无已分析项目。上传第一份标书后，AI 会自动生成投标优先级建议。
    </div>
  </section>
</template>

<script setup>
import { ArrowRightIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

defineProps({
  projects: { type: Array, default: () => [] },
  decisionClass: { type: Function, required: true },
  riskClass: { type: Function, required: true },
})

function formatBudget(value) {
  const amount = Number(value || 0)
  if (!amount) return '待确认'
  return `¥ ${(amount / 10000).toLocaleString('zh-CN')} 万`
}

function normalizedRisk(value) {
  if (['高', '中', '低'].includes(value)) return value
  return '待核验'
}

function nextAction(project) {
  if (project.decision === 'not_recommended') return '记录放弃原因'
  if (project.risk_level === '高') return '优先复核风险'
  if (project.overdue_task_count) return '处理逾期任务'
  if (project.pending_task_count) return '跟进待办任务'
  return '完善材料并推进'
}
</script>
