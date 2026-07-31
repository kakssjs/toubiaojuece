<template>
  <section class="workspace-urgency" aria-label="近期紧急事项">
    <div class="workspace-urgency-head">
      <h2>近期紧急事项</h2>
      <span>{{ reminders.length }}</span>
    </div>
    <div v-if="reminders.length" class="workspace-urgency-grid">
      <a
        v-for="item in reminders"
        :key="item.title"
        href="/projects/"
        :class="`urgency-item urgency-item--${item.level}`"
      >
        <ExclamationTriangleIcon v-if="item.level === 'high'" class="urgency-icon danger" aria-hidden="true" />
        <ClockIcon v-else class="urgency-icon warning" aria-hidden="true" />
        <span>
          <strong>{{ item.title }}</strong>
          <small>{{ item.description }}</small>
        </span>
        <ArrowRightIcon />
      </a>
    </div>
    <div v-else class="workspace-urgency-grid">
      <a href="/agent/">
        <DocumentArrowUpIcon class="urgency-icon primary" aria-hidden="true" />
        <span><strong>上传标书开始分析</strong><small>完成首次分析后，紧急提醒会在这里显示</small></span>
        <ArrowRightIcon />
      </a>
    </div>
  </section>
</template>

<script setup>
import {
  ArrowRightIcon,
  ClockIcon,
  DocumentArrowUpIcon,
  ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline'

defineProps({ reminders: { type: Array, default: () => [] } })
</script>
