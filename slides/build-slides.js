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
const { execFileSync } = require("child_process");

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

// ── LIVE DATA — computed from the repository at build time ────────────────
const repoRoot = path.resolve(__dirname, "..");

function walkFiles(dir, extension) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    return entry.isDirectory()
      ? walkFiles(fullPath, extension)
      : entry.name.endsWith(extension) ? [fullPath] : [];
  });
}

const docFiles = walkFiles(path.join(repoRoot, "docs-vnext"), ".mdx");
const canonicalDocFiles = walkFiles(path.join(repoRoot, "docs"), ".mdx");
const workflowFiles = walkFiles(path.join(repoRoot, ".github", "workflows"), ".md");
const workflowText = workflowFiles.map((file) => ({ file, text: fs.readFileSync(file, "utf8") }));
const sectionCounts = new Map();
for (const file of docFiles) {
  const section = path.relative(path.join(repoRoot, "docs-vnext"), file).split(path.sep)[0];
  sectionCounts.set(section, (sectionCounts.get(section) || 0) + 1);
}
const sectionLabel = (name) => name.split("-").map((word) => word[0].toUpperCase() + word.slice(1)).join(" ");
const triggerCount = (name) => workflowText.filter(({ text }) => new RegExp(`^  ${name}:`, "m").test(text)).length;
const sdkMonitor = fs.readFileSync(path.join(repoRoot, ".github", "workflows", "sdk-release-monitor.md"), "utf8");
const sdkRepos = new Set(sdkMonitor.match(/Azure\/azure-sdk-for-(?:python|js|net|java)/g) || []).size;
const glossaryTerms = (fs.readFileSync(path.join(repoRoot, "docs-vnext", "reference", "glossary.mdx"), "utf8")
  .match(/^## /gm) || []).length;
const canonicalNames = new Set(canonicalDocFiles.map((file) => path.basename(file)));
const vnextOnly = docFiles.filter((file) => !canonicalNames.has(path.basename(file))).length;

function workflowCategoryCount(pattern) {
  return workflowFiles.filter((file) => pattern.test(path.basename(file))).length;
}

function liveGitHubPrCounts() {
  const fallback = { merged: 14, agentic: 12, asOf: "2026-09-14" };
  try {
    const query = (q) => {
      const input = JSON.stringify({ query: q, perPage: 100, fields: ["number", "title", "url"] });
      return JSON.parse(execFileSync("github", ["search_pull_requests", "."], {
        cwd: repoRoot, input, encoding: "utf8", stdio: ["pipe", "pipe", "ignore"],
      }));
    };
    const merged = query("repo:nicholasdbrady/foundry-docs is:pr is:merged label:docs-vnext").length;
    const agentic = query(
      "repo:nicholasdbrady/foundry-docs is:pr is:merged label:docs-vnext author:app/github-actions"
    ).length;
    return { merged, agentic, asOf: new Date().toISOString().slice(0, 10) };
  } catch {
    console.warn("GitHub metrics unavailable; using the dated snapshot from 2026-09-14.");
    return fallback;
  }
}

const GITHUB = liveGitHubPrCounts();
const DATA = {
  mdxDocs: docFiles.length,
  canonicalDocs: canonicalDocFiles.length,
  agenticWorkflows: workflowFiles.length,
  slashCommands: triggerCount("slash_command"),
  workflowChains: triggerCount("workflow_run"),
  scheduleWorkflows: triggerCount("schedule"),
  pushWorkflows: triggerCount("push"),
  prWorkflows: triggerCount("pull_request"),
  issueWorkflows: triggerCount("issues"),
  dispatchWorkflows: triggerCount("workflow_dispatch") + triggerCount("repository_dispatch"),
  sdkRepos,
  glossaryTerms,
  vnextOnly,
  docSections: sectionCounts.size,
  sections: [...sectionCounts.entries()]
    .map(([name, count]) => ({ name: sectionLabel(name), count }))
    .sort((a, b) => b.count - a.count),
  workflowCategories: {
    monitoring: workflowCategoryCount(/monitor|diff|dependabot/),
    testing: workflowCategoryCount(/test|audit|review|verify/),
    updating: workflowCategoryCount(/updater|sync|unbloat|glossary|fix|changelog|catalog/),
    community: workflowCategoryCount(/community|reddit|triage/),
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
      { label: "MicrosoftDocs\nupstream", sub: "azure-ai-docs", color: C.darkBg,   textCol: C.white,  subCol: C.lightTeal },
      { label: "Sync &\nConvert",         sub: "scripts/",         color: C.primary,  textCol: C.white,  subCol: C.accent },
      { label: "docs-vnext/",             sub: `${DATA.mdxDocs} MDX pages`, color: C.secondary,textCol: C.white, subCol: C.darkBg },
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
      { icon: FaEye, label: "Monitoring", count: DATA.workflowCategories.monitoring, desc: "Upstream, SDK, community,\nReddit, diff reports, Dependabot" },
      { icon: FaFlask, label: "Testing & Review", count: DATA.workflowCategories.testing, desc: "Noob tests, search quality,\naudits, PR and merge checks" },
      { icon: MdUpdate, label: "Content Updates", count: DATA.workflowCategories.updating, desc: "Updater, sync, unbloat,\nglossary, fixes, catalog" },
      { icon: FaBolt, label: "Slash Commands", count: DATA.slashCommands, desc: "On-demand operations from\nissues and pull requests" },
      { icon: FaUsers, label: "Community", count: DATA.workflowCategories.community, desc: "Discussions, Reddit signals,\nand automated triage" },
      { icon: FaCog, label: "Total Fleet", count: DATA.agenticWorkflows, desc: "Post-consolidation workflow\ndefinitions in the repository" },
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
  // SLIDE 8 — docs-vnext History & Impact
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.primary }, line: { color: C.primary, width: 0 },
    });
    s.addText("docs-vnext History & Impact", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 36, fontFace: "Trebuchet MS", bold: true, color: C.darkBg, margin: 0,
    });
    s.addText(`GitHub snapshot ${GITHUB.asOf} · repository metrics calculated at build time`, {
      x: 0.4, y: 1.0, w: 9.2, h: 0.28,
      fontSize: 10.5, fontFace: "Calibri", color: C.textMuted, margin: 0,
    });

    const impact = [
      { value: GITHUB.merged, label: "Merged docs-vnext PRs", color: C.primary },
      { value: GITHUB.agentic, label: "Agent-created merges", color: C.secondary },
      { value: GITHUB.merged - GITHUB.agentic, label: "Human-created merges", color: C.darkBg },
      { value: DATA.vnextOnly, label: "Filename additions vs docs/", color: "025E6A" },
    ];
    impact.forEach((item, index) => {
      const x = 0.35 + index * 2.4;
      s.addShape(pres.shapes.RECTANGLE, {
        x, y: 1.38, w: 2.15, h: 1.15,
        fill: { color: item.color }, line: { color: item.color, width: 0 }, shadow: mkShadowSm(),
      });
      s.addText(String(item.value), {
        x, y: 1.48, w: 2.15, h: 0.58,
        fontSize: 34, fontFace: "Trebuchet MS", bold: true, color: C.white, align: "center", margin: 0,
      });
      s.addText(item.label, {
        x: x + 0.08, y: 2.08, w: 1.99, h: 0.28,
        fontSize: 10.5, fontFace: "Calibri", color: C.accent, align: "center", margin: 0,
      });
    });

    s.addText("Milestone arc", {
      x: 0.4, y: 2.82, w: 2.2, h: 0.32,
      fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.primary, margin: 0,
    });
    s.addShape(pres.shapes.LINE, {
      x: 0.75, y: 3.65, w: 8.5, h: 0,
      line: { color: C.primary, width: 3 },
    });
    const milestones = [
      { date: "Mar 1", title: "Unbloat PR #23", note: "Cloud evaluation simplified" },
      { date: "Mar 2", title: "Glossary PR #28", note: "35 terms created from zero" },
      { date: "Mar 5", title: "Monitor issues #53/#54", note: "SDK + upstream chains proven" },
      { date: "Current", title: `${DATA.mdxDocs} pages`, note: `${DATA.docSections} top-level sections` },
    ];
    milestones.forEach((item, index) => {
      const x = 0.55 + index * 2.35;
      s.addShape(pres.shapes.OVAL, {
        x: x + 0.72, y: 3.48, w: 0.34, h: 0.34,
        fill: { color: index === milestones.length - 1 ? C.accent : C.primary },
        line: { color: C.white, width: 1.5 },
      });
      s.addText(item.date, {
        x, y: 3.12, w: 1.8, h: 0.25,
        fontSize: 10, fontFace: "Calibri", bold: true, color: C.textMuted, align: "center", margin: 0,
      });
      s.addText(item.title, {
        x, y: 3.95, w: 1.8, h: 0.3,
        fontSize: 11.5, fontFace: "Trebuchet MS", bold: true, color: C.darkBg, align: "center", margin: 0,
      });
      s.addText(item.note, {
        x, y: 4.33, w: 1.8, h: 0.5,
        fontSize: 9.5, fontFace: "Calibri", color: C.textMuted, align: "center", margin: 0,
      });
    });
    s.addText(
      `Automation evidence: SDK release issue #53 and upstream-sync issue #54 were both created, assessed, and closed.`,
      {
        x: 0.5, y: 5.05, w: 9, h: 0.3,
        fontSize: 10.5, fontFace: "Calibri", italic: true, color: C.textMuted, align: "center", margin: 0,
      }
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 9 — Deep Dive: Agentic Chain
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.darkBg };
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.25,
      fill: { color: C.accent }, line: { color: C.accent, width: 0 },
    });
    s.addText("Deep Dive: Agentic Chain in Action", {
      x: 0.4, y: 0.36, w: 9.2, h: 0.62,
      fontSize: 34, fontFace: "Trebuchet MS", bold: true, color: C.white, margin: 0,
    });
    s.addText("A real upstream commit becomes an assessed documentation action without manual routing", {
      x: 0.4, y: 1.0, w: 9.2, h: 0.3,
      fontSize: 12.5, fontFace: "Calibri", color: C.accent, margin: 0,
    });

    const chain = [
      { n: "1", title: "Upstream Docs Monitor", detail: "Detected MicrosoftDocs commit 34b7019\n(blocklist instruction update)" },
      { n: "2", title: "Issue #54", detail: "Recorded 1 changed commit and impact\nRun 22709537548 · succeeded" },
      { n: "3", title: "sync-and-convert", detail: "Dispatched extraction + MDX conversion\nOutcome: sync requested" },
      { n: "4", title: "Post-Sync Updater", detail: "Analyzes resulting delta\nCreates docs-vnext PR or noops" },
    ];
    chain.forEach((item, index) => {
      const x = 0.35 + index * 2.42;
      s.addShape(pres.shapes.RECTANGLE, {
        x, y: 1.62, w: 2.12, h: 2.22,
        fill: { color: index % 2 ? "025E6A" : C.primary },
        line: { color: C.accent, width: 1 }, shadow: mkShadow(),
      });
      s.addShape(pres.shapes.OVAL, {
        x: x + 0.72, y: 1.82, w: 0.68, h: 0.68,
        fill: { color: C.accent }, line: { color: C.accent, width: 0 },
      });
      s.addText(item.n, {
        x: x + 0.72, y: 1.94, w: 0.68, h: 0.34,
        fontSize: 18, fontFace: "Trebuchet MS", bold: true, color: C.darkBg, align: "center", margin: 0,
      });
      s.addText(item.title, {
        x: x + 0.12, y: 2.68, w: 1.88, h: 0.42,
        fontSize: 12, fontFace: "Trebuchet MS", bold: true, color: C.white, align: "center", margin: 0,
      });
      s.addText(item.detail, {
        x: x + 0.12, y: 3.15, w: 1.88, h: 0.55,
        fontSize: 9.2, fontFace: "Calibri", color: C.lightTeal, align: "center", margin: 0,
      });
      if (index < chain.length - 1) {
        s.addShape(pres.shapes.LINE, {
          x: x + 2.14, y: 2.72, w: 0.25, h: 0,
          line: { color: C.accent, width: 2.5, beginArrowType: "none", endArrowType: "triangle" },
        });
      }
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.35, y: 4.15, w: 9.3, h: 0.88,
      fill: { color: "022C33" }, line: { color: C.primary, width: 1 },
    });
    s.addText("Parallel SDK chain", {
      x: 0.55, y: 4.36, w: 1.6, h: 0.3,
      fontSize: 12.5, fontFace: "Trebuchet MS", bold: true, color: C.accent, margin: 0,
    });
    s.addText(
      "SDK Release Monitor → Java 2.0.0-beta.2 → Issue #53 → breaking-change assessment (Index rename, flags removed, DayOfWeek import change)",
      {
        x: 2.15, y: 4.32, w: 7.15, h: 0.4,
        fontSize: 10.5, fontFace: "Calibri", color: C.lightTeal, margin: 0,
      }
    );
    s.addText("Run durations are not exposed by the available read interface; outcomes and run IDs are cited instead.", {
      x: 0.5, y: 5.18, w: 9, h: 0.22,
      fontSize: 9, fontFace: "Calibri", italic: true, color: C.textMuted, align: "center", margin: 0,
    });
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 10 — Deep Dive: Content Improvements
  // ══════════════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: C.lightBg };
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.28,
      fill: { color: C.secondary }, line: { color: C.secondary, width: 0 },
    });
    s.addText("Deep Dive: Content Improvements", {
      x: 0.4, y: 0.38, w: 9.2, h: 0.62,
      fontSize: 34, fontFace: "Trebuchet MS", bold: true, color: C.darkBg, margin: 0,
    });

    const cards = [
      {
        x: 0.35, color: C.primary, eyebrow: "PR #28 · GLOSSARY MAINTAINER",
        title: "From zero to a usable glossary",
        metric: "35 terms · 16 alphabetical sections · 1 run",
        before: "Before: no docs-vnext glossary or Reference navigation group.",
        after: `After: generated glossary, navigation wiring, and terminology coverage. Current glossary has ${DATA.glossaryTerms} top-level term groups after later restructuring.`,
      },
      {
        x: 5.08, color: C.darkBg, eyebrow: "PR #23 · DOCUMENTATION UNBLOAT",
        title: "Cloud evaluation, less repetition",
        metric: "3,412 → 3,180 words · bullets −34.5%",
        before: "Before: duplicate intro text, four repetitive prerequisite tips, verbose lists, and a trivial tip.",
        after: "After: one reference table, direct prose, and retained technical content. Net change: +10/−39 lines.",
      },
    ];
    cards.forEach((card) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x: card.x, y: 1.25, w: 4.57, h: 3.88,
        fill: { color: card.color }, line: { color: card.color, width: 0 }, shadow: mkShadow(),
      });
      s.addText(card.eyebrow, {
        x: card.x + 0.22, y: 1.52, w: 4.13, h: 0.28,
        fontSize: 9.5, fontFace: "Consolas", bold: true, color: C.accent, margin: 0,
      });
      s.addText(card.title, {
        x: card.x + 0.22, y: 1.92, w: 4.13, h: 0.55,
        fontSize: 20, fontFace: "Trebuchet MS", bold: true, color: C.white, margin: 0,
      });
      s.addShape(pres.shapes.RECTANGLE, {
        x: card.x + 0.22, y: 2.66, w: 4.13, h: 0.52,
        fill: { color: C.accent, transparency: 8 }, line: { color: C.accent, width: 0 },
      });
      s.addText(card.metric, {
        x: card.x + 0.3, y: 2.78, w: 3.97, h: 0.24,
        fontSize: 11, fontFace: "Trebuchet MS", bold: true, color: C.darkBg, align: "center", margin: 0,
      });
      s.addText(card.before, {
        x: card.x + 0.22, y: 3.45, w: 4.13, h: 0.62,
        fontSize: 11, fontFace: "Calibri", color: C.lightTeal, margin: 0,
      });
      s.addText(card.after, {
        x: card.x + 0.22, y: 4.18, w: 4.13, h: 0.68,
        fontSize: 11, fontFace: "Calibri", color: C.white, margin: 0,
      });
    });
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

    s.addText("Latest readable snapshot · 300 evaluations · 4 servers · 3 frontier models · 2026-03-05", {
      x: 0.4, y: 0.98, w: 9.2, h: 0.28,
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
        { text: "Server",               options: { bold: true, color: "FFFFFF", fill: hdrFill, align: "left" } },
        { text: "claude-opus-4.6",      options: { bold: true, color: "FFFFFF", fill: hdrFill, align: "center" } },
        { text: "gemini-3-pro",         options: { bold: true, color: "FFFFFF", fill: hdrFill, align: "center" } },
        { text: "gpt-5.3-codex",        options: { bold: true, color: "FFFFFF", fill: hdrFill, align: "center" } },
        { text: "Avg",                  options: { bold: true, color: "FFFFFF", fill: hdrFill, align: "center" } },
      ],
      [
        { text: "MS Learn 🥇",          options: { color: "1A2E30", fill: bodyFill } },
        { text: "0.933",                options: { color: "1A2E30", fill: bodyFill, align: "center" } },
        { text: "0.882",                options: { color: "1A2E30", fill: bodyFill, align: "center" } },
        { text: "0.906",                options: { color: "1A2E30", fill: bodyFill, align: "center" } },
        { text: "0.908",                options: { bold: true, color: "1A2E30", fill: bodyFill, align: "center" } },
      ],
      [
        { text: "Mintlify MCP 🥈",      options: { color: "1A2E30", fill: bodyFill } },
        { text: "0.949",                options: { color: "1A2E30", fill: bodyFill, align: "center" } },
        { text: "0.868",                options: { color: "1A2E30", fill: bodyFill, align: "center" } },
        { text: "0.905",                options: { color: "1A2E30", fill: bodyFill, align: "center" } },
        { text: "0.908",                options: { bold: true, color: "1A2E30", fill: bodyFill, align: "center" } },
      ],
      [
        { text: "docs-vnext/ 🥉",       options: { bold: true, color: C.accent, fill: vnextFill } },
        { text: "0.927",                options: { bold: true, color: C.accent, fill: vnextFill, align: "center" } },
        { text: "0.879",                options: { bold: true, color: C.accent, fill: vnextFill, align: "center" } },
        { text: "0.912",                options: { bold: true, color: C.accent, fill: vnextFill, align: "center" } },
        { text: "0.906",                options: { bold: true, color: C.accent, fill: vnextFill, align: "center" } },
      ],
      [
        { text: "docs/ (baseline)",     options: { color: "5A8087", fill: baseFill } },
        { text: "0.924",                options: { color: "5A8087", fill: baseFill, align: "center" } },
        { text: "0.860",                options: { color: "5A8087", fill: baseFill, align: "center" } },
        { text: "0.931",                options: { color: "5A8087", fill: baseFill, align: "center" } },
        { text: "0.904",                options: { color: "5A8087", fill: baseFill, align: "center" } },
      ],
    ];

    s.addTable(tableData, {
      x: 0.35, y: 1.3, w: 5.65, h: 1.9,
      fontSize: 11, fontFace: "Calibri",
      border: { type: "solid", pt: 0.5, color: "028090" },
      colW: [1.8, 0.97, 0.97, 0.97, 0.94],
    });

    // ── Hypothesis results ────────────────────────────────────────────────
    s.addText("Hypothesis Testing", {
      x: 0.35, y: 3.3, w: 5.65, h: 0.34,
      fontSize: 12.5, fontFace: "Trebuchet MS", bold: true,
      color: C.accent, margin: 0,
    });

    const hyps = [
      { id: "H1", badge: "⚠️ MARGINAL", detail: "docs-vnext (0.906) vs docs/ (0.904), δ=+0.002",  badgeColor: "C9A800" },
      { id: "H2", badge: "❌ REJECTED",  detail: "vs Mintlify MCP (0.908), δ=−0.002",              badgeColor: "C04040" },
      { id: "H3", badge: "❌ REJECTED",  detail: "vs MS Learn (0.908), δ=−0.002",                  badgeColor: "C04040" },
      { id: "H4", badge: "⚠️ MIXED",     detail: "Rankings vary: gpt-5.3 ranks docs-vnext 2nd",   badgeColor: "C9A800" },
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
        x: 0.9, y: hy + 0.05, w: 1.35, h: 0.25,
        fontSize: 10, fontFace: "Trebuchet MS", bold: true,
        color: h.badgeColor, margin: 0,
      });
      s.addText(h.detail, {
        x: 2.28, y: hy + 0.06, w: 3.6, h: 0.23,
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

    const cats = [
      { name: "agent-development",   vnext: 0.971, docs: 0.962, lead: true  },
      { name: "getting-started",     vnext: 0.887, docs: 0.867, lead: true  },
      { name: "infra-security",      vnext: 0.927, docs: 0.918, lead: true  },
      { name: "observability",       vnext: 0.802, docs: 0.829, lead: false },
      { name: "sdk-api",             vnext: 0.947, docs: 0.947, lead: false },
    ];

    const barMaxW = 3.1;
    const barScale = 0.75; // scale scores (0.75–1.0) visually
    for (let i = 0; i < cats.length; i++) {
      const c = cats[i];
      const cy = 1.72 + i * 0.72;
      const barW = barMaxW * ((c.vnext - 0.75) / 0.25);

      // Category label
      s.addText(c.name, {
        x: 6.22, y: cy, w: 3.4, h: 0.25,
        fontSize: 9.5, fontFace: "Consolas",
        color: C.lightTeal, margin: 0,
      });

      // Bar background
      s.addShape(pres.shapes.RECTANGLE, {
        x: 6.22, y: cy + 0.28, w: barMaxW, h: 0.28,
        fill: { color: "022C33" },
        line: { color: C.primary, width: 0 },
      });
      // docs-vnext bar
      s.addShape(pres.shapes.RECTANGLE, {
        x: 6.22, y: cy + 0.28, w: Math.max(0.1, barW), h: 0.28,
        fill: { color: c.lead ? C.secondary : "5A8087" },
        line: { color: c.lead ? C.secondary : "5A8087", width: 0 },
      });
      // Score label
      s.addText(`${c.vnext} ${c.lead ? "▲" : "—"}`, {
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
      "docs-vnext leads in agent-development (0.971) and getting-started (0.887) — areas benefiting most from Mintlify MDX enhancements",
      {
        x: 0.4, y: 5.24, w: 9.2, h: 0.35,
        fontSize: 10.5, fontFace: "Calibri", italic: true,
        color: C.lightTeal, align: "center", margin: 0,
      }
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // SLIDE 9 — Community Integration (Light)
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
  // SLIDE 10 — SDK Monitoring (Dark)
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
  // SLIDE 11 — Key Metrics (Light)
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
      { val: `${DATA.mdxDocs}`,          label: "MDX Pages",           sub: `${DATA.docSections} top-level sections`, icon: FaFileAlt },
      { val: `${DATA.agenticWorkflows}`, label: "Agentic Workflows",   sub: "post-consolidation definitions", icon: FaRobot },
      { val: `${DATA.slashCommands}`,    label: "Slash Commands",      sub: "on-demand agent entry points", icon: FaBolt },
      { val: `${DATA.vnextOnly}`,        label: "Filename Additions",  sub: "docs-vnext vs canonical docs/", icon: FaList },
      { val: `${GITHUB.agentic}`,        label: "Agentic PR Merges",   sub: `of ${GITHUB.merged} docs-vnext merges`, icon: FaCodeBranch },
      { val: "0.906",                    label: "Eval Average",        sub: "latest readable 4×3 snapshot", icon: FaChartBar },
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
  // SLIDE 12 — What's Next (Dark)
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
      { icon: MdOutlineMonitor, item: "Improve observability coverage — the latest readable evaluation remains weakest in this category" },
      { icon: FaCodeBranch, item: "Increase agentic PR merge rate while preserving reviewer and post-merge quality gates" },
      { icon: FaFlask, item: "Expand evaluation scenarios across new Foundry capabilities, SDK changes, and operational journeys" },
      { icon: FaChartBar, item: "Track category-level scores over time so content changes connect to measurable retrieval outcomes" },
      { icon: FaEye, item: "Add durable workflow-duration telemetry for end-to-end chain performance reporting" },
      { icon: FaUsers, item: "Close the loop from community signals to documented fixes and validated reader outcomes" },
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
