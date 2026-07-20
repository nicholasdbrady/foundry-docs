'use strict';
const PptxGenJS = require('pptxgenjs');
const path = require('path');
const fs = require('fs');

// ── Palette: Midnight Executive ────────────────────────────────────────────
const C = {
  navy:     '1E2761',
  ice:      'CADCFC',
  teal:     '028090',
  seafoam:  '00A896',
  mint:     '02C39A',
  white:    'FFFFFF',
  offwhite: 'F0F4FF',
  dark:     '0D1440',
  gray:     '8899BB',
  lightgray:'D0D8EE',
  accent:   'FF6B6B',
  gold:     'FFD166',
  green:    '06D6A0',
};

const W = 13.33; // slide width inches (widescreen)
const H = 7.5;

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';

// ─────────────────────────────────────────────────────────────────────────────
// Helper: add background rect
function bg(slide, color) {
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color } });
}

function accentBar(slide, color = C.teal) {
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.08, h: H, fill: { color } });
}

function title(slide, text, opts = {}) {
  slide.addText(text, {
    x: opts.x ?? 0.5, y: opts.y ?? 0.25,
    w: opts.w ?? W - 1, h: opts.h ?? 0.85,
    fontSize: opts.fs ?? 32, bold: true, color: opts.color ?? C.white,
    fontFace: 'Calibri',
  });
}

function subtitle(slide, text, opts = {}) {
  slide.addText(text, {
    x: opts.x ?? 0.5, y: opts.y ?? 1.1,
    w: opts.w ?? W - 1, h: opts.h ?? 0.5,
    fontSize: opts.fs ?? 16, color: opts.color ?? C.ice,
    fontFace: 'Calibri',
  });
}

function body(slide, text, opts = {}) {
  slide.addText(text, {
    x: opts.x ?? 0.5, y: opts.y ?? 1.6,
    w: opts.w ?? W - 1, h: opts.h ?? 4.5,
    fontSize: opts.fs ?? 14, color: opts.color ?? C.offwhite,
    fontFace: 'Calibri', valign: 'top',
  });
}

function tag(slide, text, x, y, bgColor = C.teal, textColor = C.white) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w: 1.8, h: 0.38, fill: { color: bgColor }, rectRadius: 0.1 });
  slide.addText(text, { x, y, w: 1.8, h: 0.38, fontSize: 11, bold: true, color: textColor, align: 'center', valign: 'middle', fontFace: 'Calibri' });
}

function metricBox(slide, value, label, x, y, accent = C.teal) {
  slide.addShape(pptx.ShapeType.rect, { x, y, w: 2.4, h: 1.3, fill: { color: C.dark }, line: { color: accent, width: 2 } });
  slide.addText(value, { x, y: y + 0.1, w: 2.4, h: 0.7, fontSize: 28, bold: true, color: accent, align: 'center', fontFace: 'Calibri' });
  slide.addText(label, { x, y: y + 0.75, w: 2.4, h: 0.45, fontSize: 11, color: C.ice, align: 'center', fontFace: 'Calibri' });
}

function sectionDot(slide, text, x, y, color = C.teal) {
  slide.addShape(pptx.ShapeType.ellipse, { x, y: y + 0.04, w: 0.18, h: 0.18, fill: { color } });
  slide.addText(text, { x: x + 0.28, y, w: 3.5, h: 0.28, fontSize: 13, color: C.offwhite, fontFace: 'Calibri' });
}

function divider(slide, y, color = C.teal) {
  slide.addShape(pptx.ShapeType.line, { x: 0.5, y, w: W - 1, h: 0, line: { color, width: 1 } });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 1 — Title
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  // gradient band
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 2.8, w: W, h: 0.06, fill: { color: C.teal } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 2.86, w: W, h: 0.04, fill: { color: C.seafoam } });

  // Decorative circles
  s.addShape(pptx.ShapeType.ellipse, { x: 10.5, y: -1, w: 4, h: 4, fill: { color: C.navy }, line: { color: C.teal, width: 1 } });
  s.addShape(pptx.ShapeType.ellipse, { x: 11.2, y: 4.5, w: 2.5, h: 2.5, fill: { color: C.dark }, line: { color: C.seafoam, width: 1 } });

  s.addText('foundry-docs', {
    x: 0.6, y: 0.6, w: 9, h: 0.7,
    fontSize: 20, bold: false, color: C.teal, fontFace: 'Calibri',
  });
  s.addText('Agentic Documentation\nfor Microsoft Foundry', {
    x: 0.6, y: 1.3, w: 9.5, h: 2.2,
    fontSize: 44, bold: true, color: C.white, fontFace: 'Calibri',
  });
  s.addText('FastMCP · GitHub Copilot Agentic Workflows · Azure AI Search · Mintlify MDX', {
    x: 0.6, y: 3.3, w: 10, h: 0.5,
    fontSize: 15, color: C.ice, fontFace: 'Calibri',
  });
  s.addText('July 2026', {
    x: 0.6, y: 6.8, w: 3, h: 0.4,
    fontSize: 13, color: C.gray, fontFace: 'Calibri',
  });
  s.addText('nicholasdbrady/foundry-docs', {
    x: 9, y: 6.8, w: 4, h: 0.4,
    fontSize: 12, color: C.gray, align: 'right', fontFace: 'Calibri',
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 2 — What is Foundry-Docs
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.teal);
  title(s, 'What is Foundry-Docs?');
  divider(s, 1.08);

  // Left column: description
  s.addText([
    { text: 'A FastMCP server ', options: { bold: true, color: C.white } },
    { text: 'that extracts Microsoft Foundry documentation from upstream MicrosoftDocs/azure-ai-docs, converts it to ', options: { color: C.ice } },
    { text: 'Mintlify MDX', options: { bold: true, color: C.teal } },
    { text: ', and serves it via two intelligent MCP servers.', options: { color: C.ice } },
  ], { x: 0.5, y: 1.25, w: 7.5, h: 1.1, fontSize: 15, fontFace: 'Calibri' });

  const cards = [
    { label: 'foundry-docs-mcp', desc: 'Primary content\ndocs/ (canonical)', color: C.teal },
    { label: 'foundry-docs-vnext', desc: 'A/B/C/D variant\ndocs-vnext/ (agent-improved)', color: C.seafoam },
  ];
  cards.forEach((c, i) => {
    const x = 0.5 + i * 4.0;
    s.addShape(pptx.ShapeType.rect, { x, y: 2.5, w: 3.7, h: 1.5, fill: { color: C.navy }, line: { color: c.color, width: 2 } });
    s.addText(c.label, { x, y: 2.6, w: 3.7, h: 0.5, fontSize: 15, bold: true, color: c.color, align: 'center', fontFace: 'Calibri' });
    s.addText(c.desc, { x, y: 3.1, w: 3.7, h: 0.7, fontSize: 12, color: C.ice, align: 'center', fontFace: 'Calibri' });
  });

  // Key capabilities
  const caps = [
    '🔍  Hybrid Search — Azure AI Search (vector + keyword + semantic) + local TF-IDF fallback',
    '🤖  Agentic Workflows — 29 GitHub Actions workflows monitoring, improving, and testing docs',
    '📊  Evaluation Harness — 4-server × multi-model comparison (200 evaluations per run)',
    '🔄  Auto-Sync — Daily upstream sync from MicrosoftDocs/azure-ai-docs',
  ];
  caps.forEach((c, i) => {
    s.addText(c, {
      x: 0.5, y: 4.2 + i * 0.55, w: 12.3, h: 0.48,
      fontSize: 13, color: C.offwhite, fontFace: 'Calibri',
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 3 — Architecture
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.mint);
  title(s, 'Architecture & Ingestion Pipeline', { color: C.white });
  divider(s, 1.08);

  // Pipeline boxes
  const steps = [
    { n: '1', label: 'extract_manifest', sub: 'Parse TOC files\ninto manifest', color: C.teal },
    { n: '2', label: 'download_docs', sub: 'Fetch raw docs\nfrom GitHub', color: C.seafoam },
    { n: '3', label: 'convert_to_mdx', sub: 'MS Learn MD →\nMintlify MDX', color: C.mint },
    { n: '4', label: 'build_navigation', sub: 'Generate docs.json\nnav config', color: C.teal },
    { n: '5', label: 'ingest_to_azure', sub: 'Chunk → embed →\nupsert (hash-based)', color: C.seafoam },
  ];
  const boxW = 2.3, boxH = 1.4, startX = 0.4, stepY = 1.4;
  steps.forEach((st, i) => {
    const x = startX + i * (boxW + 0.12);
    s.addShape(pptx.ShapeType.rect, { x, y: stepY, w: boxW, h: boxH, fill: { color: C.navy }, line: { color: st.color, width: 2 } });
    s.addText(st.n, { x, y: stepY + 0.05, w: boxW, h: 0.35, fontSize: 18, bold: true, color: st.color, align: 'center', fontFace: 'Calibri' });
    s.addText(st.label, { x, y: stepY + 0.38, w: boxW, h: 0.35, fontSize: 10, bold: true, color: C.white, align: 'center', fontFace: 'Calibri' });
    s.addText(st.sub, { x, y: stepY + 0.72, w: boxW, h: 0.6, fontSize: 10, color: C.ice, align: 'center', fontFace: 'Calibri' });
    if (i < steps.length - 1) {
      s.addShape(pptx.ShapeType.line, { x: x + boxW, y: stepY + boxH / 2, w: 0.12, h: 0, line: { color: st.color, width: 2 } });
    }
  });

  // Dual search mode
  s.addText('Dual Search Mode', { x: 0.5, y: 3.05, w: 5, h: 0.4, fontSize: 14, bold: true, color: C.gold, fontFace: 'Calibri' });
  const searchBoxes = [
    { label: 'Local TF-IDF', desc: 'Always-on fallback\nLoaded at startup\nfrom .mdx files', color: C.teal },
    { label: 'Azure AI Search', desc: 'Keyword + Vector\n+ Semantic reranking\nActivated via env var', color: C.mint },
  ];
  searchBoxes.forEach((b, i) => {
    const x = 0.5 + i * 3.2;
    s.addShape(pptx.ShapeType.rect, { x, y: 3.5, w: 3.0, h: 1.3, fill: { color: C.dark }, line: { color: b.color, width: 1.5 } });
    s.addText(b.label, { x, y: 3.55, w: 3.0, h: 0.4, fontSize: 13, bold: true, color: b.color, align: 'center', fontFace: 'Calibri' });
    s.addText(b.desc, { x, y: 3.95, w: 3.0, h: 0.75, fontSize: 11, color: C.ice, align: 'center', fontFace: 'Calibri' });
  });

  // Right panel: key infra
  const infra = [
    { label: 'Chunker', detail: 'h2–h4 section splits with sentence-boundary overlap' },
    { label: 'Retry/Throttle', detail: 'Exponential backoff + 429 AdaptiveThrottle' },
    { label: 'Telemetry', detail: 'OpenTelemetry → App Insights + local JSONL feedback' },
    { label: 'FoundryProjectOpenAI', detail: 'Embeddings + query rewriting via Responses API' },
  ];
  s.addText('Infrastructure', { x: 7.3, y: 3.05, w: 5.5, h: 0.4, fontSize: 14, bold: true, color: C.gold, fontFace: 'Calibri' });
  infra.forEach((item, i) => {
    s.addShape(pptx.ShapeType.rect, { x: 7.3, y: 3.5 + i * 0.85, w: 5.7, h: 0.72, fill: { color: C.navy }, line: { color: C.teal, width: 1 } });
    s.addText(item.label, { x: 7.4, y: 3.55 + i * 0.85, w: 1.8, h: 0.62, fontSize: 12, bold: true, color: C.teal, valign: 'middle', fontFace: 'Calibri' });
    s.addText(item.detail, { x: 9.2, y: 3.55 + i * 0.85, w: 3.7, h: 0.62, fontSize: 11, color: C.ice, valign: 'middle', fontFace: 'Calibri' });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 4 — Documentation Coverage
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.seafoam);
  title(s, 'Documentation Coverage');
  divider(s, 1.08);

  // Header stats
  const stats = [
    { v: '526', l: 'docs-vnext\nMDX pages', c: C.teal },
    { v: '324', l: 'docs/\nMDX pages', c: C.seafoam },
    { v: '+266', l: 'New files\nin docs-vnext', c: C.mint },
    { v: '260', l: 'Shared\nfiles', c: C.gold },
  ];
  stats.forEach((st, i) => {
    metricBox(s, st.v, st.l, 0.4 + i * 3.25, 1.2, st.c);
  });

  // Section breakdown
  s.addText('Section Breakdown (docs-vnext)', {
    x: 0.5, y: 2.75, w: 7, h: 0.4, fontSize: 14, bold: true, color: C.gold, fontFace: 'Calibri',
  });

  const sections = [
    { name: 'foundry-models', count: 112, color: C.teal },
    { name: 'agent-service', count: 95, color: C.seafoam },
    { name: 'models', count: 75, color: C.mint },
    { name: 'agents', count: 63, color: C.teal },
    { name: 'observability', count: 31, color: C.seafoam },
    { name: 'security', count: 24, color: C.mint },
    { name: 'setup', count: 22, color: C.teal },
    { name: 'developer-experience', count: 21, color: C.seafoam },
    { name: 'guardrails', count: 19, color: C.mint },
    { name: 'api-sdk', count: 17, color: C.teal },
    { name: 'other', count: 47, color: C.gray },
  ];
  const maxVal = 112;
  sections.forEach((sec, i) => {
    const col = i < 6 ? 0 : 1;
    const row = i < 6 ? i : i - 6;
    const x = col === 0 ? 0.5 : 6.8;
    const y = 3.25 + row * 0.55;
    const barW = (sec.count / maxVal) * 5.8;
    s.addText(sec.name, { x, y, w: 2.4, h: 0.38, fontSize: 12, color: C.ice, valign: 'middle', fontFace: 'Calibri' });
    s.addShape(pptx.ShapeType.rect, { x: x + 2.4, y: y + 0.08, w: barW, h: 0.22, fill: { color: sec.color } });
    s.addText(String(sec.count), { x: x + 2.4 + barW + 0.05, y, w: 0.5, h: 0.38, fontSize: 11, color: sec.color, fontFace: 'Calibri' });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 5 — Agentic Workflows
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.mint);
  title(s, 'Agentic Workflows (29 Total)');
  divider(s, 1.08);

  const categories = [
    {
      name: '📡 Monitoring & Detection',
      color: C.teal,
      items: ['docs-upstream-monitor', 'sdk-release-monitor', 'reddit-community-monitor', 'community-discussions-monitor', 'dependabot-docs-check'],
    },
    {
      name: '✍️ Content Improvement',
      color: C.seafoam,
      items: ['unbloat-docs', 'glossary-maintainer', 'docs-auditor', 'changelog-updater', 'model-catalog-sync'],
    },
    {
      name: '🧪 Quality & Testing',
      color: C.mint,
      items: ['docs-noob-tester', 'pr-docs-reviewer', 'post-merge-docs-verify', 'search-test', 'post-index-sync-testbench'],
    },
    {
      name: '🔄 Sync & Update',
      color: C.gold,
      items: ['sync-and-convert', 'post-sync-updater', 'daily-doc-updater', 'docs-vnext-sync', 'docs-vnext-diff-report'],
    },
    {
      name: '⚡ Slash Commands (7)',
      color: C.accent,
      items: ['/ask', '/audit', '/improve', '/unbloat', '/noob-test', '/sync', '/eval'],
    },
  ];

  const colW = 2.5;
  categories.forEach((cat, i) => {
    const x = 0.3 + i * 2.6;
    s.addShape(pptx.ShapeType.rect, { x, y: 1.2, w: colW, h: 0.45, fill: { color: cat.color } });
    s.addText(cat.name, { x, y: 1.2, w: colW, h: 0.45, fontSize: 10, bold: true, color: C.dark, align: 'center', valign: 'middle', fontFace: 'Calibri' });
    cat.items.forEach((item, j) => {
      s.addShape(pptx.ShapeType.rect, { x, y: 1.7 + j * 0.55, w: colW, h: 0.48, fill: { color: C.navy }, line: { color: cat.color, width: 1 } });
      s.addText(item, { x, y: 1.7 + j * 0.55, w: colW, h: 0.48, fontSize: 10, color: C.ice, align: 'center', valign: 'middle', fontFace: 'Calibri' });
    });
  });

  // Bottom stats
  const wfStats = [
    { v: '29', l: 'Total Workflows', c: C.teal },
    { v: '7', l: 'Slash Commands', c: C.accent },
    { v: '3', l: 'Workflow Chains\n(workflow_run)', c: C.mint },
    { v: '23', l: 'Automated\nWorkflows', c: C.seafoam },
  ];
  wfStats.forEach((st, i) => {
    s.addShape(pptx.ShapeType.rect, { x: 0.3 + i * 3.25, y: 6.1, w: 3.0, h: 1.1, fill: { color: C.dark }, line: { color: st.c, width: 1.5 } });
    s.addText(st.v, { x: 0.3 + i * 3.25, y: 6.12, w: 3.0, h: 0.55, fontSize: 26, bold: true, color: st.c, align: 'center', fontFace: 'Calibri' });
    s.addText(st.l, { x: 0.3 + i * 3.25, y: 6.65, w: 3.0, h: 0.45, fontSize: 11, color: C.ice, align: 'center', fontFace: 'Calibri' });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 6 — Trigger Coverage
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.gold);
  title(s, 'Event-Driven Trigger Coverage');
  divider(s, 1.08);

  const triggers = [
    { event: 'schedule', icon: '⏰', desc: 'Cron-based daily/weekly runs', examples: 'docs-upstream-monitor, sdk-release-monitor,\nglossary-maintainer, daily-doc-updater', color: C.teal, count: '10+' },
    { event: 'push', icon: '⬆️', desc: 'On commit to main branch', examples: 'post-merge-docs-verify,\ndocs-vnext-diff-report', color: C.seafoam, count: '4' },
    { event: 'pull_request', icon: '🔀', desc: 'PR lifecycle events', examples: 'pr-docs-reviewer, label-ops-docs-fix', color: C.mint, count: '3' },
    { event: 'issues', icon: '🐛', desc: 'Issue open/label events', examples: 'auto-triage-issues', color: C.gold, count: '2' },
    { event: 'workflow_dispatch', icon: '▶️', desc: 'Manual or programmatic trigger', examples: 'sync-and-convert, search-test,\nslide-deck-maintainer', color: C.accent, count: '8' },
    { event: 'workflow_run', icon: '🔗', desc: 'Chained on workflow completion', examples: 'post-sync-updater (after sync-and-convert),\npost-index-sync-testbench (after index-sync)', color: C.teal, count: '3' },
    { event: 'repository_dispatch', icon: '📡', desc: 'Cross-repo API trigger', examples: 'community-discussions-monitor\n(microsoft-foundry/discussions)', color: C.seafoam, count: '2' },
    { event: 'issue_comment', icon: '💬', desc: 'Slash command triggers', examples: '/ask, /audit, /improve,\n/unbloat, /noob-test, /sync, /eval', color: C.mint, count: '7' },
  ];

  const cols = 4;
  triggers.forEach((t, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = 0.3 + col * 3.25;
    const y = 1.3 + row * 2.8;
    s.addShape(pptx.ShapeType.rect, { x, y, w: 3.1, h: 2.55, fill: { color: C.navy }, line: { color: t.color, width: 1.5 } });
    s.addText(`${t.icon} ${t.event}`, { x, y: y + 0.05, w: 3.1, h: 0.42, fontSize: 13, bold: true, color: t.color, align: 'center', fontFace: 'Calibri' });
    s.addShape(pptx.ShapeType.rect, { x: x + 0.1, y: y + 0.5, w: 2.9, h: 0.01, fill: { color: t.color } });
    s.addText(t.desc, { x, y: y + 0.58, w: 3.1, h: 0.38, fontSize: 11, color: C.ice, align: 'center', fontFace: 'Calibri' });
    s.addText(t.examples, { x, y: y + 0.98, w: 3.1, h: 0.8, fontSize: 10, color: C.gray, align: 'center', fontFace: 'Calibri' });
    s.addShape(pptx.ShapeType.rect, { x: x + 1.0, y: y + 2.0, w: 1.1, h: 0.38, fill: { color: t.color } });
    s.addText(t.count + ' wf', { x: x + 1.0, y: y + 2.0, w: 1.1, h: 0.38, fontSize: 12, bold: true, color: C.dark, align: 'center', valign: 'middle', fontFace: 'Calibri' });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 7 — Quality Pipeline
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.accent);
  title(s, 'Quality Pipeline');
  divider(s, 1.08);

  const agents = [
    {
      name: '🔍 Docs Auditor',
      wf: 'docs-auditor',
      color: C.teal,
      points: [
        'Scans docs-vnext for structural issues',
        'Checks frontmatter completeness',
        'Validates internal links',
        'Creates labeled issues for fixes',
        'Triggered: daily + slash /audit',
      ],
    },
    {
      name: '👶 Noob Tester',
      wf: 'docs-noob-tester',
      color: C.seafoam,
      points: [
        'Simulates beginner developer perspective',
        'Multi-device viewport testing (mobile, tablet, desktop)',
        'Tests critical getting-started paths',
        'Playwright browser automation',
        'Creates PR issues with specific blockers',
      ],
    },
    {
      name: '👁️ PR Reviewer',
      wf: 'pr-docs-reviewer',
      color: C.mint,
      points: [
        'Reviews every docs-vnext PR',
        'Checks Mintlify MDX compliance',
        'Validates Diátaxis framework adherence',
        'Flags terminology violations',
        'Approves or requests changes',
      ],
    },
    {
      name: '✅ Post-Merge Verify',
      wf: 'post-merge-docs-verify',
      color: C.gold,
      points: [
        'Runs after every merge to main',
        'Validates deployed docs site',
        'Checks for broken links',
        'Confirms nav structure integrity',
        'Triggers re-index if needed',
      ],
    },
  ];

  agents.forEach((a, i) => {
    const x = 0.3 + i * 3.25;
    s.addShape(pptx.ShapeType.rect, { x, y: 1.2, w: 3.1, h: 5.85, fill: { color: C.navy }, line: { color: a.color, width: 2 } });
    s.addShape(pptx.ShapeType.rect, { x, y: 1.2, w: 3.1, h: 0.55, fill: { color: a.color } });
    s.addText(a.name, { x, y: 1.2, w: 3.1, h: 0.55, fontSize: 13, bold: true, color: C.dark, align: 'center', valign: 'middle', fontFace: 'Calibri' });
    s.addText(a.wf, { x, y: 1.78, w: 3.1, h: 0.35, fontSize: 10, color: a.color, align: 'center', fontFace: 'Calibri' });
    a.points.forEach((pt, j) => {
      s.addShape(pptx.ShapeType.ellipse, { x: x + 0.2, y: 2.2 + j * 0.82 + 0.07, w: 0.14, h: 0.14, fill: { color: a.color } });
      s.addText(pt, { x: x + 0.4, y: 2.2 + j * 0.82, w: 2.6, h: 0.7, fontSize: 11, color: C.ice, valign: 'middle', fontFace: 'Calibri' });
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 8 — docs-vnext History & Impact
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.seafoam);
  title(s, 'docs-vnext: History & Impact');
  divider(s, 1.08);

  // Top metrics row
  const topMetrics = [
    { v: '30', l: 'Merged PRs\n(docs-vnext)', c: C.teal },
    { v: '10', l: 'Agentic PRs\n(bot-authored)', c: C.seafoam },
    { v: '20', l: 'Human-reviewed\nPRs', c: C.mint },
    { v: '526', l: 'MDX pages\nin docs-vnext', c: C.gold },
  ];
  topMetrics.forEach((m, i) => {
    metricBox(s, m.v, m.l, 0.4 + i * 3.25, 1.25, m.c);
  });

  // Timeline
  s.addText('Key Milestones', { x: 0.5, y: 2.8, w: 4, h: 0.38, fontSize: 14, bold: true, color: C.gold, fontFace: 'Calibri' });

  const milestones = [
    { date: 'Mar 2026', event: 'First agentic PR merged — unbloat cloud-evaluation.mdx (PR #23)' },
    { date: 'Mar 2026', event: 'Glossary created from zero — 35 terms, 16 sections (PR #28)' },
    { date: 'Mar 2026', event: 'Noob tester launched — multi-device viewport testing' },
    { date: 'Jun 2026', event: 'Daily glossary scans automated (PR #456)' },
    { date: 'Jul 2026', event: 'Eval harness launched — 4-server × 2-model matrix' },
    { date: 'Jul 2026', event: 'docs-vnext reaches 526 pages (+202 vs docs/ baseline of 324)' },
  ];
  milestones.forEach((m, i) => {
    const y = 3.25 + i * 0.55;
    s.addShape(pptx.ShapeType.ellipse, { x: 0.5, y: y + 0.1, w: 0.16, h: 0.16, fill: { color: i % 2 === 0 ? C.teal : C.seafoam } });
    s.addShape(pptx.ShapeType.line, { x: 0.58, y: y + 0.26, w: 0, h: 0.29, line: { color: C.gray, width: 1 } });
    s.addText(m.date, { x: 0.75, y, w: 1.2, h: 0.38, fontSize: 11, bold: true, color: C.gold, fontFace: 'Calibri' });
    s.addText(m.event, { x: 2.0, y, w: 7.5, h: 0.38, fontSize: 12, color: C.ice, fontFace: 'Calibri' });
  });

  // Right: file delta
  s.addShape(pptx.ShapeType.rect, { x: 9.8, y: 2.8, w: 3.2, h: 4.3, fill: { color: C.navy }, line: { color: C.teal, width: 1.5 } });
  s.addText('File Delta', { x: 9.8, y: 2.88, w: 3.2, h: 0.42, fontSize: 14, bold: true, color: C.teal, align: 'center', fontFace: 'Calibri' });
  divider(s, 3.32);
  const deltas = [
    { label: 'docs-vnext only', v: '266', c: C.mint },
    { label: 'Shared files', v: '260', c: C.seafoam },
    { label: 'docs/ baseline', v: '324', c: C.gray },
  ];
  deltas.forEach((d, i) => {
    s.addText(d.v, { x: 9.8, y: 3.5 + i * 1.1, w: 3.2, h: 0.6, fontSize: 28, bold: true, color: d.c, align: 'center', fontFace: 'Calibri' });
    s.addText(d.label, { x: 9.8, y: 4.1 + i * 1.1, w: 3.2, h: 0.35, fontSize: 12, color: C.ice, align: 'center', fontFace: 'Calibri' });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 9 — Deep Dive: Agentic Chain in Action
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.teal);
  title(s, 'Deep Dive: Agentic Chain in Action');
  divider(s, 1.08);

  // Chain diagram
  s.addText('Upstream Sync Chain', { x: 0.5, y: 1.15, w: 6, h: 0.38, fontSize: 14, bold: true, color: C.gold, fontFace: 'Calibri' });

  const chain = [
    { icon: '👁️', step: 'Upstream Docs\nMonitor', detail: 'Detects commit in\nMicrosoftDocs/azure-ai-docs', color: C.teal },
    { icon: '📋', step: 'Creates Issue', detail: 'e.g., Issue #576\n"Changes Detected — 2026-07-17"', color: C.seafoam },
    { icon: '🔄', step: 'Dispatches\nSync-and-Convert', detail: 'workflow_dispatch →\ndownload + convert MDX', color: C.mint },
    { icon: '🤖', step: 'Post-Sync\nUpdater', detail: 'Analyzes changes,\ncreates docs-vnext PR or noop', color: C.gold },
  ];
  const cw = 2.9, cy = 1.65;
  chain.forEach((c, i) => {
    const x = 0.3 + i * 3.1;
    s.addShape(pptx.ShapeType.rect, { x, y: cy, w: cw, h: 1.7, fill: { color: C.navy }, line: { color: c.color, width: 2 } });
    s.addText(c.icon + ' ' + c.step, { x, y: cy + 0.05, w: cw, h: 0.65, fontSize: 13, bold: true, color: c.color, align: 'center', fontFace: 'Calibri' });
    s.addShape(pptx.ShapeType.line, { x: x + 0.2, y: cy + 0.72, w: cw - 0.4, h: 0, line: { color: c.color, width: 1 } });
    s.addText(c.detail, { x, y: cy + 0.8, w: cw, h: 0.8, fontSize: 11, color: C.ice, align: 'center', fontFace: 'Calibri' });
    if (i < chain.length - 1) {
      s.addShape(pptx.ShapeType.line, { x: x + cw, y: cy + 0.85, w: 0.2, h: 0, line: { color: c.color, width: 2 } });
      s.addText('→', { x: x + cw, y: cy + 0.7, w: 0.2, h: 0.4, fontSize: 14, bold: true, color: c.color, align: 'center', fontFace: 'Calibri' });
    }
  });

  // Real data
  divider(s, 3.5, C.gray);
  s.addText('Real Example — July 17, 2026', { x: 0.5, y: 3.6, w: 6, h: 0.38, fontSize: 13, bold: true, color: C.teal, fontFace: 'Calibri' });
  const realData = [
    'Issue #576 created: "📄 Upstream Foundry Docs Changes Detected — 2026-07-17"',
    '18 changed areas including: model matrices, agents enable/disable, Cosmos DB setup, admin guide (new)',
    'Workflow run §29546350095 dispatched sync-and-convert automatically',
    'Post-sync-updater analyzed changes and queued docs-vnext update',
  ];
  realData.forEach((d, i) => {
    s.addShape(pptx.ShapeType.ellipse, { x: 0.5, y: 4.1 + i * 0.5 + 0.06, w: 0.14, h: 0.14, fill: { color: C.teal } });
    s.addText(d, { x: 0.75, y: 4.1 + i * 0.5, w: 12.1, h: 0.45, fontSize: 12, color: C.ice, fontFace: 'Calibri' });
  });

  // SDK chain
  s.addText('SDK Release Chain Example', { x: 7.5, y: 1.15, w: 5.5, h: 0.38, fontSize: 14, bold: true, color: C.gold, fontFace: 'Calibri' });
  s.addShape(pptx.ShapeType.rect, { x: 7.5, y: 1.65, w: 5.5, h: 1.7, fill: { color: C.navy }, line: { color: C.accent, width: 1.5 } });
  s.addText('🔍 SDK Release Monitor → Issue #552', { x: 7.6, y: 1.72, w: 5.3, h: 0.38, fontSize: 13, bold: true, color: C.accent, fontFace: 'Calibri' });
  s.addText('Detected: JS/TS 2.3.1 (2026-07-09)\nPython 2.3.0 stable · .NET 2.1.0-beta.4 · Java 2.2.0\nAssessed docs impact → flagged SDK references needing update', {
    x: 7.6, y: 2.1, w: 5.3, h: 1.15, fontSize: 11, color: C.ice, fontFace: 'Calibri',
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 10 — Deep Dive: Content Improvements
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.mint);
  title(s, 'Deep Dive: Agentic Content Improvements');
  divider(s, 1.08);

  // PR #28 — Glossary
  s.addShape(pptx.ShapeType.rect, { x: 0.4, y: 1.2, w: 6.1, h: 5.85, fill: { color: C.navy }, line: { color: C.teal, width: 2 } });
  s.addShape(pptx.ShapeType.rect, { x: 0.4, y: 1.2, w: 6.1, h: 0.52, fill: { color: C.teal } });
  s.addText('PR #28 — Glossary Creation from Zero', { x: 0.4, y: 1.2, w: 6.1, h: 0.52, fontSize: 13, bold: true, color: C.dark, align: 'center', valign: 'middle', fontFace: 'Calibri' });
  s.addText('Merged: 2026-03-02 · Author: github-actions[bot] · +194 lines', { x: 0.5, y: 1.8, w: 5.9, h: 0.35, fontSize: 11, color: C.gold, fontFace: 'Calibri' });

  const glossaryTerms = [
    { cat: 'Core Foundry (10)', items: 'Agent, Microsoft Foundry, Azure AI Foundry, Capability Host, Guardrails...' },
    { cat: 'MCP Ecosystem (7)', items: 'MCP, MCP Gateway (MCPG), FastMCP, docs-vnext, Mintlify, MDX...' },
    { cat: 'Search & Retrieval (10)', items: 'RAG, Hybrid Search, Embeddings, Vector Search, HNSW, TF-IDF...' },
    { cat: 'Agent Tools (3)', items: 'Code Interpreter, File Search, Function Calling' },
    { cat: 'Evaluation (5)', items: 'Evaluator, Hit@K, MRR, A/B/C/D evaluation' },
  ];
  glossaryTerms.forEach((gt, i) => {
    s.addText(gt.cat, { x: 0.6, y: 2.2 + i * 0.78, w: 5.8, h: 0.32, fontSize: 12, bold: true, color: C.teal, fontFace: 'Calibri' });
    s.addText(gt.items, { x: 0.6, y: 2.52 + i * 0.78, w: 5.8, h: 0.32, fontSize: 11, color: C.ice, fontFace: 'Calibri' });
  });
  s.addShape(pptx.ShapeType.rect, { x: 0.9, y: 6.4, w: 2.2, h: 0.4, fill: { color: C.navy }, line: { color: C.gold, width: 1 } });
  s.addText('35 total terms', { x: 0.9, y: 6.4, w: 2.2, h: 0.4, fontSize: 13, bold: true, color: C.gold, align: 'center', valign: 'middle', fontFace: 'Calibri' });
  s.addShape(pptx.ShapeType.rect, { x: 3.2, y: 6.4, w: 2.8, h: 0.4, fill: { color: C.navy }, line: { color: C.teal, width: 1 } });
  s.addText('16 alphabetical sections', { x: 3.2, y: 6.4, w: 2.8, h: 0.4, fontSize: 13, bold: true, color: C.teal, align: 'center', valign: 'middle', fontFace: 'Calibri' });

  // PR #23 — Unbloat
  s.addShape(pptx.ShapeType.rect, { x: 6.9, y: 1.2, w: 6.1, h: 5.85, fill: { color: C.navy }, line: { color: C.mint, width: 2 } });
  s.addShape(pptx.ShapeType.rect, { x: 6.9, y: 1.2, w: 6.1, h: 0.52, fill: { color: C.mint } });
  s.addText('PR #23 — Unbloat cloud-evaluation.mdx', { x: 6.9, y: 1.2, w: 6.1, h: 0.52, fontSize: 13, bold: true, color: C.dark, align: 'center', valign: 'middle', fontFace: 'Calibri' });
  s.addText('Merged: 2026-03-02 · Author: github-actions[bot] · −29 lines, −232 words', { x: 7.0, y: 1.8, w: 5.9, h: 0.35, fontSize: 11, color: C.gold, fontFace: 'Calibri' });

  const bloatTypes = [
    { type: 'Duplicate paragraph', detail: 'Restated evaluator support already covered 2 paragraphs earlier' },
    { type: 'Repetitive tip boxes', detail: 'Removed 4 identical "Before you begin" Tip callouts' },
    { type: 'Trivial tip', detail: '"To add another evaluation run, use the same code" — no value' },
    { type: 'Redundant sentence', detail: 'Restated info from preceding paragraph in "Collect response IDs"' },
    { type: 'Verbose bullets → table', detail: '"Interpret results" 5-bullet schema → concise reference table' },
    { type: 'Bullet lists → prose', detail: '"Rate limit errors" 5 bullets → 2 direct prose sentences' },
  ];
  bloatTypes.forEach((b, i) => {
    s.addShape(pptx.ShapeType.rect, { x: 7.0, y: 2.25 + i * 0.66, w: 5.8, h: 0.58, fill: { color: C.dark }, line: { color: C.mint, width: 1 } });
    s.addText('✂ ' + b.type, { x: 7.1, y: 2.28 + i * 0.66, w: 2.3, h: 0.52, fontSize: 11, bold: true, color: C.mint, valign: 'middle', fontFace: 'Calibri' });
    s.addText(b.detail, { x: 9.45, y: 2.28 + i * 0.66, w: 3.3, h: 0.52, fontSize: 10, color: C.ice, valign: 'middle', fontFace: 'Calibri' });
  });

  // Metrics table for PR #23
  const beforeAfter = [
    { m: 'Words', before: '3,412', after: '3,180', delta: '−7%' },
    { m: 'Bullets', before: '29', after: '19', delta: '−34.5% ✅' },
  ];
  const headers = ['Metric', 'Before', 'After', 'Reduction'];
  headers.forEach((h, i) => {
    s.addShape(pptx.ShapeType.rect, { x: 7.0 + i * 1.45, y: 6.3, w: 1.45, h: 0.38, fill: { color: C.mint } });
    s.addText(h, { x: 7.0 + i * 1.45, y: 6.3, w: 1.45, h: 0.38, fontSize: 11, bold: true, color: C.dark, align: 'center', valign: 'middle', fontFace: 'Calibri' });
  });
  beforeAfter.forEach((row, ri) => {
    [row.m, row.before, row.after, row.delta].forEach((v, ci) => {
      s.addShape(pptx.ShapeType.rect, { x: 7.0 + ci * 1.45, y: 6.68 + ri * 0.37, w: 1.45, h: 0.37, fill: { color: C.navy }, line: { color: C.mint, width: 1 } });
      s.addText(v, { x: 7.0 + ci * 1.45, y: 6.68 + ri * 0.37, w: 1.45, h: 0.37, fontSize: 11, color: ci === 3 ? C.gold : C.ice, align: 'center', valign: 'middle', fontFace: 'Calibri' });
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 11 — Evaluation Harness Results
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.gold);
  title(s, 'Evaluation Harness Results');
  s.addText('Issue #582 · Run 2026-07-19 · 200 Total Evaluations', {
    x: 0.5, y: 0.92, w: 12, h: 0.35, fontSize: 12, color: C.gray, fontFace: 'Calibri',
  });
  divider(s, 1.28);

  // Scoreboard table
  s.addText('Scoreboard: Server × Model Matrix', { x: 0.4, y: 1.38, w: 7, h: 0.38, fontSize: 14, bold: true, color: C.gold, fontFace: 'Calibri' });

  const headers = ['Server', 'claude-sonnet-4.6', 'gpt-5.4', 'Average'];
  const colXs = [0.4, 3.4, 5.3, 7.1];
  const colWs = [2.9, 1.8, 1.7, 1.5];
  headers.forEach((h, i) => {
    s.addShape(pptx.ShapeType.rect, { x: colXs[i], y: 1.8, w: colWs[i], h: 0.4, fill: { color: C.navy }, line: { color: C.gold, width: 1 } });
    s.addText(h, { x: colXs[i], y: 1.8, w: colWs[i], h: 0.4, fontSize: 11, bold: true, color: C.gold, align: 'center', valign: 'middle', fontFace: 'Calibri' });
  });

  const rows = [
    { server: '🥇 docs-vnext (Treatment)', s1: '0.863', s2: '0.881', avg: '0.872', highlight: true, color: C.teal },
    { server: '🥈 MS Learn (Control A)', s1: '0.862', s2: '0.872', avg: '0.867', highlight: false, color: C.ice },
    { server: '🥉 docs/ (Control C)', s1: '0.845', s2: '0.858', avg: '0.851', highlight: false, color: C.ice },
    { server: 'Mintlify MCP (Control B)', s1: '0.809', s2: '0.877', avg: '0.843', highlight: false, color: C.ice },
  ];
  rows.forEach((r, i) => {
    const rowY = 2.22 + i * 0.48;
    const rowColor = r.highlight ? C.dark : C.dark;
    [r.server, r.s1, r.s2, r.avg].forEach((v, ci) => {
      s.addShape(pptx.ShapeType.rect, { x: colXs[ci], y: rowY, w: colWs[ci], h: 0.44, fill: { color: r.highlight ? '0D1A40' : C.dark }, line: { color: r.highlight ? C.teal : C.navy, width: r.highlight ? 1.5 : 1 } });
      s.addText(v, { x: colXs[ci], y: rowY, w: colWs[ci], h: 0.44, fontSize: ci === 0 ? 11 : 12, bold: ci === 3, color: r.highlight && ci === 3 ? C.teal : r.color, align: ci === 0 ? 'left' : 'center', valign: 'middle', fontFace: 'Calibri', margin: ci === 0 ? [0, 0, 0, 5] : [0] });
    });
  });

  // Category breakdown
  s.addText('Category Breakdown (docs-vnext vs docs/)', { x: 0.4, y: 4.45, w: 8.5, h: 0.38, fontSize: 13, bold: true, color: C.seafoam, fontFace: 'Calibri' });
  const cats = [
    { name: 'agent-development', vnext: 0.778, docs: 0.765, learn: 0.807 },
    { name: 'getting-started', vnext: 0.852, docs: 0.868, learn: 0.842 },
    { name: 'infrastructure-security', vnext: 0.987, docs: 0.913, learn: 0.873 },
    { name: 'observability-evaluation', vnext: 0.797, docs: 0.750, learn: 0.853 },
    { name: 'sdk-api', vnext: 0.947, docs: 0.960, learn: 0.960 },
  ];
  cats.forEach((c, i) => {
    const x = 0.4 + i * 2.6;
    const maxV = Math.max(c.vnext, c.docs, c.learn);
    s.addText(c.name.replace('-', '\n'), { x, y: 4.88, w: 2.5, h: 0.5, fontSize: 10, bold: true, color: C.ice, align: 'center', fontFace: 'Calibri' });
    [
      { v: c.vnext, color: C.teal, label: 'vnext' },
      { v: c.docs, color: C.seafoam, label: 'docs' },
      { v: c.learn, color: C.gray, label: 'learn' },
    ].forEach((bar, bi) => {
      const barH = (bar.v - 0.7) / 0.3 * 1.3;
      const barX = x + 0.25 + bi * 0.7;
      s.addShape(pptx.ShapeType.rect, { x: barX, y: 6.5 - barH, w: 0.55, h: barH, fill: { color: bar.v === maxV ? bar.color : bar.color }, transparency: bar.v === maxV ? 0 : 30 });
      s.addText(bar.v.toFixed(2), { x: barX, y: 6.52, w: 0.55, h: 0.3, fontSize: 9, color: C.ice, align: 'center', fontFace: 'Calibri' });
    });
  });

  // Hypothesis results
  s.addShape(pptx.ShapeType.rect, { x: 9.0, y: 1.38, w: 4.0, h: 5.8, fill: { color: C.navy }, line: { color: C.gold, width: 1.5 } });
  s.addText('Hypothesis Testing', { x: 9.0, y: 1.43, w: 4.0, h: 0.42, fontSize: 13, bold: true, color: C.gold, align: 'center', fontFace: 'Calibri' });
  const hyps = [
    { h: 'H1', result: '⚠️ MARGINAL', detail: 'docs-vnext (0.872)\nvs docs/ (0.851)\n+0.021 delta', color: C.gold },
    { h: 'H2', result: '⚠️ MARGINAL', detail: 'vs Mintlify MCP\n(0.843), +0.029\ndelta', color: C.gold },
    { h: 'H3', result: '⚠️ MARGINAL', detail: 'vs MS Learn\n(0.867), +0.005\ndelta', color: C.gold },
    { h: 'H4', result: '⚠️ MIXED', detail: 'Rankings differ\nbetween claude and\ngpt-5.4', color: C.accent },
  ];
  hyps.forEach((h, i) => {
    s.addShape(pptx.ShapeType.rect, { x: 9.1, y: 1.95 + i * 1.28, w: 3.8, h: 1.2, fill: { color: C.dark }, line: { color: h.color, width: 1 } });
    s.addText(h.h + ': ' + h.result, { x: 9.1, y: 2.0 + i * 1.28, w: 3.8, h: 0.38, fontSize: 12, bold: true, color: h.color, align: 'center', fontFace: 'Calibri' });
    s.addText(h.detail, { x: 9.1, y: 2.38 + i * 1.28, w: 3.8, h: 0.72, fontSize: 10, color: C.ice, align: 'center', fontFace: 'Calibri' });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 12 — Community Integration
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.accent);
  title(s, 'Community Integration & Signal Detection');
  divider(s, 1.08);

  const channels = [
    {
      name: '💬 Microsoft Foundry\nDiscussions',
      workflow: 'community-discussions-monitor',
      trigger: 'repository_dispatch\nfrom microsoft-foundry',
      actions: ['Monitors community Q&A threads', 'Identifies undocumented topics', 'Creates issues for doc gaps', 'Dispatches improvement workflows'],
      color: C.teal,
    },
    {
      name: '🔬 Foundry Samples\nMonitor',
      workflow: 'dependabot-docs-check',
      trigger: 'schedule (daily)',
      actions: ['Watches foundry-samples repo', 'Detects new code examples', 'Flags docs out of sync with samples', 'Auto-creates update issues'],
      color: C.seafoam,
    },
    {
      name: '🤖 Reddit\nCommunity',
      workflow: 'reddit-community-monitor',
      trigger: 'schedule (weekly)',
      actions: ['Scrapes r/AzureAI, r/MicrosoftCopilot', 'Identifies common pain points', 'Maps questions to doc pages', 'Signals doc quality gaps'],
      color: C.accent,
    },
  ];

  channels.forEach((ch, i) => {
    const x = 0.4 + i * 4.3;
    s.addShape(pptx.ShapeType.rect, { x, y: 1.2, w: 4.1, h: 5.85, fill: { color: C.navy }, line: { color: ch.color, width: 2 } });
    s.addShape(pptx.ShapeType.rect, { x, y: 1.2, w: 4.1, h: 0.65, fill: { color: ch.color } });
    s.addText(ch.name, { x, y: 1.2, w: 4.1, h: 0.65, fontSize: 14, bold: true, color: C.dark, align: 'center', valign: 'middle', fontFace: 'Calibri' });
    s.addText('🔧 ' + ch.workflow, { x: x + 0.1, y: 1.93, w: 3.9, h: 0.35, fontSize: 11, color: ch.color, fontFace: 'Calibri' });
    s.addText('⚡ ' + ch.trigger, { x: x + 0.1, y: 2.28, w: 3.9, h: 0.45, fontSize: 11, color: C.gold, fontFace: 'Calibri' });
    divider(s, 2.75);
    s.addText('Actions:', { x: x + 0.1, y: 2.82, w: 3.9, h: 0.35, fontSize: 12, bold: true, color: C.ice, fontFace: 'Calibri' });
    ch.actions.forEach((a, ai) => {
      s.addShape(pptx.ShapeType.ellipse, { x: x + 0.15, y: 3.27 + ai * 0.68 + 0.07, w: 0.14, h: 0.14, fill: { color: ch.color } });
      s.addText(a, { x: x + 0.38, y: 3.27 + ai * 0.68, w: 3.6, h: 0.6, fontSize: 12, color: C.ice, valign: 'middle', fontFace: 'Calibri' });
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 13 — SDK Monitoring
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.seafoam);
  title(s, 'SDK Release Monitoring');
  divider(s, 1.08);

  // SDK table
  s.addText('4 SDK Repositories Tracked', { x: 0.4, y: 1.15, w: 6, h: 0.38, fontSize: 14, bold: true, color: C.gold, fontFace: 'Calibri' });

  const sdks = [
    { lang: '🐍 Python', pkg: 'azure-ai-projects', v: '2.3.0', type: 'Stable ✅', date: '2026-07-01', color: C.teal },
    { lang: '⚡ JS/TS', pkg: '@azure/ai-projects', v: '2.3.1 🆕', type: 'Stable ✅', date: '2026-07-09', color: C.mint },
    { lang: '🟣 .NET', pkg: 'Azure.AI.Projects', v: '2.1.0-beta.4', type: 'Beta', date: '2026-06-30', color: C.gold },
    { lang: '☕ Java', pkg: 'azure-ai-projects', v: '2.2.0', type: 'Stable ✅', date: '2026-07-01', color: C.seafoam },
  ];
  const sdkCols = ['Language', 'Package', 'Version', 'Type', 'Date'];
  const sdkColX = [0.4, 1.8, 4.6, 6.6, 8.2];
  const sdkColW = [1.3, 2.7, 1.9, 1.5, 1.8];
  sdkCols.forEach((h, i) => {
    s.addShape(pptx.ShapeType.rect, { x: sdkColX[i], y: 1.6, w: sdkColW[i], h: 0.4, fill: { color: C.navy }, line: { color: C.gold, width: 1 } });
    s.addText(h, { x: sdkColX[i], y: 1.6, w: sdkColW[i], h: 0.4, fontSize: 11, bold: true, color: C.gold, align: 'center', valign: 'middle', fontFace: 'Calibri' });
  });
  sdks.forEach((sdk, i) => {
    const rowY = 2.02 + i * 0.52;
    [sdk.lang, sdk.pkg, sdk.v, sdk.type, sdk.date].forEach((v, ci) => {
      s.addShape(pptx.ShapeType.rect, { x: sdkColX[ci], y: rowY, w: sdkColW[ci], h: 0.48, fill: { color: C.dark }, line: { color: sdk.color, width: 1 } });
      s.addText(v, { x: sdkColX[ci], y: rowY, w: sdkColW[ci], h: 0.48, fontSize: 11, color: sdk.color, align: 'center', valign: 'middle', fontFace: 'Calibri' });
    });
  });

  // Capabilities
  s.addText('Monitor Capabilities', { x: 0.4, y: 4.25, w: 4, h: 0.38, fontSize: 14, bold: true, color: C.seafoam, fontFace: 'Calibri' });
  const caps = [
    '🔍 Changelog detection — parses GitHub releases and tags daily',
    '📊 Version diff — tracks previous vs new version for all 4 SDKs',
    '🚨 Breaking change detection — flags major version bumps and beta releases',
    '📋 Docs impact assessment — identifies docs pages referencing changed APIs',
    '🏷️ Creates labeled issues — sdk-update + automation labels for triage',
  ];
  caps.forEach((c, i) => {
    s.addText(c, { x: 0.5, y: 4.7 + i * 0.52, w: 9.3, h: 0.46, fontSize: 13, color: C.ice, fontFace: 'Calibri' });
  });

  // Example issue
  s.addShape(pptx.ShapeType.rect, { x: 10.0, y: 1.15, w: 3.0, h: 6.0, fill: { color: C.navy }, line: { color: C.accent, width: 2 } });
  s.addShape(pptx.ShapeType.rect, { x: 10.0, y: 1.15, w: 3.0, h: 0.5, fill: { color: C.accent } });
  s.addText('Example Alert', { x: 10.0, y: 1.15, w: 3.0, h: 0.5, fontSize: 13, bold: true, color: C.dark, align: 'center', valign: 'middle', fontFace: 'Calibri' });
  s.addText('Issue #552', { x: 10.1, y: 1.72, w: 2.8, h: 0.35, fontSize: 12, bold: true, color: C.accent, fontFace: 'Calibri' });
  s.addText('JS/TS 2.3.1\nDetected 2026-07-09\n\nPrevious: 2.3.0\n\nType: Stable Release\n\nDocs flagged for\nreview: 12 pages\nreferencing\n@azure/ai-projects\nJS/TS examples', {
    x: 10.1, y: 2.1, w: 2.8, h: 4.8, fontSize: 11, color: C.ice, fontFace: 'Calibri',
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 14 — Key Metrics
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  accentBar(s, C.teal);
  title(s, 'Key Metrics (Live as of July 2026)');
  divider(s, 1.08);

  const bigMetrics = [
    { v: '526', l: 'docs-vnext MDX Pages', c: C.teal },
    { v: '324', l: 'docs/ MDX Pages', c: C.seafoam },
    { v: '29', l: 'Agentic Workflows', c: C.mint },
    { v: '0.872', l: 'docs-vnext Avg Score\n(Eval Harness)', c: C.gold },
    { v: '10', l: 'Agentic PRs Merged\n(bot-authored)', c: C.accent },
    { v: '30', l: 'Total docs-vnext\nPRs Merged', c: C.teal },
    { v: '7', l: 'Slash Commands', c: C.seafoam },
    { v: '200', l: 'Eval Runs\n(per report)', c: C.mint },
  ];

  const cols = 4;
  bigMetrics.forEach((m, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    metricBox(s, m.v, m.l, 0.4 + col * 3.25, 1.3 + row * 1.65, m.c);
  });

  // Eval breakdown mini
  s.addText('Eval Score Breakdown', { x: 0.4, y: 4.65, w: 5, h: 0.38, fontSize: 13, bold: true, color: C.gold, fontFace: 'Calibri' });
  const evalBreakdown = [
    { cat: 'infrastructure-security', score: '0.987', color: C.mint },
    { cat: 'sdk-api', score: '0.947', color: C.teal },
    { cat: 'getting-started', score: '0.852', color: C.seafoam },
    { cat: 'observability-evaluation', score: '0.797', color: C.gold },
    { cat: 'agent-development', score: '0.778', color: C.accent },
  ];
  evalBreakdown.forEach((e, i) => {
    const x = 0.4 + i * 2.6;
    const barH = (parseFloat(e.score) - 0.7) / 0.3 * 1.4;
    s.addShape(pptx.ShapeType.rect, { x: x + 0.5, y: 6.3 - barH, w: 1.6, h: barH, fill: { color: e.color } });
    s.addText(e.score, { x, y: 6.3 - barH - 0.3, w: 2.6, h: 0.28, fontSize: 11, color: e.color, align: 'center', bold: true, fontFace: 'Calibri' });
    s.addText(e.cat.replace('-', '\n'), { x, y: 6.32, w: 2.6, h: 0.55, fontSize: 10, color: C.gray, align: 'center', fontFace: 'Calibri' });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 15 — What's Next
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pptx.addSlide();
  bg(s, C.navy);
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: H, fill: { color: C.dark } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: W, h: 0.08, fill: { color: C.teal } });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: H - 0.08, w: W, h: 0.08, fill: { color: C.seafoam } });

  title(s, "What's Next", { y: 0.3, fs: 36 });
  divider(s, 1.08);

  const roadmap = [
    {
      priority: '🔴 HIGH',
      item: 'Improve Observability Docs Coverage',
      detail: 'observability-evaluation scores lowest at 0.797 in docs-vnext. Add tracing tutorials, evaluation how-tos, and telemetry reference pages.',
      color: C.accent,
    },
    {
      priority: '🟡 MEDIUM',
      item: 'Increase Agentic PR Merge Rate',
      detail: 'Currently 10 of 30 docs-vnext PRs are agent-authored (33%). Target 50%+ by improving PR reviewer confidence thresholds and merge automation.',
      color: C.gold,
    },
    {
      priority: '🟡 MEDIUM',
      item: 'Expand Eval Scenarios',
      detail: 'Current 200 scenarios focus on 5 categories. Add SDK/API integration scenarios, troubleshooting paths, and multi-turn conversation evaluation.',
      color: C.gold,
    },
    {
      priority: '🟢 PLANNED',
      item: 'Agent-Development Coverage',
      detail: 'agent-development category scores 0.778, below MS Learn (0.807). Expand agents/ section with real-world patterns, error handling, and advanced tooling guides.',
      color: C.mint,
    },
    {
      priority: '🔵 FUTURE',
      item: 'Real-Time Sync SLA',
      detail: 'Reduce upstream-to-docs-vnext latency from daily to <4 hours for critical doc changes (security, breaking API changes).',
      color: C.seafoam,
    },
  ];

  roadmap.forEach((r, i) => {
    const y = 1.3 + i * 1.16;
    s.addShape(pptx.ShapeType.rect, { x: 0.4, y, w: 12.5, h: 1.05, fill: { color: C.navy }, line: { color: r.color, width: 1.5 } });
    s.addShape(pptx.ShapeType.rect, { x: 0.4, y, w: 0.08, h: 1.05, fill: { color: r.color } });
    s.addText(r.priority, { x: 0.6, y: y + 0.05, w: 1.5, h: 0.4, fontSize: 12, bold: true, color: r.color, fontFace: 'Calibri' });
    s.addText(r.item, { x: 2.2, y: y + 0.05, w: 10.5, h: 0.4, fontSize: 14, bold: true, color: C.white, fontFace: 'Calibri' });
    s.addText(r.detail, { x: 2.2, y: y + 0.48, w: 10.5, h: 0.5, fontSize: 12, color: C.ice, fontFace: 'Calibri' });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Write output
// ─────────────────────────────────────────────────────────────────────────────
const outPath = path.resolve(__dirname, '../../home/runner/work/foundry-docs/foundry-docs/slides/foundry-docs-overview.pptx');
// Use env or relative path
const slidesDir = process.env.SLIDES_DIR || path.resolve(process.cwd(), 'slides');
const outFile = path.join(slidesDir, 'foundry-docs-overview.pptx');

fs.mkdirSync(slidesDir, { recursive: true });

pptx.writeFile({ fileName: outFile }).then(() => {
  console.log('✅ Deck written to:', outFile);
}).catch(err => {
  console.error('❌ Error writing deck:', err);
  process.exit(1);
});
