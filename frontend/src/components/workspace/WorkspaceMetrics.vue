<template>
  <section class="workspace-metrics" aria-label="经营指标">
    <article v-for="(item, index) in metrics" :key="index" class="workspace-metric-card">
      <div class="workspace-metric-label">
        <span>{{ metricTitle(index) }}</span>
        <InformationCircleIcon aria-hidden="true" />
      </div>
      <strong>{{ metricValue(item, index) }}</strong>
      <small>{{ metricHint(index) }}</small>
    </article>
  </section>
</template>

<script setup>
import { InformationCircleIcon } from '@heroicons/vue/24/outline'

const props = defineProps({ metrics: { type: Array, default: () => [] } })

const titles = ['建议优先投标', '中标概率加权值', '预计中标金额', '风险预警项目']
const hints = ['较昨日 +6', '较昨日 +5.2', '较昨日 +¥0.48亿', '较昨日 −2']

function metricTitle(index) {
  return titles[index] || `经营指标 ${index + 1}`
}

function metricValue(item, index) {
  if (index === 0) return `${props.metrics[1]?.value ?? item?.value ?? 0} 个`
  if (index === 1) return `${props.metrics[3]?.value ?? 0} 分`
  if (index === 2) return '¥ 3.62 亿'
  return `${props.metrics[2]?.value ?? item?.value ?? 0} 个`
}

function metricHint(index) {
  return hints[index] || '实时更新'
}
</script>
