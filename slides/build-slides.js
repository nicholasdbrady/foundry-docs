"use strict";
/**
 * Foundry-Docs Stakeholder Slide Deck
 * Built with PptxGenJS — Teal Trust color palette
 *
 * Run: node /tmp/build-slides.js
 * Output: slides/foundry-docs-overview.pptx
 */

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const path = require("path");
const fs = require("fs");

const {
  FaServer, FaRobot, FaBook, FaSearch, FaList, FaSync, FaArrowRight,
  FaCheckCircle, FaBell, FaFlask, FaCode, FaUsers, FaComments,
  FaShieldAlt, FaRocket, FaCog, FaBoxOpen, FaGlobe, FaBug,
  FaChartBar, FaFileAlt, FaTachometerAlt, FaEye, FaPython,
  FaJs, FaCodeBranch, FaTag, FaDatabase, FaLayerGroup,
  FaClipboardCheck, FaBolt, FaHeartbeat
} = require("react-icons/fa");
const { MdUpdate, MdOutlineMonitor, MdGroups } = require("react-icons/md");

// ── Color Palette: Teal Trust ──────────────────────────────────────────────
const C = {
  darkBg:    "01363D",   // Dark teal — title/dark slides
  primary:   "028090",   // Teal
  secondary: "00A896",   // Seafoam
  accent:    "02C39A",   // Mint
  lightBg:   "F2FAFA",   // Very light teal tint
  white:     "FFFFFF",
  textDark:  "1A2E30",   // Dark teal-grey body
  textMuted: "5A8087",   // Muted teal-grey
  lightTeal: "B8DADD",   // Subtle teal
};

// ── LIVE DATA — computed from repo ────────────────────────────────────────
const DATA = {
  mdxDocs:           280,
  agenticWorkflows:  29,
  totalWorkflows:    29,
  slashCommands:     7,
  workflowChains:    3,
  scheduleWorkflows: 12,
  pushWorkflows:     1,
  prWorkflows:       3,
  issueWorkflows:    25,
  dispatchWorkflows: 22,
  sdkRepos:          4,
  docSections:       15,
  sections: [
    { name: "Models",            count: 73 },
    { name: "Agents",            count: 60 },
    { name: "Observability",     count: 24 },
    { name: "Setup",             count: 20 },
    { name: "Security",          count: 20 },
    { name: "API & SDK",         count: 17 },
    { name: "Guardrails",        count: 15 },
    { name: "Dev Experience",    count: 11 },
    { name: "Manage",            count: 9  },
    { name: "Responsible AI",    count: 8  },
    { name: "Operate",           count: 8  },
    { name: "Get Started",       count: 6  },
    { name: "Best Practices",    count: 5  },
    { name: "Overview",          count: 3  },
    { name: "Reference",         count: 1  },
  ],
  // History & impact metrics
  agenticPRsCreated: 38,
  upstreamSyncEvents: 15,
  sdkReleaseAlerts: 7,
  docsVnextUniqueFiles: 14,
  docsVnextSharedFiles: 266,
  // Eval data — June 28, 2026
  eval: {
    date: "2026-06-28",
    totalEvals: 200,
    servers: 4,
    models: 2,
    scores: {
      docsControl:  0.907,
      msLearn:      0.900,
      docsVnext:    0.889,
      mintlify:     0.889,
    },
    categories: [
      { name: "agent-development",        docsControl: 0.880, docsVnext: 0.880 },
      { name: "getting-started",          docsControl: 0.913, docsVnext: 0.827 },
      { name: "infrastructure-security",  docsControl: 0.913, docsVnext: 0.913 },
      { name: "observability-evaluation", docsControl: 0.853, docsVnext: 0.880 },
      { name: "sdk-api",                  docsControl: 0.973, docsVnext: 0.947 },
    ],
  },
};

// ── Icon helper ───────────────────────────────────────────────────────────
async function iconPng(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// ── Shadow factory (never reuse objects — PptxGenJS mutates in-place) ─────
const mkShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.12 });
const mkShadowSm = () => ({ type: "outer", blur: 4, offset: 2, angle: 135, color: "000000", opacity: 0.10 });

// ─────────────────────────────────────────────────────────────────────────
async function buildPresentation() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";  // 10" × 5.625"
  pres.author  = "Foundry-Docs Slide Agent";
  pres.title   = "Foundry-Docs Overview";

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 1 — Title (Dark)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.darkBg };

    // Decorative large circle top-right
    s.addShape(pres.shapes.OVAL, {
      x: 7.2, y: -1.5, w: 4.5, h: 4.5,
      fill: { color: C.primary, transparency: 78 },
      line: { color: C.primary, transparency: 78, width: 0 },
    });

    // Decorative smaller circle mid-right
    s.addShape(pres.shapes.OVAL, {
      x: 8.8, y: 2.8, w: 2.2, h: 2.2,
      fill: { color: C.secondary, transparency: 82 },
      line: { color: C.secondary, transparency: 82, width: 0 },
    });

    // Mint left accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 1.4, w: 0.18, h: 2.2,
      fill: { color: C.accent },
      line: { color: C.accent, width: 0 },
    });

    // Main title
    s.addText("Foundry-Docs", {
      x: 0.5, y: 1.5, w: 9, h: 1.1,
      fontSize: 52, fontFace: "Trebuchet MS", bold: true,
      color: C.white, margin: 0,
    });

    // Subtitle
    s.addText("Agentic Documentation Platform for Microsoft Foundry", {
      x: 0.5, y: 2.8, w: 8.2, h: 0.65,
      fontSize: 20, fontFace: "Calibri",
      color: C.accent, margin: 0,
    });

    // Tagline bar background
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 4.9, w: 10, h: 0.725,
      fill: { color: C.primary, transparency: 75 },
      line: { color: C.primary, transparency: 75, width: 0 },
    });

    // Tagline text
    s.addText(
      `${DATA.mdxDocs} docs  ·  ${DATA.agenticWorkflows} agentic workflows  ·  ${DATA.sdkRepos} SDK repos monitored  ·  FastMCP server`,
      {
        x: 0.4, y: 4.95, w: 9.2, h: 0.5,
        fontSize: 13, fontFace: "Calibri", color: C.lightTeal,
        align: "center", margin: 0,
      }
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 2 — What is Foundry-Docs (Light)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.lightBg };

    // Left accent strip
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.18, h: 5.625,
      fill: { color: C.primary },
      line: { color: C.primary, width: 0 },
    });

    // Title
    s.addText("What is Foundry-Docs?", {
      x: 0.45, y: 0.32, w: 5.5, h: 0.65,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    // Description
    s.addText(
      "A FastMCP server that extracts, converts, and serves Microsoft Foundry documentation to AI assistants — with a fleet of autonomous agents keeping it accurate and up to date.",
      {
        x: 0.45, y: 1.1, w: 5.1, h: 0.9,
        fontSize: 14, fontFace: "Calibri", color: C.textDark,
        margin: 0,
      }
    );

    // MCP Tools (left side)
    const tools = [
      { icon: FaSearch,   label: "search_docs(query)",   desc: "Hybrid full-text + vector search" },
      { icon: FaFileAlt,  label: "get_doc(path)",        desc: "Retrieve a specific doc by path" },
      { icon: FaList,     label: "list_sections()",      desc: "Browse all TOC sections" },
      { icon: FaDatabase, label: "get_section(section)", desc: "All docs in a section" },
    ];

    for (let i = 0; i < tools.length; i++) {
      const t = tools[i];
      const yRow = 2.2 + i * 0.72;

      // Icon circle bg
      s.addShape(pres.shapes.OVAL, {
        x: 0.45, y: yRow, w: 0.42, h: 0.42,
        fill: { color: C.primary },
        line: { color: C.primary, width: 0 },
      });
      const ic = await iconPng(t.icon, "#FFFFFF", 128);
      s.addImage({ data: ic, x: 0.53, y: yRow + 0.06, w: 0.27, h: 0.27 });

      s.addText(t.label, {
        x: 1.0, y: yRow, w: 4.6, h: 0.25,
        fontSize: 13, fontFace: "Consolas", bold: true,
        color: C.primary, margin: 0,
      });
      s.addText(t.desc, {
        x: 1.0, y: yRow + 0.26, w: 4.6, h: 0.22,
        fontSize: 12, fontFace: "Calibri",
        color: C.textMuted, margin: 0,
      });
    }

    // Right panel — visual summary cards
    const serverIcon = await iconPng(FaServer, "#" + C.white, 256);

    // Right panel bg
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.85, y: 0.28, w: 3.9, h: 5.07,
      fill: { color: C.primary },
      line: { color: C.primary, width: 0 },
      shadow: mkShadow(),
    });

    // Server icon
    s.addImage({ data: serverIcon, x: 7.05, y: 0.55, w: 1.5, h: 1.5 });

    s.addText("FastMCP Server", {
      x: 5.85, y: 2.15, w: 3.9, h: 0.45,
      fontSize: 18, fontFace: "Trebuchet MS", bold: true,
      color: C.white, align: "center", margin: 0,
    });

    s.addText("serving Microsoft Foundry\ndocumentation via MCP", {
      x: 5.85, y: 2.68, w: 3.9, h: 0.6,
      fontSize: 13, fontFace: "Calibri",
      color: C.accent, align: "center", margin: 0,
    });

    // Stats on right panel
    const stats = [
      { val: `${DATA.mdxDocs}`, label: "MDX Pages" },
      { val: `${DATA.docSections}`, label: "Doc Sections" },
      { val: "Hybrid",  label: "Search Mode" },
    ];
    for (let i = 0; i < stats.length; i++) {
      const sx = 5.85 + i * 1.3;
      s.addShape(pres.shapes.RECTANGLE, {
        x: sx + 0.05, y: 3.55, w: 1.2, h: 1.5,
        fill: { color: C.darkBg },
        line: { color: C.darkBg, width: 0 },
      });
      s.addText(stats[i].val, {
        x: sx + 0.05, y: 3.65, w: 1.2, h: 0.65,
        fontSize: 26, fontFace: "Trebuchet MS", bold: true,
        color: C.accent, align: "center", margin: 0,
      });
      s.addText(stats[i].label, {
        x: sx + 0.05, y: 4.32, w: 1.2, h: 0.45,
        fontSize: 11, fontFace: "Calibri",
        color: C.lightTeal, align: "center", margin: 0,
      });
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 3 — Architecture (Light)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.white };

    // Top color bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.primary },
      line: { color: C.primary, width: 0 },
    });

    s.addText("Pipeline Architecture", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    // Pipeline boxes
    const boxes = [
      { label: "MicrosoftDocs\nupstream", sub: "azure-ai-docs-pr", color: C.darkBg,   textCol: C.white,  subCol: C.lightTeal },
      { label: "Sync &\nConvert",         sub: "scripts/",         color: C.primary,  textCol: C.white,  subCol: C.accent },
      { label: "docs-vnext/",             sub: "280 MDX pages",    color: C.secondary,textCol: C.white,  subCol: C.darkBg },
      { label: "FastMCP\nServer",         sub: "foundry_docs_mcp/",color: C.primary,  textCol: C.white,  subCol: C.accent },
      { label: "AI Assistants\n& IDEs",   sub: "via MCP protocol", color: C.darkBg,   textCol: C.white,  subCol: C.lightTeal },
    ];

    const boxW = 1.55, boxH = 1.1, yBox = 1.5;
    const startX = 0.3;
    const gap = 0.45;

    for (let i = 0; i < boxes.length; i++) {
      const b = boxes[i];
      const x = startX + i * (boxW + gap);

      s.addShape(pres.shapes.RECTANGLE, {
        x, y: yBox, w: boxW, h: boxH,
        fill: { color: b.color },
        line: { color: b.color, width: 0 },
        shadow: mkShadow(),
      });
      s.addText(b.label, {
        x, y: yBox + 0.1, w: boxW, h: 0.6,
        fontSize: 13, fontFace: "Trebuchet MS", bold: true,
        color: b.textCol, align: "center", margin: 0,
      });
      s.addText(b.sub, {
        x, y: yBox + 0.72, w: boxW, h: 0.28,
        fontSize: 10, fontFace: "Calibri",
        color: b.subCol, align: "center", margin: 0,
      });

      // Arrow between boxes
      if (i < boxes.length - 1) {
        const arrowX = x + boxW + 0.05;
        s.addShape(pres.shapes.LINE, {
          x: arrowX, y: yBox + boxH / 2, w: gap - 0.1, h: 0,
          line: { color: C.primary, width: 2 },
        });
        // Arrowhead triangle
        s.addShape(pres.shapes.RECTANGLE, {
          x: arrowX + gap - 0.15, y: yBox + boxH / 2 - 0.09, w: 0.12, h: 0.18,
          fill: { color: C.primary },
          line: { color: C.primary, width: 0 },
        });
      }
    }

    // Details below pipeline
    const bullets = [
      { icon: FaSync,        text: "Auto-sync from upstream MicrosoftDocs 4×/day via GitHub Actions" },
      { icon: FaCode,        text: "Convert MS Learn markdown to Mintlify MDX — callouts, tabs, code groups" },
      { icon: FaRobot,       text: "Agentic workflows continuously improve accuracy, structure, and completeness" },
      { icon: FaServer,      text: "FastMCP server with hybrid Azure Search (keyword + vector + semantic reranking)" },
    ];

    for (let i = 0; i < bullets.length; i++) {
      const yRow = 3.0 + i * 0.54;
      const ic = await iconPng(bullets[i].icon, "#" + C.secondary, 128);
      s.addImage({ data: ic, x: 0.3, y: yRow + 0.06, w: 0.26, h: 0.26 });
      s.addText(bullets[i].text, {
        x: 0.7, y: yRow, w: 9.0, h: 0.38,
        fontSize: 13.5, fontFace: "Calibri",
        color: C.textDark, margin: 0,
      });
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 4 — Documentation Coverage (Light + Chart)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.lightBg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.secondary },
      line: { color: C.secondary, width: 0 },
    });

    s.addText(`Documentation Coverage — ${DATA.mdxDocs} Pages Across ${DATA.docSections} Sections`, {
      x: 0.4, y: 0.38, w: 9.2, h: 0.6,
      fontSize: 30, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    // Horizontal bar chart
    const chartData = [{
      name: "Pages",
      labels: DATA.sections.map(s => s.name).reverse(),
      values: DATA.sections.map(s => s.count).reverse(),
    }];

    s.addChart(pres.charts.BAR, chartData, {
      x: 0.3, y: 1.1, w: 9.4, h: 4.2,
      barDir: "bar",
      chartColors: [C.primary],
      chartArea: { fill: { color: C.lightBg }, roundedCorners: false },
      catAxisLabelColor: C.textDark,
      catAxisLabelFontSize: 11,
      catAxisLabelFontFace: "Calibri",
      valAxisLabelColor: C.textMuted,
      valAxisLabelFontSize: 10,
      valGridLine: { color: "D5E8E9", size: 0.5 },
      catGridLine: { style: "none" },
      showValue: true,
      dataLabelColor: C.white,
      dataLabelFontSize: 10,
      dataLabelFontFace: "Calibri",
      dataLabelPosition: "inEnd",
      showLegend: false,
    });
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 5 — Agentic Workflows (Dark)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.darkBg };

    // Top accent line
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.25,
      fill: { color: C.accent },
      line: { color: C.accent, width: 0 },
    });

    s.addText(`${DATA.agenticWorkflows} Agentic Workflows`, {
      x: 0.4, y: 0.38, w: 6.5, h: 0.72,
      fontSize: 40, fontFace: "Trebuchet MS", bold: true,
      color: C.white, margin: 0,
    });

    s.addText("Event-driven AI agents maintaining docs automatically", {
      x: 0.4, y: 1.12, w: 9.2, h: 0.38,
      fontSize: 15, fontFace: "Calibri",
      color: C.accent, margin: 0,
    });

    // Category cards — 2 rows × 3 cols
    const categories = [
      { icon: FaEye,           label: "Monitoring",     count: 6,  desc: "Upstream, SDK, community,\nReddit, diff reports, Dependabot" },
      { icon: FaFlask,         label: "Testing",        count: 4,  desc: "Noob tester, multi-device,\nsearch quality, testbench" },
      { icon: MdUpdate,        label: "Content Updates",count: 7,  desc: "Healer, updater, unbloat,\nglossary, labels, sync" },
      { icon: FaShieldAlt,     label: "Quality Review", count: 5,  desc: "Auditor, PR reviewer,\nmerge verify, push check" },
      { icon: FaUsers,         label: "Community",      count: 3,  desc: "Discussion monitor,\nresponder, auto-triage" },
      { icon: FaCog,           label: "Operations",     count: 1,  desc: "Slide deck maintainer\n(this deck!)" },
    ];

    const cardW = 2.95, cardH = 1.55;
    const cardColors = [C.primary, C.secondary, "025E6A", C.primary, C.secondary, "025E6A"];

    for (let i = 0; i < categories.length; i++) {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const cx = 0.35 + col * (cardW + 0.22);
      const cy = 1.7 + row * (cardH + 0.2);
      const cat = categories[i];

      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cardW, h: cardH,
        fill: { color: cardColors[i] },
        line: { color: cardColors[i], width: 0 },
        shadow: mkShadow(),
      });

      // Accent top strip on card
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cardW, h: 0.08,
        fill: { color: C.accent },
        line: { color: C.accent, width: 0 },
      });

      const ic = await iconPng(cat.icon, "#" + C.accent, 128);
      s.addImage({ data: ic, x: cx + 0.18, y: cy + 0.18, w: 0.35, h: 0.35 });

      s.addText(`${cat.count}  ${cat.label}`, {
        x: cx + 0.62, y: cy + 0.16, w: cardW - 0.72, h: 0.38,
        fontSize: 14.5, fontFace: "Trebuchet MS", bold: true,
        color: C.white, margin: 0,
      });

      s.addText(cat.desc, {
        x: cx + 0.18, y: cy + 0.62, w: cardW - 0.26, h: 0.75,
        fontSize: 11.5, fontFace: "Calibri",
        color: C.lightTeal, margin: 0,
      });
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 6 — Trigger Coverage (Light)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.primary },
      line: { color: C.primary, width: 0 },
    });

    s.addText("Event-Driven Trigger Coverage", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    // Trigger stat boxes — 3 per row, 2 rows
    const triggers = [
      { icon: FaComments,   label: "Issues",       count: DATA.issueWorkflows,    sub: "issue opened/labeled" },
      { icon: FaBolt,       label: "Dispatch",     count: DATA.dispatchWorkflows, sub: "workflow_dispatch + repo_dispatch" },
      { icon: FaTachometerAlt, label: "Schedule",  count: DATA.scheduleWorkflows, sub: "daily/weekly cron jobs" },
      { icon: FaCodeBranch, label: "Pull Request", count: DATA.prWorkflows,       sub: "PR open/sync/merge" },
      { icon: FaLayerGroup, label: "Workflow Run", count: DATA.workflowChains,    sub: "chained workflow triggers" },
      { icon: FaTag,        label: "Push",         count: DATA.pushWorkflows,     sub: "commit to main branch" },
    ];

    const boxW = 2.9, boxH = 1.8;
    const colors = [C.primary, C.darkBg, C.secondary, C.primary, C.darkBg, C.secondary];

    for (let i = 0; i < triggers.length; i++) {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const bx = 0.35 + col * (boxW + 0.28);
      const by = 1.25 + row * (boxH + 0.22);
      const t = triggers[i];

      s.addShape(pres.shapes.RECTANGLE, {
        x: bx, y: by, w: boxW, h: boxH,
        fill: { color: colors[i] },
        line: { color: colors[i], width: 0 },
        shadow: mkShadow(),
      });

      const ic = await iconPng(t.icon, "#" + C.accent, 128);
      s.addImage({ data: ic, x: bx + 0.22, y: by + 0.28, w: 0.5, h: 0.5 });

      s.addText(String(t.count), {
        x: bx + 0.85, y: by + 0.18, w: boxW - 0.95, h: 0.82,
        fontSize: 52, fontFace: "Trebuchet MS", bold: true,
        color: C.white, margin: 0,
      });

      s.addText(t.label, {
        x: bx + 0.18, y: by + 1.12, w: boxW - 0.26, h: 0.32,
        fontSize: 13, fontFace: "Trebuchet MS", bold: true,
        color: C.accent, margin: 0,
      });
      s.addText(t.sub, {
        x: bx + 0.18, y: by + 1.44, w: boxW - 0.26, h: 0.26,
        fontSize: 10, fontFace: "Calibri",
        color: C.lightTeal, margin: 0,
      });
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 7 — Quality Pipeline (Light)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.lightBg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.secondary },
      line: { color: C.secondary, width: 0 },
    });

    s.addText("Quality Assurance Pipeline", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    // 4 pipeline stage cards
    const stages = [
      {
        icon: FaCodeBranch, label: "Pre-Merge",
        items: ["on-push-docs-check", "pr-docs-reviewer"],
        color: C.primary,
      },
      {
        icon: FaCheckCircle, label: "Post-Merge",
        items: ["post-merge-docs-verify", "post-sync-updater"],
        color: C.darkBg,
      },
      {
        icon: FaHeartbeat, label: "Daily Healing",
        items: ["docs-auditor", "daily-doc-healer", "daily-doc-updater"],
        color: C.secondary,
      },
      {
        icon: FaFlask, label: "Testing",
        items: ["docs-noob-tester", "multi-device-tester", "search-test"],
        color: C.primary,
      },
    ];

    const stW = 2.1, stH = 3.4;
    for (let i = 0; i < stages.length; i++) {
      const st = stages[i];
      const sx = 0.35 + i * (stW + 0.35);
      const sy = 1.25;

      s.addShape(pres.shapes.RECTANGLE, {
        x: sx, y: sy, w: stW, h: stH,
        fill: { color: st.color },
        line: { color: st.color, width: 0 },
        shadow: mkShadow(),
      });

      // Icon circle at top of card
      s.addShape(pres.shapes.OVAL, {
        x: sx + (stW - 0.7) / 2, y: sy + 0.2, w: 0.7, h: 0.7,
        fill: { color: C.accent },
        line: { color: C.accent, width: 0 },
      });
      const ic = await iconPng(st.icon, "#" + C.darkBg, 128);
      s.addImage({ data: ic, x: sx + (stW - 0.7) / 2 + 0.1, y: sy + 0.3, w: 0.5, h: 0.5 });

      s.addText(st.label, {
        x: sx, y: sy + 1.05, w: stW, h: 0.4,
        fontSize: 14, fontFace: "Trebuchet MS", bold: true,
        color: C.white, align: "center", margin: 0,
      });

      // Item list
      for (let j = 0; j < st.items.length; j++) {
        s.addText(st.items[j], {
          x: sx + 0.1, y: sy + 1.58 + j * 0.52, w: stW - 0.2, h: 0.38,
          fontSize: 10.5, fontFace: "Consolas",
          color: C.accent, align: "center", margin: 0,
        });
      }

      // Arrow between stages
      if (i < stages.length - 1) {
        const arrowX = sx + stW + 0.07;
        const arrowY = sy + stH / 2;
        s.addShape(pres.shapes.LINE, {
          x: arrowX, y: arrowY, w: 0.23, h: 0,
          line: { color: C.primary, width: 2.5 },
        });
      }
    }

    // Footer note
    s.addText(
      "Every merge triggers automated checks · Daily audits catch regressions · Noob testing validates first-time reader experience",
      {
        x: 0.4, y: 4.88, w: 9.2, h: 0.4,
        fontSize: 11.5, fontFace: "Calibri", italic: true,
        color: C.textMuted, align: "center", margin: 0,
      }
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 8 — docs-vnext History & Impact (Light)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.lightBg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.secondary },
      line: { color: C.secondary, width: 0 },
    });

    s.addText("docs-vnext: History & Impact", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    // ── Left column: timeline ────────────────────────────────────────────
    const milestones = [
      { date: "Feb 2026", label: "Project launch — first agentic workflows wired up" },
      { date: "Mar 2026", label: "PR #23 unbloat + PR #28 glossary (35 terms) — first agentic content" },
      { date: "May 2026", label: "Baseline sync (PR #279) — full docs/ ↔ docs-vnext alignment" },
      { date: "Jun 2026", label: "280-page expansion — 15 upstream sync events auto-propagated" },
    ];

    for (let i = 0; i < milestones.length; i++) {
      const yRow = 1.2 + i * 0.92;
      const m = milestones[i];

      // Timeline dot
      s.addShape(pres.shapes.OVAL, {
        x: 0.35, y: yRow + 0.08, w: 0.28, h: 0.28,
        fill: { color: C.secondary },
        line: { color: C.secondary, width: 0 },
      });
      // Timeline line (except last)
      if (i < milestones.length - 1) {
        s.addShape(pres.shapes.LINE, {
          x: 0.485, y: yRow + 0.36, w: 0, h: 0.64,
          line: { color: C.lightTeal, width: 1.5 },
        });
      }

      s.addText(m.date, {
        x: 0.75, y: yRow, w: 1.1, h: 0.3,
        fontSize: 10.5, fontFace: "Trebuchet MS", bold: true,
        color: C.primary, margin: 0,
      });
      s.addText(m.label, {
        x: 0.75, y: yRow + 0.3, w: 4.65, h: 0.45,
        fontSize: 11, fontFace: "Calibri",
        color: C.textDark, margin: 0,
      });
    }

    // ── Right column: impact stat cards ─────────────────────────────────
    const stats = [
      { val: `${DATA.agenticPRsCreated}+`, label: "Automation PRs",    sub: "created by agents",          icon: FaRobot      },
      { val: `${DATA.upstreamSyncEvents}+`,label: "Upstream Events",   sub: "detected & propagated",      icon: FaSync       },
      { val: `${DATA.sdkReleaseAlerts}`,   label: "SDK Alerts",        sub: "release notifications sent",  icon: FaTag        },
      { val: `${DATA.docsVnextUniqueFiles}`,label:"Unique Pages",      sub: "only in docs-vnext",          icon: FaFileAlt    },
    ];

    const statW = 2.1, statH = 1.7;
    const statColors = [C.primary, C.darkBg, C.secondary, "025E6A"];

    for (let i = 0; i < stats.length; i++) {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const sx = 5.65 + col * (statW + 0.28);
      const sy = 1.2 + row * (statH + 0.22);
      const st = stats[i];

      s.addShape(pres.shapes.RECTANGLE, {
        x: sx, y: sy, w: statW, h: statH,
        fill: { color: statColors[i] },
        line: { color: statColors[i], width: 0 },
        shadow: mkShadowSm(),
      });

      const ic = await iconPng(st.icon, "#" + C.accent, 128);
      s.addImage({ data: ic, x: sx + 0.18, y: sy + 0.18, w: 0.38, h: 0.38 });

      s.addText(st.val, {
        x: sx + 0.68, y: sy + 0.08, w: statW - 0.78, h: 0.78,
        fontSize: 36, fontFace: "Trebuchet MS", bold: true,
        color: C.white, margin: 0,
      });
      s.addText(st.label, {
        x: sx + 0.1, y: sy + 1.05, w: statW - 0.2, h: 0.3,
        fontSize: 11.5, fontFace: "Trebuchet MS", bold: true,
        color: C.accent, margin: 0,
      });
      s.addText(st.sub, {
        x: sx + 0.1, y: sy + 1.35, w: statW - 0.2, h: 0.26,
        fontSize: 9.5, fontFace: "Calibri",
        color: C.lightTeal, margin: 0,
      });
    }

    // File delta note
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.65, y: 4.78, w: 4.16, h: 0.52,
      fill: { color: C.primary, transparency: 85 },
      line: { color: C.lightTeal, width: 0.5 },
    });
    s.addText(`${DATA.docsVnextSharedFiles} pages shared with docs/  ·  ${DATA.mdxDocs} total in docs-vnext`, {
      x: 5.68, y: 4.84, w: 4.1, h: 0.35,
      fontSize: 10, fontFace: "Calibri",
      color: C.textDark, align: "center", margin: 0,
    });
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 9 — Deep Dive: Agentic Chain in Action (Dark)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.darkBg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.25,
      fill: { color: C.accent },
      line: { color: C.accent, width: 0 },
    });

    s.addText("Deep Dive: Agentic Chain in Action", {
      x: 0.4, y: 0.35, w: 9.2, h: 0.6,
      fontSize: 34, fontFace: "Trebuchet MS", bold: true,
      color: C.white, margin: 0,
    });

    // ── Chain 1: Upstream Docs Chain ─────────────────────────────────────
    s.addText("CHAIN 1  ·  Upstream Docs Monitor → Issue → Sync → PR", {
      x: 0.4, y: 1.05, w: 9.2, h: 0.32,
      fontSize: 12, fontFace: "Trebuchet MS", bold: true,
      color: C.accent, margin: 0,
    });

    const chain1Steps = [
      { label: "MicrosoftDocs\ncommit detected",  sub: "3707cad1 Jun 26",   icon: FaBell,        color: C.primary  },
      { label: "Issue #454\ncreated",             sub: "upstream-sync label", icon: FaComments,   color: "025E6A"   },
      { label: "sync-and-convert\ndispatched",    sub: "run #28211218103",  icon: FaSync,         color: C.secondary},
      { label: "post-sync-updater\nanalyzes diff", sub: "checks MDX delta", icon: FaRobot,        color: C.primary  },
      { label: "docs-vnext PR\nor noop",           sub: "closes Issue #454", icon: FaCheckCircle, color: "025E6A"   },
    ];

    const cW = 1.68, cH = 1.3, cyR1 = 1.45;
    for (let i = 0; i < chain1Steps.length; i++) {
      const step = chain1Steps[i];
      const cx = 0.38 + i * (cW + 0.27);

      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cyR1, w: cW, h: cH,
        fill: { color: step.color },
        line: { color: step.color, width: 0 },
        shadow: mkShadowSm(),
      });

      const ic = await iconPng(step.icon, "#" + C.accent, 128);
      s.addImage({ data: ic, x: cx + (cW - 0.32) / 2, y: cyR1 + 0.1, w: 0.32, h: 0.32 });

      s.addText(step.label, {
        x: cx + 0.06, y: cyR1 + 0.48, w: cW - 0.12, h: 0.45,
        fontSize: 10, fontFace: "Trebuchet MS", bold: true,
        color: C.white, align: "center", margin: 0,
      });
      s.addText(step.sub, {
        x: cx + 0.06, y: cyR1 + 0.95, w: cW - 0.12, h: 0.28,
        fontSize: 8.5, fontFace: "Calibri",
        color: C.lightTeal, align: "center", margin: 0,
      });

      if (i < chain1Steps.length - 1) {
        const arrowX = cx + cW + 0.03;
        s.addShape(pres.shapes.LINE, {
          x: arrowX, y: cyR1 + cH / 2, w: 0.2, h: 0,
          line: { color: C.accent, width: 1.5 },
        });
      }
    }

    // ── Chain 2: SDK Release Chain ────────────────────────────────────────
    s.addText("CHAIN 2  ·  SDK Release Monitor → Issue → Docs Impact Assessment", {
      x: 0.4, y: 2.92, w: 9.2, h: 0.32,
      fontSize: 12, fontFace: "Trebuchet MS", bold: true,
      color: C.accent, margin: 0,
    });

    const chain2Steps = [
      { label: "JS 2.2.0 released\n.NET 2.1.0-beta.3", sub: "May 29, 2026",    icon: FaTag,       color: C.primary   },
      { label: "Issue #387\ncreated",                  sub: "sdk-release label", icon: FaComments, color: "025E6A"    },
      { label: "Breaking changes\nassessed",            sub: "3 SDKs updated",   icon: FaBug,       color: C.secondary },
      { label: "Docs impact\nreport written",           sub: "code-snippet delta", icon: FaFileAlt, color: C.primary   },
    ];

    const cyR2 = 3.32;
    for (let i = 0; i < chain2Steps.length; i++) {
      const step = chain2Steps[i];
      const cx = 0.38 + i * (cW + 0.58);

      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cyR2, w: cW, h: cH,
        fill: { color: step.color },
        line: { color: step.color, width: 0 },
        shadow: mkShadowSm(),
      });

      const ic = await iconPng(step.icon, "#" + C.accent, 128);
      s.addImage({ data: ic, x: cx + (cW - 0.32) / 2, y: cyR2 + 0.1, w: 0.32, h: 0.32 });

      s.addText(step.label, {
        x: cx + 0.06, y: cyR2 + 0.48, w: cW - 0.12, h: 0.45,
        fontSize: 10, fontFace: "Trebuchet MS", bold: true,
        color: C.white, align: "center", margin: 0,
      });
      s.addText(step.sub, {
        x: cx + 0.06, y: cyR2 + 0.95, w: cW - 0.12, h: 0.28,
        fontSize: 8.5, fontFace: "Calibri",
        color: C.lightTeal, align: "center", margin: 0,
      });

      if (i < chain2Steps.length - 1) {
        const arrowX = cx + cW + 0.1;
        s.addShape(pres.shapes.LINE, {
          x: arrowX, y: cyR2 + cH / 2, w: 0.42, h: 0,
          line: { color: C.accent, width: 1.5 },
        });
      }
    }

    // Footer note
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 5.2, w: 10, h: 0.425,
      fill: { color: C.primary, transparency: 75 },
      line: { color: C.primary, transparency: 75, width: 0 },
    });
    s.addText(
      "Both chains are fully automated — humans review PRs and issues but do not trigger or orchestrate the pipelines",
      {
        x: 0.4, y: 5.24, w: 9.2, h: 0.35,
        fontSize: 10.5, fontFace: "Calibri", italic: true,
        color: C.lightTeal, align: "center", margin: 0,
      }
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 10 — Deep Dive: Content Improvements (Light)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.primary },
      line: { color: C.primary, width: 0 },
    });

    s.addText("Deep Dive: Content Improvements", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    // ── Left panel: Glossary creation ────────────────────────────────────
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.35, y: 1.22, w: 4.35, h: 3.9,
      fill: { color: C.primary },
      line: { color: C.primary, width: 0 },
      shadow: mkShadow(),
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.35, y: 1.22, w: 4.35, h: 0.08,
      fill: { color: C.accent },
      line: { color: C.accent, width: 0 },
    });

    const glossaryIcon = await iconPng(FaBook, "#" + C.accent, 256);
    s.addImage({ data: glossaryIcon, x: 0.6, y: 1.4, w: 0.52, h: 0.52 });

    s.addText("PR #28 — Glossary Creation", {
      x: 1.22, y: 1.38, w: 3.3, h: 0.56,
      fontSize: 13, fontFace: "Trebuchet MS", bold: true,
      color: C.white, margin: 0,
    });

    s.addText("March 2, 2026  ·  glossary-maintainer  ·  +194 lines", {
      x: 0.48, y: 2.08, w: 4.1, h: 0.28,
      fontSize: 9.5, fontFace: "Consolas",
      color: C.accent, margin: 0,
    });

    const glossaryPoints = [
      "Created docs-vnext/glossary.mdx from zero",
      "35 terms across 16 alphabetical sections",
      "Core Foundry, MCP Ecosystem, Search & Retrieval,",
      "Agent Tools, Evaluation, Developer Tooling",
      "Scanned 5 key commits to derive terminology",
      "Also added Reference nav group to docs.json",
    ];

    for (let i = 0; i < glossaryPoints.length; i++) {
      s.addText("• " + glossaryPoints[i], {
        x: 0.48, y: 2.45 + i * 0.36, w: 4.1, h: 0.3,
        fontSize: 10.5, fontFace: "Calibri",
        color: C.lightTeal, margin: 0,
      });
    }

    // Metric chips
    const gMetrics = [
      { val: "35", lbl: "Terms" },
      { val: "16", lbl: "Sections" },
      { val: "0→1", lbl: "Files" },
    ];
    for (let i = 0; i < gMetrics.length; i++) {
      const gx = 0.5 + i * 1.42;
      s.addShape(pres.shapes.RECTANGLE, {
        x: gx, y: 4.62, w: 1.25, h: 0.38,
        fill: { color: C.darkBg },
        line: { color: C.darkBg, width: 0 },
      });
      s.addText(`${gMetrics[i].val}  ${gMetrics[i].lbl}`, {
        x: gx, y: 4.64, w: 1.25, h: 0.3,
        fontSize: 10, fontFace: "Trebuchet MS", bold: true,
        color: C.accent, align: "center", margin: 0,
      });
    }

    // ── Right panel: Unbloat improvement ────────────────────────────────
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.0, y: 1.22, w: 4.65, h: 3.9,
      fill: { color: C.darkBg },
      line: { color: C.darkBg, width: 0 },
      shadow: mkShadow(),
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.0, y: 1.22, w: 4.65, h: 0.08,
      fill: { color: C.accent },
      line: { color: C.accent, width: 0 },
    });

    const unbloatIcon = await iconPng(FaClipboardCheck, "#" + C.accent, 256);
    s.addImage({ data: unbloatIcon, x: 5.22, y: 1.4, w: 0.52, h: 0.52 });

    s.addText("PR #23 — Unbloat cloud-evaluation.mdx", {
      x: 5.85, y: 1.38, w: 3.68, h: 0.56,
      fontSize: 12.5, fontFace: "Trebuchet MS", bold: true,
      color: C.white, margin: 0,
    });

    s.addText("March 1, 2026  ·  unbloat-docs  ·  −39 lines, +10 lines", {
      x: 5.1, y: 2.08, w: 4.4, h: 0.28,
      fontSize: 9.5, fontFace: "Consolas",
      color: C.accent, margin: 0,
    });

    const bloatTable = [
      ["Bloat Type", "Detail"],
      ["Duplicate paragraph", "Repeated evaluator support info"],
      ["4× identical Tips", "\"Before you begin\" in each section"],
      ["Trivial tip", "\"To add another eval run, use same code\""],
      ["Verbose bullets → table", "5-bullet Interpret results → ref table"],
      ["Bullet lists → prose", "Two Rate limit error sections condensed"],
    ];

    for (let i = 0; i < bloatTable.length; i++) {
      const rowY = 2.44 + i * 0.34;
      const isHeader = i === 0;
      s.addShape(pres.shapes.RECTANGLE, {
        x: 5.1, y: rowY, w: 4.45, h: 0.3,
        fill: { color: isHeader ? C.primary : (i % 2 === 0 ? "022C33" : "01363D") },
        line: { color: isHeader ? C.primary : "025E6A", width: isHeader ? 0 : 0.3 },
      });
      s.addText(bloatTable[i][0], {
        x: 5.15, y: rowY + 0.04, w: 1.45, h: 0.24,
        fontSize: 8.5, fontFace: isHeader ? "Trebuchet MS" : "Calibri",
        bold: isHeader, color: isHeader ? C.white : C.lightTeal, margin: 0,
      });
      s.addText(bloatTable[i][1], {
        x: 6.65, y: rowY + 0.04, w: 2.85, h: 0.24,
        fontSize: 8.5, fontFace: isHeader ? "Trebuchet MS" : "Calibri",
        bold: isHeader, color: isHeader ? C.white : C.textMuted, margin: 0,
      });
    }

    // Result metrics
    const uMetrics = [
      { before: "913", after: "884", label: "Lines", pct: "−3%" },
      { before: "3,412", after: "3,180", label: "Words", pct: "−7%" },
      { before: "29", after: "19", label: "Bullets", pct: "−34%" },
    ];

    for (let i = 0; i < uMetrics.length; i++) {
      const mx = 5.1 + i * 1.52;
      s.addShape(pres.shapes.RECTANGLE, {
        x: mx, y: 4.62, w: 1.42, h: 0.38,
        fill: { color: C.primary },
        line: { color: C.primary, width: 0 },
      });
      s.addText(`${uMetrics[i].before}→${uMetrics[i].after}  ${uMetrics[i].pct}  ${uMetrics[i].label}`, {
        x: mx + 0.04, y: 4.65, w: 1.34, h: 0.28,
        fontSize: 9, fontFace: "Trebuchet MS", bold: true,
        color: C.accent, align: "center", margin: 0,
      });
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 11 — Evaluation Harness Results (Dark)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.darkBg };

    // Top accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.25,
      fill: { color: C.accent },
      line: { color: C.accent, width: 0 },
    });

    s.addText("Evaluation Harness Results", {
      x: 0.4, y: 0.35, w: 7.5, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.white, margin: 0,
    });

    s.addText(`${DATA.eval.totalEvals} evaluations · ${DATA.eval.servers} servers · ${DATA.eval.models} frontier models · ${DATA.eval.date}`, {      x: 0.4, y: 0.98, w: 9.2, h: 0.28,
      fontSize: 11.5, fontFace: "Calibri",
      color: C.textMuted, margin: 0,
    });

    // ── Scoreboard table ─────────────────────────────────────────────────
    const hdrFill  = { color: C.primary };
    const vnextFill = { color: "022C33" };
    const bodyFill  = { color: "F4FAFA" };
    const baseFill  = { color: "EFF6F6" };

    const tableData = [
      [
        { text: "Server",                   options: { bold: true, color: "FFFFFF", fill: hdrFill, align: "left" } },
        { text: "claude-sonnet-4.6",        options: { bold: true, color: "FFFFFF", fill: hdrFill, align: "center" } },
        { text: "Avg",                      options: { bold: true, color: "FFFFFF", fill: hdrFill, align: "center" } },
      ],
      [
        { text: "docs/ (Control C) 🥇",     options: { color: "1A2E30", fill: bodyFill } },
        { text: "0.907",                    options: { color: "1A2E30", fill: bodyFill, align: "center" } },
        { text: "0.907",                    options: { bold: true, color: "1A2E30", fill: bodyFill, align: "center" } },
      ],
      [
        { text: "MS Learn (A) 🥈",          options: { color: "1A2E30", fill: bodyFill } },
        { text: "0.900",                    options: { color: "1A2E30", fill: bodyFill, align: "center" } },
        { text: "0.900",                    options: { bold: true, color: "1A2E30", fill: bodyFill, align: "center" } },
      ],
      [
        { text: "docs-vnext/ 🥉",           options: { bold: true, color: C.accent, fill: vnextFill } },
        { text: "0.889",                    options: { bold: true, color: C.accent, fill: vnextFill, align: "center" } },
        { text: "0.889",                    options: { bold: true, color: C.accent, fill: vnextFill, align: "center" } },
      ],
      [
        { text: "Mintlify MCP (B)",         options: { color: "5A8087", fill: baseFill } },
        { text: "0.889",                    options: { color: "5A8087", fill: baseFill, align: "center" } },
        { text: "0.889",                    options: { color: "5A8087", fill: baseFill, align: "center" } },
      ],
    ];

    s.addTable(tableData, {
      x: 0.35, y: 1.3, w: 5.65, h: 1.9,
      fontSize: 11, fontFace: "Calibri",
      border: { type: "solid", pt: 0.5, color: "028090" },
      colW: [2.8, 1.5, 1.35],
    });

    // ── Hypothesis results ────────────────────────────────────────────────
    s.addText("Hypothesis Testing", {
      x: 0.35, y: 3.3, w: 5.65, h: 0.34,
      fontSize: 12.5, fontFace: "Trebuchet MS", bold: true,
      color: C.accent, margin: 0,
    });

    const hyps = [
      { id: "H1", badge: "❌ REJECTED",      detail: "docs-vnext (0.889) vs docs/ (0.907), δ=−0.018",  badgeColor: "C04040" },
      { id: "H2", badge: "➖ NO DIFFERENCE", detail: "docs-vnext (0.889) vs Mintlify (0.889), δ=0.000", badgeColor: "C9A800" },
      { id: "H3", badge: "❌ REJECTED",      detail: "docs-vnext (0.889) vs MS Learn (0.900), δ=−0.011",badgeColor: "C04040" },
      { id: "H4", badge: "✅ SUPPORTED",     detail: "Results consistent across both models",            badgeColor: "00A896" },
    ];

    for (let i = 0; i < hyps.length; i++) {
      const h = hyps[i];
      const hy = 3.72 + i * 0.43;

      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.35, y: hy, w: 5.65, h: 0.35,
        fill: { color: "022C33" },
        line: { color: C.primary, width: 0.5 },
      });
      s.addText(h.id, {
        x: 0.48, y: hy + 0.05, w: 0.38, h: 0.25,
        fontSize: 10.5, fontFace: "Trebuchet MS", bold: true,
        color: C.accent, margin: 0,
      });
      s.addText(h.badge, {
        x: 0.9, y: hy + 0.05, w: 1.55, h: 0.25,
        fontSize: 10, fontFace: "Trebuchet MS", bold: true,
        color: h.badgeColor, margin: 0,
      });
      s.addText(h.detail, {
        x: 2.48, y: hy + 0.06, w: 3.45, h: 0.23,
        fontSize: 9.5, fontFace: "Calibri",
        color: C.lightTeal, margin: 0,
      });
    }

    // ── Category breakdown (right column) ────────────────────────────────
    s.addText("Category Breakdown", {
      x: 6.22, y: 1.3, w: 3.4, h: 0.34,
      fontSize: 12.5, fontFace: "Trebuchet MS", bold: true,
      color: C.accent, margin: 0,
    });

    const cats = DATA.eval.categories.map(c => ({
      name: c.name,
      vnext: c.docsVnext,
      docs:  c.docsControl,
      lead: c.docsVnext >= c.docsControl,
    }));

    const barMaxW = 3.1;
    for (let i = 0; i < cats.length; i++) {
      const c = cats[i];
      const cy = 1.72 + i * 0.72;
      const barW = barMaxW * ((c.vnext - 0.75) / 0.25);

      s.addText(c.name, {
        x: 6.22, y: cy, w: 3.4, h: 0.25,
        fontSize: 9.5, fontFace: "Consolas",
        color: C.lightTeal, margin: 0,
      });

      s.addShape(pres.shapes.RECTANGLE, {
        x: 6.22, y: cy + 0.28, w: barMaxW, h: 0.28,
        fill: { color: "022C33" },
        line: { color: C.primary, width: 0 },
      });
      s.addShape(pres.shapes.RECTANGLE, {
        x: 6.22, y: cy + 0.28, w: Math.max(0.1, barW), h: 0.28,
        fill: { color: c.lead ? C.secondary : "5A8087" },
        line: { color: c.lead ? C.secondary : "5A8087", width: 0 },
      });
      s.addText(`${c.vnext} ${c.lead ? "▲" : "▼"}`, {
        x: 6.22 + barMaxW + 0.08, y: cy + 0.28, w: 0.55, h: 0.28,
        fontSize: 9, fontFace: "Calibri", bold: c.lead,
        color: c.lead ? C.accent : C.textMuted, margin: 0,
      });
    }

    // Footer insight
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 5.2, w: 10, h: 0.425,
      fill: { color: C.primary, transparency: 70 },
      line: { color: C.primary, transparency: 70, width: 0 },
    });
    s.addText(
      "docs-vnext leads in observability-evaluation (0.880 vs 0.853) — opportunity to improve getting-started coverage (0.827 vs 0.913)",
      {
        x: 0.4, y: 5.24, w: 9.2, h: 0.35,
        fontSize: 10.5, fontFace: "Calibri", italic: true,
        color: C.lightTeal, align: "center", margin: 0,
      }
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 12 — Community Integration (Light)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.primary },
      line: { color: C.primary, width: 0 },
    });

    s.addText("Community Integration", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    // Three integration blocks
    const integrations = [
      {
        icon: FaComments,
        title: "Community Discussions",
        repo: "microsoft-foundry/discussions",
        desc: "Cross-repo repository_dispatch fires whenever a new discussion is posted. The agent reads context from cache-memory and determines if docs need updating or a response is warranted.",
        color: C.primary,
      },
      {
        icon: FaUsers,
        title: "Discussion Feedback Responder",
        repo: "issue_comment events",
        desc: "Automatically responds to discussions referencing documentation gaps. Surfaces the most relevant docs and flags content needing improvement.",
        color: C.darkBg,
      },
      {
        icon: FaBug,
        title: "Auto-Triage Issues",
        repo: "issues: opened, labeled",
        desc: "Labels and triages new GitHub issues, routing documentation bugs to the appropriate agent workflows. Integrates with label-ops for structured labeling.",
        color: C.secondary,
      },
    ];

    for (let i = 0; i < integrations.length; i++) {
      const intr = integrations[i];
      const bx = 0.35 + i * 3.22;
      const by = 1.25;
      const bw = 3.0, bh = 3.85;

      s.addShape(pres.shapes.RECTANGLE, {
        x: bx, y: by, w: bw, h: bh,
        fill: { color: intr.color },
        line: { color: intr.color, width: 0 },
        shadow: mkShadow(),
      });

      // Icon
      s.addShape(pres.shapes.OVAL, {
        x: bx + (bw - 0.72) / 2, y: by + 0.22, w: 0.72, h: 0.72,
        fill: { color: C.accent },
        line: { color: C.accent, width: 0 },
      });
      const ic = await iconPng(intr.icon, "#" + C.darkBg, 128);
      s.addImage({ data: ic, x: bx + (bw - 0.72) / 2 + 0.1, y: by + 0.32, w: 0.52, h: 0.52 });

      s.addText(intr.title, {
        x: bx + 0.12, y: by + 1.08, w: bw - 0.24, h: 0.5,
        fontSize: 13.5, fontFace: "Trebuchet MS", bold: true,
        color: C.white, align: "center", margin: 0,
      });

      s.addText(intr.repo, {
        x: bx + 0.12, y: by + 1.62, w: bw - 0.24, h: 0.3,
        fontSize: 10, fontFace: "Consolas",
        color: C.accent, align: "center", margin: 0,
      });

      s.addText(intr.desc, {
        x: bx + 0.14, y: by + 2.02, w: bw - 0.28, h: 1.6,
        fontSize: 11.5, fontFace: "Calibri",
        color: C.lightTeal, margin: 0,
      });
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 13 — SDK Monitoring (Dark)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.darkBg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.25,
      fill: { color: C.secondary },
      line: { color: C.secondary, width: 0 },
    });

    s.addText(`SDK Release Monitoring — ${DATA.sdkRepos} Repos`, {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.white, margin: 0,
    });

    s.addText("Detects new azure-ai-projects releases and assesses documentation impact", {
      x: 0.4, y: 1.08, w: 9.2, h: 0.38,
      fontSize: 14, fontFace: "Calibri",
      color: C.accent, margin: 0,
    });

    // SDK cards
    const sdks = [
      { lang: "Python",     icon: FaPython,    repo: "Azure/azure-sdk-for-python",  path: "sdk/ai/azure-ai-projects/CHANGELOG.md" },
      { lang: "JavaScript", icon: FaJs,        repo: "Azure/azure-sdk-for-js",      path: "sdk/ai/ai-projects/CHANGELOG.md" },
      { lang: ".NET",       icon: FaCode,      repo: "Azure/azure-sdk-for-net",     path: "sdk/ai/Azure.AI.Projects/CHANGELOG.md" },
      { lang: "Java",       icon: FaBoxOpen,   repo: "Azure/azure-sdk-for-java",    path: "sdk/ai/azure-ai-projects/CHANGELOG.md" },
    ];

    const sdkW = 2.1, sdkH = 3.2;
    const sdkColors = [C.primary, "014A55", C.secondary, "025E6A"];

    for (let i = 0; i < sdks.length; i++) {
      const sdk = sdks[i];
      const sx = 0.35 + i * (sdkW + 0.38);
      const sy = 1.7;

      s.addShape(pres.shapes.RECTANGLE, {
        x: sx, y: sy, w: sdkW, h: sdkH,
        fill: { color: sdkColors[i] },
        line: { color: sdkColors[i], width: 0 },
        shadow: mkShadow(),
      });

      s.addShape(pres.shapes.RECTANGLE, {
        x: sx, y: sy, w: sdkW, h: 0.07,
        fill: { color: C.accent },
        line: { color: C.accent, width: 0 },
      });

      const ic = await iconPng(sdk.icon, "#" + C.accent, 256);
      s.addImage({ data: ic, x: sx + (sdkW - 0.72) / 2, y: sy + 0.22, w: 0.72, h: 0.72 });

      s.addText(sdk.lang, {
        x: sx, y: sy + 1.05, w: sdkW, h: 0.42,
        fontSize: 18, fontFace: "Trebuchet MS", bold: true,
        color: C.white, align: "center", margin: 0,
      });

      s.addText(sdk.repo, {
        x: sx + 0.1, y: sy + 1.56, w: sdkW - 0.2, h: 0.35,
        fontSize: 9, fontFace: "Consolas",
        color: C.accent, align: "center", margin: 0,
      });

      s.addText(sdk.path, {
        x: sx + 0.08, y: sy + 1.96, w: sdkW - 0.16, h: 0.55,
        fontSize: 8.5, fontFace: "Consolas",
        color: C.lightTeal, align: "center", margin: 0,
      });

      // "CHANGELOG" badge
      s.addShape(pres.shapes.RECTANGLE, {
        x: sx + 0.25, y: sy + 2.6, w: sdkW - 0.5, h: 0.38,
        fill: { color: C.darkBg },
        line: { color: C.darkBg, width: 0 },
      });
      s.addText("CHANGELOG.md", {
        x: sx + 0.25, y: sy + 2.65, w: sdkW - 0.5, h: 0.28,
        fontSize: 9, fontFace: "Consolas", bold: true,
        color: C.accent, align: "center", margin: 0,
      });
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 14 — Key Metrics (Light)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.lightBg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.secondary },
      line: { color: C.secondary, width: 0 },
    });

    s.addText("By The Numbers", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true,
      color: C.darkBg, margin: 0,
    });

    const metrics = [
      { val: `${DATA.mdxDocs}`,           label: "MDX Pages",            sub: "in docs-vnext/",            icon: FaFileAlt },
      { val: `${DATA.agenticWorkflows}`,  label: "Agentic Workflows",    sub: ".md definitions",           icon: FaRobot },
      { val: `${DATA.docSections}`,       label: "Doc Sections",         sub: "topic areas covered",       icon: FaList },
      { val: `${DATA.slashCommands}`,     label: "Slash Commands",       sub: "/audit /unbloat /sdk-check…", icon: FaBolt },
      { val: `${DATA.sdkRepos}`,          label: "SDK Repos Tracked",    sub: "Python · JS · .NET · Java", icon: FaCode },
      { val: `${DATA.scheduleWorkflows}`, label: "Scheduled Jobs",       sub: "daily/weekly cron",         icon: FaTachometerAlt },
    ];

    const mW = 2.9, mH = 2.15;
    const mColors = [C.primary, C.darkBg, C.secondary, C.primary, C.darkBg, C.secondary];

    for (let i = 0; i < metrics.length; i++) {
      const m = metrics[i];
      const col = i % 3;
      const row = Math.floor(i / 3);
      const mx = 0.35 + col * (mW + 0.28);
      const my = 1.22 + row * (mH + 0.2);

      s.addShape(pres.shapes.RECTANGLE, {
        x: mx, y: my, w: mW, h: mH,
        fill: { color: mColors[i] },
        line: { color: mColors[i], width: 0 },
        shadow: mkShadow(),
      });

      const ic = await iconPng(m.icon, "#" + C.accent, 128);
      s.addImage({ data: ic, x: mx + 0.2, y: my + 0.25, w: 0.48, h: 0.48 });

      s.addText(m.val, {
        x: mx + 0.8, y: my + 0.12, w: mW - 0.9, h: 0.82,
        fontSize: 52, fontFace: "Trebuchet MS", bold: true,
        color: C.white, margin: 0,
      });

      s.addText(m.label, {
        x: mx + 0.15, y: my + 1.2, w: mW - 0.3, h: 0.36,
        fontSize: 13, fontFace: "Trebuchet MS", bold: true,
        color: C.accent, margin: 0,
      });

      s.addText(m.sub, {
        x: mx + 0.15, y: my + 1.56, w: mW - 0.3, h: 0.34,
        fontSize: 10.5, fontFace: "Calibri",
        color: C.lightTeal, margin: 0,
      });
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 15 — What's Next (Dark)
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.darkBg };

    // Decorative circle
    s.addShape(pres.shapes.OVAL, {
      x: 6.5, y: -1.2, w: 5.0, h: 5.0,
      fill: { color: C.primary, transparency: 80 },
      line: { color: C.primary, transparency: 80, width: 0 },
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.18, h: 5.625,
      fill: { color: C.accent },
      line: { color: C.accent, width: 0 },
    });

    s.addText("What's Next", {
      x: 0.45, y: 0.35, w: 5.8, h: 0.72,
      fontSize: 40, fontFace: "Trebuchet MS", bold: true,
      color: C.white, margin: 0,
    });

    const roadmap = [
      { icon: FaGlobe,        item: "Improve getting-started coverage — eval weak spot (0.827 vs 0.913 for docs/)" },
      { icon: FaChartBar,     item: "Search quality dashboard — track MRR/NDCG trends over time" },
      { icon: FaRocket,       item: "Proactive gap filling — auto-draft missing pages from upstream signals" },
      { icon: FaSync,         item: "Docs-vnext → Mintlify deployment via GitHub Pages or Vercel" },
      { icon: FaShieldAlt,    item: "Responsible AI guardrails section expansion with worked examples" },
      { icon: MdOutlineMonitor, item: "Real-time ops dashboard embedding MCP server telemetry" },
    ];

    for (let i = 0; i < roadmap.length; i++) {
      const yRow = 1.3 + i * 0.68;
      const r = roadmap[i];

      s.addShape(pres.shapes.OVAL, {
        x: 0.45, y: yRow + 0.06, w: 0.44, h: 0.44,
        fill: { color: C.primary },
        line: { color: C.primary, width: 0 },
      });
      const ic = await iconPng(r.icon, "#" + C.accent, 128);
      s.addImage({ data: ic, x: 0.53, y: yRow + 0.1, w: 0.28, h: 0.28 });

      s.addText(r.item, {
        x: 1.05, y: yRow + 0.05, w: 8.5, h: 0.44,
        fontSize: 14, fontFace: "Calibri",
        color: C.lightTeal, margin: 0,
      });
    }

    // Bottom tagline
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 5.15, w: 10, h: 0.475,
      fill: { color: C.primary, transparency: 75 },
      line: { color: C.primary, transparency: 75, width: 0 },
    });
    s.addText("foundry-docs · github.com/nicholasdbrady/foundry-docs", {
      x: 0.4, y: 5.2, w: 9.2, h: 0.35,
      fontSize: 12, fontFace: "Calibri",
      color: C.lightTeal, align: "center", margin: 0,
    });
  }

  // ── Write file ───────────────────────────────────────────────────────
  const outDir = path.resolve(path.dirname(__filename), ".");
  fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, "foundry-docs-overview.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log(`✅  Written: ${outPath}`);
}

buildPresentation().catch(err => {
  console.error("❌ Build failed:", err);
  process.exit(1);
});
