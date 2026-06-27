<template>
  <main class="site-shell">
    <header v-if="currentPage !== 'home'" class="site-header">
      <a class="brand" href="/" aria-label="策标首页">
        <span class="brand-symbol brand-logo" aria-hidden="true">
          <svg viewBox="0 0 48 48" role="img" focusable="false">
            <path class="brand-logo-core" d="M14 34L24 14L34 34" />
            <path class="brand-logo-cross" d="M19 26H29" />
            <path class="brand-logo-base" d="M11 38H37" />
          </svg>
        </span>
        <span class="brand-text">策标</span>
      </a>

      <nav class="site-nav" aria-label="网站导航">
        <a
          v-for="item in navItems"
          :key="item.href"
          :href="item.href"
          :class="{ active: currentPage === item.key }"
        >
          {{ item.label }}
        </a>
      </nav>
    </header>

    <section v-if="currentPage === 'home'">
      <div v-if="workspaceLoading" class="page-section">
        <div class="loading-panel">
          <p class="section-kicker">Workspace</p>
          <h1>工作台加载中</h1>
          <p>正在聚合项目池、企业档案和风险提醒...</p>
        </div>
      </div>
      <div v-else-if="workspaceState.error" class="page-section">
        <div class="loading-panel loading-panel-error">
          <p class="section-kicker">Workspace</p>
          <h1>工作台暂时无法打开</h1>
          <p>{{ workspaceState.error }}</p>
          <div class="loading-panel-actions">
            <button class="button-primary" type="button" @click="loadWorkspaceDashboard">重新加载</button>
            <a class="button-secondary" href="/projects/">查看项目看板</a>
          </div>
        </div>
      </div>
      <WorkspaceDashboard
        v-else
        :nav-items="workspaceNavItems"
        :current-page="currentPage"
        :company-name="companyForm.name"
        :profile-completeness="profileCompletion"
        :metrics="workspaceMetrics"
        :projects="workspaceProjects"
        :reminders="workspaceReminders"
        :decision-class="decisionClass"
        :risk-class="riskClass"
      />
    </section>

    <section v-else-if="currentPage === 'product'" class="page-section content-page">
      <div class="page-heading">
        <p class="section-kicker">Product Features</p>
        <h1>产品功能</h1>
        <p>
          覆盖招标文件阅读、抽取、匹配、风险识别与报告生成，帮助企业把投标筛选过程标准化、
          数据化、可追溯。
        </p>
      </div>
      <div class="feature-grid">
        <article v-for="feature in features" :key="feature.title" class="feature-card">
          <span>{{ feature.index }}</span>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </article>
      </div>

      <div class="page-expansion">
        <div class="section-subhead">
          <p class="section-kicker">Capability Matrix</p>
          <h2>从文件解析到领导摘要，覆盖投标前判断的关键链路</h2>
        </div>
        <div class="matrix-grid">
          <article v-for="item in productMatrix" :key="item.title">
            <span>{{ item.type }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <div class="deliverable-panel">
          <div>
            <p class="section-kicker">Output</p>
            <h2>每次分析可沉淀为标准化交付物</h2>
          </div>
          <ul>
            <li v-for="item in deliverables" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="section-subhead wide">
          <p class="section-kicker">Feature Depth</p>
          <h2>围绕投标前决策，把每个关键问题拆成可检查的能力项</h2>
        </div>
        <div class="capability-table">
          <article v-for="item in capabilityRows" :key="item.question">
            <strong>{{ item.question }}</strong>
            <p>{{ item.answer }}</p>
            <span>{{ item.result }}</span>
          </article>
        </div>
        <div class="system-panel">
          <div>
            <p class="section-kicker">System Fit</p>
            <h2>既能作为独立工具，也能融入企业已有投标流程</h2>
          </div>
          <div class="system-columns">
            <article v-for="item in systemFits" :key="item.title">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </div>
        <div class="section-subhead wide">
          <p class="section-kicker">Checklist</p>
          <h2>把投标前核查拆解为可执行、可复核的清单</h2>
        </div>
        <div class="checklist-grid">
          <article v-for="item in productChecklist" :key="item.title">
            <span>{{ item.group }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <div class="integration-panel">
          <div>
            <p class="section-kicker">Integration</p>
            <h2>前端官网之后，可逐步接入真实业务能力</h2>
          </div>
          <div class="integration-steps">
            <article v-for="item in integrationSteps" :key="item.title">
              <span>{{ item.step }}</span>
              <div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.description }}</p>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>

    <section v-else-if="currentPage === 'solutions'" class="page-section content-page">
      <div class="page-heading">
        <p class="section-kicker">Solutions</p>
        <h1>解决方案</h1>
        <p>
          为经营、售前、管理层和招采信息团队建立统一投标判断标准，减少无效投标，
          让项目筛选更快、更稳、更可控。
        </p>
      </div>
      <div class="solution-layout">
        <div class="solution-copy">
          <p>
            策标将企业能力档案、历史业绩、资质证书、禁投条件和招标文件要求进行统一比对，
            输出清晰的推荐理由和风险边界。
          </p>
          <dl>
            <div v-for="metric in metrics" :key="metric.label">
              <dt>{{ metric.value }}</dt>
              <dd>{{ metric.label }}</dd>
            </div>
          </dl>
        </div>

        <div class="solution-list">
          <article v-for="solution in solutions" :key="solution.title">
            <h3>{{ solution.title }}</h3>
            <p>{{ solution.description }}</p>
          </article>
        </div>
      </div>

      <div class="page-expansion">
        <div class="section-subhead">
          <p class="section-kicker">Operating Model</p>
          <h2>让投标筛选从个人经验变成团队协同流程</h2>
        </div>
        <div class="role-grid">
          <article v-for="role in roleWorkflows" :key="role.title">
            <span>{{ role.owner }}</span>
            <h3>{{ role.title }}</h3>
            <p>{{ role.description }}</p>
          </article>
        </div>
        <div class="section-subhead wide">
          <p class="section-kicker">Governance</p>
          <h2>围绕“能不能投、值不值得投、怎么投”形成管理闭环</h2>
        </div>
        <div class="governance-grid">
          <article v-for="item in governanceItems" :key="item.title">
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <div class="adoption-panel">
          <div>
            <p class="section-kicker">Adoption Path</p>
            <h2>从单份文件分析到企业级项目池管理</h2>
          </div>
          <ol>
            <li v-for="item in adoptionSteps" :key="item.title">
              <strong>{{ item.title }}</strong>
              <span>{{ item.description }}</span>
            </li>
          </ol>
        </div>
        <div class="section-subhead wide">
          <p class="section-kicker">Department Value</p>
          <h2>不同团队看到不同视角，但共用同一份事实依据</h2>
        </div>
        <div class="department-grid">
          <article v-for="item in departmentValues" :key="item.title">
            <span>{{ item.department }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <div class="management-panel">
          <div>
            <p class="section-kicker">Management Benefits</p>
            <h2>把投标决策从临时讨论变成可度量的管理动作</h2>
          </div>
          <div class="management-list">
            <article v-for="item in managementBenefits" :key="item.title">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </div>
      </div>
    </section>

    <section v-else-if="currentPage === 'process'" class="page-section content-page">
      <div class="page-heading">
        <p class="section-kicker">AI Analysis Workflow</p>
        <h1>AI分析流程</h1>
        <p>
          从招标文件到投标建议，系统通过多 Agent 协同完成解析、抽取、分类、匹配、
          风险识别和报告生成，每个结论都保留来源依据。
        </p>
      </div>
      <div class="process-panel">
        <article v-for="step in processSteps" :key="step.title" class="process-step">
          <span>{{ step.step }}</span>
          <h3>{{ step.title }}</h3>
          <p>{{ step.description }}</p>
        </article>
      </div>

      <div class="page-expansion">
        <div class="section-subhead">
          <p class="section-kicker">Agent Collaboration</p>
          <h2>多智能体分工处理复杂招标文件</h2>
        </div>
        <div class="agent-grid">
          <article v-for="agent in agents" :key="agent.title">
            <h3>{{ agent.title }}</h3>
            <p>{{ agent.description }}</p>
          </article>
        </div>
        <div class="evidence-panel">
          <h3>报告结论保留原文证据链</h3>
          <p>
            关键字段、风险判断和资质匹配结果均可关联原文页码或章节来源，便于投标负责人复核，
            也便于后续归档审计。
          </p>
        </div>
        <div class="section-subhead wide">
          <p class="section-kicker">Quality Control</p>
          <h2>AI 不是替代复核，而是把复核点提前标出来</h2>
        </div>
        <div class="quality-grid">
          <article v-for="item in qualityControls" :key="item.title">
            <span>{{ item.level }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <div class="process-detail-panel">
          <div>
            <p class="section-kicker">Decision Logic</p>
            <h2>最终建议由多项指标共同决定，而不是单一评分</h2>
          </div>
          <div class="logic-list">
            <article v-for="item in decisionLogic" :key="item.title">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </div>
        <div class="section-subhead wide">
          <p class="section-kicker">Exception Handling</p>
          <h2>复杂文件和不确定结论，会被标记出来等待人工复核</h2>
        </div>
        <div class="exception-grid">
          <article v-for="item in exceptionHandling" :key="item.title">
            <span>{{ item.type }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <div class="audit-panel">
          <div>
            <p class="section-kicker">Audit Trail</p>
            <h2>每一次分析都可以形成可追踪记录</h2>
          </div>
          <div class="audit-list">
            <article v-for="item in auditTrail" :key="item.title">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </div>
      </div>
    </section>

    <section v-else-if="currentPage === 'agent'" class="page-section content-page agent-page">
      <div class="page-heading">
        <p class="section-kicker">Live Agent Demo</p>
        <h1>智能体在线体验</h1>
        <p>
          选择企业档案，粘贴一段招标文件文本，系统会调用当前规则版 AI 招投标智能体，
          自动生成投标建议、匹配评分、风险清单和下一步动作，并保存到后台。
        </p>
      </div>

      <div class="agent-workbench">
        <form class="agent-form" @submit.prevent="runAgentAnalysis">
          <label>
            <span>选择企业档案</span>
            <select v-model="agentForm.companyId">
              <option disabled value="">请选择企业</option>
              <option v-for="company in companies" :key="company.id" :value="company.id">
                {{ company.name }}
              </option>
            </select>
          </label>

          <div class="agent-upload-note">
            <strong>企业档案会直接影响 AI 判断</strong>
            <span>维护主营业务、资质证书和历史业绩后，系统才能更准确判断是否建议投标。</span>
            <a href="/company/">维护企业能力档案</a>
          </div>

          <label>
            <span>上传招标 PDF</span>
            <input type="file" accept="application/pdf,.pdf" @change="handlePdfChange" />
          </label>

          <div class="agent-upload-note">
            <strong>优先推荐上传 PDF</strong>
            <span>系统会自动提取文件文本并调用智能体分析。扫描件 OCR 将在后续版本增强。</span>
          </div>

          <label>
            <span>招标文件文本备用输入</span>
            <textarea v-model="agentForm.tenderText" rows="13"></textarea>
          </label>

          <div class="agent-actions">
            <button class="button-primary" type="button" :disabled="agentState.loading" @click="runPdfAnalysis">
              {{ agentState.loading ? '分析中...' : '上传PDF并分析' }}
            </button>
            <button class="button-secondary" type="submit" :disabled="agentState.loading">
              {{ agentState.loading ? '分析中...' : '开始AI分析' }}
            </button>
            <button class="button-secondary" type="button" @click="fillSampleTender">填入示例文本</button>
          </div>

          <p v-if="agentState.error" class="agent-error">{{ agentState.error }}</p>
        </form>

        <aside class="agent-result">
          <div v-if="!agentState.report" class="empty-result">
            <p class="section-kicker">Result Preview</p>
            <h2>等待智能体分析</h2>
            <p>提交后，这里会展示投标建议、综合评分、风险清单、缺失材料和后台保存编号。</p>
          </div>

          <div v-else>
            <div class="result-header">
              <span>{{ agentState.report.project_type }}</span>
              <strong>{{ agentState.report.decision }}</strong>
            </div>
            <div class="result-score">
              <span>综合匹配评分</span>
              <strong>{{ agentState.report.match_score }}</strong>
            </div>
            <dl class="result-meta">
              <div>
                <dt>采购方式</dt>
                <dd>{{ agentState.report.procurement_method }}</dd>
              </div>
              <div>
                <dt>项目预算</dt>
                <dd>{{ formatBudget(agentState.report.budget_amount) }}</dd>
              </div>
              <div>
                <dt>项目编号</dt>
                <dd>#{{ agentState.projectId || '-' }}</dd>
              </div>
              <div>
                <dt>报告编号</dt>
                <dd>#{{ agentState.reportId || '-' }}</dd>
              </div>
              <div>
                <dt>文件编号</dt>
                <dd>#{{ agentState.documentId || '-' }}</dd>
              </div>
            </dl>
            <div class="result-section">
              <h3>决策理由</h3>
              <p>{{ agentState.report.decision_reason }}</p>
            </div>
            <div class="result-section">
              <h3>缺失材料</h3>
              <ul>
                <li v-for="item in agentState.report.qualification_match.missing" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div class="result-section">
              <h3>风险清单</h3>
              <ul>
                <li v-for="risk in agentState.report.risks" :key="risk.type + risk.description">
                  {{ risk.level }}｜{{ risk.type }}：{{ risk.description }}
                </li>
              </ul>
            </div>
            <div class="result-section">
              <h3>下一步动作</h3>
              <ul>
                <li v-for="action in agentState.report.next_actions" :key="action">{{ action }}</li>
              </ul>
            </div>
            <a v-if="agentState.reportId" class="report-link button-primary" :href="`/reports/${agentState.reportId}/`">
              查看完整报告
            </a>
            <a class="report-link button-secondary" href="/projects/">
              返回项目看板
            </a>
          </div>
        </aside>
      </div>

      <section class="agent-recent">
        <div class="section-subhead">
          <p class="section-kicker">Recent Analyses</p>
          <h2>最近分析项目</h2>
        </div>
        <div v-if="agentState.recentLoading" class="recent-empty">最近项目加载中...</div>
        <div v-else-if="agentState.recentError" class="recent-empty">{{ agentState.recentError }}</div>
        <div v-else class="recent-projects">
          <article v-for="project in agentState.recentProjects" :key="project.id">
            <div>
              <strong>{{ project.name }}</strong>
              <span>{{ project.project_type || '未识别类型' }}｜{{ project.company_name }}</span>
            </div>
            <b :class="decisionClass(project.decision)">{{ project.decision_label }}</b>
            <em>{{ project.match_score ?? '-' }}</em>
            <span :class="riskClass(project.risk_level)">{{ project.risk_level }}</span>
            <small>{{ project.status_label }}</small>
            <div class="recent-actions">
              <a v-if="project.report_id" class="table-link" :href="`/reports/${project.report_id}/`">报告</a>
              <a class="table-link" :href="`/projects/${project.id}/`">项目</a>
            </div>
          </article>
          <div v-if="!agentState.recentProjects.length" class="recent-empty">
            暂无分析项目，完成一次文本或 PDF 分析后会自动出现在这里。
          </div>
        </div>
      </section>
    </section>

    <section v-else-if="currentPage === 'projects'" class="page-section content-page projects-page">
      <div class="page-heading">
        <p class="section-kicker">Project Dashboard</p>
        <h1>项目分析看板</h1>
        <p>
          集中查看所有已分析招标项目，按 AI 建议、匹配评分、风险等级和项目状态进行筛选，
          帮助投标团队从单份报告进入项目池管理。
        </p>
      </div>

      <div v-if="projectState.loading" class="loading-panel">
        <p class="section-kicker">Projects</p>
        <h1>项目看板加载中</h1>
      </div>

      <div v-else-if="projectState.error" class="loading-panel">
        <p class="section-kicker">Projects</p>
        <h1>项目看板无法打开</h1>
        <p>{{ projectState.error }}</p>
      </div>

      <template v-else>
        <div class="project-summary">
          <article>
            <span>项目总数</span>
            <strong>{{ projectState.summary.total || 0 }}</strong>
          </article>
          <article>
            <span>推荐投标</span>
            <strong>{{ projectState.summary.recommended || 0 }}</strong>
          </article>
          <article>
            <span>谨慎投标</span>
            <strong>{{ projectState.summary.cautious || 0 }}</strong>
          </article>
          <article>
            <span>高风险项目</span>
            <strong>{{ projectState.summary.high_risk || 0 }}</strong>
          </article>
        </div>

        <div class="project-toolbar">
          <div>
            <button
              v-for="filter in projectFilters"
              :key="filter.value"
              class="button-secondary compact-button"
              :class="{ selected: projectState.decisionFilter === filter.value }"
              type="button"
              @click="loadProjectDashboard(filter.value)"
            >
              {{ filter.label }}
            </button>
          </div>
          <a class="button-primary" href="/agent/">新增分析</a>
        </div>

        <div class="project-table">
          <div class="project-table-head">
            <span>项目名称</span>
            <span>类型 / 地区</span>
            <span>预算</span>
            <span>AI建议</span>
            <span>匹配度</span>
            <span>风险</span>
            <span>状态</span>
            <span>状态流转</span>
          </div>
          <article v-for="project in projectState.projects" :key="project.id" class="project-row">
            <div>
              <strong>{{ project.name }}</strong>
              <small>{{ project.company_name }}｜{{ project.procurement_method || '未识别采购方式' }}</small>
            </div>
            <div>
              <span>{{ project.project_type || '未识别类型' }}</span>
              <small>{{ project.region || '未识别地区' }}</small>
            </div>
            <div>{{ formatBudget(project.budget_amount) }}</div>
            <div>
              <b :class="decisionClass(project.decision)">{{ project.decision_label }}</b>
            </div>
            <div>
              <span class="score-chip">{{ project.match_score ?? '-' }}</span>
            </div>
            <div>
              <span :class="riskClass(project.risk_level)">{{ project.risk_level }}</span>
            </div>
            <div>
              <span class="status-chip">{{ project.status_label }}</span>
            </div>
            <div class="project-actions-cell">
              <select v-model="project.pendingStatus" :disabled="projectState.updatingId === project.id">
                <option v-for="status in projectStatusOptions" :key="status.value" :value="status.value">
                  {{ status.label }}
                </option>
              </select>
              <button
                class="button-secondary compact-button"
                type="button"
                :disabled="projectState.updatingId === project.id || project.pendingStatus === project.status"
                @click="updateProjectStatus(project)"
              >
                {{ projectState.updatingId === project.id ? '保存中' : '保存' }}
              </button>
              <a class="table-link" :href="`/projects/${project.id}/`">项目详情</a>
              <a v-if="project.report_id" class="table-link" :href="`/reports/${project.report_id}/`">查看报告</a>
              <span v-else>-</span>
            </div>
          </article>
          <p v-if="projectState.actionError" class="project-action-error">{{ projectState.actionError }}</p>
          <div v-if="!projectState.projects.length" class="empty-projects">
            <h2>暂无项目</h2>
            <p>先进入智能体体验页上传或粘贴招标文件，完成分析后会自动进入项目看板。</p>
            <a class="button-primary" href="/agent/">去分析第一个项目</a>
          </div>
        </div>
      </template>
    </section>

    <section v-else-if="currentPage === 'projectDetail'" class="page-section content-page project-detail-page">
      <div v-if="projectDetailState.loading" class="loading-panel">
        <p class="section-kicker">Project Workspace</p>
        <h1>项目详情加载中</h1>
      </div>

      <div v-else-if="projectDetailState.error" class="loading-panel">
        <p class="section-kicker">Project Workspace</p>
        <h1>项目详情无法打开</h1>
        <p>{{ projectDetailState.error }}</p>
      </div>

      <template v-else-if="projectDetailState.detail">
        <div class="project-detail-hero">
          <div>
            <p class="section-kicker">Project Workspace</p>
            <h1>{{ projectDetailState.detail.project.name }}</h1>
            <p>{{ projectDetailState.detail.report?.summary || '该项目尚未生成AI分析摘要。' }}</p>
            <div class="report-actions">
              <a class="button-secondary" href="/projects/">返回项目看板</a>
              <a v-if="projectDetailState.detail.project.report_id" class="button-primary" :href="`/reports/${projectDetailState.detail.project.report_id}/`">查看AI报告</a>
              <a v-if="projectDetailState.detail.report" class="button-secondary" :href="`/api/reports/${projectDetailState.detail.report.id}/export/pdf/`">导出PDF</a>
              <a v-if="projectDetailState.detail.report" class="button-secondary" :href="`/api/reports/${projectDetailState.detail.report.id}/export/word/`">导出Word</a>
            </div>
          </div>
          <aside>
            <span>{{ projectDetailState.detail.project.status_label }}</span>
            <strong>{{ projectDetailState.detail.report?.decision_label || '待分析' }}</strong>
            <em>{{ projectDetailState.detail.report?.match_score ?? '-' }}</em>
          </aside>
        </div>

        <div class="project-detail-grid">
          <section class="project-card">
            <h2>项目状态</h2>
            <div class="status-control">
              <select v-model="projectDetailState.pendingStatus" :disabled="projectDetailState.updating">
                <option v-for="status in projectStatusOptions" :key="status.value" :value="status.value">
                  {{ status.label }}
                </option>
              </select>
              <button
                class="button-primary"
                type="button"
                :disabled="projectDetailState.updating || projectDetailState.pendingStatus === projectDetailState.detail.project.status"
                @click="updateProjectDetailStatus"
              >
                {{ projectDetailState.updating ? '保存中...' : '保存状态' }}
              </button>
            </div>
            <p v-if="projectDetailState.actionError" class="project-action-error">{{ projectDetailState.actionError }}</p>
          </section>

          <section class="project-card">
            <h2>项目基础信息</h2>
            <dl class="detail-meta">
              <div><dt>企业</dt><dd>{{ projectDetailState.detail.project.company_name }}</dd></div>
              <div><dt>项目类型</dt><dd>{{ projectDetailState.detail.project.project_type || '-' }}</dd></div>
              <div><dt>采购方式</dt><dd>{{ projectDetailState.detail.project.procurement_method || '-' }}</dd></div>
              <div><dt>地区</dt><dd>{{ projectDetailState.detail.project.region || '-' }}</dd></div>
              <div><dt>预算金额</dt><dd>{{ formatBudget(projectDetailState.detail.project.budget_amount) }}</dd></div>
              <div><dt>风险等级</dt><dd>{{ projectDetailState.detail.project.risk_level }}</dd></div>
            </dl>
          </section>

          <section class="project-card">
            <h2>协作待办</h2>
            <ul class="workspace-list">
              <li v-for="item in projectDetailState.detail.workspace.next_actions" :key="item">{{ item }}</li>
              <li v-if="!projectDetailState.detail.workspace.next_actions.length">暂无下一步动作。</li>
            </ul>
          </section>

          <section class="project-card">
            <h2>材料清单</h2>
            <ul class="workspace-list">
              <li v-for="item in projectDetailState.detail.workspace.material_checklist" :key="item.category + item.name">
                {{ item.category }}｜{{ item.name }}｜{{ item.status }}
              </li>
              <li v-for="item in projectDetailState.detail.workspace.missing_materials" :key="item">
                缺失材料｜{{ item }}
              </li>
              <li v-if="!projectDetailState.detail.workspace.material_checklist.length && !projectDetailState.detail.workspace.missing_materials.length">暂无材料清单。</li>
            </ul>
          </section>

          <section class="project-card wide">
            <h2>风险处理</h2>
            <div class="detail-risk-grid">
              <article v-for="risk in projectDetailState.detail.workspace.risks" :key="risk.type + risk.description">
                <span>{{ risk.level }}</span>
                <h3>{{ risk.type }}</h3>
                <p>{{ risk.description }}</p>
              </article>
              <p v-if="!projectDetailState.detail.workspace.risks.length">暂无风险项。</p>
            </div>
          </section>

          <section class="project-card">
            <h2>资质与业绩匹配</h2>
            <dl class="detail-meta">
              <div><dt>资质状态</dt><dd>{{ projectDetailState.detail.workspace.qualification_match.status || '-' }}</dd></div>
              <div><dt>资质评分</dt><dd>{{ projectDetailState.detail.workspace.qualification_match.score ?? '-' }}</dd></div>
              <div><dt>业绩评分</dt><dd>{{ projectDetailState.detail.workspace.experience_match.score ?? '-' }}</dd></div>
              <div><dt>业绩说明</dt><dd>{{ projectDetailState.detail.workspace.experience_match.summary || '-' }}</dd></div>
            </dl>
          </section>

          <section class="project-card">
            <h2>Agent执行轨迹</h2>
            <div class="trace-list compact">
              <article v-for="step in projectDetailState.detail.workspace.agent_trace" :key="step.agent">
                <span>{{ step.status }}</span>
                <strong>{{ step.agent }}</strong>
              </article>
              <p v-if="!projectDetailState.detail.workspace.agent_trace.length">暂无执行轨迹。</p>
            </div>
          </section>

          <section class="project-card wide">
            <h2>处理记录</h2>
            <form class="note-form" @submit.prevent="createProjectNote">
              <label>
                <span>记录类型</span>
                <select v-model="projectDetailState.noteForm.note_type" :disabled="projectDetailState.creatingNote">
                  <option v-for="type in projectNoteTypes" :key="type.value" :value="type.value">
                    {{ type.label }}
                  </option>
                </select>
              </label>
              <label>
                <span>操作人</span>
                <input v-model="projectDetailState.noteForm.operator_name" type="text" :disabled="projectDetailState.creatingNote" />
              </label>
              <label class="full-field">
                <span>记录内容</span>
                <textarea v-model="projectDetailState.noteForm.content" rows="4" :disabled="projectDetailState.creatingNote"></textarea>
              </label>
              <div class="note-form-actions">
                <button class="button-primary" type="submit" :disabled="projectDetailState.creatingNote">
                  {{ projectDetailState.creatingNote ? '保存中...' : '新增记录' }}
                </button>
                <p v-if="projectDetailState.noteError">{{ projectDetailState.noteError }}</p>
              </div>
            </form>
            <div class="note-list">
              <article v-for="note in projectDetailState.detail.notes" :key="note.id">
                <div>
                  <span>{{ note.note_type_label }}</span>
                  <strong>{{ note.operator_name }}</strong>
                  <time>{{ formatDateTime(note.created_at) }}</time>
                </div>
                <p>{{ note.content }}</p>
              </article>
              <p v-if="!projectDetailState.detail.notes.length" class="empty-note">暂无处理记录，建议先记录报名判断、材料缺口或风险处理意见。</p>
            </div>
          </section>
        </div>
      </template>
    </section>

    <section v-else-if="currentPage === 'company'" class="page-section content-page company-page">
      <div class="page-heading">
        <p class="section-kicker">Company Capability Profile</p>
        <h1>企业能力档案</h1>
        <p>
          这里维护企业主营业务、服务地区、可承接金额、资质证书、历史业绩与禁投条件。
          AI 招投标 Agent 会基于这份档案判断项目是否匹配企业能力。
        </p>
      </div>

      <div v-if="companyState.loading" class="loading-panel">
        <p class="section-kicker">Profile</p>
        <h1>企业档案加载中</h1>
      </div>

      <div v-else class="company-workbench">
        <form class="company-form" @submit.prevent="saveCompanyProfile">
          <section class="company-form-section">
            <div class="form-section-title">
              <span>01</span>
              <h2>基础能力</h2>
            </div>
            <div class="company-form-grid">
              <label>
                <span>企业名称</span>
                <input v-model="companyForm.name" type="text" placeholder="例如：小苏科技" />
              </label>
              <label>
                <span>最大可承接金额</span>
                <input v-model="companyForm.max_project_amount" type="number" min="0" step="10000" placeholder="例如：8000000" />
              </label>
              <label>
                <span>主营业务</span>
                <textarea v-model="companyForm.main_business" rows="4" placeholder="例如：AI应用开发、政企信息化系统集成、数据中台建设"></textarea>
              </label>
              <label>
                <span>服务地区</span>
                <textarea v-model="companyForm.service_regions" rows="4" placeholder="例如：全国、江苏、上海、浙江"></textarea>
              </label>
              <label class="full-field">
                <span>禁投 / 高风险条件</span>
                <textarea v-model="companyForm.forbidden_conditions" rows="4" placeholder="例如：不接受纯垫资项目、付款周期超过12个月需谨慎、偏远地区驻场项目需复核"></textarea>
              </label>
            </div>
          </section>

          <section class="company-form-section">
            <div class="form-section-title">
              <span>02</span>
              <h2>资质证书</h2>
              <button class="button-secondary compact-button" type="button" @click="addQualification">新增资质</button>
            </div>
            <div class="repeat-list">
              <article v-for="(item, index) in companyForm.qualifications" :key="index" class="repeat-item">
                <label>
                  <span>资质名称</span>
                  <input v-model="item.name" type="text" placeholder="例如：ISO9001质量管理体系认证" />
                </label>
                <label>
                  <span>证书编号</span>
                  <input v-model="item.certificate_no" type="text" />
                </label>
                <label>
                  <span>发证机构</span>
                  <input v-model="item.issuer" type="text" />
                </label>
                <label>
                  <span>有效期至</span>
                  <input v-model="item.valid_until" type="date" />
                </label>
                <button class="button-secondary compact-button" type="button" @click="removeQualification(index)">删除</button>
              </article>
            </div>
          </section>

          <section class="company-form-section">
            <div class="form-section-title">
              <span>03</span>
              <h2>历史业绩</h2>
              <button class="button-secondary compact-button" type="button" @click="addExperience">新增业绩</button>
            </div>
            <div class="repeat-list">
              <article v-for="(item, index) in companyForm.experiences" :key="index" class="repeat-item experience-item">
                <label>
                  <span>项目名称</span>
                  <input v-model="item.name" type="text" placeholder="例如：智慧园区数字化平台" />
                </label>
                <label>
                  <span>项目类型</span>
                  <input v-model="item.industry" type="text" placeholder="例如：软件信息化" />
                </label>
                <label>
                  <span>合同金额</span>
                  <input v-model="item.amount" type="number" min="0" step="10000" />
                </label>
                <label>
                  <span>客户名称</span>
                  <input v-model="item.client_name" type="text" />
                </label>
                <label>
                  <span>完成日期</span>
                  <input v-model="item.completed_at" type="date" />
                </label>
                <label class="full-field">
                  <span>项目说明</span>
                  <textarea v-model="item.description" rows="3"></textarea>
                </label>
                <button class="button-secondary compact-button" type="button" @click="removeExperience(index)">删除</button>
              </article>
            </div>
          </section>

          <div class="company-save-bar">
            <button class="button-primary" type="submit" :disabled="companyState.saving">
              {{ companyState.saving ? '保存中...' : '保存企业档案' }}
            </button>
            <a class="button-secondary" href="/agent/">去智能体分析</a>
            <span v-if="companyState.message">{{ companyState.message }}</span>
          </div>
          <p v-if="companyState.error" class="agent-error">{{ companyState.error }}</p>
        </form>

        <aside class="company-summary">
          <p class="section-kicker">AI Decision Basis</p>
          <h2>这份档案将成为智能体的判断依据</h2>
          <div class="profile-score">
            <strong>{{ profileCompletion }}%</strong>
            <span>档案完整度</span>
          </div>
          <dl>
            <div>
              <dt>资质数量</dt>
              <dd>{{ filledQualifications.length }}</dd>
            </div>
            <div>
              <dt>历史业绩</dt>
              <dd>{{ filledExperiences.length }}</dd>
            </div>
            <div>
              <dt>服务地区</dt>
              <dd>{{ companyForm.service_regions || '-' }}</dd>
            </div>
          </dl>
          <div class="company-guidance">
            <h3>建议优先完善</h3>
            <ul>
              <li v-for="item in profileSuggestions" :key="item">{{ item }}</li>
            </ul>
          </div>
        </aside>
      </div>
    </section>

    <section v-else-if="currentPage === 'report'" class="page-section content-page report-page">
      <div v-if="reportState.loading" class="loading-panel">
        <p class="section-kicker">Report</p>
        <h1>报告加载中</h1>
      </div>

      <div v-else-if="reportState.error" class="loading-panel">
        <p class="section-kicker">Report</p>
        <h1>报告无法打开</h1>
        <p>{{ reportState.error }}</p>
      </div>

      <template v-else-if="reportState.detail">
        <div class="report-hero">
          <div>
            <p class="section-kicker">AI Analysis Report</p>
            <h1>{{ reportState.detail.project.name }}</h1>
            <p>{{ reportState.detail.summary }}</p>
            <div class="report-actions">
              <a class="button-primary" :href="`/api/reports/${reportState.detail.id}/export/pdf/`">导出PDF</a>
              <a class="button-secondary" :href="`/api/reports/${reportState.detail.id}/export/word/`">导出Word</a>
              <a class="button-secondary" href="/projects/">返回项目看板</a>
              <a class="button-secondary" href="/agent/">返回智能体体验页</a>
            </div>
          </div>
          <aside>
            <span>{{ reportState.detail.project.project_type || '未识别类型' }}</span>
            <strong>{{ reportState.detail.decision_label }}</strong>
            <em>{{ reportState.detail.match_score }}</em>
          </aside>
        </div>

        <div class="report-overview">
          <article>
            <span>企业</span>
            <strong>{{ reportState.detail.project.company?.name || '-' }}</strong>
          </article>
          <article>
            <span>采购方式</span>
            <strong>{{ reportState.detail.project.procurement_method || '-' }}</strong>
          </article>
          <article>
            <span>预算金额</span>
            <strong>{{ formatBudget(reportState.detail.project.budget_amount) }}</strong>
          </article>
          <article>
            <span>报告编号</span>
            <strong>#{{ reportState.detail.id }}</strong>
          </article>
        </div>

        <div class="report-layout">
          <section class="report-card">
            <h2>资质匹配</h2>
            <dl class="report-match">
              <div>
                <dt>状态</dt>
                <dd>{{ reportState.detail.qualification_match.status || '-' }}</dd>
              </div>
              <div>
                <dt>评分</dt>
                <dd>{{ reportState.detail.qualification_match.score ?? '-' }}</dd>
              </div>
            </dl>
            <h3>缺失材料</h3>
            <ul>
              <li v-for="item in reportState.detail.missing_materials" :key="item">{{ item }}</li>
            </ul>
          </section>

          <section class="report-card">
            <h2>业绩匹配</h2>
            <p>{{ reportState.detail.experience_match.summary || '暂无业绩匹配摘要' }}</p>
            <h3>匹配案例</h3>
            <ul>
              <li v-for="item in reportState.detail.experience_match.matched_cases || []" :key="item">{{ item }}</li>
            </ul>
          </section>

          <section class="report-card wide">
            <h2>风险清单</h2>
            <div class="report-risk-grid">
              <article v-for="risk in reportState.detail.risks" :key="risk.type + risk.description">
                <span>{{ risk.level }}</span>
                <h3>{{ risk.type }}</h3>
                <p>{{ risk.description }}</p>
              </article>
            </div>
          </section>

          <section class="report-card">
            <h2>下一步动作</h2>
            <ul>
              <li v-for="item in reportState.detail.next_actions" :key="item">{{ item }}</li>
            </ul>
          </section>

          <section class="report-card">
            <h2>材料清单</h2>
            <ul>
              <li v-for="item in reportState.detail.material_checklist" :key="item.category + item.name">
                {{ item.category }}｜{{ item.name }}
              </li>
            </ul>
          </section>

          <section class="report-card wide">
            <h2>Agent执行轨迹</h2>
            <div class="trace-list">
              <article v-for="step in reportState.detail.agent_trace" :key="step.agent">
                <span>{{ step.status }}</span>
                <strong>{{ step.agent }}</strong>
              </article>
            </div>
          </section>

          <section class="report-card wide report-qa-card">
            <div class="qa-heading">
              <div>
                <p class="section-kicker">AI Q&A Assistant</p>
                <h2>AI追问助手</h2>
              </div>
              <span>基于当前报告回答</span>
            </div>
            <div class="qa-prompts">
              <button
                v-for="question in reportQuickQuestions"
                :key="question"
                class="button-secondary compact-button"
                type="button"
                @click="askReportQuestion(question)"
              >
                {{ question }}
              </button>
            </div>
            <form class="qa-form" @submit.prevent="askReportQuestion()">
              <input v-model="reportState.question" type="text" placeholder="输入你的追问，例如：这份标有什么废标风险？" />
              <button class="button-primary" type="submit" :disabled="reportState.asking">
                {{ reportState.asking ? '分析中...' : '发送追问' }}
              </button>
            </form>
            <p v-if="reportState.askError" class="qa-error">{{ reportState.askError }}</p>
            <div class="qa-history">
              <article v-for="item in reportState.answers" :key="item.id">
                <strong>{{ item.question }}</strong>
                <p>{{ item.answer }}</p>
                <div>
                  <span v-for="reference in item.references" :key="reference">{{ reference }}</span>
                </div>
              </article>
              <p v-if="!reportState.answers.length" class="empty-note">可以追问投标建议、缺失材料、风险清单、业绩匹配和下一步动作。</p>
            </div>
          </section>
        </div>
      </template>
    </section>

    <section v-else class="page-section content-page">
      <div class="page-heading">
        <p class="section-kicker">Use Cases</p>
        <h1>应用场景</h1>
        <p>
          适用于政府采购、工程建设、软件信息化、服务采购、框架协议和批量公告筛选等多种场景，
          让不同项目都能被统一、快速地评估。
        </p>
      </div>
      <div class="scene-grid">
        <article v-for="scene in scenes" :key="scene.title" class="scene-card">
          <h3>{{ scene.title }}</h3>
          <p>{{ scene.description }}</p>
        </article>
      </div>

      <div class="page-expansion">
        <div class="section-subhead">
          <p class="section-kicker">Scenario Depth</p>
          <h2>不同类型项目，关注点不同，判断标准也不同</h2>
        </div>
        <div class="scenario-table">
          <article v-for="scenario in scenarioDetails" :key="scenario.title">
            <h3>{{ scenario.title }}</h3>
            <p>{{ scenario.focus }}</p>
            <span>{{ scenario.output }}</span>
          </article>
        </div>
        <div class="section-subhead wide">
          <p class="section-kicker">Industry Adaptation</p>
          <h2>按行业沉淀不同的招标关注点和风险词典</h2>
        </div>
        <div class="industry-grid">
          <article v-for="item in industryPlaybooks" :key="item.title">
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <div class="batch-panel">
          <div>
            <p class="section-kicker">Batch Screening</p>
            <h2>适合每天面对大量公告和文件的团队</h2>
          </div>
          <div class="batch-list">
            <article v-for="item in batchScreening" :key="item.title">
              <span>{{ item.metric }}</span>
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </div>
        <div class="section-subhead wide">
          <p class="section-kicker">Evaluation Dimensions</p>
          <h2>不同场景可以使用同一套维度，但权重不同</h2>
        </div>
        <div class="dimension-grid">
          <article v-for="item in evaluationDimensions" :key="item.title">
            <span>{{ item.weight }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
        <div class="question-panel">
          <div>
            <p class="section-kicker">Typical Questions</p>
            <h2>每类招标项目，都可以围绕关键问题快速展开判断</h2>
          </div>
          <div class="question-list">
            <article v-for="item in sceneQuestions" :key="item.question">
              <strong>{{ item.question }}</strong>
              <p>{{ item.answer }}</p>
            </article>
          </div>
        </div>
      </div>
    </section>

    <section class="closing-section">
      <div>
        <p class="section-kicker">Decision First</p>
        <h2>让每一次投标决策都有依据、有速度、有边界。</h2>
      </div>
      <a class="button-primary" href="/">返回首页</a>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import WorkspaceDashboard from './components/workspace/WorkspaceDashboard.vue'
import {
  buildRiskReminders,
  buildWorkspaceMetrics,
  rankWorkspaceProjects,
} from './workspace/dashboard-data.js'

const routeMap = {
  '/': 'home',
  '/product/': 'product',
  '/solutions/': 'solutions',
  '/process/': 'process',
  '/scenes/': 'scenes',
  '/agent/': 'agent',
  '/company/': 'company',
  '/projects/': 'projects',
}

const normalizedPath = window.location.pathname.endsWith('/')
  ? window.location.pathname
  : `${window.location.pathname}/`

const reportMatch = normalizedPath.match(/^\/reports\/(\d+)\/$/)
const projectMatch = normalizedPath.match(/^\/projects\/(\d+)\/$/)
const currentPage = reportMatch ? 'report' : projectMatch ? 'projectDetail' : routeMap[normalizedPath] || 'home'
const currentReportId = reportMatch ? reportMatch[1] : null
const currentProjectId = projectMatch ? projectMatch[1] : null

const navItems = [
  { key: 'home', label: '首页', href: '/' },
  { key: 'product', label: '产品功能', href: '/product/' },
  { key: 'solutions', label: '解决方案', href: '/solutions/' },
  { key: 'process', label: 'AI分析流程', href: '/process/' },
  { key: 'scenes', label: '应用场景', href: '/scenes/' },
]

const workspaceNavItems = [
  { key: 'home', label: '经营总览', href: '/' },
  { key: 'agent', label: '智能分析', href: '/agent/' },
  { key: 'projects', label: '机会池', href: '/projects/' },
  { key: 'projects', label: '项目看板', href: '/projects/' },
  { key: 'projects', label: '报告中心', href: '/projects/' },
  { key: 'company', label: '企业档案', href: '/company/' },
]

const sampleTenderText =
  '智慧园区数字化平台建设项目，采购方式为公开招标，预算金额480万元。投标人须具备软件开发、系统集成相关能力，具有近三年类似项目业绩。本项目要求提供CMMI三级认证、ISO9001质量管理体系认证和原厂授权函。投标保证金为人民币5万元。付款条件为验收合格后支付70%，质保期满后支付30%。评分标准：技术分50分，商务分30分，价格分20分。投标截止时间为2026年7月20日09:30。'

const companies = ref([])
const agentForm = reactive({
  companyId: '',
  tenderText: sampleTenderText,
  pdfFile: null,
})
const agentState = reactive({
  loading: false,
  error: '',
  report: null,
  projectId: null,
  reportId: null,
  documentId: null,
  recentLoading: false,
  recentError: '',
  recentProjects: [],
})
const reportState = reactive({
  loading: false,
  error: '',
  detail: null,
  question: '',
  asking: false,
  askError: '',
  answers: [],
})
const projectState = reactive({
  loading: false,
  error: '',
  actionError: '',
  updatingId: null,
  projects: [],
  summary: {},
  decisionFilter: '',
})
const projectDetailState = reactive({
  loading: false,
  error: '',
  actionError: '',
  noteError: '',
  updating: false,
  creatingNote: false,
  detail: null,
  pendingStatus: '',
  noteForm: {
    note_type: 'follow_up',
    operator_name: '投标经理',
    content: '',
  },
})
const companyState = reactive({
  loading: false,
  saving: false,
  error: '',
  message: '',
})
const workspaceState = reactive({
  loading: true,
  error: '',
})
const companyForm = reactive(emptyCompanyProfile())

const filledQualifications = computed(() => companyForm.qualifications.filter((item) => item.name.trim()))
const filledExperiences = computed(() => companyForm.experiences.filter((item) => item.name.trim()))
const profileCompletion = computed(() => {
  const checks = [
    companyForm.name.trim(),
    companyForm.main_business.trim(),
    companyForm.service_regions.trim(),
    companyForm.max_project_amount,
    companyForm.forbidden_conditions.trim(),
    filledQualifications.value.length > 0,
    filledExperiences.value.length > 0,
  ]
  const completed = checks.filter(Boolean).length
  return Math.round((completed / checks.length) * 100)
})
const profileSuggestions = computed(() => {
  const suggestions = []
  if (!companyForm.main_business.trim()) suggestions.push('补充主营业务，帮助 AI 判断项目类型是否匹配。')
  if (!companyForm.service_regions.trim()) suggestions.push('补充服务地区，避免推荐超出服务范围的项目。')
  if (!filledQualifications.value.length) suggestions.push('至少录入一项核心资质，用于资质门槛匹配。')
  if (!filledExperiences.value.length) suggestions.push('至少录入一个类似业绩，用于评分和案例匹配。')
  if (!companyForm.forbidden_conditions.trim()) suggestions.push('补充禁投条件，帮助系统提前识别高风险项目。')
  return suggestions.length ? suggestions : ['档案基础信息较完整，可以进入智能体体验页进行分析。']
})
const workspaceProjects = computed(() => rankWorkspaceProjects(projectState.projects).slice(0, 5))
const workspaceMetrics = computed(() => buildWorkspaceMetrics(projectState.projects))
const workspaceReminders = computed(() => buildRiskReminders(projectState.projects))
const workspaceLoading = computed(
  () => workspaceState.loading || projectState.loading || companyState.loading,
)
const projectFilters = [
  { label: '全部项目', value: '' },
  { label: '推荐投标', value: 'recommended' },
  { label: '谨慎投标', value: 'cautious' },
  { label: '不建议投标', value: 'not_recommended' },
]
const projectStatusOptions = [
  { label: '待分析', value: 'pending' },
  { label: '分析中', value: 'analyzing' },
  { label: '已分析', value: 'analyzed' },
  { label: '推荐报名', value: 'recommended' },
  { label: '已放弃', value: 'abandoned' },
  { label: '已归档', value: 'archived' },
]
const reportQuickQuestions = [
  '这份标我们能投吗？',
  '需要补充哪些材料？',
  '有哪些主要风险？',
  '下一步应该做什么？',
]
const projectNoteTypes = [
  { label: '跟进记录', value: 'follow_up' },
  { label: '风险说明', value: 'risk' },
  { label: '决策记录', value: 'decision' },
  { label: '材料补充', value: 'material' },
]

onMounted(async () => {
  if (currentPage === 'home') {
    await loadWorkspaceDashboard()
    return
  }

  if (currentPage === 'report') {
    await loadReportDetail()
    return
  }

  if (currentPage === 'projects') {
    await loadProjectDashboard()
    return
  }

  if (currentPage === 'projectDetail') {
    await loadProjectDetail()
    return
  }

  if (currentPage === 'company') {
    await loadCompanyProfile()
    return
  }

  if (currentPage !== 'agent') {
    return
  }

  try {
    await Promise.all([loadCompaniesForAgent(), loadRecentAgentProjects()])
  } catch (error) {
    agentState.error = '企业列表加载失败，请稍后刷新页面。'
  }
})

async function loadWorkspaceDashboard() {
  workspaceState.loading = true
  workspaceState.error = ''

  try {
    await Promise.all([loadProjectDashboard(), loadCompanyProfile()])
  } catch (error) {
    workspaceState.error = error.message || '工作台加载失败'
  } finally {
    workspaceState.loading = false
  }
}

async function loadCompaniesForAgent() {
  const response = await fetch('/api/companies/')
  const payload = await response.json()
  if (!response.ok || !payload.ok) {
    throw new Error(payload.error || '企业列表加载失败')
  }
  companies.value = payload.companies
  if (!agentForm.companyId && companies.value.length > 0) {
    agentForm.companyId = companies.value[0].id
  }
}

async function loadRecentAgentProjects() {
  agentState.recentLoading = true
  agentState.recentError = ''

  try {
    const response = await fetch('/api/projects/recent/')
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '最近分析项目加载失败')
    }
    agentState.recentProjects = payload.projects
  } catch (error) {
    agentState.recentError = error.message || '最近分析项目加载失败'
  } finally {
    agentState.recentLoading = false
  }
}

async function loadReportDetail() {
  reportState.loading = true
  reportState.error = ''
  reportState.detail = null
  reportState.askError = ''
  reportState.answers = []

  try {
    const response = await fetch(`/api/reports/${currentReportId}/`)
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '报告不存在')
    }
    reportState.detail = payload.report
  } catch (error) {
    reportState.error = error.message || '报告加载失败'
  } finally {
    reportState.loading = false
  }
}

async function askReportQuestion(quickQuestion = '') {
  const question = String(quickQuestion || reportState.question || '').trim()
  if (!question || !reportState.detail) {
    reportState.askError = '请先输入要追问的问题。'
    return
  }

  reportState.asking = true
  reportState.askError = ''

  try {
    const response = await fetch(`/api/reports/${reportState.detail.id}/ask/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '追问失败')
    }
    reportState.answers.unshift({
      id: Date.now(),
      question: payload.question,
      answer: payload.answer,
      references: payload.references || [],
    })
    reportState.question = ''
  } catch (error) {
    reportState.askError = error.message || '追问失败'
  } finally {
    reportState.asking = false
  }
}

async function loadProjectDashboard(decision = projectState.decisionFilter) {
  projectState.loading = true
  projectState.error = ''
  projectState.actionError = ''
  projectState.decisionFilter = decision

  try {
    const params = decision ? `?decision=${encodeURIComponent(decision)}` : ''
    const response = await fetch(`/api/projects/${params}`)
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '项目看板加载失败')
    }
    projectState.projects = payload.projects.map(normalizeProjectRow)
    projectState.summary = payload.summary
  } catch (error) {
    projectState.error = error.message || '项目看板加载失败'
  } finally {
    projectState.loading = false
  }
}

async function loadProjectDetail() {
  projectDetailState.loading = true
  projectDetailState.error = ''
  projectDetailState.actionError = ''
  projectDetailState.noteError = ''
  projectDetailState.detail = null

  try {
    const response = await fetch(`/api/projects/${currentProjectId}/`)
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '项目详情加载失败')
    }
    projectDetailState.detail = payload
    projectDetailState.pendingStatus = payload.project.status
  } catch (error) {
    projectDetailState.error = error.message || '项目详情加载失败'
  } finally {
    projectDetailState.loading = false
  }
}

function normalizeProjectRow(project) {
  return {
    ...project,
    pendingStatus: project.status,
  }
}

async function updateProjectDetailStatus() {
  if (!projectDetailState.detail) {
    return
  }

  projectDetailState.actionError = ''
  projectDetailState.updating = true

  try {
    const response = await fetch(`/api/projects/${projectDetailState.detail.project.id}/status/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status: projectDetailState.pendingStatus,
      }),
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '项目状态更新失败')
    }
    projectDetailState.detail.project = payload.project
    projectDetailState.pendingStatus = payload.project.status
    await refreshProjectDetail()
  } catch (error) {
    projectDetailState.actionError = error.message || '项目状态更新失败'
    projectDetailState.pendingStatus = projectDetailState.detail.project.status
  } finally {
    projectDetailState.updating = false
  }
}

async function refreshProjectDetail() {
  const response = await fetch(`/api/projects/${currentProjectId}/`)
  const payload = await response.json()
  if (!response.ok || !payload.ok) {
    throw new Error(payload.error || '项目详情刷新失败')
  }
  projectDetailState.detail = payload
  projectDetailState.pendingStatus = payload.project.status
}

async function createProjectNote() {
  if (!projectDetailState.detail) {
    return
  }

  projectDetailState.noteError = ''
  projectDetailState.creatingNote = true

  try {
    const response = await fetch(`/api/projects/${projectDetailState.detail.project.id}/notes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(projectDetailState.noteForm),
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '处理记录保存失败')
    }
    projectDetailState.detail.notes.unshift(payload.note)
    projectDetailState.noteForm.content = ''
  } catch (error) {
    projectDetailState.noteError = error.message || '处理记录保存失败'
  } finally {
    projectDetailState.creatingNote = false
  }
}

async function updateProjectStatus(project) {
  projectState.actionError = ''
  projectState.updatingId = project.id

  try {
    const response = await fetch(`/api/projects/${project.id}/status/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status: project.pendingStatus,
      }),
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '项目状态更新失败')
    }
    const nextProject = normalizeProjectRow(payload.project)
    const index = projectState.projects.findIndex((item) => item.id === project.id)
    if (index >= 0) {
      projectState.projects.splice(index, 1, nextProject)
    }
  } catch (error) {
    projectState.actionError = error.message || '项目状态更新失败'
    project.pendingStatus = project.status
  } finally {
    projectState.updatingId = null
  }
}

function fillSampleTender() {
  agentForm.tenderText = sampleTenderText
}

function emptyCompanyProfile() {
  return {
    id: null,
    name: '',
    main_business: '',
    service_regions: '',
    max_project_amount: '',
    forbidden_conditions: '',
    qualifications: [],
    experiences: [],
  }
}

function emptyQualification() {
  return {
    name: '',
    certificate_no: '',
    issuer: '',
    valid_until: '',
  }
}

function emptyExperience() {
  return {
    name: '',
    industry: '',
    amount: '',
    client_name: '',
    completed_at: '',
    description: '',
  }
}

function applyCompanyProfile(profile) {
  const source = profile || emptyCompanyProfile()
  companyForm.id = source.id || null
  companyForm.name = source.name || ''
  companyForm.main_business = source.main_business || ''
  companyForm.service_regions = source.service_regions || ''
  companyForm.max_project_amount = source.max_project_amount ?? ''
  companyForm.forbidden_conditions = source.forbidden_conditions || ''
  companyForm.qualifications = source.qualifications?.length
    ? source.qualifications.map((item) => ({ ...emptyQualification(), ...item }))
    : [emptyQualification()]
  companyForm.experiences = source.experiences?.length
    ? source.experiences.map((item) => ({ ...emptyExperience(), ...item }))
    : [emptyExperience()]
}

async function loadCompanyProfile() {
  companyState.loading = true
  companyState.error = ''
  companyState.message = ''

  try {
    const response = await fetch('/api/company-profile/')
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '企业档案加载失败')
    }
    applyCompanyProfile(payload.company)
  } catch (error) {
    companyState.error = error.message || '企业档案加载失败'
    applyCompanyProfile(null)
  } finally {
    companyState.loading = false
  }
}

async function saveCompanyProfile() {
  companyState.error = ''
  companyState.message = ''
  if (!companyForm.name.trim()) {
    companyState.error = '请填写企业名称。'
    return
  }

  companyState.saving = true
  try {
    const response = await fetch('/api/company-profile/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...companyForm,
        qualifications: companyForm.qualifications.filter((item) => item.name.trim()),
        experiences: companyForm.experiences.filter((item) => item.name.trim()),
      }),
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '企业档案保存失败')
    }
    applyCompanyProfile(payload.company)
    companyState.message = '企业能力档案已保存，AI 分析会使用最新资料。'
  } catch (error) {
    companyState.error = error.message || '企业档案保存失败'
  } finally {
    companyState.saving = false
  }
}

function addQualification() {
  companyForm.qualifications.push(emptyQualification())
}

function removeQualification(index) {
  companyForm.qualifications.splice(index, 1)
  if (!companyForm.qualifications.length) {
    addQualification()
  }
}

function addExperience() {
  companyForm.experiences.push(emptyExperience())
}

function removeExperience(index) {
  companyForm.experiences.splice(index, 1)
  if (!companyForm.experiences.length) {
    addExperience()
  }
}

function handlePdfChange(event) {
  const [file] = event.target.files
  agentForm.pdfFile = file || null
}

function formatBudget(value) {
  if (!value) {
    return '-'
  }
  return `${Number(value).toLocaleString('zh-CN')} 元`
}

function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function decisionClass(decision) {
  return {
    'decision-recommended': decision === 'recommended',
    'decision-cautious': decision === 'cautious',
    'decision-negative': decision === 'not_recommended',
  }
}

function riskClass(level) {
  return {
    'risk-high': level === '高',
    'risk-medium': level === '中',
    'risk-low': level === '低',
  }
}

async function runAgentAnalysis() {
  agentState.error = ''
  agentState.report = null
  agentState.projectId = null
  agentState.reportId = null
  agentState.documentId = null

  if (!agentForm.companyId) {
    agentState.error = '请先选择企业档案。'
    return
  }
  if (!agentForm.tenderText.trim()) {
    agentState.error = '请粘贴招标文件文本。'
    return
  }

  agentState.loading = true
  try {
    const response = await fetch('/api/agent/analyze/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tender_text: agentForm.tenderText,
        company_id: agentForm.companyId,
        save: true,
      }),
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || '分析失败')
    }
    agentState.report = payload.report
    agentState.projectId = payload.project_id
    agentState.reportId = payload.report_id
    agentState.documentId = payload.document_id || null
    await loadRecentAgentProjects()
  } catch (error) {
    agentState.error = error.message || '分析失败，请稍后重试。'
  } finally {
    agentState.loading = false
  }
}

async function runPdfAnalysis() {
  agentState.error = ''
  agentState.report = null
  agentState.projectId = null
  agentState.reportId = null
  agentState.documentId = null

  if (!agentForm.companyId) {
    agentState.error = '请先选择企业档案。'
    return
  }
  if (!agentForm.pdfFile) {
    agentState.error = '请先上传 PDF 文件。'
    return
  }

  const formData = new FormData()
  formData.append('company_id', agentForm.companyId)
  formData.append('pdf_file', agentForm.pdfFile)

  agentState.loading = true
  try {
    const response = await fetch('/api/agent/analyze-pdf/', {
      method: 'POST',
      body: formData,
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || 'PDF分析失败')
    }
    agentState.report = payload.report
    agentState.projectId = payload.project_id
    agentState.reportId = payload.report_id
    agentState.documentId = payload.document_id
    await loadRecentAgentProjects()
  } catch (error) {
    agentState.error = error.message || 'PDF分析失败，请确认文件是否为文本型 PDF。'
  } finally {
    agentState.loading = false
  }
}

const features = [
  {
    index: '01',
    title: 'PDF智能解析',
    description: '支持招标文件、附件、澄清文件和扫描件解析，自动识别正文、表格、章节与页码来源。',
  },
  {
    index: '02',
    title: '招标信息抽取',
    description: '提取项目名称、编号、预算、投标截止、资格要求、评分标准、保证金和付款条件。',
  },
  {
    index: '03',
    title: '企业资质匹配',
    description: '将招标资格门槛与企业资质证书、服务范围、可承接金额和地区能力逐项比对。',
  },
  {
    index: '04',
    title: '历史业绩匹配',
    description: '自动查找企业过往类似项目，判断业绩年限、金额、行业、合同类型是否满足要求。',
  },
  {
    index: '05',
    title: '风险条款识别',
    description: '识别废标条款、付款周期、违约责任、工期压力、响应格式和商务偏离风险。',
  },
  {
    index: '06',
    title: '投标决策报告',
    description: '输出推荐理由、风险清单、缺失材料、关键要求与原文引用，支持后续导出和归档。',
  },
]

const productMatrix = [
  {
    type: '解析层',
    title: '多附件统一解析',
    description: '将招标正文、资格附件、评分表、合同条款和补遗文件统一纳入同一个分析任务。',
  },
  {
    type: '判断层',
    title: '企业画像动态匹配',
    description: '围绕资质、业绩、人员、地区、预算和业务范围生成匹配结论，减少人工漏判。',
  },
  {
    type: '报告层',
    title: '领导摘要与执行清单',
    description: '为管理层提供结论，为投标负责人提供材料清单、风险复核点和下一步动作。',
  },
]

const deliverables = [
  '项目关键信息摘要',
  '投标资格匹配表',
  '风险与废标条款清单',
  '缺失材料与补充建议',
  '投标决策建议报告',
]

const capabilityRows = [
  {
    question: '这份标我们能不能投？',
    answer: '综合企业资质、业务范围、地区限制、预算规模和禁投条件进行初步判断。',
    result: '输出推荐、谨慎或不建议投标。',
  },
  {
    question: '会不会因为材料问题废标？',
    answer: '识别资格证明、授权材料、响应格式、签章要求、保证金和截止时间。',
    result: '输出缺失材料与高风险条款。',
  },
  {
    question: '评分标准对我们是否有利？',
    answer: '拆解商务分、技术分、价格分和业绩分，判断企业优势与短板。',
    result: '输出评分友好度和补强方向。',
  },
  {
    question: '项目投入是否值得？',
    answer: '结合预算金额、合同周期、付款条件、竞争风险和交付压力进行评估。',
    result: '输出项目优先级和投入建议。',
  },
]

const systemFits = [
  {
    title: '独立筛标工作台',
    description: '适合中小型投标团队直接上传文件、查看报告、导出结论并进行项目流转。',
  },
  {
    title: '企业知识库增强',
    description: '与企业资质、案例、人员、证书、区域能力等档案结合，形成持续更新的匹配依据。',
  },
  {
    title: '投标管理系统扩展',
    description: '可作为现有 CRM、OA、项目管理或投标管理系统的 AI 分析模块。',
  },
]

const productChecklist = [
  {
    group: '资格',
    title: '主体资格与资质证书',
    description: '检查营业范围、资质等级、证书有效期、授权关系和供应商资格要求。',
  },
  {
    group: '业绩',
    title: '类似项目与金额门槛',
    description: '判断案例行业、合同金额、完成时间、验收材料和客户类型是否符合要求。',
  },
  {
    group: '商务',
    title: '付款、保证金与合同条件',
    description: '提取付款节点、履约保证、违约责任、报价方式和不可偏离条款。',
  },
  {
    group: '技术',
    title: '服务范围与响应要求',
    description: '识别技术参数、实施周期、验收标准、驻场要求和售后服务承诺。',
  },
]

const integrationSteps = [
  {
    step: '01',
    title: '企业档案建模',
    description: '录入资质、案例、人员、服务区域、业务方向和禁投条件。',
  },
  {
    step: '02',
    title: '文件解析接入',
    description: '接入 PDF、OCR、表格抽取和文本切分能力，形成可分析语料。',
  },
  {
    step: '03',
    title: 'AI 分析编排',
    description: '把抽取、分类、匹配、风险识别和报告生成串成稳定任务流。',
  },
  {
    step: '04',
    title: '协作与归档',
    description: '将分析结论进入项目状态流转、负责人跟进、报告导出和历史复盘。',
  },
]

const metrics = [
  { value: '1min', label: '单份文件初步分析' },
  { value: '10+', label: '核心投标判断维度' },
  { value: 'A/B/C', label: '项目优先级分层' },
]

const solutions = [
  {
    title: '经营与投标部门',
    description: '快速筛掉不匹配项目，将时间集中在高价值、高胜率、高契合度的标的上。',
  },
  {
    title: '售前与方案团队',
    description: '提前理解技术评分、服务范围、交付周期和响应材料，为方案准备争取时间。',
  },
  {
    title: '企业管理层',
    description: '用统一指标查看项目池质量、投标风险、推荐数量和放弃原因，提升管理透明度。',
  },
  {
    title: '招采信息团队',
    description: '批量处理公告和文件，自动归类项目来源、行业方向、地区分布与截止时间。',
  },
]

const roleWorkflows = [
  {
    owner: '经营负责人',
    title: '从项目池中筛选高价值机会',
    description: '按匹配度、预算金额、风险等级和截止时间进行排序，优先处理最值得投入的项目。',
  },
  {
    owner: '投标经理',
    title: '快速确认资格与材料缺口',
    description: '系统列出必须响应的资质、人员、业绩和商务材料，降低遗漏和废标概率。',
  },
  {
    owner: '方案负责人',
    title: '提前理解评分偏好',
    description: '识别技术分、商务分、价格分的权重，判断评分标准对企业优势是否友好。',
  },
  {
    owner: '管理层',
    title: '统一复盘投标质量',
    description: '沉淀推荐、放弃、报名、中标与未中标原因，为后续投标策略提供数据依据。',
  },
]

const governanceItems = [
  {
    title: '项目准入规则',
    description: '将金额下限、区域限制、行业方向、资质门槛和禁投条件配置为企业级判断规则。',
  },
  {
    title: '负责人处理机制',
    description: '对推荐项目、谨慎项目和高风险项目设置不同处理状态，避免项目无人跟进。',
  },
  {
    title: '投标质量复盘',
    description: '按中标率、放弃原因、风险类型和行业分布回看项目质量，优化后续筛选标准。',
  },
]

const adoptionSteps = [
  {
    title: '第一阶段：单文件智能分析',
    description: '先解决招标 PDF 快速阅读和投标建议输出问题。',
  },
  {
    title: '第二阶段：企业档案匹配',
    description: '录入资质、业绩、人员和业务范围，让判断结果更贴合企业实际。',
  },
  {
    title: '第三阶段：批量项目看板',
    description: '将多来源项目统一分层，形成投标机会池和负责人协作机制。',
  },
]

const departmentValues = [
  {
    department: '经营',
    title: '看项目质量',
    description: '关注项目是否符合企业方向、预算是否值得投入、是否存在明显禁投条件。',
  },
  {
    department: '投标',
    title: '看材料缺口',
    description: '关注资质、业绩、授权、签章、保证金和响应格式是否会造成废标。',
  },
  {
    department: '方案',
    title: '看技术胜率',
    description: '关注评分标准、技术参数、实施周期和交付要求是否符合团队能力。',
  },
  {
    department: '管理',
    title: '看投入产出',
    description: '关注项目优先级、团队占用、风险敞口和中标复盘数据。',
  },
]

const managementBenefits = [
  {
    title: '减少临时拍板',
    description: '用结构化报告替代碎片化讨论，让投标决策有统一依据。',
  },
  {
    title: '提升项目池透明度',
    description: '管理者能看到项目来源、行业分布、风险等级和负责人处理状态。',
  },
  {
    title: '持续优化投标策略',
    description: '从放弃原因和失败原因中发现企业能力短板，反向指导资质和案例建设。',
  },
]

const processSteps = [
  {
    step: 'Step 01',
    title: '上传招标文件',
    description: '上传 PDF、附件或扫描件，系统自动创建分析任务并记录文件状态。',
  },
  {
    step: 'Step 02',
    title: 'OCR与文本解析',
    description: '解析正文、目录、表格、页码和章节结构，为后续 AI 抽取提供干净语料。',
  },
  {
    step: 'Step 03',
    title: '关键信息抽取',
    description: '识别项目类型、采购方式、预算限价、资格要求、评分标准和合同条件。',
  },
  {
    step: 'Step 04',
    title: '企业能力匹配',
    description: '结合企业档案中的资质、业绩、人员、地区、业务范围和禁投条件进行比对。',
  },
  {
    step: 'Step 05',
    title: '风险评估',
    description: '综合商务、技术、时间、竞争和废标风险，形成可解释的风险等级。',
  },
  {
    step: 'Step 06',
    title: '生成决策报告',
    description: '输出投标建议、推荐原因、缺失材料、关键原文引用和后续处理动作。',
  },
]

const agents = [
  {
    title: '文档解析Agent',
    description: '负责 PDF、扫描件、表格和章节结构解析，尽可能保留页码和原文位置。',
  },
  {
    title: '资质匹配Agent',
    description: '将招标门槛与企业档案逐条比对，输出满足、缺失、疑似不满足三类结论。',
  },
  {
    title: '风险分析Agent',
    description: '识别付款、工期、违约、保证金、格式响应和废标条款中的关键风险。',
  },
  {
    title: '决策建议Agent',
    description: '综合匹配度、风险等级、材料缺口和竞争因素，形成投标建议与推荐理由。',
  },
]

const qualityControls = [
  {
    level: '字段级',
    title: '关键字段校验',
    description: '项目名称、金额、日期、保证金、开标方式等字段保留来源，便于人工复核。',
  },
  {
    level: '条款级',
    title: '风险条款定位',
    description: '付款、违约、工期、格式响应、废标条款等内容按风险类型归类。',
  },
  {
    level: '结论级',
    title: '建议理由拆解',
    description: '投标建议由匹配度、缺口、风险、竞争与投入产出共同支撑。',
  },
]

const decisionLogic = [
  {
    title: '匹配度不是唯一标准',
    description: '即使资质匹配，也会结合付款压力、交付难度和评分偏好判断是否值得投入。',
  },
  {
    title: '风险项区分轻重缓急',
    description: '系统将风险分为提示、需复核、高风险三类，帮助负责人快速排序处理。',
  },
  {
    title: '报告支持二次追问',
    description: '后续可结合问答 Agent 追问资质要求、评分标准、废标风险和材料清单。',
  },
]

const exceptionHandling = [
  {
    type: '扫描件',
    title: '低质量文本提醒',
    description: '当 OCR 置信度不足或表格结构复杂时，系统标记为需人工复核。',
  },
  {
    type: '冲突项',
    title: '多处条款不一致',
    description: '当公告、正文、附件或补遗文件存在时间和金额冲突时，系统提示对照确认。',
  },
  {
    type: '模糊项',
    title: '要求表达不明确',
    description: '对“类似项目”“相关资质”“不少于”等模糊表述保留原文，避免过度判断。',
  },
]

const auditTrail = [
  {
    title: '任务记录',
    description: '记录上传文件、分析时间、分析版本和处理状态，便于后续追踪。',
  },
  {
    title: '结论记录',
    description: '保留每次推荐结论、评分结果、风险等级和修改前后的处理意见。',
  },
  {
    title: '证据记录',
    description: '关键字段和风险判断关联原文页码、章节或附件来源，方便复核审计。',
  },
]

const scenes = [
  {
    title: '政府采购项目',
    description: '识别采购方式、资格条件、评分标准和政府采购常见响应要求。',
  },
  {
    title: '工程与建设项目',
    description: '关注资质等级、项目经理要求、工期、保证金、履约责任和工程业绩。',
  },
  {
    title: '软件信息化项目',
    description: '匹配软件著作权、系统集成能力、类似案例、技术方案要求和交付周期。',
  },
  {
    title: '服务采购项目',
    description: '分析人员配置、服务范围、驻场要求、服务期限、考核标准和付款节点。',
  },
  {
    title: '框架协议采购',
    description: '识别入围规则、报价方式、服务区域、二次竞价机制和长期履约风险。',
  },
  {
    title: '批量公告筛选',
    description: '对每天新增的大量招标文件进行自动分层，优先推送高匹配项目。',
  },
]

const scenarioDetails = [
  {
    title: '高频政府采购',
    focus: '重点关注采购方式、资格条件、评分标准、政策性要求和响应文件格式。',
    output: '适合批量公告初筛与投标优先级排序。',
  },
  {
    title: '大型信息化项目',
    focus: '重点关注技术方案、系统集成能力、案例相似度、交付周期和运维要求。',
    output: '适合售前团队快速判断方案准备难度。',
  },
  {
    title: '工程建设项目',
    focus: '重点关注资质等级、项目经理、工期节点、安全责任、履约保证和同类业绩。',
    output: '适合工程类企业控制资格风险与履约风险。',
  },
]

const industryPlaybooks = [
  {
    title: '信息化与软件服务',
    description: '关注技术路线、系统集成能力、运维服务、案例相似度、知识产权和交付周期。',
  },
  {
    title: '工程建设与施工',
    description: '关注资质等级、项目经理、施工周期、安全责任、履约保证和同类工程业绩。',
  },
  {
    title: '综合服务采购',
    description: '关注服务团队、驻场要求、服务区域、考核方式、付款节点和长期履约能力。',
  },
  {
    title: '货物与设备采购',
    description: '关注授权证明、供货周期、售后服务、质保要求、检测报告和价格评分规则。',
  },
]

const batchScreening = [
  {
    metric: '批量导入',
    title: '每天新增公告自动入池',
    description: '对多个招标文件同时解析，按行业、地区、金额、截止时间自动归类。',
  },
  {
    metric: '优先级',
    title: '高匹配项目优先推送',
    description: '先让团队看到更值得投入的项目，减少无序阅读和临时决策。',
  },
  {
    metric: '预警',
    title: '截止时间和风险同步提醒',
    description: '对报名、保证金、投标截止和高风险条款进行提醒，避免错过关键节点。',
  },
]

const evaluationDimensions = [
  {
    weight: '资质',
    title: '准入条件',
    description: '判断企业是否具备投标资格，是所有场景的第一层筛选。',
  },
  {
    weight: '业绩',
    title: '类似案例',
    description: '判断过往项目是否能支撑评分和资格要求，尤其影响服务、工程和信息化项目。',
  },
  {
    weight: '商务',
    title: '合同风险',
    description: '关注付款周期、保证金、违约责任和报价方式，决定项目投入边界。',
  },
  {
    weight: '技术',
    title: '交付难度',
    description: '关注实施周期、技术参数、服务范围和验收要求，判断方案准备压力。',
  },
]

const sceneQuestions = [
  {
    question: '这个场景最容易漏掉什么？',
    answer: '不同场景风险不同，系统会按行业词典提示容易忽视的资格、材料和合同要求。',
  },
  {
    question: '批量项目如何排序？',
    answer: '先按企业匹配度和截止时间分层，再结合风险等级和预算规模决定处理顺序。',
  },
  {
    question: '为什么同样是推荐投标，优先级不同？',
    answer: '推荐结论还会结合投入成本、竞争优势、付款条件和交付压力形成优先级。',
  },
]
</script>
