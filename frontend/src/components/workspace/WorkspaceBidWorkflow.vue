<template>
  <section class="bid-workflow-section">
    <header class="workspace-section-heading">
      <div><p class="section-kicker">BID WORKFLOW</p><h2>标书生成工作流</h2></div>
      <span class="workflow-progress-label">整体进度 {{ progress }}%</span>
    </header>

    <div class="bid-workflow-card">
      <div class="workflow-project-panel">
        <label for="workflow-project">当前投标项目</label>
        <select id="workflow-project" v-model="selectedProjectId" @change="restoreWorkflow">
          <option value="demo">智慧医院建设项目</option>
          <option v-for="project in projects" :key="project.id" :value="String(project.id)">{{ project.name }}</option>
        </select>
        <div class="workflow-project-meta">
          <span>{{ selectedProject?.company_name || '企业数字化招标项目' }}</span>
          <span>{{ selectedProject?.region || '全国' }}</span>
        </div>
        <div class="workflow-progress-track"><b :style="{ width: `${progress}%` }"></b></div>
        <strong>{{ completedCount }}/{{ stages.length }} 个环节已完成</strong>
        <p>每个环节由对应 AI 智能体处理，结果会自动流转至下一阶段。</p>
        <a class="button-primary" href="/agent/">进入完整投标工作台</a>
      </div>

      <ol class="workflow-stage-list">
        <li v-for="(stage, index) in stages" :key="stage.key" :class="`is-${stage.status}`">
          <div class="workflow-stage-number">
            <CheckIcon v-if="stage.status === 'completed'" />
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="workflow-stage-copy">
            <span>{{ stage.eyebrow }}</span>
            <h3>{{ stage.title }}</h3>
            <p>{{ stage.description }}</p>
          </div>
          <div class="workflow-stage-action">
            <span>{{ statusLabel(stage.status) }}</span>
            <button v-if="stage.status === 'active'" type="button" @click="completeStage(index)">完成并继续</button>
            <button v-else-if="stage.status === 'pending' && canStart(index)" type="button" @click="startStage(index)">开始处理</button>
            <button v-else-if="stage.status === 'completed'" type="button" @click="restartStage(index)">重新检查</button>
          </div>
        </li>
      </ol>
    </div>
  </section>
</template>

<script setup>
import { CheckIcon } from '@heroicons/vue/24/solid'
import { computed, ref } from 'vue'

const props = defineProps({ projects: { type: Array, default: () => [] } })
const selectedProjectId = ref(props.projects[0]?.id ? String(props.projects[0].id) : 'demo')
const stageTemplate = [
  ['requirements', 'STEP 01', '招标要求解析', '提取资格门槛、评分办法、交付范围与关键时间。'],
  ['technical', 'STEP 02', '技术方案生成', '根据评分点生成技术架构、实施方案与服务承诺。'],
  ['commercial', 'STEP 03', '商务文件检查', '核对资质、业绩、授权文件和商务响应完整性。'],
  ['pricing', 'STEP 04', '报价策略', '结合历史项目、竞争强度与成本测算推荐报价区间。'],
  ['review', 'STEP 05', '最终审核', '执行合规检查、废标风险扫描与终稿确认。'],
]
const stages = ref(buildStages())
const selectedProject = computed(() => props.projects.find((item) => String(item.id) === selectedProjectId.value))
const completedCount = computed(() => stages.value.filter((stage) => stage.status === 'completed').length)
const progress = computed(() => Math.round((completedCount.value / stages.value.length) * 100))

function storageKey() { return `cebiao-bid-workflow-${selectedProjectId.value}` }
function buildStages(statuses = ['completed', 'active', 'pending', 'pending', 'pending']) {
  return stageTemplate.map(([key, eyebrow, title, description], index) => ({ key, eyebrow, title, description, status: statuses[index] || 'pending' }))
}
function persist() { localStorage.setItem(storageKey(), JSON.stringify(stages.value.map((stage) => stage.status))) }
function restoreWorkflow() {
  try { stages.value = buildStages(JSON.parse(localStorage.getItem(storageKey()) || 'null') || undefined) }
  catch { stages.value = buildStages() }
}
function canStart(index) { return index === 0 || stages.value[index - 1].status === 'completed' }
function startStage(index) { stages.value[index].status = 'active'; persist() }
function completeStage(index) {
  stages.value[index].status = 'completed'
  if (stages.value[index + 1]) stages.value[index + 1].status = 'active'
  persist()
}
function restartStage(index) {
  stages.value.forEach((stage, stageIndex) => { stage.status = stageIndex < index ? 'completed' : stageIndex === index ? 'active' : 'pending' })
  persist()
}
function statusLabel(status) { return ({ completed: '已完成', active: '生成中', pending: '未开始' })[status] }
restoreWorkflow()
</script>
