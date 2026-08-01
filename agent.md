# AI招投标Agent 项目说明

## 项目定位

AI招投标Agent 是面向企业投标团队的智能招标文件分析与投标决策平台。

目标用户每天需要阅读大量招标文件，本系统希望通过上传 PDF、自动解析招标内容、匹配企业资质与业绩、识别投标风险，并输出结构化分析报告，帮助企业快速判断项目是否值得投标。

核心判断结果包括：

- 推荐投标
- 谨慎投标
- 不建议投标

核心分析维度包括：

- 招标类型
- 企业业务范围匹配
- 企业资质匹配
- 历史业绩匹配
- 项目金额匹配
- 地区与服务范围匹配
- 人员与交付能力匹配
- 废标风险
- 商务风险
- 技术风险
- 时间风险

## 当前技术栈

后端：

- Python 3.14.5
- Django 6.0.6
- SQLite
- django-simpleui 2026.1.13

前端：

- Vue 3
- Vite
- npm

当前集成方式：

- Django 提供主服务入口。
- Vue 前台源码位于 `frontend/`。
- Vue 构建产物输出到 `static/frontend/`。
- Django 根路径 `/` 返回 Vue 构建后的 `index.html`。
- Django 后台 `/admin/` 使用 SimpleUI。

## 目录结构

```text
D:\2
├── .venv
├── bid_agent
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── tenders
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── frontend
│   ├── src
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── package.json
│   └── vite.config.js
├── static
│   └── frontend
├── logs
├── db.sqlite3
├── manage.py
├── requirements.txt
└── agent.md
```

## 后端配置要点

Django 项目名：

```text
bid_agent
```

Django 应用名：

```text
tenders
```

后台主题：

```python
INSTALLED_APPS = [
    'simpleui',
    'django.contrib.admin',
    ...
]
```

默认语言和时区：

```python
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
```

静态资源配置：

```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

前台路由：

```python
urlpatterns = [
    path('', frontend_app, name='frontend_app'),
    path('admin/', admin.site.urls),
]
```

`tenders.views.frontend_app` 负责返回：

```text
static/frontend/index.html
```

## 前端配置要点

Vue 项目位置：

```text
D:\2\frontend
```

Vite 构建配置：

```js
export default defineConfig({
  base: '/static/frontend/',
  plugins: [vue()],
  build: {
    outDir: '../static/frontend',
    emptyOutDir: true,
  },
})
```

这表示：

- 开发 Vue 时修改 `frontend/src/`。
- 发布到 Django 前台时运行 `npm.cmd run build`。
- 构建后的文件进入 `static/frontend/`。
- Django 通过 `/static/frontend/...` 提供 JS、CSS、图片等资源。

## 本地启动

进入项目目录：

```powershell
cd D:\2
```

激活 Python 虚拟环境：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
```

启动 Django：

```powershell
python manage.py runserver 127.0.0.1:8001
```

访问前台：

```text
http://127.0.0.1:8001/
```

访问后台：

```text
http://127.0.0.1:8001/admin/
```

## 前端开发与构建

进入前端目录：

```powershell
cd D:\2\frontend
```

安装依赖：

```powershell
npm.cmd install
```

本地前端开发服务：

```powershell
npm.cmd run dev
```

构建给 Django 使用：

```powershell
npm.cmd run build
```

每次修改 Vue 前端后，如果希望通过 Django 的 `http://127.0.0.1:8001/` 看到最新页面，都需要重新运行：

```powershell
npm.cmd run build
```

## 后台超级管理员

当前已创建超级管理员：

```text
账号：xiaosukeji
密码：123123
邮箱：3096864933@qq.com
昵称：xskj
```

说明：

- 当前使用 Django 默认用户模型。
- 默认用户模型没有 `nickname` 字段。
- 昵称 `xskj` 当前写入默认用户模型的 `first_name` 字段。

## 当前前台页面

当前 Vue 前台已经替换 Django 默认首页，页面内容围绕 AI招投标Agent 展示，包括：

- 顶部导航
- 上传招标文件入口
- AI 分析摘要面板
- PDF 到投标决策流程
- 招标类型识别
- 资质与业绩匹配
- 风险与废标条款识别
- 投标材料清单
- 批量项目筛选看板
- 后台管理入口

当前页面主要文件：

```text
frontend/src/App.vue
frontend/src/style.css
```

## 后续产品模块建议

建议按以下顺序继续开发：

1. 企业能力档案
2. 招标项目模型
3. PDF 文件上传
4. PDF 文本解析
5. AI 信息抽取任务
6. 招标类型识别
7. 企业资质匹配
8. 风险识别
9. 投标决策报告
10. 项目列表与筛选
11. 报告导出
12. AI 问答助手
13. 提醒与预警

## 推荐 Django 数据模型方向

后续可在 `tenders/models.py` 中逐步增加：

- `CompanyProfile`：企业档案
- `Qualification`：资质证书
- `ProjectExperience`：历史业绩
- `TenderProject`：招标项目
- `TenderDocument`：招标文件
- `AnalysisTask`：AI 分析任务
- `AnalysisReport`：分析报告
- `RiskItem`：风险项
- `MaterialChecklistItem`：投标材料清单

## 开发注意事项

- 不要删除 `.venv`，这是当前 Python 虚拟环境。
- 不要直接编辑 `static/frontend/assets/` 里的构建产物，应修改 `frontend/src/` 后重新构建。
- 如果前台页面空白，优先检查 `/static/frontend/assets/*.js` 和 `/static/frontend/assets/*.css` 是否返回 200。
- 如果 PowerShell 无法执行 `npm`，使用 `npm.cmd`。
- 如果 PowerShell 无法激活虚拟环境，先执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

- 当前开发环境使用 SQLite，后续生产环境建议迁移到 PostgreSQL 或 MySQL。
- 当前 Django `SECRET_KEY` 是开发环境默认值，生产部署前必须改为环境变量。
- 当前 `DEBUG = True`，生产部署前必须关闭。

## 验证命令

Django 配置检查：

```powershell
cd D:\2
.\.venv\Scripts\python.exe manage.py check
```

Vue 构建检查：

```powershell
cd D:\2\frontend
npm.cmd run build
```

HTTP 验证：

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/" -UseBasicParsing
Invoke-WebRequest -Uri "http://127.0.0.1:8001/admin/" -UseBasicParsing
```
