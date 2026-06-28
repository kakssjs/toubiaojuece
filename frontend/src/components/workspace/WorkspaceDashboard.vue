<template>
  <section class="workspace-page">
    <WorkspaceSidebar
      :nav-items="navItems"
      :current-page="currentPage"
      :company-name="companyName"
      :profile-completeness="profileCompleteness"
    />

    <div class="workspace-main">
      <header class="workspace-hero">
        <div class="workspace-hero-copy">
          <p class="section-kicker">Executive Dashboard</p>
          <div class="workspace-hero-badges" aria-label="工作台能力">
            <span>实时项目池</span>
            <span>AI投标建议</span>
            <span>风险优先级</span>
          </div>
          <h1>今天优先处理哪些投标机会？</h1>
          <p>
            按匹配度、风险等级和项目状态聚合当前机会池，帮助投标团队先处理最值得投入的项目。
          </p>
        </div>
        <div class="workspace-hero-actions">
          <a class="button-primary" href="/agent/">上传标书分析</a>
          <a class="button-secondary" href="/projects/">查看项目看板</a>
        </div>
      </header>

      <WorkspaceMetrics :metrics="metrics" />

      <div class="workspace-content">
        <WorkspaceOpportunityList
          :projects="projects"
          :decision-class="decisionClass"
          :risk-class="riskClass"
        />
        <WorkspaceQuickActions :reminders="reminders" />
      </div>
    </div>
  </section>
</template>

<script setup>
import WorkspaceMetrics from './WorkspaceMetrics.vue'
import WorkspaceOpportunityList from './WorkspaceOpportunityList.vue'
import WorkspaceQuickActions from './WorkspaceQuickActions.vue'
import WorkspaceSidebar from './WorkspaceSidebar.vue'

defineProps({
  navItems: {
    type: Array,
    default: () => [],
  },
  currentPage: {
    type: String,
    default: '',
  },
  companyName: {
    type: String,
    default: '',
  },
  profileCompleteness: {
    type: Number,
    default: 0,
  },
  metrics: {
    type: Array,
    default: () => [],
  },
  projects: {
    type: Array,
    default: () => [],
  },
  reminders: {
    type: Array,
    default: () => [],
  },
  decisionClass: {
    type: Function,
    required: true,
  },
  riskClass: {
    type: Function,
    required: true,
  },
})
</script>
