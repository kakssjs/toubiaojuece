<template>
  <section class="company-ai-profile">
    <div class="company-ai-score"><div><span>综合投标能力</span><strong>{{ score }}<small>分</small></strong></div><svg viewBox="0 0 42 42"><circle cx="21" cy="21" r="16"/><circle class="score-ring" cx="21" cy="21" r="16" :style="{strokeDasharray:`${score} 100`}"/></svg></div>
    <div class="company-capability-tags"><span v-for="tag in tags" :key="tag">{{ tag }}</span></div>
    <div class="company-ai-capabilities">
      <div v-for="item in capabilities" :key="item.label"><span>{{ item.label }}</span><strong>{{ stars(item.value) }}</strong></div>
    </div>
    <dl><div><dt>优势</dt><dd>{{ advantage }}</dd></div><div><dt>短板</dt><dd>{{ weakness }}</dd></div><div><dt>适合项目</dt><dd>{{ suitableProjects }}</dd></div></dl>
    <p>AI 画像会随资质、业绩和企业资料完善而动态更新。</p>
  </section>
</template>
<script setup>
import { computed } from 'vue'
const props=defineProps({profile:{type:Object,default:()=>({})}})
const qualifications=computed(()=>(props.profile.qualifications||[]).filter(i=>i.name));const experiences=computed(()=>(props.profile.experiences||[]).filter(i=>i.name))
const tags=computed(()=>String(props.profile.capability_tags||props.profile.main_business||'软件开发、数字化服务').split(/[、，,]/).filter(Boolean).slice(0,5))
const score=computed(()=>Math.min(96,50+qualifications.value.length*5+experiences.value.length*6+[props.profile.industry,props.profile.registered_capital,props.profile.employee_scale,props.profile.service_regions].filter(Boolean).length*4))
const capabilities=computed(()=>[{label:tags.value[0]||'软件开发能力',value:Math.min(5,3+Math.floor(experiences.value.length/2))},{label:'政府项目经验',value:Math.min(5,2+experiences.value.length)},{label:'大型案例数量',value:Math.min(5,2+Math.floor(experiences.value.filter(i=>Number(i.amount)>=5000000).length))}])
const advantage=computed(()=>qualifications.value.length>=experiences.value.length?'资质与技术能力较强':'同类项目经验较丰富')
const weakness=computed(()=>experiences.value.filter(i=>Number(i.amount)>=5000000).length?'能力标签仍可继续细化':'大型项目案例数量不足')
const suitableProjects=computed(()=>tags.value.slice(0,3).join('、')||'智慧城市、数字政府、医疗信息化')
function stars(value){return '★'.repeat(value)+'☆'.repeat(5-value)}
</script>
