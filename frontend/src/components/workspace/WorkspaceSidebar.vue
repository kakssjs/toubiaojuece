<template>
  <aside class="workspace-sidebar">
    <div class="workspace-brand">
      <span class="workspace-brand-mark">策</span>
      <div>
        <strong>策标</strong>
        <span>投标决策工作台</span>
      </div>
    </div>

    <nav class="workspace-nav" aria-label="工作台导航">
      <a
        v-for="item in navItems"
        :key="item.href"
        :href="item.href"
        :class="{ active: currentPage === item.key }"
      >
        {{ item.label }}
      </a>
    </nav>

    <div class="workspace-company-card">
      <span class="workspace-company-label">当前企业</span>
      <strong>{{ companyName || '未设置企业档案' }}</strong>
      <p>档案完整度 {{ profileCompleteness }}%</p>
    </div>
  </aside>
</template>

<script setup>
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
})
</script>
