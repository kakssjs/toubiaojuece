<template>
  <section class="workspace-metrics" aria-label="经营指标">
    <article v-for="(item, index) in metrics" :key="index" class="workspace-metric-card">
      <div class="workspace-metric-label">
        <span>{{ item.label }}</span>
        <InformationCircleIcon aria-hidden="true" />
      </div>
      <strong>{{ metricValue(item, index) }}</strong>
      <small>{{ item.hint || '实时更新' }}</small>
    </article>
  </section>
</template>

<script setup>
import { InformationCircleIcon } from '@heroicons/vue/24/outline'

defineProps({ metrics: { type: Array, default: () => [] } })

function metricValue(item, index) {
  return index === 3 ? `${item.value ?? 0} 分` : `${item.value ?? 0} 个`
}
</script>
