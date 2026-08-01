<template>
  <section class="advanced-ai-suite">
    <header class="workspace-section-heading"><div><p class="section-kicker">ADVANCED AI SUITE</p><h2>AI 投标数据与生成中心</h2></div><nav><button v-for="item in tabs" :key="item.key" :class="{active:tab===item.key}" @click="tab=item.key">{{ item.label }}</button></nav></header>

    <div v-if="tab==='radar'" class="radar-panel">
      <div class="suite-panel-intro"><SignalIcon/><div><span>AI 项目雷达</span><h3>今日推荐项目</h3><p>基于平台招标参考库与企业画像进行匹配排序。</p></div><strong>{{ radarTotal }}<small> 条库内数据</small></strong></div>
      <div class="radar-cards"><article v-for="item in radarProjects.slice(0,4)" :key="item.id"><div><span>{{ item.industry }} · {{ item.region }}</span><strong>★★★★★</strong></div><h4>{{ item.title }}</h4><p>招标单位：{{ item.issuing_organization||'待补充' }}</p><dl><div><dt>预算</dt><dd>{{ money(item.budget_amount) }}</dd></div><div><dt>匹配度</dt><dd>{{ item.match_score }}%</dd></div></dl><footer>{{ item.recommendation }}<ArrowRightIcon/></footer></article></div>
      <p v-if="radarError" class="suite-error">{{ radarError }}</p>
    </div>

    <div v-else-if="tab==='prediction'" class="prediction-panel">
      <div class="suite-panel-intro"><ChartBarIcon/><div><span>AI 投标预测模型</span><h3>谁更可能中标？</h3><p>调整竞争企业的实力、报价、技术和地区经验，生成可解释预测。</p></div><button class="button-primary" :disabled="predicting" @click="runPrediction">{{ predicting?'计算中':'重新预测' }}</button></div>
      <div class="prediction-grid"><div class="prediction-inputs"><article v-for="item in participants" :key="item.name"><input v-model="item.name" aria-label="企业名称"/><label>企业实力<input v-model.number="item.strength" type="range" min="20" max="100"/></label><label>报价竞争力<input v-model.number="item.price" type="range" min="20" max="100"/></label><label>技术方案<input v-model.number="item.technical" type="range" min="20" max="100"/></label><label>地区经验<input v-model.number="item.regional" type="range" min="20" max="100"/></label></article></div><div class="prediction-results"><article v-for="item in predictions" :key="item.name"><div><strong>{{ item.name }}</strong><span>{{ item.probability }}%</span></div><i><b :style="{width:`${item.probability}%`}"></b></i></article><p>预测结果用于投标决策辅助，不构成中标保证。</p></div></div>
    </div>

    <div v-else class="generator-panel">
      <div class="suite-panel-intro"><DocumentTextIcon/><div><span>专业标书生成系统</span><h3>从招标文件到完整响应框架</h3><p>选择已分析项目，生成技术标、商务标和自动检查结果。</p></div><div class="generator-actions"><select v-model="selectedProjectId"><option value="">选择项目</option><option v-for="item in projects" :key="item.id" :value="item.id">{{ item.name }}</option></select><button class="button-primary" :disabled="generating||!selectedProjectId" @click="generateBid">{{ generating?'生成中':'生成标书大纲' }}</button></div></div>
      <div v-if="generatedBid" class="generated-bid-grid"><section><span>技术标</span><article v-for="item in generatedBid.technical_bid" :key="item.title"><CheckCircleIcon/><div><strong>{{ item.title }}</strong><p>{{ item.summary }}</p></div></article></section><section><span>商务标</span><article v-for="item in generatedBid.commercial_bid" :key="item.title"><component :is="item.status==='missing'?ExclamationCircleIcon:CheckCircleIcon"/><div><strong>{{ item.title }}</strong><p>{{ statusText(item.status) }}</p></div></article></section><section class="bid-checks"><span>自动检查</span><article v-for="item in generatedBid.checks" :key="item.message"><ShieldExclamationIcon/><div><strong>{{ item.type }}</strong><p>{{ item.message }}</p></div></article></section></div>
      <div v-else class="generator-placeholder"><DocumentPlusIcon/><strong>选择项目后开始生成</strong><span>将自动整理项目理解、技术路线、实施运维、企业业绩和缺项检查。</span></div><p v-if="generatorError" class="suite-error">{{ generatorError }}</p>
    </div>
  </section>
</template>
<script setup>
import { ArrowRightIcon, ChartBarIcon, CheckCircleIcon, DocumentPlusIcon, DocumentTextIcon, ExclamationCircleIcon, SignalIcon, ShieldExclamationIcon } from '@heroicons/vue/24/outline'
import { onMounted, ref } from 'vue'
const props=defineProps({projects:{type:Array,default:()=>[]},csrfToken:{type:String,default:''}})
const tabs=[{key:'radar',label:'项目雷达'},{key:'prediction',label:'中标预测'},{key:'generator',label:'标书生成'}];const tab=ref('radar')
const radarProjects=ref([]),radarTotal=ref(0),radarError=ref('');const predicting=ref(false),predictions=ref([])
const participants=ref([{name:'您的企业',strength:82,price:78,technical:88,regional:76},{name:'A公司',strength:88,price:72,technical:80,regional:86},{name:'B公司',strength:74,price:91,technical:76,regional:68}])
const selectedProjectId=ref(''),generating=ref(false),generatedBid=ref(null),generatorError=ref('')
async function loadRadar(){try{const r=await fetch('/api/project-radar/');const p=await r.json();if(!r.ok||!p.ok)throw new Error(p.error||'项目雷达加载失败');radarProjects.value=p.projects||[];radarTotal.value=p.total||0}catch(e){radarError.value=e.message}}
async function runPrediction(){predicting.value=true;try{const r=await fetch('/api/bid-prediction/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':props.csrfToken},body:JSON.stringify({participants:participants.value})});const p=await r.json();if(!r.ok||!p.ok)throw new Error(p.error||'预测失败');predictions.value=p.predictions}catch(e){predictions.value=[]}finally{predicting.value=false}}
async function generateBid(){generating.value=true;generatorError.value='';try{const r=await fetch('/api/bid-generator/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':props.csrfToken},body:JSON.stringify({project_id:selectedProjectId.value})});const p=await r.json();if(!r.ok||!p.ok)throw new Error(p.error||'生成失败');generatedBid.value=p}catch(e){generatorError.value=e.message}finally{generating.value=false}}
function money(v){return v?`${Math.round(Number(v)/10000).toLocaleString('zh-CN')} 万元`:'待确认'}function statusText(v){return({generated:'已匹配企业档案',missing:'资料缺失，需补充',review:'需人工确认人员配置'})[v]||v}
onMounted(()=>{loadRadar();runPrediction()})
</script>
