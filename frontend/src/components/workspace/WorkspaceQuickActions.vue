<template>
  <div class="workspace-rail">
    <section class="workspace-panel workspace-panel-compact">
      <div class="workspace-panel-head compact">
        <div>
          <p class="section-kicker">Quick Analysis</p>
          <h2>快速分析</h2>
        </div>
      </div>
      <p class="workspace-rail-copy">直接进入智能分析流程，继续上传 PDF 或粘贴招标文本。</p>
      <div class="workspace-rail-actions">
        <a class="button-primary" href="/agent/">上传标书分析</a>
        <a class="button-secondary" href="/company/">维护企业档案</a>
      </div>
    </section>

    <section class="workspace-panel workspace-panel-compact">
      <div class="workspace-panel-head compact">
        <div>
          <p class="section-kicker">Risk Alerts</p>
          <h2>风险提醒</h2>
        </div>
      </div>

      <div v-if="reminders.length" class="workspace-reminders">
        <article
          v-for="item in reminders"
          :key="item.title"
          :class="['workspace-reminder', `workspace-reminder-${item.level}`]"
        >
          <strong>{{ item.title }}</strong>
          <p>{{ item.description }}</p>
        </article>
      </div>
      <div v-else class="workspace-empty">当前没有需要优先提醒的高风险事项。</div>
    </section>
  </div>
</template>

<script setup>
defineProps({
  reminders: {
    type: Array,
    default: () => [],
  },
})
</script>
