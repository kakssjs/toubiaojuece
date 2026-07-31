# Workspace Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Rework the current marketing-style Vue homepage into an executive workspace dashboard while preserving the existing product modules and Django-backed data flows.

**Architecture:** Keep the current lightweight Vue SPA approach, but split the oversized homepage and shared UI into focused components. The homepage becomes a dashboard view fed by existing Django APIs, while existing module pages like agent analysis, projects, reports, and company profile remain accessible through a new workspace navigation structure.

**Tech Stack:** Vue 3, Vite, Django JSON APIs, static build output to `static/frontend/`

---

## File Structure

### Existing files to modify

- Modify: `frontend/src/App.vue`
  Current monolithic view/router/data store. It will remain the main shell and page switcher, but homepage-specific markup should move out into dedicated components.

- Modify: `frontend/src/style.css`
  Current global stylesheet. It will keep shared tokens and layout rules, but homepage dashboard styles should be grouped and legacy homepage marketing blocks should be reduced or removed.

### New files to create

- Create: `frontend/src/components/workspace/WorkspaceDashboard.vue`
  Executive dashboard homepage view containing the top summary region, metric cards, opportunity list, and right rail.

- Create: `frontend/src/components/workspace/WorkspaceSidebar.vue`
  Stable workspace navigation for dashboard-oriented information architecture.

- Create: `frontend/src/components/workspace/WorkspaceMetrics.vue`
  Reusable metric card strip for the four top-level KPIs.

- Create: `frontend/src/components/workspace/WorkspaceOpportunityList.vue`
  Priority-ranked opportunity list rendered from existing project API data.

- Create: `frontend/src/components/workspace/WorkspaceQuickActions.vue`
  Right-rail module for quick PDF analysis entry and risk reminders.

## Task 1: Create the implementation scaffold for workspace components

**Files:**
- Create: `frontend/src/components/workspace/WorkspaceDashboard.vue`
- Create: `frontend/src/components/workspace/WorkspaceSidebar.vue`
- Create: `frontend/src/components/workspace/WorkspaceMetrics.vue`
- Create: `frontend/src/components/workspace/WorkspaceOpportunityList.vue`
- Create: `frontend/src/components/workspace/WorkspaceQuickActions.vue`

- [x] **Step 1: Create the workspace component directory**

Use `apply_patch` to create the five new Vue component files under `frontend/src/components/workspace/`.

- [x] **Step 2: Add minimal component shells**

Create each file with a minimal `<template>` and `<script setup>` block so the app can import them without failing.

Expected component responsibilities:

- `WorkspaceSidebar.vue`: receives `navItems`, `currentPage`, `companyName`, `profileCompleteness`
- `WorkspaceMetrics.vue`: receives a `metrics` array
- `WorkspaceOpportunityList.vue`: receives prioritized `projects`
- `WorkspaceQuickActions.vue`: receives quick analysis state and risk reminders
- `WorkspaceDashboard.vue`: composes the above components

- [x] **Step 3: Run a build to verify the empty scaffolding does not break Vite**

Run: `npm.cmd run build`

Expected: build succeeds and writes output into `static/frontend/`

- [x] **Step 4: Commit scaffold changes**

```bash
git add frontend/src/components/workspace
git commit -m "feat: scaffold workspace dashboard components"
```

## Task 2: Move homepage layout into a dedicated dashboard view

**Files:**
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/components/workspace/WorkspaceDashboard.vue`
- Create: `frontend/src/components/workspace/WorkspaceSidebar.vue`

- [x] **Step 1: Update `App.vue` imports**

Import the new workspace components and remove direct homepage dashboard markup from the `home` branch of the main template.

- [x] **Step 2: Replace the current homepage hero block with `WorkspaceDashboard`**

The `currentPage === 'home'` branch should render the new dashboard component instead of the current marketing hero, stats, editorial, and value-grid sections.

- [x] **Step 3: Replace top marketing navigation usage with workspace-style nav props**

Keep the current page-switching model, but pass dashboard-oriented navigation labels into `WorkspaceSidebar.vue`.

Navigation target labels should map to existing pages:

- `经营总览` -> `home`
- `智能分析` -> `agent`
- `机会池` -> `projects`
- `项目看板` -> `projects`
- `报告中心` -> report-oriented routes already present in `App.vue`
- `企业档案` -> `company`

- [x] **Step 4: Render current company summary in sidebar**

Use existing company profile data already loaded in `App.vue` to derive:

- `companyName`
- `profileCompleteness`

If there is no saved profile yet, render fallback values instead of leaving the sidebar blank.

- [x] **Step 5: Run build to verify the homepage view swap**

Run: `npm.cmd run build`

Expected: build succeeds and the app still renders all routes after static generation.

- [x] **Step 6: Commit the homepage view extraction**

```bash
git add frontend/src/App.vue frontend/src/components/workspace/WorkspaceDashboard.vue frontend/src/components/workspace/WorkspaceSidebar.vue
git commit -m "feat: extract workspace dashboard homepage"
```

## Task 3: Map existing Django data into dashboard metrics and opportunity ranking

**Files:**
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/components/workspace/WorkspaceMetrics.vue`
- Create: `frontend/src/components/workspace/WorkspaceOpportunityList.vue`

- [x] **Step 1: Identify existing project/company fetch logic in `App.vue`**

Reuse the current dashboard/project API integration rather than creating new endpoints.

Primary sources should stay:

- `/api/projects/`
- `/api/company-profile/`

- [x] **Step 2: Derive dashboard metrics in `App.vue`**

Create computed or helper-derived values for:

- `待评估机会`
- `推荐投标`
- `高风险项目`
- `平均匹配度`

Use the existing project payload fields like:

- `decision`
- `risk_level`
- `match_score`

- [x] **Step 3: Derive priority-ranked opportunity list**

Create a sorted top list from existing projects using this order:

1. recommended over cautious over not recommended
2. nearest deadline if present, otherwise newest projects first
3. higher match score
4. lower risk when scores are similar

If current API data lacks enough deadline detail, use the best available fallback ordering and keep the implementation local to the frontend.

- [x] **Step 4: Pass metrics and prioritized projects into the dashboard child components**

`WorkspaceDashboard.vue` should receive only the data it needs and pass smaller prop slices into `WorkspaceMetrics.vue` and `WorkspaceOpportunityList.vue`.

- [x] **Step 5: Build and verify metric rendering**

Run: `npm.cmd run build`

Expected: build succeeds, and dashboard data bindings compile cleanly.

- [x] **Step 6: Commit data-mapping changes**

```bash
git add frontend/src/App.vue frontend/src/components/workspace/WorkspaceMetrics.vue frontend/src/components/workspace/WorkspaceOpportunityList.vue
git commit -m "feat: wire dashboard metrics and opportunities"
```

## Task 4: Add quick analysis entry and risk reminders to the dashboard rail

**Files:**
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/components/workspace/WorkspaceQuickActions.vue`

- [x] **Step 1: Reuse existing analysis actions from `App.vue`**

Do not duplicate the full agent page. Expose a lightweight dashboard entry that reuses the same upload and analysis handlers already present for the agent flow.

- [x] **Step 2: Define dashboard risk reminder data**

Derive a concise set of alerts from existing project and report data, such as:

- high-risk projects
- recommended projects needing follow-up
- missing materials if available in current loaded state

Keep the reminder count small and actionable.

- [x] **Step 3: Render quick actions rail in `WorkspaceQuickActions.vue`**

Include:

- quick PDF upload trigger
- analysis CTA
- a compact reminder list

This is a shortcut surface, not the full agent workbench.

- [x] **Step 4: Keep full analysis on the `agent` page unchanged**

The dashboard rail must link or hand off into the existing `agent` workflow instead of re-implementing all result details in the sidebar.

- [x] **Step 5: Run build after wiring the right rail**

Run: `npm.cmd run build`

Expected: build succeeds and the quick action rail compiles with the current app state.

- [x] **Step 6: Commit quick action integration**

```bash
git add frontend/src/App.vue frontend/src/components/workspace/WorkspaceQuickActions.vue
git commit -m "feat: add dashboard quick analysis rail"
```

## Task 5: Refine shared styles for a workspace system instead of a marketing homepage

**Files:**
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/components/workspace/WorkspaceDashboard.vue`
- Modify: `frontend/src/components/workspace/WorkspaceSidebar.vue`
- Modify: `frontend/src/components/workspace/WorkspaceMetrics.vue`
- Modify: `frontend/src/components/workspace/WorkspaceOpportunityList.vue`
- Modify: `frontend/src/components/workspace/WorkspaceQuickActions.vue`

- [x] **Step 1: Add or reorganize CSS tokens for dashboard surfaces**

Keep the existing brand palette, but define clear shared surface values for:

- workspace shell background
- sidebar background
- raised panels
- muted text
- warning and danger accents

- [x] **Step 2: Remove homepage-first hero styling from the active `home` path**

The current oversized hero and editorial sections should no longer shape the homepage visual hierarchy.

- [x] **Step 3: Style dashboard sections for scanability**

Ensure the homepage supports:

- dense but readable cards
- stable grid alignment
- quick scanning of metrics and project rows
- restrained but intentional visual hierarchy

- [x] **Step 4: Keep mobile behavior intact**

Reuse or extend responsive rules so the dashboard stacks cleanly on narrow screens without text overlap or broken button layouts.

- [x] **Step 5: Run build after style rework**

Run: `npm.cmd run build`

Expected: build succeeds with updated CSS bundle.

- [x] **Step 6: Commit dashboard styling pass**

```bash
git add frontend/src/style.css frontend/src/components/workspace
git commit -m "feat: restyle homepage as workspace dashboard"
```

## Task 6: Verify the Django-served frontend end to end

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/components/workspace/*.vue`

- [x] **Step 1: Rebuild the frontend for Django**

Run: `npm.cmd run build`

Expected: fresh files are emitted into `static/frontend/`

- [x] **Step 2: Verify Django health**

Run: `D:\\2\\.venv\\Scripts\\python.exe manage.py check`

Expected: `System check identified no issues (0 silenced).`

- [x] **Step 3: Verify homepage HTML is served**

Run:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/" -UseBasicParsing
```

Expected: `StatusCode` is `200`

- [x] **Step 4: Verify project API still serves data**

Run:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/projects/" -UseBasicParsing
```

Expected: `StatusCode` is `200`

- [x] **Step 5: Visually inspect the homepage in the browser**

Check that:

- the new dashboard appears on `/`
- navigation still moves between existing product modules
- metrics, opportunity list, and quick actions render without blank states breaking layout

- [x] **Step 6: Commit final verified implementation**

```bash
git add frontend/src frontend/index.html static/frontend docs/superpowers/plans/2026-06-27-workspace-dashboard-implementation.md
git commit -m "feat: redesign homepage as workspace dashboard"
```

## Self-Review

### Spec coverage

Covered spec requirements:

- executive dashboard homepage
- workspace navigation structure
- top KPI metric cards
- prioritized opportunity list
- quick analysis entry
- risk reminders
- reuse of existing business modules
- limited component extraction from `App.vue`

Not included by design:

- permissions
- message center
- drag-and-drop process board
- new backend subsystems

### Placeholder scan

The plan uses exact file paths, exact commands, and bounded feature steps. No `TODO`, `TBD`, or vague “add handling later” placeholders remain.

### Type consistency

Component names, route labels, and API sources are consistent across tasks:

- `WorkspaceDashboard`
- `WorkspaceSidebar`
- `WorkspaceMetrics`
- `WorkspaceOpportunityList`
- `WorkspaceQuickActions`

