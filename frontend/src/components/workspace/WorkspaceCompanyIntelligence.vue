<template>
  <section class="company-intelligence">
    <header class="workspace-section-heading">
      <div><p class="section-kicker">ENTERPRISE INTELLIGENCE</p><h2>企业投标能力画像</h2></div>
      <a href="/company/">完善企业档案</a>
    </header>

    <div class="company-intelligence-grid">
      <article class="enterprise-profile-card">
        <div class="enterprise-profile-head">
          <div><span>企业</span><h3>{{ companyName }}</h3></div>
          <strong>{{ profileCompleteness }}<small>%</small></strong>
        </div>
        <p class="profile-caption">AI 根据企业资质、历史业绩与承接能力动态生成</p>
        <div class="capability-list">
          <div v-for="item in capabilities" :key="item.label">
            <span>{{ item.label }}</span><i><b :style="{ width: `${item.score}%` }"></b></i><strong>{{ stars(item.score) }}</strong>
          </div>
        </div>
        <div class="profile-insight-columns">
          <div><span>优势</span><p v-for="item in strengths" :key="item">✓ {{ item }}</p></div>
          <div class="profile-gaps"><span>待提升</span><p v-for="item in gaps" :key="item">△ {{ item }}</p></div>
        </div>
        <footer><span>推荐项目</span><strong>{{ recommendedRange }}</strong><p>{{ recommendedTypes }}</p></footer>
      </article>

      <article class="historical-bid-library">
        <div class="historical-library-head">
          <div><span>招标知识库</span><h3>历史项目数据库</h3></div>
          <strong>{{ historicalTotal }}<small> 个案例样本</small></strong>
        </div>
        <div class="industry-pills"><span v-for="item in industries" :key="item.industry">{{ item.industry }} {{ item.count }}</span></div>
        <div v-if="historicalLoading" class="historical-empty">正在加载历史项目...</div>
        <div v-else-if="historicalError" class="historical-empty">{{ historicalError }}</div>
        <div v-else class="historical-case-list">
          <article v-for="item in historicalCases" :key="item.id">
            <div><span>{{ item.industry }} · {{ item.region }} · {{ item.year }}</span><h4>{{ item.title }}</h4><p>中标单位：{{ item.winning_company }}</p></div>
            <dl>
              <div><dt>预算</dt><dd>{{ money(item.budget_amount) }}</dd></div>
              <div><dt>竞争数量</dt><dd>{{ item.participant_count }} 家</dd></div>
              <div><dt>平均报价</dt><dd>{{ money(item.average_bid_amount) }}</dd></div>
            </dl>
          </article>
        </div>
        <p class="historical-data-note">案例为平台分析样本，用于行业趋势与报价策略参考。</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  companyProfile: { type: Object, default: () => ({}) },
  profileCompleteness: { type: Number, default: 0 },
  historicalCases: { type: Array, default: () => [] },
  industries: { type: Array, default: () => [] },
  historicalTotal: { type: Number, default: 0 },
  historicalLoading: { type: Boolean, default: false },
  historicalError: { type: String, default: '' },
})
const companyName = computed(() => props.companyProfile.name || '待完善企业档案')
const qualifications = computed(() => (props.companyProfile.qualifications || []).filter((item) => item.name))
const experiences = computed(() => (props.companyProfile.experiences || []).filter((item) => item.name))
const business = computed(() => props.companyProfile.main_business || '')
const capabilities = computed(() => [
  { label: business.value.split(/[、，,]/)[0] || '行业解决方案能力', score: Math.min(96, 62 + experiences.value.length * 7) },
  { label: '资质与合规能力', score: Math.min(95, 55 + qualifications.value.length * 9) },
  { label: '同类项目经验', score: Math.min(94, 52 + experiences.value.length * 10) },
])
const strengths = computed(() => [
  qualifications.value[0]?.name || '已建立基础投标能力档案',
  experiences.value[0]?.name ? `具备${experiences.value[0].name}经验` : (business.value || '主营方向清晰'),
].slice(0, 2))
const gaps = computed(() => {
  const rows = []
  if (qualifications.value.length < 3) rows.push('核心资质覆盖仍可扩充')
  if (experiences.value.length < 3) rows.push('大型同类项目案例不足')
  if (!props.companyProfile.service_regions) rows.push('服务区域尚未完善')
  return rows.length ? rows.slice(0, 2) : ['持续沉淀中标数据与复盘结论']
})
const recommendedRange = computed(() => {
  const max = Number(props.companyProfile.max_project_amount || 5_000_000)
  return `${Math.max(50, Math.round(max * 0.2 / 10000))}-${Math.max(100, Math.round(max * 0.75 / 10000))} 万元`
})
const recommendedTypes = computed(() => business.value || '政府数字化、软件与智慧项目')
function stars(score) { return '★'.repeat(Math.max(3, Math.min(5, Math.round(score / 20)))) }
function money(value) { return `${Math.round(Number(value || 0) / 10000).toLocaleString('zh-CN')} 万` }
</script>
