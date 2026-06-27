<template>
  <section class="workspace-metrics">
    <article v-for="item in metrics" :key="item.label" class="workspace-metric-card">
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
      <small>{{ item.hint }}</small>
    </article>
  </section>
</template>

<script setup>
defineProps({
  metrics: {
    type: Array,
    default: () => [],
  },
})
</script>
