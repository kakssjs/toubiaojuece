<template>
  <section class="project-management-center">
    <div class="project-center-header">
      <div><span>AI BID WORKSPACE</span><h2>投标项目管理中心</h2><p>从项目发现到结果复盘，集中管理每一个投标机会。</p></div>
      <div class="project-center-search"><MagnifyingGlassIcon /><input v-model.trim="query" type="search" placeholder="搜索项目、招标单位或地区" /></div>
    </div>
    <div class="project-pipeline" aria-label="投标流程">
      <template v-for="(stage, index) in stages" :key="stage.key">
        <button type="button" :class="{ active: stageFilter === stage.key }" @click="stageFilter = stageFilter === stage.key ? '' : stage.key">
          <span>{{ index + 1 }}</span><strong>{{ stage.label }}</strong><small>{{ stageCount(stage.key) }}</small>
        </button><ChevronRightIcon v-if="index < stages.length - 1" />
      </template>
    </div>
    <div class="project-center-list">
      <article v-for="project in filteredProjects" :key="project.id">
        <div class="project-center-title"><span>{{ project.project_type || '招投标项目' }}</span><h3>{{ project.name }}</h3><p>招标单位：{{ project.issuing_organization || '待 AI 识别' }}</p></div>
        <div class="project-center-metric"><span>项目金额</span><strong>{{ compactMoney(project.budget_amount) }}</strong></div>
        <div class="project-center-metric"><span>截止时间</span><strong :class="{ urgent: deadlineUrgent(project.deadline) }">{{ dateOnly(project.deadline) }}</strong></div>
        <div class="project-center-stage"><span>当前阶段</span><strong>{{ stageLabel(project) }}</strong><small>{{ project.status_label }}</small></div>
        <div class="project-center-score"><span>AI 评分</span><strong>{{ project.match_score ?? '-' }}<small>分</small></strong></div>
        <a :href="`/projects/${project.id}/`" aria-label="查看项目详情"><ArrowUpRightIcon /></a>
      </article>
      <div v-if="!filteredProjects.length" class="project-center-empty">没有找到符合条件的项目</div>
    </div>
  </section>
</template>
<script setup>
import { ArrowUpRightIcon, ChevronRightIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline'
import { computed, ref } from 'vue'
const props = defineProps({ projects:{type:Array,default:()=>[]} })
const query=ref(''); const stageFilter=ref('')
const stages=[['discovery','项目发现'],['assessment','AI评估'],['decision','投标决策'],['generation','方案生成'],['review','文件审核'],['submission','提交投标'],['retrospective','结果复盘']].map(([key,label])=>({key,label}))
function stageKey(project){
  if(project.status==='pending') return 'discovery'; if(project.status==='analyzing') return 'assessment';
  if(project.status==='analyzed') return project.pending_task_count ? 'generation' : 'decision';
  if(project.status==='recommended') return project.pending_task_count ? 'review' : 'submission';
  if(['archived','abandoned'].includes(project.status)) return 'retrospective'; return 'decision'
}
function stageLabel(project){return stages.find(item=>item.key===stageKey(project))?.label || '投标决策'}
function stageCount(key){return props.projects.filter(item=>stageKey(item)===key).length}
const filteredProjects=computed(()=>{const q=query.value.toLowerCase();return props.projects.filter(item=>(!stageFilter.value||stageKey(item)===stageFilter.value)&&(!q||[item.name,item.issuing_organization,item.region,item.project_type].some(value=>String(value||'').toLowerCase().includes(q))))})
function compactMoney(value){if(!value)return '待识别';const amount=Number(value);return amount>=10000?`${(amount/10000).toLocaleString('zh-CN',{maximumFractionDigits:1})} 万元`:`${amount.toLocaleString('zh-CN')} 元`}
function dateOnly(value){return value?new Date(value).toLocaleDateString('zh-CN',{year:'numeric',month:'2-digit',day:'2-digit'}):'待确认'}
function deadlineUrgent(value){if(!value)return false;const days=(new Date(value)-new Date())/86400000;return days>=0&&days<=7}
</script>
