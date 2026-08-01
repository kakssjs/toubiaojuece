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
        <div ref="topbarActions" class="workspace-topbar-actions">
          <button type="button" aria-label="搜索项目" :aria-expanded="searchOpen" @click="toggleSearch"><MagnifyingGlassIcon /></button>
          <button type="button" aria-label="站内通知" :aria-expanded="notificationsOpen" @click="toggleNotifications">
            <BellIcon /><span v-if="notificationUnreadCount">{{ notificationUnreadCount }}</span>
          </button>

          <section v-if="searchOpen" class="workspace-topbar-popover workspace-search-popover" aria-label="项目搜索">
            <label for="workspace-project-search">搜索项目</label>
            <div class="workspace-search-field">
              <MagnifyingGlassIcon />
              <input id="workspace-project-search" ref="searchInput" v-model.trim="searchQuery" type="search" placeholder="输入项目、企业、地区或类型" autocomplete="off" @keydown.enter.prevent="openFirstSearchResult" />
            </div>
            <div class="workspace-search-results">
              <a v-for="project in searchResults" :key="project.id" :href="`/projects/${project.id}/`">
                <strong>{{ project.name }}</strong>
                <span>{{ project.company_name || '未关联企业' }} · {{ project.region || '地区待确认' }}</span>
              </a>
              <p v-if="searchQuery && !searchResults.length">没有找到匹配项目</p>
              <p v-else-if="!searchQuery">输入关键词搜索全部项目</p>
            </div>
          </section>

          <section v-if="notificationsOpen" class="workspace-topbar-popover workspace-notification-popover" aria-label="站内通知">
            <header>
              <div><strong>站内通知</strong><span>{{ notificationUnreadCount }} 条未读</span></div>
              <a href="/projects/">查看全部项目</a>
            </header>
            <div class="workspace-notification-list">
              <article v-for="item in notifications" :key="item.id" :class="{ unread: item.reminder_unread }">
                <a :href="`/projects/${item.project_id}/`"><strong>{{ item.title }}</strong><span>{{ item.project_name }} · {{ taskReminderLabel(item) }}</span></a>
                <button v-if="item.reminder_unread" type="button" @click="markNotificationRead(item)">标为已读</button>
              </article>
              <p v-if="!notifications.length">当前没有新的任务提醒</p>
            </div>
          </section>
        </div>
      </header>

      <section class="workspace-hero">
        <div class="workspace-hero-copy">
          <p class="section-kicker">AI BID DECISION PLATFORM</p>
          <h1>AI驱动的招投标<br />智能决策平台</h1>
          <p>集中查看项目优先级、近期截止事项和投标进度，让团队先处理最重要的工作。</p>
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
      <WorkspaceBidWorkflow :projects="allProjects" />
      <WorkspaceAgentCenter :projects="allProjects" :csrf-token="csrfToken" />
      <WorkspaceAdvancedAiSuite :projects="allProjects" :csrf-token="csrfToken" />
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  ArrowUpTrayIcon,
  BellIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  UserGroupIcon,
} from '@heroicons/vue/24/outline'
import WorkspaceMetrics from './WorkspaceMetrics.vue'
import WorkspaceAgentCenter from './WorkspaceAgentCenter.vue'
import WorkspaceBidWorkflow from './WorkspaceBidWorkflow.vue'
import WorkspaceAdvancedAiSuite from './WorkspaceAdvancedAiSuite.vue'
import WorkspaceOpportunityList from './WorkspaceOpportunityList.vue'
import WorkspaceQuickActions from './WorkspaceQuickActions.vue'
import WorkspaceSidebar from './WorkspaceSidebar.vue'
import { formatWorkspaceDate, greetingForHour } from '../../workspace/time-greeting.js'

const props = defineProps({
  navItems: { type: Array, default: () => [] },
  currentPage: { type: String, default: '' },
  companyName: { type: String, default: '' },
  companyProfile: { type: Object, default: () => ({}) },
  profileCompleteness: { type: Number, default: 0 },
  metrics: { type: Array, default: () => [] },
  projects: { type: Array, default: () => [] },
  allProjects: { type: Array, default: () => [] },
  csrfToken: { type: String, default: '' },
  historicalCases: { type: Array, default: () => [] },
  historicalIndustries: { type: Array, default: () => [] },
  historicalTotal: { type: Number, default: 0 },
  historicalLoading: { type: Boolean, default: false },
  historicalError: { type: String, default: '' },
  reminders: { type: Array, default: () => [] },
  notifications: { type: Array, default: () => [] },
  notificationUnreadCount: { type: Number, default: 0 },
  markNotificationRead: { type: Function, required: true },
  taskReminderLabel: { type: Function, required: true },
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
const searchOpen = ref(false)
const notificationsOpen = ref(false)
const searchQuery = ref('')
const searchInput = ref(null)
const topbarActions = ref(null)
const searchResults = computed(() => {
  const query = searchQuery.value.toLocaleLowerCase()
  if (!query) return []
  return props.allProjects.filter((project) => [
    project.name, project.company_name, project.region, project.project_type,
    project.procurement_method, project.decision_label,
  ].some((value) => String(value || '').toLocaleLowerCase().includes(query))).slice(0, 8)
})

function toggleSearch() {
  searchOpen.value = !searchOpen.value
  notificationsOpen.value = false
  if (searchOpen.value) nextTick(() => searchInput.value?.focus())
}

function toggleNotifications() {
  notificationsOpen.value = !notificationsOpen.value
  searchOpen.value = false
}

function openFirstSearchResult() {
  const project = searchResults.value[0]
  if (project) window.location.assign(`/projects/${project.id}/`)
}

function closeTopbarPopovers(event) {
  if (event.key === 'Escape' || (event.type === 'click' && !topbarActions.value?.contains(event.target))) {
    searchOpen.value = false
    notificationsOpen.value = false
  }
}

let clockTimer

onMounted(() => {
  clockTimer = window.setInterval(() => {
    currentTime.value = new Date()
  }, 60_000)
  document.addEventListener('click', closeTopbarPopovers)
  document.addEventListener('keydown', closeTopbarPopovers)
})

onBeforeUnmount(() => {
  window.clearInterval(clockTimer)
  document.removeEventListener('click', closeTopbarPopovers)
  document.removeEventListener('keydown', closeTopbarPopovers)
})
</script>
