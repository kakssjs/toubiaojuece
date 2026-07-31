<template>
  <aside class="workspace-sidebar">
    <a class="workspace-brand" href="/" aria-label="策标经营总览">
      <img :src="brandMark" alt="" />
      <div>
        <strong>策标</strong>
        <span>智能投标决策</span>
      </div>
    </a>

    <nav class="workspace-nav" aria-label="工作台导航">
      <a
        v-for="item in navItems"
        :key="item.label"
        :href="item.href"
        :class="{ active: currentPage === item.key && item.label === activeLabel(item) }"
      >
        <component :is="iconFor(item)" aria-hidden="true" />
        <span>{{ item.label }}</span>
      </a>
    </nav>

    <div class="workspace-company-card">
      <span class="workspace-company-label">当前企业</span>
      <strong>{{ companyName || '尚未设置企业档案' }}</strong>
      <div class="workspace-company-progress">
        <span>档案完整度</span>
        <b>{{ profileCompleteness }}%</b>
      </div>
      <div class="workspace-profile-bar" aria-hidden="true">
        <span :style="{ width: `${profileCompleteness}%` }"></span>
      </div>
      <a href="/company/">管理企业档案</a>
    </div>
  </aside>
</template>

<script setup>
import {
  ArchiveBoxIcon,
  BuildingOffice2Icon,
  ChartBarSquareIcon,
  DocumentChartBarIcon,
  HomeIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline'

const brandMark = `${import.meta.env.BASE_URL}brand-mark-color.png`

defineProps({
  navItems: { type: Array, default: () => [] },
  currentPage: { type: String, default: '' },
  companyName: { type: String, default: '' },
  profileCompleteness: { type: Number, default: 0 },
})

function iconFor(item) {
  const icons = {
    经营总览: HomeIcon,
    智能分析: SparklesIcon,
    机会池: ArchiveBoxIcon,
    项目看板: ChartBarSquareIcon,
    报告中心: DocumentChartBarIcon,
    企业档案: BuildingOffice2Icon,
  }
  return icons[item.label] || HomeIcon
}

function activeLabel(item) {
  if (item.key !== 'projects') return item.label
  return '机会池'
}
</script>
