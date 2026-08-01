<template>
  <section class="security-trust-section" aria-labelledby="security-trust-title">
    <div class="security-trust-intro">
      <div class="security-shield"><ShieldCheckIcon /></div>
      <p class="section-kicker">ENTERPRISE DATA SECURITY</p>
      <h2 id="security-trust-title">企业标书，始终由企业掌控</h2>
      <p>从上传、分析到结果存储，按企业级权限边界处理敏感材料，降低标书外泄与跨账号访问风险。</p>
      <div class="security-status"><span></span>安全机制运行中</div>
    </div>

    <div class="security-trust-grid">
      <article v-for="item in protections" :key="item.title">
        <div class="security-feature-icon"><component :is="item.icon" /></div>
        <div><span>{{ item.eyebrow }}</span><h3>{{ item.title }}</h3><p>{{ item.description }}</p></div>
        <CheckCircleIcon class="security-check" />
      </article>
    </div>

    <footer class="security-trust-footer">
      <span><LockClosedIcon />传输链路使用 HTTPS 加密</span>
      <span><EyeSlashIcon />非授权账号不可查看企业文件</span>
      <a href="/company/">查看企业权限设置 <ArrowRightIcon /></a>
    </footer>
  </section>
</template>

<script setup>
import {
  ArrowPathIcon,
  ArrowRightIcon,
  BuildingOffice2Icon,
  CheckCircleIcon,
  CircleStackIcon,
  EyeSlashIcon,
  LockClosedIcon,
  ShieldCheckIcon,
} from '@heroicons/vue/24/outline'

const protections = [
  { eyebrow: 'ENCRYPTED', title: '文件加密传输与存储', description: '上传链路采用 HTTPS，文件进入受控的私有存储空间。', icon: LockClosedIcon },
  { eyebrow: 'LIFECYCLE', title: '文件生命周期管理', description: '支持按企业策略清理分析后的原始文件，减少长期留存风险。', icon: ArrowPathIcon },
  { eyebrow: 'ISOLATED', title: '企业数据隔离', description: '通过账号与企业归属校验，隔离不同企业的项目、报告和材料。', icon: CircleStackIcon },
  { eyebrow: 'PRIVATE', title: '支持私有化部署', description: '可面向企业专属环境规划独立部署、权限和数据留存方案。', icon: BuildingOffice2Icon },
]
</script>
