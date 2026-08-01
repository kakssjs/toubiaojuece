<template>
  <section class="ai-value-showcase" aria-labelledby="ai-value-title">
    <div class="ai-value-heading">
      <div>
        <p class="section-kicker">AI DECISION INTELLIGENCE</p>
        <h2 id="ai-value-title">AI 5分钟读懂一个项目</h2>
      </div>
      <p>不止提取标书内容，而是把项目价值、竞争强度、投标风险与下一步策略转化为可执行的决策结论。</p>
    </div>

    <div class="ai-value-layout">
      <div class="ai-outcome-list" aria-label="AI分析结果">
        <article v-for="(item, index) in outcomes" :key="item.title">
          <span>0{{ index + 1 }}</span>
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </div>
        </article>
      </div>

      <article class="ai-scorecard" aria-label="智慧城市项目AI决策示例">
        <header>
          <div>
            <span>AI 项目决策卡 · 示例</span>
            <h3>城市运行智能中枢建设项目</h3>
          </div>
          <b class="decision-badge">推荐参与</b>
        </header>

        <div class="ai-score-overview">
          <div class="score-ring" aria-label="AI综合评分86分">
            <strong>86</strong>
            <span>综合评分</span>
          </div>
          <dl>
            <div><dt>竞争胜率</dt><dd>区间研判</dd></div>
            <div><dt>企业能力匹配</dt><dd>92%</dd></div>
            <div><dt>竞争强度</dt><dd>中高</dd></div>
          </dl>
        </div>

        <div class="ai-score-details">
          <section>
            <h4>核心优势</h4>
            <ul>
              <li>公司核心资质满足资格门槛</li>
              <li>同类智慧城市项目业绩匹配</li>
              <li>技术方案与评分重点高度一致</li>
            </ul>
          </section>
          <section class="risk-column">
            <h4>重点风险</h4>
            <ul>
              <li>潜在竞争企业数量较多</li>
              <li>价格评分权重带来报价压力</li>
              <li>驻场团队证明材料需要补齐</li>
            </ul>
          </section>
        </div>

        <footer>
          <span>AI策略建议</span>
          <p>建议参与。优先突出同类案例与交付团队优势，报价控制在预算的 91%–94%，并提前补齐驻场人员证明。</p>
        </footer>
      </article>
    </div>

    <ol class="ai-process-loop" aria-label="AI投标决策全流程">
      <li v-for="(step, index) in processSteps" :key="step">
        <span>{{ String(index + 1).padStart(2, '0') }}</span>
        <strong>{{ step }}</strong>
      </li>
    </ol>
  </section>
</template>

<script setup>
const outcomes = [
  { title: '项目价值评分', description: '结合预算、交付周期、企业能力和投入产出，判断项目是否值得参与。' },
  { title: '竞争胜率研判', description: '综合企业实力、报价、技术方案和竞争强度，形成可解释的辅助研判。' },
  { title: '竞争对手分析', description: '识别潜在竞争格局、优势差距和需要重点防守的评分维度。' },
  { title: '废标风险提醒', description: '提前发现资格、材料、签章、工期和实质性条款中的高风险项。' },
  { title: '投标策略建议', description: '输出报价区间、技术侧重点、材料补齐和下一步行动建议。' },
]

const processSteps = ['项目发现', '投标判断', '竞争分析', '报价策略', '标书生成', '中标复盘']
</script>
