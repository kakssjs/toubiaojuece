<template>
  <section class="workspace-page">
    <WorkspaceSidebar
      :nav-items="navItems"
      :current-page="currentPage"
      :company-name="companyName"
      :profile-completeness="profileCompleteness"
    />

    <div class="workspace-main">
      <header class="workspace-topbar">
        <div>
          <strong>{{ timeGreeting }}，欢迎回来</strong>
          <span>{{ currentDateLabel }}</span>
        </div>
        <div class="workspace-topbar-actions">
          <button type="button" aria-label="搜索"><MagnifyingGlassIcon /></button>
          <button type="button" aria-label="消息通知"><BellIcon /><span v-if="overdueTaskCount">{{ overdueTaskCount }}</span></button>
          <button type="button" aria-label="帮助"><QuestionMarkCircleIcon /></button>
        </div>
      </header>

      <section class="workspace-hero">
        <div class="workspace-hero-copy">
          <p class="section-kicker">EXECUTIVE BRIEFING</p>
          <h1>数据驱动投标决策，<br />让每一次投标更有把握</h1>
          <p>基于企业档案、历史业绩与实时风控的智能建议，助你优先投对标、少走弯路、赢在起点。</p>
          <div class="workspace-hero-actions">
            <a class="button-primary" href="/agent/"><ArrowUpTrayIcon />上传标书分析</a>
            <a class="button-secondary" href="/projects/">进入机会池</a>
          </div>
        </div>
        <aside class="workspace-decision-summary">
          <span>今日决策摘要</span>
          <ul>
            <li><CheckCircleIcon /><b>建议优先投标项目</b><strong>{{ recommendedCount }} 个</strong></li>
            <li><ExclamationTriangleIcon /><b>高风险项目</b><strong>{{ highRiskCount }} 个</strong></li>
            <li><ClockIcon /><b>待跟进任务</b><strong>{{ pendingTaskCount }} 项</strong></li>
            <li><UserGroupIcon /><b>已逾期任务</b><strong>{{ overdueTaskCount }} 项</strong></li>
          </ul>
        </aside>
      </section>

      <WorkspaceMetrics :metrics="metrics" />
      <WorkspaceOpportunityList
        :projects="projects"
        :decision-class="decisionClass"
        :risk-class="riskClass"
      />
      <WorkspaceQuickActions :reminders="reminders" />
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  ArrowUpTrayIcon,
  BellIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  QuestionMarkCircleIcon,
  UserGroupIcon,
} from '@heroicons/vue/24/outline'
import WorkspaceMetrics from './WorkspaceMetrics.vue'
import WorkspaceOpportunityList from './WorkspaceOpportunityList.vue'
import WorkspaceQuickActions from './WorkspaceQuickActions.vue'
import WorkspaceSidebar from './WorkspaceSidebar.vue'
import { formatWorkspaceDate, greetingForHour } from '../../workspace/time-greeting.js'

const props = defineProps({
  navItems: { type: Array, default: () => [] },
  currentPage: { type: String, default: '' },
  companyName: { type: String, default: '' },
  profileCompleteness: { type: Number, default: 0 },
  metrics: { type: Array, default: () => [] },
  projects: { type: Array, default: () => [] },
  reminders: { type: Array, default: () => [] },
  decisionClass: { type: Function, required: true },
  riskClass: { type: Function, required: true },
})

const recommendedCount = computed(() => props.projects.filter((item) => item.decision === 'recommended').length)
const highRiskCount = computed(() => props.projects.filter((item) => item.risk_level === '高').length)
const pendingTaskCount = computed(() => props.projects.reduce((sum, item) => sum + Number(item.pending_task_count || 0), 0))
const overdueTaskCount = computed(() => props.projects.reduce((sum, item) => sum + Number(item.overdue_task_count || 0), 0))
const currentTime = ref(new Date())
const timeGreeting = computed(() => greetingForHour(currentTime.value.getHours()))
const currentDateLabel = computed(() => formatWorkspaceDate(currentTime.value))

let clockTimer

onMounted(() => {
  clockTimer = window.setInterval(() => {
    currentTime.value = new Date()
  }, 60_000)
})

onBeforeUnmount(() => {
  window.clearInterval(clockTimer)
})
</script>
