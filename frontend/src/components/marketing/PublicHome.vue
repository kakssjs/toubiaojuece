<template>
  <section class="public-home">
    <section class="public-hero">
      <div class="public-hero-copy">
        <p class="section-kicker">AI BID DECISION & COLLABORATION</p>
        <h1>AI驱动的企业投标<br />决策与标书协作平台</h1>
        <p>从项目筛选、投标决策到标书生成和风险审核，让企业在一个工作台完成完整投标流程。</p>
        <div><a class="button-primary" href="/agent/">免费分析一份招标文件</a><a class="button-secondary" href="/workspace/">进入企业工作台</a></div>
        <small>AI结果用于辅助决策，关键结论和投标文件仍需企业人工复核。</small>
      </div>
      <aside class="public-decision-card">
        <div><span>项目决策示例</span><b>辅助研判</b></div><h2>智慧医院建设项目</h2>
        <div class="public-score"><strong>86</strong><span>企业匹配度<br />基于资质、业绩与项目要求</span></div>
        <dl><div><dt>项目价值分</dt><dd>92</dd></div><div><dt>风险等级</dt><dd>中</dd></div><div><dt>AI建议</dt><dd>建议关注</dd></div></dl>
      </aside>
    </section>

    <section class="public-value-strip"><article><strong>更快判断</strong><span>自动提取资格、评分、截止时间与风险</span></article><article><strong>更稳决策</strong><span>统一企业匹配度、项目价值和竞争研判</span></article><article><strong>更好协作</strong><span>专家Agent、标书流程与任务集中管理</span></article></section>

    <section class="public-capabilities">
      <header><p class="section-kicker">CORE CAPABILITIES</p><h2>围绕投标全流程，而不是只生成一份报告</h2><p>每项能力明确标注当前可用状态，便于企业判断适用范围。</p></header>
      <div><article v-for="item in capabilities" :key="item.title"><span :class="item.stateClass">{{ item.state }}</span><component :is="item.icon"/><h3>{{ item.title }}</h3><p>{{ item.description }}</p><a :href="item.href">{{ item.action }} <ArrowRightIcon/></a></article></div>
    </section>

    <WorkspaceAiValueShowcase />
    <WorkspaceSecurityTrust />
    <WorkspaceCaseStudies />

    <section class="public-final-cta"><div><p class="section-kicker">START WITH ONE TENDER</p><h2>从下一份招标文件开始，建立更清晰的投标流程</h2><p>先完成一次项目分析，再决定是否纳入企业投标工作台。</p></div><a class="button-primary" href="/agent/">免费体验AI分析</a></section>
  </section>
</template>
<script setup>
import { ArrowRightIcon,ChartBarSquareIcon,CircleStackIcon,DocumentCheckIcon,SparklesIcon,UserGroupIcon } from '@heroicons/vue/24/outline'
import WorkspaceAiValueShowcase from '../workspace/WorkspaceAiValueShowcase.vue'
import WorkspaceSecurityTrust from '../workspace/WorkspaceSecurityTrust.vue'
import WorkspaceCaseStudies from '../workspace/WorkspaceCaseStudies.vue'
const capabilities=[
  {title:'项目发现与AI雷达',description:'基于平台参考库和企业画像排序潜在项目。',state:'已上线',stateClass:'live',icon:CircleStackIcon,href:'/workspace/',action:'进入工作台'},
  {title:'投标决策与预测',description:'分别展示企业匹配度、项目价值分和竞争胜率。',state:'内测中',stateClass:'beta',icon:ChartBarSquareIcon,href:'/product/',action:'了解计算逻辑'},
  {title:'AI专家团队',description:'技术、商务、报价、审核Agent围绕真实项目协作。',state:'已上线',stateClass:'live',icon:UserGroupIcon,href:'/workspace/',action:'启动专家团队'},
  {title:'标书生成与检查',description:'生成技术标、商务标框架并检查缺项和风险。',state:'内测中',stateClass:'beta',icon:DocumentCheckIcon,href:'/agent/',action:'分析招标文件'},
  {title:'企业知识与私有部署',description:'企业素材调用和专属环境部署按需求规划。',state:'支持定制',stateClass:'custom',icon:SparklesIcon,href:'/solutions/',action:'查看企业方案'},
]
</script>
