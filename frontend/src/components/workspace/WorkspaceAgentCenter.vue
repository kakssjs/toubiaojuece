<template>
  <section class="agent-team-center" aria-labelledby="agent-team-title">
    <header class="workspace-section-heading">
      <div><p class="section-kicker">MULTI-AGENT COLLABORATION</p><h2 id="agent-team-title">AI 投标专家团队</h2></div>
      <div class="agent-team-controls"><select v-model="selectedProjectId"><option value="">选择协作项目</option><option v-for="item in projects" :key="item.id" :value="item.id">{{ item.name }}</option></select><button class="button-primary" type="button" :disabled="running||!selectedProjectId" @click="runTeam">{{ running?'团队协作中...':'启动专家团队' }}</button></div>
    </header>
    <div class="agent-team-flow">
      <template v-for="(agent,index) in displayAgents" :key="agent.key"><article :class="`is-${agent.status}`"><div class="agent-team-icon"><component :is="icons[agent.key]"/></div><span>{{ agent.role }}</span><h3>{{ agent.name }}</h3><p>{{ agent.output||agent.description }}</p><footer><CheckCircleIcon v-if="agent.status==='completed'"/><span>{{ statusText(agent.status) }}</span></footer></article><ArrowLongRightIcon v-if="index<displayAgents.length-1" class="agent-flow-arrow"/></template>
    </div>
    <div v-if="teamSummary" class="agent-team-consensus"><UserGroupIcon/><div><span>团队协作结论</span><h3>{{ teamSummary.decision }} · AI {{ teamSummary.score }} 分</h3><p>{{ teamSummary.next_action }}</p></div><a href="/projects/">进入项目中心 <ArrowRightIcon/></a></div>
    <p v-if="error" class="suite-error">{{ error }}</p>
  </section>
</template>
<script setup>
import { ArrowLongRightIcon,ArrowRightIcon,BanknotesIcon,BriefcaseIcon,CheckCircleIcon,CpuChipIcon,DocumentCheckIcon,ShieldCheckIcon,UserGroupIcon } from '@heroicons/vue/24/outline'
import { ref } from 'vue'
const props=defineProps({projects:{type:Array,default:()=>[]},csrfToken:{type:String,default:''}})
const selectedProjectId=ref(''),running=ref(false),error=ref(''),teamSummary=ref(null)
const icons={manager:BriefcaseIcon,technical:CpuChipIcon,commercial:DocumentCheckIcon,pricing:BanknotesIcon,review:ShieldCheckIcon}
const initial=[{key:'manager',name:'项目经理 Agent',role:'整体策略',status:'ready',description:'统筹投标决策、任务分工与最终团队结论。'},{key:'technical',name:'技术专家 Agent',role:'技术方案',status:'waiting',description:'设计技术路线、实施计划与服务方案。'},{key:'commercial',name:'商务专家 Agent',role:'商务文件',status:'waiting',description:'核验资质、业绩、人员和授权材料。'},{key:'pricing',name:'报价专家 Agent',role:'价格策略',status:'waiting',description:'测算报价区间与价格竞争策略。'},{key:'review',name:'审核专家 Agent',role:'风险审核',status:'waiting',description:'检查废标风险、偏离项与文件完整性。'}]
const displayAgents=ref(initial.map(item=>({...item})))
async function runTeam(){running.value=true;error.value='';teamSummary.value=null;displayAgents.value=initial.map((item,index)=>({...item,status:index===0?'running':'waiting'}));try{const r=await fetch('/api/agent-team/run/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':props.csrfToken},body:JSON.stringify({project_id:selectedProjectId.value})});const p=await r.json();if(!r.ok||!p.ok)throw new Error(p.error||'专家团队协作失败');for(let i=0;i<p.agents.length;i++){displayAgents.value.splice(i,1,{...p.agents[i],status:'running'});await new Promise(resolve=>setTimeout(resolve,180));displayAgents.value.splice(i,1,{...p.agents[i],status:'completed'})}teamSummary.value=p.team_summary}catch(e){error.value=e.message;displayAgents.value=initial.map(item=>({...item}))}finally{running.value=false}}
function statusText(status){return({completed:'已完成',running:'分析中',ready:'等待启动',waiting:'等待协作'})[status]||status}
</script>
