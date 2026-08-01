<template>
  <section class="case-study-section" aria-labelledby="case-study-title">
    <header class="workspace-section-heading">
      <div><p class="section-kicker">AI BID CASE STUDIES</p><h2 id="case-study-title">AI 投标案例</h2></div>
      <span class="case-demo-label">脱敏效果示例</span>
    </header>

    <div class="case-study-shell">
      <nav class="case-study-tabs" aria-label="选择投标案例">
        <button v-for="(item, index) in cases" :key="item.project" type="button" :class="{ active: selectedIndex === index }" :aria-pressed="selectedIndex === index" @click="selectedIndex = index">
          <span>案例 {{ index + 1 }}</span><strong>{{ item.company }}</strong><small>{{ item.industry }}</small>
        </button>
      </nav>

      <article class="case-study-detail">
        <div class="case-study-project">
          <span>{{ selectedCase.industry }} · {{ selectedCase.region }}</span>
          <h3>{{ selectedCase.project }}</h3>
          <p>{{ selectedCase.summary }}</p>
        </div>

        <div class="case-time-comparison">
          <div><span>原人工分析</span><strong>{{ selectedCase.before }}</strong><small>小时</small></div>
          <ArrowLongRightIcon />
          <div class="case-time-ai"><span>使用 AI 后</span><strong>{{ selectedCase.after }}</strong><small>分钟</small></div>
          <p>分析时间缩短 <strong>{{ selectedCase.efficiency }}%</strong></p>
        </div>

        <div class="case-study-results">
          <div v-for="result in selectedCase.results" :key="result.label">
            <component :is="result.icon" />
            <strong>{{ result.value }}</strong>
            <span>{{ result.label }}</span>
          </div>
        </div>

        <blockquote>“{{ selectedCase.quote }}”<footer>— {{ selectedCase.role }}</footer></blockquote>
      </article>
    </div>
    <p class="case-study-disclaimer">以上为脱敏后的产品效果示例，用于说明工作流程与可量化产出，不代表对所有项目作相同结果承诺。</p>
  </section>
</template>

<script setup>
import { ArrowLongRightIcon, DocumentCheckIcon, DocumentTextIcon, ShieldExclamationIcon, SparklesIcon } from '@heroicons/vue/24/outline'
import { computed, ref } from 'vue'

const cases = [
  { company:'某科技公司', industry:'智慧园区', region:'华东', project:'智慧园区建设项目', summary:'包含数字孪生、园区物联和综合运营中心建设内容。', before:4, after:15, efficiency:94, quote:'以前先花半天找风险，现在先看 AI 清单，再让团队集中完善高分项。', role:'项目投标负责人', results:[{value:'3 个',label:'废标风险',icon:ShieldExclamationIcon},{value:'80 页',label:'技术方案',icon:DocumentTextIcon},{value:'42 项',label:'评分点响应',icon:DocumentCheckIcon}] },
  { company:'某医疗信息企业', industry:'智慧医疗', region:'华南', project:'区域医疗数据平台项目', summary:'涉及医疗数据治理、互联互通与医院业务系统集成。', before:6, after:22, efficiency:94, quote:'资质和接口要求被自动归类后，商务与技术团队可以同步推进。', role:'解决方案总监', results:[{value:'5 个',label:'合规风险',icon:ShieldExclamationIcon},{value:'96 页',label:'方案初稿',icon:DocumentTextIcon},{value:'57 项',label:'关键要求',icon:SparklesIcon}] },
  { company:'某软件服务商', industry:'政务数字化', region:'全国', project:'城市运行一网统管项目', summary:'覆盖多部门数据汇聚、事件闭环和城市运行指挥体系。', before:8, after:28, efficiency:94, quote:'AI 先完成拆标与响应框架，专家时间更多用在策略和差异化方案上。', role:'投标中心经理', results:[{value:'7 个',label:'潜在风险',icon:ShieldExclamationIcon},{value:'112 页',label:'响应框架',icon:DocumentTextIcon},{value:'68 项',label:'任务拆解',icon:DocumentCheckIcon}] },
]
const selectedIndex = ref(0)
const selectedCase = computed(() => cases[selectedIndex.value])
</script>
