<template>
  <section class="workspace-panel">
    <div class="workspace-panel-head">
      <div>
        <p class="section-kicker">Priority Queue</p>
        <h2>优先处理机会</h2>
      </div>
      <a class="table-link" href="/projects/">查看全部</a>
    </div>

    <div v-if="projects.length" class="workspace-opportunity-list">
      <article v-for="project in projects" :key="project.id" class="workspace-opportunity-row">
        <div>
          <strong>{{ project.name }}</strong>
          <span>{{ project.project_type || '未识别类型' }} · {{ project.company_name }}</span>
        </div>
        <b :class="decisionClass(project.decision)">{{ project.decision_label }}</b>
        <span class="score-chip">{{ project.match_score ?? '-' }}</span>
        <span :class="riskClass(project.risk_level)">{{ project.risk_level }}</span>
        <a class="table-link" :href="`/projects/${project.id}/`">查看项目</a>
      </article>
    </div>
    <div v-else class="workspace-empty">
      暂无已分析项目，先进入智能分析页上传第一份标书。
    </div>
  </section>
</template>

<script setup>
defineProps({
  projects: {
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
