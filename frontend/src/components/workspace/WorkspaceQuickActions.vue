<template>
  <section class="workspace-urgency" aria-label="近期紧急事项">
    <div class="workspace-urgency-head">
      <h2>近期紧急事项</h2>
      <span>{{ reminders.length || 4 }}</span>
    </div>
    <div class="workspace-urgency-grid">
      <a href="/projects/">
        <ClockIcon class="urgency-icon danger" />
        <span><strong>4 个项目临近截止</strong><small>未来 3 天内需要提交或补齐材料</small></span>
        <ArrowRightIcon />
      </a>
      <a href="/projects/">
        <ExclamationTriangleIcon class="urgency-icon warning" />
        <span><strong>{{ reminders.length || 2 }} 个风险需要复核</strong><small>付款条件与资质要求存在预警</small></span>
        <ArrowRightIcon />
      </a>
      <a href="/projects/">
        <UserGroupIcon class="urgency-icon primary" />
        <span><strong>7 个项目待团队跟进</strong><small>部分项目已超过建议跟进时间</small></span>
        <ArrowRightIcon />
      </a>
      <a href="/agent/">
        <DocumentArrowUpIcon class="urgency-icon primary" />
        <span><strong>2 份标书待提交</strong><small>建议在截止前完成最终检查</small></span>
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
  UserGroupIcon,
} from '@heroicons/vue/24/outline'

defineProps({ reminders: { type: Array, default: () => [] } })
</script>
