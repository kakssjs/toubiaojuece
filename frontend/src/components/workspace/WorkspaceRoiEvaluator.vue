<template>
  <section class="roi-evaluator" aria-labelledby="roi-title">
    <div class="roi-intro">
      <p class="section-kicker">BID ROI PREDICTION</p>
      <h2 id="roi-title">项目价值评估系统</h2>
      <p>在投入大量售前与标书资源前，先用可解释的模型判断项目价值、竞争难度和企业匹配程度。</p>
      <div class="roi-method-note">
        <strong>模型输入</strong>
        <span>项目金额 · 行业 · 地区 · 企业资质 · 历史中标记录</span>
      </div>
    </div>

    <form class="roi-form" @submit.prevent>
      <label>
        <span>项目金额（万元）</span>
        <input v-model.number="form.amount" type="number" min="1" max="100000" step="10" />
      </label>
      <label>
        <span>所属行业</span>
        <select v-model="form.industry">
          <option value="government">政务信息化</option>
          <option value="medical">医疗与健康</option>
          <option value="education">教育信息化</option>
          <option value="manufacturing">工业与制造</option>
          <option value="general">综合服务</option>
        </select>
      </label>
      <label>
        <span>项目地区</span>
        <select v-model="form.region">
          <option value="core">一线及核心城市</option>
          <option value="growth">重点省会及成长地区</option>
          <option value="local">本地优势地区</option>
        </select>
      </label>
      <label>
        <span>企业资质匹配度</span>
        <div class="roi-range-field">
          <input v-model.number="form.qualification" type="range" min="0" max="100" step="1" />
          <b>{{ form.qualification }}%</b>
        </div>
      </label>
      <label>
        <span>近三年同类中标数量</span>
        <input v-model.number="form.historicalWins" type="number" min="0" max="100" step="1" />
      </label>
    </form>

    <article class="roi-result" aria-live="polite">
      <header>
        <div><span>AI综合推荐</span><strong>{{ starLabel }}</strong></div>
        <b :class="recommendationClass">{{ recommendation }}</b>
      </header>

      <div class="roi-metrics">
        <div>
          <span>市场价值</span>
          <strong>{{ marketValue }}%</strong>
          <i><b :style="{ width: `${marketValue}%` }"></b></i>
        </div>
        <div>
          <span>竞争难度</span>
          <strong>{{ competitionDifficulty }}%</strong>
          <i class="competition"><b :style="{ width: `${competitionDifficulty}%` }"></b></i>
        </div>
        <div>
          <span>匹配程度</span>
          <strong>{{ matchDegree }}%</strong>
          <i><b :style="{ width: `${matchDegree}%` }"></b></i>
        </div>
      </div>

      <div class="roi-probability">
        <span>预计中标概率</span>
        <strong>{{ probabilityRange }}</strong>
        <p>{{ strategySummary }}</p>
      </div>

      <footer>
        <small>结果为基于当前输入的辅助决策测算，不构成中标承诺。</small>
        <a href="/agent/">上传标书进行完整分析 <ArrowRightIcon /></a>
      </footer>
    </article>
  </section>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { ArrowRightIcon } from '@heroicons/vue/24/outline'

const form = reactive({ amount: 480, industry: 'government', region: 'growth', qualification: 85, historicalWins: 6 })
const industryValue = { government: 12, medical: 10, education: 7, manufacturing: 9, general: 4 }
const industryCompetition = { government: 10, medical: 8, education: 4, manufacturing: 7, general: 2 }
const regionValue = { core: 9, growth: 7, local: 5 }
const regionCompetition = { core: 16, growth: 10, local: 3 }
const clamp = (value, min = 0, max = 100) => Math.min(max, Math.max(min, Math.round(value)))

const marketValue = computed(() => clamp(42 + Math.log10(Math.max(form.amount, 1)) * 10 + industryValue[form.industry] + regionValue[form.region]))
const competitionDifficulty = computed(() => clamp(42 + Math.log10(Math.max(form.amount, 1)) * 7 + industryCompetition[form.industry] + regionCompetition[form.region] - Math.min(form.historicalWins, 15) * 0.7))
const matchDegree = computed(() => clamp(form.qualification * 0.72 + Math.min(form.historicalWins * 3.2, 25) + (form.region === 'local' ? 6 : 0)))
const totalScore = computed(() => clamp(marketValue.value * 0.35 + (100 - competitionDifficulty.value) * 0.25 + matchDegree.value * 0.4))
const probabilityMidpoint = computed(() => clamp(12 + matchDegree.value * 0.28 + (100 - competitionDifficulty.value) * 0.14 + Math.min(form.historicalWins, 15) * 0.8, 15, 78))
const probabilityRange = computed(() => `${clamp(probabilityMidpoint.value - 5, 5, 95)}%–${clamp(probabilityMidpoint.value + 5, 5, 95)}%`)
const starLabel = computed(() => `${'★'.repeat(Math.max(1, Math.ceil(totalScore.value / 20)))}${'☆'.repeat(5 - Math.max(1, Math.ceil(totalScore.value / 20)))} ${totalScore.value}分`)
const recommendation = computed(() => totalScore.value >= 75 ? '建议投标' : totalScore.value >= 60 ? '谨慎参与' : '暂缓投标')
const recommendationClass = computed(() => totalScore.value >= 75 ? 'recommended' : totalScore.value >= 60 ? 'cautious' : 'declined')
const strategySummary = computed(() => {
  if (matchDegree.value < 65) return '当前能力匹配不足，建议先补齐核心资质与同类案例，再决定是否投入。'
  if (competitionDifficulty.value > 78) return '项目价值较高但竞争激烈，建议强化差异化技术方案并谨慎控制报价。'
  if (totalScore.value >= 75) return '项目价值与企业能力匹配良好，建议进入深度读标并制定针对性投标策略。'
  return '建议进一步核验评分办法、竞争格局与交付成本后再作决策。'
})
</script>
