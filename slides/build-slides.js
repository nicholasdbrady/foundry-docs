"use strict";
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const path = require("path");
const fs = require("fs");

// --- Icons ---
const { FaRobot, FaSearch, FaCodeBranch, FaSyncAlt, FaShieldAlt, FaChartLine,
        FaBook, FaBell, FaTools, FaLayerGroup, FaCheckCircle, FaServer,
        FaEye, FaLightbulb, FaRocket, FaCogs, FaUsers, FaFlask } = require("react-icons/fa");
const { MdOutlineAutoAwesome } = require("react-icons/md");

// --- Palette: Teal Trust ---
const C = {
  teal:     "028090",
  seafoam:  "00A896",
  mint:     "02C39A",
  dark:     "01363D",
  darker:   "011F24",
  white:    "FFFFFF",
  offwhite: "F0FAFB",
  lightbg:  "E8F7F9",
  muted:    "5A8A90",
  accent:   "F4A261",
  accentlt: "FFF3E8",
  gray:     "64748B",
  lightgray:"E2E8F0",
  text:     "1E293B",
};

// --- Helpers ---
async function iconToBase64(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function makeShadow() {
  return { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.12 };
}

// ── Slide builders ─────────────────────────────────────────────────────────────

// 1. Title Slide (dark teal)
function addTitleSlide(pres, icons) {
  const s = pres.addSlide();
  s.background = { color: C.darker };

  // Left accent bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: 5.625, fill: { color: C.mint }, line: { color: C.mint } });

  // Top accent strip
  s.addShape(pres.shapes.RECTANGLE, { x: 0.18, y: 0, w: 9.82, h: 0.06, fill: { color: C.seafoam }, line: { color: C.seafoam } });

  // Robot icon
  s.addImage({ data: icons.robot, x: 0.45, y: 0.9, w: 0.9, h: 0.9 });

  // Title
  s.addText("Foundry-Docs", {
    x: 0.45, y: 1.9, w: 9.2, h: 0.9,
    fontSize: 44, bold: true, color: C.white, fontFace: "Calibri", margin: 0,
  });
  s.addText("Agentic Documentation for Microsoft Foundry", {
    x: 0.45, y: 2.75, w: 9.2, h: 0.55,
    fontSize: 20, color: C.mint, fontFace: "Calibri", italic: true, margin: 0,
  });

  // Subtitle line
  s.addShape(pres.shapes.RECTANGLE, { x: 0.45, y: 3.38, w: 3.5, h: 0.04, fill: { color: C.seafoam }, line: { color: C.seafoam } });

  // Tagline
  s.addText("280 docs  ·  33 agentic workflows  ·  46 merged PRs  ·  200 eval queries", {
    x: 0.45, y: 3.55, w: 9.2, h: 0.4,
    fontSize: 13, color: C.muted, fontFace: "Calibri", margin: 0,
  });

  // Date bottom-right
  s.addText("May 2026", {
    x: 7, y: 5.1, w: 2.7, h: 0.35,
    fontSize: 12, color: C.muted, align: "right", fontFace: "Calibri", margin: 0,
  });

  // Bottom bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });

  return s;
}

// 2. What is Foundry-Docs
function addWhatIsSlide(pres, icons) {
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  // Title bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("What is Foundry-Docs?", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Left column — description
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.9, w: 4.7, h: 3.9, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
  s.addImage({ data: icons.server, x: 0.55, y: 1.05, w: 0.5, h: 0.5 });
  s.addText("FastMCP Server", { x: 1.15, y: 1.05, w: 3.7, h: 0.5, fontSize: 16, bold: true, color: C.dark, fontFace: "Calibri", valign: "middle", margin: 0 });

  s.addText([
    { text: "A FastMCP server serving Microsoft Foundry documentation as searchable, agent-accessible MDX content.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Two content variants:", options: { bold: true, breakLine: true } },
    { text: "docs/  — canonical upstream mirror", options: { bullet: true, breakLine: true } },
    { text: "docs-vnext/  — agent-improved derivative", options: { bullet: true, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Search backends:", options: { bold: true, breakLine: true } },
    { text: "Local TF-IDF (always available)", options: { bullet: true, breakLine: true } },
    { text: "Azure AI Search — keyword + vector + semantic reranking", options: { bullet: true } },
  ], { x: 0.45, y: 1.65, w: 4.4, h: 3.0, fontSize: 13, color: C.text, fontFace: "Calibri", valign: "top" });

  // Right column — approach
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 0.9, w: 4.4, h: 3.9, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
  s.addImage({ data: icons.robot, x: 5.55, y: 1.05, w: 0.5, h: 0.5 });
  s.addText("Agentic Approach", { x: 6.15, y: 1.05, w: 3.4, h: 0.5, fontSize: 16, bold: true, color: C.dark, fontFace: "Calibri", valign: "middle", margin: 0 });

  s.addText([
    { text: "Documentation is maintained and improved by a fleet of 33 agentic GitHub Actions workflows.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Agents monitor, sync, audit, and improve docs autonomously — creating PRs, filing issues, and running evaluations with minimal human intervention.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "12 of 46 merged PRs were authored by agents.", options: { bold: true } },
  ], { x: 5.45, y: 1.65, w: 4.1, h: 3.0, fontSize: 13, color: C.text, fontFace: "Calibri", valign: "top" });

  // Bottom accent
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });
  return s;
}

// 3. Architecture
function addArchitectureSlide(pres, icons) {
  const s = pres.addSlide();
  s.background = { color: C.dark };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.darker }, line: { color: C.darker } });
  s.addText("Architecture", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.mint, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Pipeline steps
  const steps = [
    { icon: icons.sync, label: "Upstream\nMonitor", sub: "Detects commits in\nMicrosoftDocs/azure-ai-docs-pr" },
    { icon: icons.tools, label: "Sync &\nConvert", sub: "MS Learn markdown\n→ Mintlify MDX" },
    { icon: icons.layers, label: "Post-Sync\nUpdater", sub: "Analyzes changes,\ncreates docs-vnext PRs" },
    { icon: icons.search, label: "Index\nSync", sub: "Azure AI Search\nhybrid retrieval" },
    { icon: icons.check, label: "Eval\nHarness", sub: "4-server × model\nquality gate" },
  ];

  const bw = 1.5, bh = 2.6, startX = 0.3, y = 1.1;
  const gap = (10 - startX * 2 - bw * steps.length) / (steps.length - 1);

  steps.forEach((st, i) => {
    const x = startX + i * (bw + gap);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: bw, h: bh, fill: { color: "01434D" }, shadow: makeShadow(), line: { color: C.seafoam, width: 0.5 } });
    s.addImage({ data: st.icon, x: x + (bw - 0.45) / 2, y: y + 0.2, w: 0.45, h: 0.45 });
    s.addText(st.label, { x, y: y + 0.75, w: bw, h: 0.6, fontSize: 13, bold: true, color: C.mint, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(st.sub, { x, y: y + 1.4, w: bw, h: 0.9, fontSize: 10, color: "A0C4C8", align: "center", fontFace: "Calibri" });

    // Arrow between steps
    if (i < steps.length - 1) {
      const ax = x + bw + 0.06;
      s.addShape(pres.shapes.LINE, { x: ax, y: y + bh / 2, w: gap - 0.12, h: 0, line: { color: C.seafoam, width: 1.5 } });
    }
  });

  // Two-branch label
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 3.95, w: 4.2, h: 0.5, fill: { color: "01434D" }, line: { color: C.teal, width: 0.5 } });
  s.addText("docs/ — canonical upstream (280 MDX pages)", { x: 0.4, y: 3.98, w: 4.0, h: 0.44, fontSize: 12, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.5, y: 3.95, w: 4.2, h: 0.5, fill: { color: "01434D" }, line: { color: C.mint, width: 0.5 } });
  s.addText("docs-vnext/ — agent-improved (+14 unique pages)", { x: 5.6, y: 3.98, w: 4.0, h: 0.44, fontSize: 12, color: C.mint, fontFace: "Calibri", valign: "middle", margin: 0 });

  // MCP label
  s.addText("Both variants served via FastMCP  ·  TF-IDF local + Azure AI Search hybrid", {
    x: 0.4, y: 4.65, w: 9.2, h: 0.4, fontSize: 12, color: C.muted, align: "center", fontFace: "Calibri", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.mint }, line: { color: C.mint } });
  return s;
}

// 4. Documentation Coverage
function addCoverageSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("Documentation Coverage", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Stat callout
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.85, w: 2.8, h: 1.4, fill: { color: C.teal }, shadow: makeShadow(), line: { color: C.teal } });
  s.addText("280", { x: 0.3, y: 0.95, w: 2.8, h: 0.75, fontSize: 52, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
  s.addText("MDX pages in docs-vnext", { x: 0.3, y: 1.65, w: 2.8, h: 0.45, fontSize: 12, color: "CCF0F5", align: "center", fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.RECTANGLE, { x: 3.4, y: 0.85, w: 2.8, h: 1.4, fill: { color: C.seafoam }, shadow: makeShadow(), line: { color: C.seafoam } });
  s.addText("14", { x: 3.4, y: 0.95, w: 2.8, h: 0.75, fontSize: 52, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
  s.addText("agent-created unique pages", { x: 3.4, y: 1.65, w: 2.8, h: 0.45, fontSize: 12, color: "EEF9F9", align: "center", fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.RECTANGLE, { x: 6.5, y: 0.85, w: 3.2, h: 1.4, fill: { color: C.mint }, shadow: makeShadow(), line: { color: C.mint } });
  s.addText("266", { x: 6.5, y: 0.95, w: 3.2, h: 0.75, fontSize: 52, bold: true, color: C.dark, align: "center", fontFace: "Calibri", margin: 0 });
  s.addText("pages shared with docs/ baseline", { x: 6.5, y: 1.65, w: 3.2, h: 0.45, fontSize: 12, color: C.dark, align: "center", fontFace: "Calibri", margin: 0 });

  // Section bar chart data
  const sections = [
    { name: "models", count: 73, color: C.teal },
    { name: "agents", count: 60, color: C.seafoam },
    { name: "observability", count: 24, color: C.mint },
    { name: "security", count: 20, color: "047A86" },
    { name: "setup", count: 20, color: "056A74" },
    { name: "guardrails", count: 15, color: C.muted },
    { name: "api-sdk", count: 17, color: "035D68" },
    { name: "dev-exp", count: 11, color: "8BBFC4" },
  ];
  const maxCount = 73;
  const barAreaW = 9.0, barH = 0.26, startY = 2.55, barStartX = 1.55;
  const maxBarW = barAreaW - barStartX - 0.8;

  sections.forEach((sec, i) => {
    const y = startY + i * (barH + 0.08);
    const bw = (sec.count / maxCount) * maxBarW;
    s.addText(sec.name, { x: 0.3, y: y + 0.02, w: 1.2, h: barH, fontSize: 11, color: C.text, fontFace: "Calibri", align: "right", valign: "middle", margin: 0 });
    s.addShape(pres.shapes.RECTANGLE, { x: barStartX, y, w: bw, h: barH, fill: { color: sec.color }, line: { color: sec.color } });
    s.addText(`${sec.count}`, { x: barStartX + bw + 0.1, y: y + 0.02, w: 0.5, h: barH, fontSize: 11, color: C.gray, fontFace: "Calibri", valign: "middle", margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });
  return s;
}

// 5. Agentic Workflows
function addWorkflowsSlide(pres, icons) {
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("Agentic Workflows", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Big stat
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.85, w: 2.3, h: 1.5, fill: { color: C.dark }, shadow: makeShadow(), line: { color: C.dark } });
  s.addText("33", { x: 0.3, y: 0.9, w: 2.3, h: 0.9, fontSize: 62, bold: true, color: C.mint, align: "center", fontFace: "Calibri", margin: 0 });
  s.addText("agentic workflows", { x: 0.3, y: 1.75, w: 2.3, h: 0.45, fontSize: 12, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.RECTANGLE, { x: 2.9, y: 0.85, w: 2.1, h: 1.5, fill: { color: C.teal }, shadow: makeShadow(), line: { color: C.teal } });
  s.addText("9", { x: 2.9, y: 0.9, w: 2.1, h: 0.9, fontSize: 62, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
  s.addText("workflow chains", { x: 2.9, y: 1.75, w: 2.1, h: 0.45, fontSize: 12, color: "CCF0F5", align: "center", fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 0.85, w: 2.1, h: 1.5, fill: { color: C.seafoam }, shadow: makeShadow(), line: { color: C.seafoam } });
  s.addText("12", { x: 5.3, y: 0.9, w: 2.1, h: 0.9, fontSize: 62, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
  s.addText("bot-authored PRs", { x: 5.3, y: 1.75, w: 2.1, h: 0.45, fontSize: 12, color: "EEF9F9", align: "center", fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.RECTANGLE, { x: 7.7, y: 0.85, w: 2.0, h: 1.5, fill: { color: C.mint }, shadow: makeShadow(), line: { color: C.mint } });
  s.addText("5", { x: 7.7, y: 0.9, w: 2.0, h: 0.9, fontSize: 62, bold: true, color: C.dark, align: "center", fontFace: "Calibri", margin: 0 });
  s.addText("SDK detections", { x: 7.7, y: 1.75, w: 2.0, h: 0.45, fontSize: 12, color: C.dark, align: "center", fontFace: "Calibri", margin: 0 });

  // Category breakdown
  const cats = [
    { label: "Monitoring & Detection", items: "Upstream Docs Monitor · SDK Release Monitor · Community Discussions · Reddit Monitor", color: C.teal },
    { label: "Content Maintenance", items: "Daily Doc Updater · Glossary Maintainer · Docs Unbloat · Changelog Updater · Model Catalog Sync", color: C.seafoam },
    { label: "Quality & Testing", items: "Docs Auditor · Noob Tester · PR Reviewer · Post-Merge Verify · Search Testbench", color: C.mint },
    { label: "Automation & Ops", items: "Sync & Convert · Post-Sync Updater · Index Sync · Label Dispatch · Slide Deck Maintainer", color: "047A86" },
  ];

  cats.forEach((cat, i) => {
    const x = (i % 2) * 4.85 + 0.3;
    const y = 2.55 + Math.floor(i / 2) * 1.3;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 4.5, h: 1.15, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h: 1.15, fill: { color: cat.color }, line: { color: cat.color } });
    s.addText(cat.label, { x: x + 0.18, y: y + 0.05, w: 4.2, h: 0.35, fontSize: 13, bold: true, color: C.dark, fontFace: "Calibri", valign: "middle", margin: 0 });
    s.addText(cat.items, { x: x + 0.18, y: y + 0.42, w: 4.2, h: 0.65, fontSize: 11, color: C.gray, fontFace: "Calibri", valign: "top" });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });
  return s;
}

// 6. Trigger Coverage
function addTriggerSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.dark };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.darker }, line: { color: C.darker } });
  s.addText("Trigger Coverage — Event-Driven Design", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.mint, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  const triggers = [
    { event: "schedule", desc: "Cron-based polling — upstream docs, SDK releases, community signals", count: "8 workflows" },
    { event: "workflow_run", desc: "Chain reactions — post-sync, post-index, post-merge verification", count: "9 workflows" },
    { event: "issue_comment", desc: "Slash command dispatch — /audit, /noob-test, /unbloat, /update", count: "All 33" },
    { event: "push (main)", desc: "Automatic triggers — diff reports, index sync on docs changes", count: "4 workflows" },
    { event: "pull_request", desc: "PR review, docs noob test, documentation verification", count: "3 workflows" },
    { event: "workflow_dispatch", desc: "Manual or API trigger — sync-and-convert, eval harness, slides", count: "All 33" },
    { event: "repository_dispatch", desc: "Cross-repo events — community discussions, upstream changes", count: "3 workflows" },
    { event: "issues (opened)", desc: "Auto-triage — label detection, automated responses", count: "1 workflow" },
  ];

  triggers.forEach((t, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = col * 5.0 + 0.3;
    const y = 0.9 + row * 1.12;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 4.6, h: 0.95, fill: { color: "01434D" }, line: { color: C.seafoam, width: 0.5 } });
    s.addText(t.event, { x: x + 0.12, y: y + 0.05, w: 3.2, h: 0.35, fontSize: 13, bold: true, color: C.mint, fontFace: "Calibri", margin: 0 });
    s.addText(t.count, { x: x + 3.2, y: y + 0.05, w: 1.3, h: 0.35, fontSize: 11, color: C.accent, fontFace: "Calibri", align: "right", margin: 0 });
    s.addText(t.desc, { x: x + 0.12, y: y + 0.42, w: 4.3, h: 0.45, fontSize: 11, color: "A0C4C8", fontFace: "Calibri", margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.mint }, line: { color: C.mint } });
  return s;
}

// 7. Quality Pipeline
function addQualitySlide(pres, icons) {
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("Quality Pipeline", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  const agents = [
    {
      icon: icons.eye, title: "Docs Auditor",
      checks: ["Broken internal links", "Missing frontmatter (title/description)", "Invalid MDX syntax (bare HTML)", "Mintlify component violations", "Self-closing tag compliance (<br />)"],
      color: C.teal,
    },
    {
      icon: icons.users, title: "Noob Tester",
      checks: ["Simulates first-time developer", "Tests 3 viewport sizes (mobile / tablet / desktop)", "Validates prerequisite completeness", "Checks code example copy-paste viability", "Flags unexplained jargon"],
      color: C.seafoam,
    },
    {
      icon: icons.check, title: "PR Reviewer",
      checks: ["Diátaxis framework compliance", "Terminology enforcement (Foundry resource, not AI hub)", "Neutral tone — no we/our language", "ALL_CAPS placeholder conventions", "Cross-reference link accuracy"],
      color: C.mint,
    },
  ];

  agents.forEach((ag, i) => {
    const x = i * 3.2 + 0.3;
    const y = 0.85;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 3.0, h: 4.5, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
    // Color header
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 3.0, h: 0.7, fill: { color: ag.color }, line: { color: ag.color } });
    s.addImage({ data: ag.icon, x: x + 0.1, y: y + 0.1, w: 0.45, h: 0.45 });
    s.addText(ag.title, { x: x + 0.65, y: y + 0.1, w: 2.25, h: 0.5, fontSize: 14, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });
    // Checklist
    s.addText(
      ag.checks.map(c => ({ text: c, options: { bullet: true, breakLine: true } })).map((item, idx) => idx < ag.checks.length - 1 ? item : { ...item, options: { ...item.options, breakLine: false } }),
      { x: x + 0.15, y: y + 0.85, w: 2.7, h: 3.4, fontSize: 12, color: C.text, fontFace: "Calibri", valign: "top" }
    );
  });

  // Bottom note
  s.addText("All three agents run on every PR · Slash commands available for on-demand runs", {
    x: 0.4, y: 5.25, w: 9.2, h: 0.3, fontSize: 11, color: C.muted, align: "center", fontFace: "Calibri", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });
  return s;
}

// 8. docs-vnext History & Impact
function addHistorySlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("docs-vnext History & Impact", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // PR split chart
  s.addChart(pres.charts.PIE, [{
    name: "PR Authorship",
    labels: ["Human (34)", "Bot/Agent (12)"],
    values: [34, 12],
  }], {
    x: 0.3, y: 0.85, w: 3.5, h: 2.8,
    chartColors: [C.lightgray, C.teal],
    chartArea: { fill: { color: C.offwhite } },
    showPercent: true,
    showLegend: true,
    legendPos: "b",
    dataLabelColor: C.text,
    showTitle: true,
    title: "46 Merged PRs",
    titleFontSize: 13,
  });

  // Milestones timeline (right side)
  s.addText("Key Milestones", { x: 4.1, y: 0.88, w: 5.6, h: 0.4, fontSize: 15, bold: true, color: C.dark, fontFace: "Calibri", margin: 0 });

  const milestones = [
    { date: "Feb 2026", event: "First agentic PR merged — docs-vnext baseline created" },
    { date: "Mar 1", event: "Unbloat: cloud-evaluation.mdx − 29 lines, 10 bullets (PR #23)" },
    { date: "Mar 2", event: "Glossary created: 35 terms across 16 sections (PR #28)" },
    { date: "Mar 15", event: "Noob Tester fixes merged — 4 consecutive improvement PRs" },
    { date: "Apr 2026", event: "Eval harness launched: 4-server × model matrix, 200 queries" },
    { date: "May 2026", event: "5 SDK release detections · 5+ upstream sync issue cycles" },
  ];

  milestones.forEach((m, i) => {
    const y = 1.35 + i * 0.6;
    s.addShape(pres.shapes.OVAL, { x: 4.1, y: y + 0.08, w: 0.18, h: 0.18, fill: { color: C.teal }, line: { color: C.teal } });
    if (i < milestones.length - 1) {
      s.addShape(pres.shapes.LINE, { x: 4.185, y: y + 0.26, w: 0, h: 0.42, line: { color: C.seafoam, width: 1 } });
    }
    s.addText(m.date, { x: 4.4, y: y + 0.03, w: 1.1, h: 0.28, fontSize: 11, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });
    s.addText(m.event, { x: 5.55, y: y + 0.03, w: 4.1, h: 0.28, fontSize: 11, color: C.text, fontFace: "Calibri", margin: 0 });
  });

  // File delta stat
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 3.8, w: 3.5, h: 1.45, fill: { color: C.dark }, line: { color: C.dark } });
  s.addText([
    { text: "266", options: { fontSize: 30, bold: true, color: C.mint, breakLine: true } },
    { text: "pages shared with docs/ baseline", options: { fontSize: 11, color: "A0C4C8" } },
  ], { x: 0.35, y: 3.88, w: 3.4, h: 0.7, align: "center", fontFace: "Calibri" });
  s.addText([
    { text: "+14", options: { fontSize: 30, bold: true, color: C.accent, breakLine: true } },
    { text: "pages created exclusively by agents", options: { fontSize: 11, color: "A0C4C8" } },
  ], { x: 0.35, y: 4.58, w: 3.4, h: 0.55, align: "center", fontFace: "Calibri" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });
  return s;
}

// 9. Deep Dive: Agentic Chain in Action
function addChainSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.darker };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.dark }, line: { color: C.dark } });
  s.addText("Deep Dive: Agentic Chain in Action", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.mint, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Chain flow
  const chain = [
    { n: "1", label: "Upstream Monitor", detail: "Scheduled scan detects\n2+ commits in MicrosoftDocs\narrowhead upstream repo", color: C.teal },
    { n: "2", label: "Creates Issue", detail: "Files upstream-sync issue\n(e.g. #207, #193) with\ncommit details & file list", color: C.seafoam },
    { n: "3", label: "Dispatches Sync", detail: "sync-and-convert workflow\ndispatched automatically\ndocs + docs-vnext updated", color: C.mint },
    { n: "4", label: "Post-Sync Updater", detail: "Analyzes diff, assesses\nimpact, creates PR or\nnoop if no docs change", color: "047A86" },
    { n: "5", label: "Eval Gate", detail: "Post-index testbench\nruns regression — must\npass 90% threshold", color: "056A74" },
  ];

  const bw = 1.6, bh = 2.2, y = 0.9, startX = 0.3;
  const gap = (10 - startX * 2 - bw * chain.length) / (chain.length - 1);

  chain.forEach((c, i) => {
    const x = startX + i * (bw + gap);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: bw, h: bh, fill: { color: "01434D" }, line: { color: c.color, width: 1 } });
    s.addShape(pres.shapes.OVAL, { x: x + (bw - 0.4) / 2, y: y + 0.1, w: 0.4, h: 0.4, fill: { color: c.color }, line: { color: c.color } });
    s.addText(c.n, { x: x + (bw - 0.4) / 2, y: y + 0.1, w: 0.4, h: 0.4, fontSize: 15, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(c.label, { x, y: y + 0.62, w: bw, h: 0.45, fontSize: 12, bold: true, color: c.color, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(c.detail, { x, y: y + 1.15, w: bw, h: 0.9, fontSize: 10, color: "A0C4C8", align: "center", fontFace: "Calibri" });
    if (i < chain.length - 1) {
      const ax = x + bw + 0.06;
      s.addShape(pres.shapes.LINE, { x: ax, y: y + bh / 2, w: gap - 0.12, h: 0, line: { color: c.color, width: 1.5 } });
    }
  });

  // SDK chain box
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 3.3, w: 9.4, h: 1.8, fill: { color: "01434D" }, line: { color: C.accent, width: 0.8 } });
  s.addText("SDK Release Chain (parallel track):", { x: 0.5, y: 3.4, w: 3.5, h: 0.35, fontSize: 13, bold: true, color: C.accent, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "SDK Release Monitor", options: { bold: true, color: C.accent } },
    { text: " detects Azure AI Projects SDK across 4 languages (Python, JS/TS, .NET, Java) → creates ", options: { color: "A0C4C8" } },
    { text: "sdk-update", options: { bold: true, color: C.mint } },
    { text: " issue with breaking change analysis & docs impact assessment. Latest: Issue #270 — Python 2.1.0, JS/TS 2.1.0, .NET 2.0.1 & 2.1.0-beta.1 detected (Apr 2026). 5 total detections since launch.", options: { color: "A0C4C8" } },
  ], { x: 0.5, y: 3.82, w: 9.0, h: 1.0, fontSize: 12, fontFace: "Calibri" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.mint }, line: { color: C.mint } });
  return s;
}

// 10. Deep Dive: Content Improvements
function addContentSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("Deep Dive: Content Improvements", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Left: Glossary PR #28
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.85, w: 4.4, h: 4.4, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.85, w: 4.4, h: 0.55, fill: { color: C.seafoam }, line: { color: C.seafoam } });
  s.addText("PR #28 — Glossary Creation", { x: 0.45, y: 0.88, w: 4.1, h: 0.46, fontSize: 14, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  s.addText([
    { text: "Starting point: ", options: { bold: true } },
    { text: "zero — no glossary existed", options: {} },
    { text: "\n", options: { breakLine: true } },
    { text: "Outcome:", options: { bold: true, breakLine: true } },
    { text: "35 terms across 16 alphabetical sections", options: { bullet: true, breakLine: true } },
    { text: "Covers Foundry, MCP, Search, Agents, Eval, Dev Tools", options: { bullet: true, breakLine: true } },
    { text: "docs-vnext/docs.json updated with Reference nav group", options: { bullet: true, breakLine: true } },
    { text: "Created in a single automated run (glossary-maintainer)", options: { bullet: true, breakLine: true } },
    { text: "\n", options: { breakLine: true } },
    { text: "Sample terms:", options: { bold: true, breakLine: true } },
    { text: "MCP Gateway · FastMCP · Hybrid Search · Diátaxis · Hit@K · HNSW · Provisioned Throughput · Devvit", options: { italic: true } },
  ], { x: 0.45, y: 1.5, w: 4.1, h: 3.55, fontSize: 12, color: C.text, fontFace: "Calibri", valign: "top" });

  // Right: Unbloat PR #23
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 0.85, w: 4.4, h: 4.4, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 0.85, w: 4.4, h: 0.55, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("PR #23 — Unbloat cloud-evaluation.mdx", { x: 5.45, y: 0.88, w: 4.1, h: 0.46, fontSize: 14, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0 });

  s.addText([
    { text: "Bloat removed:", options: { bold: true, breakLine: true } },
    { text: "Duplicate paragraph (evaluator support info repeated)", options: { bullet: true, breakLine: true } },
    { text: "4 identical 'Before you begin' tip boxes removed", options: { bullet: true, breakLine: true } },
    { text: "Trivial tip, redundant sentence removed", options: { bullet: true, breakLine: true } },
    { text: "5-bullet list → concise reference table", options: { bullet: true, breakLine: true } },
    { text: "Rate limit bullets → prose sentences", options: { bullet: true, breakLine: true } },
  ], { x: 5.45, y: 1.5, w: 4.1, h: 1.9, fontSize: 12, color: C.text, fontFace: "Calibri", valign: "top" });

  // Metrics table
  const tableData = [
    [
      { text: "Metric", options: { bold: true, fill: { color: C.teal }, color: C.white } },
      { text: "Before", options: { bold: true, fill: { color: C.teal }, color: C.white } },
      { text: "After", options: { bold: true, fill: { color: C.teal }, color: C.white } },
      { text: "Δ", options: { bold: true, fill: { color: C.teal }, color: C.white } },
    ],
    ["Lines", "913", "884", "−29 (3%)"],
    ["Words", "3,412", "3,180", "−232 (7%)"],
    [{ text: "Bullets", options: { bold: true } }, { text: "29", options: { bold: true } }, { text: "19", options: { bold: true } }, { text: "−10 (35%) ✓", options: { bold: true, color: C.teal } }],
  ];

  s.addTable(tableData, {
    x: 5.3, y: 3.5, w: 4.4, h: 1.55,
    fontSize: 12, fontFace: "Calibri",
    border: { pt: 0.5, color: C.lightgray },
    colW: [1.3, 0.95, 0.95, 1.2],
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });
  return s;
}

// 11. Evaluation Harness
function addEvalSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("Evaluation Harness Results", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Score chart
  s.addChart(pres.charts.BAR, [{
    name: "Average Score",
    labels: ["docs/ (Control C)", "docs-vnext\n(Treatment)", "MS Learn\n(Control A)", "Mintlify MCP\n(Control B)"],
    values: [0.927, 0.921, 0.921, 0.921],
  }], {
    x: 0.3, y: 0.8, w: 5.3, h: 3.2,
    barDir: "col",
    chartColors: [C.teal, C.seafoam, C.muted, "AAAAAA"],
    chartArea: { fill: { color: C.white }, roundedCorners: true },
    catAxisLabelColor: C.gray,
    valAxisLabelColor: C.gray,
    valGridLine: { color: C.lightgray, size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelColor: C.text,
    showLegend: false,
    valAxisMinVal: 0.88,
    valAxisMaxVal: 0.95,
    showTitle: true,
    title: "200 Evaluations · claude-sonnet-4.6",
    titleFontSize: 12,
  });

  // Category breakdown table (right)
  s.addText("Category Breakdown", { x: 5.85, y: 0.85, w: 3.9, h: 0.35, fontSize: 14, bold: true, color: C.dark, fontFace: "Calibri", margin: 0 });

  const catData = [
    [
      { text: "Category", options: { bold: true, fill: { color: C.teal }, color: C.white, fontSize: 10 } },
      { text: "docs/", options: { bold: true, fill: { color: C.teal }, color: C.white, fontSize: 10 } },
      { text: "vnext", options: { bold: true, fill: { color: C.teal }, color: C.white, fontSize: 10 } },
    ],
    ["agent-development", "0.973", "0.973"],
    ["getting-started", "0.887", "0.887"],
    ["infrastructure-security", "0.973", "0.973"],
    ["observability-eval", { text: "0.853", options: { bold: true } }, { text: "0.853", options: { bold: true } }],
    ["sdk-api", { text: "0.947", options: { bold: true, color: C.teal } }, { text: "0.920", options: { bold: true, color: "CC3300" } }],
    [{ text: "OVERALL", options: { bold: true } }, { text: "0.927 🥇", options: { bold: true, color: C.teal } }, { text: "0.921", options: {} }],
  ];

  s.addTable(catData, {
    x: 5.85, y: 1.25, w: 3.9, h: 2.6,
    fontSize: 11, fontFace: "Calibri",
    border: { pt: 0.5, color: C.lightgray },
    colW: [2.1, 0.9, 0.9],
  });

  // Hypothesis results
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 4.1, w: 9.4, h: 1.15, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
  s.addText("Hypothesis Results (Issue #264 · 2026-05-03)", { x: 0.45, y: 4.15, w: 5, h: 0.35, fontSize: 13, bold: true, color: C.dark, fontFace: "Calibri", margin: 0 });

  const hyps = [
    { label: "H1: vnext > docs/", result: "❌ REJECTED (−0.006)", color: "CC3300" },
    { label: "H2: FastMCP > Mintlify", result: "➖ NO DIFFERENCE", color: C.gray },
    { label: "H3: FastMCP > MS Learn", result: "➖ NO DIFFERENCE", color: C.gray },
    { label: "H4: Consistent across models", result: "✅ SUPPORTED", color: C.teal },
  ];

  hyps.forEach((h, i) => {
    const x = (i % 2) * 4.8 + 0.45;
    const y = 4.55 + Math.floor(i / 2) * 0.38;
    s.addText(`${h.label}: `, { x, y, w: 2.2, h: 0.3, fontSize: 11, color: C.text, fontFace: "Calibri", margin: 0 });
    s.addText(h.result, { x: x + 2.2, y, w: 2.4, h: 0.3, fontSize: 11, bold: true, color: h.color, fontFace: "Calibri", margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });
  return s;
}

// 12. Community Integration
function addCommunitySlide(pres, icons) {
  const s = pres.addSlide();
  s.background = { color: C.dark };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.darker }, line: { color: C.darker } });
  s.addText("Community Integration", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.mint, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  const channels = [
    {
      icon: icons.users,
      title: "Microsoft Foundry Discussions",
      detail: "Monitors microsoft-foundry/discussions via repository_dispatch. Community questions trigger automated doc gap detection and cross-reference updates.",
      color: C.teal,
    },
    {
      icon: icons.search,
      title: "foundry-samples Repository",
      detail: "Watches the foundry-samples repo for new code examples. When new patterns emerge, docs-vnext gets corresponding how-to guides and code snippet updates.",
      color: C.seafoam,
    },
    {
      icon: icons.bell,
      title: "Reddit Community Monitor",
      detail: "Scheduled scan of r/AzureFoundry and related subs. Detects recurring confusion, missing docs, and frequently asked questions — feeds into daily doc updater.",
      color: C.mint,
    },
    {
      icon: icons.cogs,
      title: "Dependabot Docs Checker",
      detail: "When Dependabot raises a PR with dependency updates, this workflow checks if the dependency has docs implications and files update requests.",
      color: "047A86",
    },
  ];

  channels.forEach((ch, i) => {
    const x = (i % 2) * 4.85 + 0.3;
    const y = 0.9 + Math.floor(i / 2) * 2.1;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 4.5, h: 1.85, fill: { color: "01434D" }, line: { color: ch.color, width: 0.5 } });
    s.addImage({ data: ch.icon, x: x + 0.15, y: y + 0.15, w: 0.5, h: 0.5 });
    s.addText(ch.title, { x: x + 0.78, y: y + 0.15, w: 3.58, h: 0.5, fontSize: 13, bold: true, color: ch.color, fontFace: "Calibri", valign: "middle", margin: 0 });
    s.addText(ch.detail, { x: x + 0.15, y: y + 0.75, w: 4.2, h: 1.0, fontSize: 11.5, color: "A0C4C8", fontFace: "Calibri", valign: "top" });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.mint }, line: { color: C.mint } });
  return s;
}

// 13. SDK Monitoring
function addSDKSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.teal }, line: { color: C.teal } });
  s.addText("SDK Monitoring", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // 4 SDK cards
  const sdks = [
    { lang: "Python", latest: "2.1.0 Stable", date: "Apr 20, 2026", status: "🆕 New" },
    { lang: "JS/TS", latest: "2.1.0 Stable", date: "Apr 17, 2026", status: "🆕 New" },
    { lang: ".NET", latest: "2.1.0-beta.1", date: "Apr 21, 2026", status: "🔵 Beta" },
    { lang: "Java", latest: "2.0.0", date: "Tracked", status: "✅ Stable" },
  ];

  sdks.forEach((sdk, i) => {
    const x = i * 2.3 + 0.3;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.85, w: 2.1, h: 1.8, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 0.85, w: 2.1, h: 0.5, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText(sdk.lang, { x, y: 0.88, w: 2.1, h: 0.42, fontSize: 15, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(sdk.latest, { x, y: 1.45, w: 2.1, h: 0.4, fontSize: 13, bold: true, color: C.dark, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(sdk.date, { x, y: 1.88, w: 2.1, h: 0.3, fontSize: 10, color: C.gray, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(sdk.status, { x, y: 2.2, w: 2.1, h: 0.3, fontSize: 11, color: C.teal, align: "center", fontFace: "Calibri", margin: 0 });
  });

  // Detection count
  s.addShape(pres.shapes.RECTANGLE, { x: 9.5, y: 0.85, w: 0.2, h: 1.8, fill: { color: C.mint }, line: { color: C.mint } });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 2.85, w: 9.4, h: 0.5, fill: { color: C.lightbg }, line: { color: C.seafoam, width: 0.5 } });
  s.addText("5 detection events since launch  ·  Azure AI Projects SDK v2  ·  REST API v1 stable", {
    x: 0.5, y: 2.88, w: 9.0, h: 0.42, fontSize: 13, color: C.teal, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  // Latest detection detail box
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 3.5, w: 9.4, h: 1.8, fill: { color: C.white }, shadow: makeShadow(), line: { color: C.lightgray, width: 0.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 3.5, w: 0.08, h: 1.8, fill: { color: C.accent }, line: { color: C.accent } });
  s.addText("Latest: Issue #270 (May 2026)", { x: 0.5, y: 3.55, w: 5, h: 0.38, fontSize: 14, bold: true, color: C.dark, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "New releases detected across all four SDK languages. Docs impact assessed per-language:", options: { breakLine: true } },
    { text: "Python 2.1.0", options: { bold: true } },
    { text: " (stable) · ", options: {} },
    { text: "JS/TS 2.1.0", options: { bold: true } },
    { text: " (stable) · ", options: {} },
    { text: ".NET 2.0.1 & 2.1.0-beta.1", options: { bold: true } },
    { text: " · ", options: {} },
    { text: "Java 2.0.0", options: { bold: true } },
    { text: ". Agent files breaking changes analysis and creates targeted doc update tasks.", options: {} },
  ], { x: 0.5, y: 4.0, w: 9.0, h: 1.1, fontSize: 12, color: C.text, fontFace: "Calibri", valign: "top" });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.teal }, line: { color: C.teal } });
  return s;
}

// 14. Key Metrics
function addMetricsSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.darker };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.dark }, line: { color: C.dark } });
  s.addText("Key Metrics", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.mint, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  const metrics = [
    { value: "280", label: "MDX pages\n(docs-vnext)", color: C.mint },
    { value: "33", label: "Agentic\nworkflows", color: C.seafoam },
    { value: "9", label: "Workflow\nchains", color: C.teal },
    { value: "46", label: "Merged\nPRs", color: "047A86" },
    { value: "12", label: "Bot-authored\nPRs", color: C.accent },
    { value: "200", label: "Eval\nqueries", color: C.mint },
    { value: "0.927", label: "docs/ best\neval score", color: C.seafoam },
    { value: "5", label: "SDK release\ndetections", color: C.teal },
    { value: "14", label: "Agent-created\nunique pages", color: "047A86" },
  ];

  const cols = 3, cellW = 2.9, cellH = 1.5, startX = 0.55, startY = 0.85;
  const gapX = (10 - startX * 2 - cellW * cols) / (cols - 1);

  metrics.forEach((m, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = startX + col * (cellW + gapX);
    const y = startY + row * (cellH + 0.15);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: cellW, h: cellH, fill: { color: "01434D" }, line: { color: m.color, width: 0.5 } });
    s.addText(m.value, { x, y: y + 0.1, w: cellW, h: 0.85, fontSize: 40, bold: true, color: m.color, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(m.label, { x, y: y + 0.98, w: cellW, h: 0.45, fontSize: 11, color: "A0C4C8", align: "center", fontFace: "Calibri" });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.mint }, line: { color: C.mint } });
  return s;
}

// 15. What's Next
function addRoadmapSlide(pres, icons) {
  const s = pres.addSlide();
  s.background = { color: C.darker };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.7, fill: { color: C.dark }, line: { color: C.dark } });
  s.addText("What's Next", {
    x: 0.4, y: 0.08, w: 9.2, h: 0.54,
    fontSize: 26, bold: true, color: C.mint, fontFace: "Calibri", valign: "middle", margin: 0,
  });

  const items = [
    {
      icon: icons.chart,
      title: "Improve Observability Docs Coverage",
      detail: "Eval shows observability-evaluation is the weakest category (0.853 avg). Target: +0.05 via expanded cloud eval how-tos, tracing guides, and evaluator reference pages.",
      priority: "HIGH",
      color: C.accent,
    },
    {
      icon: icons.robot,
      title: "Increase Agentic PR Merge Rate",
      detail: "12/46 (26%) of merged PRs are agent-authored. Target: 40%+ via improved noob-tester accuracy, automated label-ops fixes, and PR reviewer pre-flight checks.",
      priority: "HIGH",
      color: C.teal,
    },
    {
      icon: icons.flask,
      title: "Expand Eval Scenarios",
      detail: "Current harness: 200 queries, 1 model, 4 servers. Roadmap: add gpt-5.4 model column, expand to 400+ scenarios, add multi-turn eval for agent documentation.",
      priority: "MED",
      color: C.seafoam,
    },
    {
      icon: icons.search,
      title: "getting-started Uplift",
      detail: "getting-started scores 0.887 (lowest after observability). Planned: quickstart rewrite, expanded prerequisite coverage, and step-by-step validation by noob-tester.",
      priority: "MED",
      color: C.mint,
    },
  ];

  items.forEach((item, i) => {
    const y = 0.9 + i * 1.1;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y, w: 9.4, h: 0.95, fill: { color: "01434D" }, line: { color: item.color, width: 0.5 } });
    s.addImage({ data: item.icon, x: 0.45, y: y + 0.23, w: 0.45, h: 0.45 });
    s.addText(item.title, { x: 1.05, y: y + 0.07, w: 6.5, h: 0.38, fontSize: 14, bold: true, color: item.color, fontFace: "Calibri", margin: 0 });
    s.addShape(pres.shapes.RECTANGLE, { x: 7.8, y: y + 0.1, w: 1.7, h: 0.3, fill: { color: item.priority === "HIGH" ? C.accent : C.teal }, line: { color: item.priority === "HIGH" ? C.accent : C.teal } });
    s.addText(item.priority, { x: 7.8, y: y + 0.1, w: 1.7, h: 0.3, fontSize: 11, bold: true, color: C.white, align: "center", fontFace: "Calibri", margin: 0 });
    s.addText(item.detail, { x: 1.05, y: y + 0.48, w: 8.1, h: 0.42, fontSize: 11, color: "A0C4C8", fontFace: "Calibri", margin: 0 });
  });

  // Closing tagline
  s.addText("foundry-docs · nicholasdbrady/foundry-docs · May 2026", {
    x: 0.4, y: 5.3, w: 9.2, h: 0.3, fontSize: 11, color: C.muted, align: "center", fontFace: "Calibri", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: C.mint }, line: { color: C.mint } });
  return s;
}

// ── Main ───────────────────────────────────────────────────────────────────────

async function main() {
  console.log("Building slide deck...");

  // Pre-render icons
  console.log("Rendering icons...");
  const icons = {
    robot:  await iconToBase64(FaRobot,      "#02C39A"),
    search: await iconToBase64(FaSearch,     "#02C39A"),
    sync:   await iconToBase64(FaSyncAlt,    "#02C39A"),
    tools:  await iconToBase64(FaTools,      "#02C39A"),
    layers: await iconToBase64(FaLayerGroup, "#02C39A"),
    check:  await iconToBase64(FaCheckCircle,"#02C39A"),
    server: await iconToBase64(FaServer,     "#028090"),
    eye:    await iconToBase64(FaEye,        "#FFFFFF"),
    users:  await iconToBase64(FaUsers,      "#02C39A"),
    bell:   await iconToBase64(FaBell,       "#02C39A"),
    cogs:   await iconToBase64(FaCogs,       "#02C39A"),
    chart:  await iconToBase64(FaChartLine,  "#02C39A"),
    flask:  await iconToBase64(FaFlask,      "#02C39A"),
    rocket: await iconToBase64(FaRocket,     "#02C39A"),
    book:   await iconToBase64(FaBook,       "#02C39A"),
  };

  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.title = "Foundry-Docs Stakeholder Overview";
  pres.author = "Slide Deck Maintainer (Agentic)";

  console.log("Building slides...");
  addTitleSlide(pres, icons);
  addWhatIsSlide(pres, icons);
  addArchitectureSlide(pres, icons);
  addCoverageSlide(pres);
  addWorkflowsSlide(pres, icons);
  addTriggerSlide(pres);
  addQualitySlide(pres, icons);
  addHistorySlide(pres);
  addChainSlide(pres);
  addContentSlide(pres);
  addEvalSlide(pres);
  addCommunitySlide(pres, icons);
  addSDKSlide(pres);
  addMetricsSlide(pres);
  addRoadmapSlide(pres, icons);

  const outPath = path.resolve(__dirname, "foundry-docs-overview.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log(`✅ Deck saved to: ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
