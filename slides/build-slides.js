const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// Icon imports
const { FaRobot, FaServer, FaFileAlt, FaNetworkWired, FaChartBar,
        FaGithub, FaCodeBranch, FaCog, FaBell, FaShieldAlt,
        FaSearch, FaUsers, FaCloud, FaBook, FaArrowRight,
        FaCheckCircle, FaSyncAlt, FaRocket, FaLayerGroup,
        FaExchangeAlt, FaEye, FaBug, FaComments, FaTools,
        FaClipboardList, FaMobileAlt } = require("react-icons/fa");
const { MdSpeed, MdAutorenew } = require("react-icons/md");

// === Color palette: Teal Trust + Dark Navy backgrounds ===
const C = {
  teal:    "028090",
  seafoam: "00A896",
  mint:    "02C39A",
  navy:    "0D1F2D",
  navyMid: "1A3449",
  slate:   "2E4A62",
  white:   "FFFFFF",
  offwhite:"F4F9FB",
  lightBg: "EEF6F8",
  muted:   "64748B",
  dark:    "1E2A35",
  accent:  "F0A500",   // warm amber accent for highlights
  accentLight: "FEF3C7",
};

// === Icon helper ===
async function iconPng(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// Add a small teal accent dot/circle with icon
async function addIconBadge(slide, IconComp, x, y, iconColor = "#FFFFFF", bgColor = C.teal, size = 0.45) {
  const ic = await iconPng(IconComp, iconColor, 256);
  slide.addShape("ellipse", {
    x, y, w: size, h: size,
    fill: { color: bgColor },
    line: { color: bgColor }
  });
  const pad = size * 0.2;
  slide.addImage({ data: ic, x: x + pad, y: y + pad, w: size - pad * 2, h: size - pad * 2 });
}

// Slide header bar (dark teal strip at top)
function addHeaderBar(slide, titleText, dark = false) {
  const bg = dark ? C.navyMid : C.teal;
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.72,
    fill: { color: bg },
    line: { color: bg }
  });
  slide.addText(titleText, {
    x: 0.35, y: 0, w: 9.3, h: 0.72,
    fontSize: 22, bold: true, color: C.white,
    fontFace: "Trebuchet MS", valign: "middle", margin: 0
  });
}

// Light content card
function addCard(slide, x, y, w, h, fillColor = C.white) {
  slide.addShape("rect", {
    x, y, w, h,
    fill: { color: fillColor },
    line: { color: "D4E8EE", width: 0.75 },
    shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.08 }
  });
}

// Stat callout card
function addStatCard(slide, x, y, w, h, number, label, color = C.teal) {
  addCard(slide, x, y, w, h);
  slide.addShape("rect", {
    x, y, w: 0.06, h,
    fill: { color: color },
    line: { color: color }
  });
  slide.addText(number, {
    x: x + 0.18, y: y + 0.08, w: w - 0.28, h: h * 0.55,
    fontSize: 40, bold: true, color: color,
    fontFace: "Trebuchet MS", valign: "bottom", margin: 0
  });
  slide.addText(label, {
    x: x + 0.18, y: y + h * 0.55, w: w - 0.28, h: h * 0.38,
    fontSize: 11, color: C.muted,
    fontFace: "Calibri", valign: "top", margin: 0
  });
}

async function buildDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Foundry-Docs Agent";
  pres.title = "Foundry-Docs: Agentic Documentation for Microsoft Foundry";

  // ─────────────────────────────────────────────
  // SLIDE 1: TITLE
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };

    // Decorative teal circle (large, top-right)
    s.addShape("ellipse", {
      x: 7.2, y: -1.8, w: 5.5, h: 5.5,
      fill: { color: C.teal, transparency: 80 },
      line: { color: C.teal, transparency: 80 }
    });
    // Smaller mint circle
    s.addShape("ellipse", {
      x: 8.5, y: 2.5, w: 2.8, h: 2.8,
      fill: { color: C.mint, transparency: 85 },
      line: { color: C.mint, transparency: 85 }
    });

    // Accent left bar
    s.addShape("rect", {
      x: 0, y: 0, w: 0.1, h: 5.625,
      fill: { color: C.teal },
      line: { color: C.teal }
    });

    // Tag line badge
    s.addShape("rect", {
      x: 0.5, y: 0.8, w: 2.8, h: 0.35,
      fill: { color: C.teal },
      line: { color: C.teal }
    });
    s.addText("STAKEHOLDER OVERVIEW  ·  2026", {
      x: 0.5, y: 0.8, w: 2.8, h: 0.35,
      fontSize: 9, bold: true, color: C.white,
      fontFace: "Calibri", align: "center", valign: "middle", margin: 0
    });

    s.addText("Foundry-Docs", {
      x: 0.5, y: 1.35, w: 8.5, h: 1.05,
      fontSize: 52, bold: true, color: C.white,
      fontFace: "Trebuchet MS", margin: 0
    });
    s.addText("Agentic Documentation for Microsoft Foundry", {
      x: 0.5, y: 2.45, w: 7.5, h: 0.65,
      fontSize: 22, color: C.mint,
      fontFace: "Trebuchet MS", margin: 0
    });
    s.addText("An intelligent MCP server + autonomous agent pipeline\nthat keeps Microsoft Foundry docs current, accurate, and discoverable.", {
      x: 0.5, y: 3.2, w: 7.2, h: 0.85,
      fontSize: 14, color: "A8C8D4",
      fontFace: "Calibri", margin: 0
    });

    // Robot icon
    const botIcon = await iconPng(FaRobot, "#02C39A", 512);
    s.addImage({ data: botIcon, x: 8.1, y: 3.0, w: 1.5, h: 1.5 });

    // Footer line
    s.addShape("rect", {
      x: 0, y: 5.25, w: 10, h: 0.375,
      fill: { color: C.navyMid },
      line: { color: C.navyMid }
    });
    s.addText("nicholasdbrady/foundry-docs  ·  github.com", {
      x: 0.5, y: 5.28, w: 9, h: 0.3,
      fontSize: 9, color: "6B8FA8",
      fontFace: "Calibri", margin: 0
    });
  }

  // ─────────────────────────────────────────────
  // SLIDE 2: WHAT IS FOUNDRY-DOCS
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };
    addHeaderBar(s, "What is Foundry-Docs?");

    // Left column — description
    addCard(s, 0.3, 0.88, 5.0, 4.42);
    s.addText("The Platform", {
      x: 0.55, y: 1.0, w: 4.5, h: 0.38,
      fontSize: 18, bold: true, color: C.dark,
      fontFace: "Trebuchet MS", margin: 0
    });
    s.addText([
      { text: "Foundry-Docs is a custom MCP (Model Context Protocol) documentation server for Microsoft Foundry — purpose-built for AI coding assistants.", options: { breakLine: true } },
      { text: "\n", options: { breakLine: true } },
      { text: "It continuously syncs from the upstream MicrosoftDocs/azure-ai-docs-pr source, converts raw content into clean Mintlify MDX, and exposes the result through a FastMCP server that any AI tool can query.", options: { breakLine: true } },
      { text: "\n", options: { breakLine: true } },
      { text: "The entire documentation pipeline is autonomous — a fleet of GitHub Actions agents monitors, improves, tests, and publishes documentation with no human intervention required." }
    ], {
      x: 0.55, y: 1.45, w: 4.55, h: 3.6,
      fontSize: 13, color: C.dark,
      fontFace: "Calibri", valign: "top", margin: 0
    });

    // Right column — 3 concept cards
    const concepts = [
      { icon: FaServer,    title: "MCP Server",       desc: "FastMCP endpoint serves 267 MDX docs to AI assistants (Copilot, Cursor, Claude)" },
      { icon: FaSyncAlt,   title: "Upstream Sync",    desc: "Monitors azure-ai-docs-pr, syncs 4× daily and converts to clean Mintlify MDX" },
      { icon: FaRobot,     title: "Agent Pipeline",   desc: "25+ agentic workflows: audit, heal, test, update, review — fully autonomous" },
    ];

    let cy = 0.88;
    for (const c of concepts) {
      addCard(s, 5.6, cy, 4.1, 1.35);
      const ic = await iconPng(c.icon, `#${C.teal}`, 256);
      s.addImage({ data: ic, x: 5.85, y: cy + 0.42, w: 0.52, h: 0.52 });
      s.addText(c.title, {
        x: 6.52, y: cy + 0.15, w: 2.98, h: 0.38,
        fontSize: 14, bold: true, color: C.dark,
        fontFace: "Trebuchet MS", margin: 0
      });
      s.addText(c.desc, {
        x: 6.52, y: cy + 0.52, w: 2.98, h: 0.72,
        fontSize: 11, color: C.muted,
        fontFace: "Calibri", margin: 0
      });
      cy += 1.5;
    }
  }

  // ─────────────────────────────────────────────
  // SLIDE 3: ARCHITECTURE
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };
    addHeaderBar(s, "Architecture", true);

    // Pipeline boxes
    const steps = [
      { icon: FaBook,       label: "Upstream Source",   sub: "azure-ai-docs-pr\n(MicrosoftDocs)", color: C.slate },
      { icon: FaSyncAlt,    label: "Sync & Convert",    sub: "docs-upstream-monitor\nsync-and-convert.yml", color: C.teal },
      { icon: FaLayerGroup, label: "docs-vnext",        sub: "267 MDX pages\nMintlify format", color: C.seafoam },
      { icon: FaRobot,      label: "Agent Pipeline",    sub: "Audit · Heal · Test\nReview · Update", color: C.mint },
      { icon: FaServer,     label: "MCP Server",        sub: "FastMCP endpoint\nfoundry_docs_mcp/", color: C.accent },
    ];

    const boxW = 1.7, boxH = 2.2, startX = 0.2, stepGap = 0.05;
    const totalW = steps.length * boxW + (steps.length - 1) * stepGap;
    const adjustedStart = (10 - totalW) / 2;

    for (let i = 0; i < steps.length; i++) {
      const st = steps[i];
      const bx = adjustedStart + i * (boxW + stepGap);
      const by = 1.4;

      // Box
      s.addShape("rect", {
        x: bx, y: by, w: boxW, h: boxH,
        fill: { color: C.navyMid },
        line: { color: st.color, width: 2 }
      });
      // Top color accent strip
      s.addShape("rect", {
        x: bx, y: by, w: boxW, h: 0.08,
        fill: { color: st.color },
        line: { color: st.color }
      });

      const ic = await iconPng(st.icon, `#${st.color}`, 256);
      s.addImage({ data: ic, x: bx + boxW / 2 - 0.28, y: by + 0.2, w: 0.56, h: 0.56 });

      s.addText(st.label, {
        x: bx + 0.08, y: by + 0.85, w: boxW - 0.16, h: 0.45,
        fontSize: 12, bold: true, color: C.white, align: "center",
        fontFace: "Trebuchet MS", margin: 0
      });
      s.addText(st.sub, {
        x: bx + 0.08, y: by + 1.3, w: boxW - 0.16, h: 0.8,
        fontSize: 10, color: "A8C8D4", align: "center",
        fontFace: "Calibri", margin: 0
      });

      // Arrow between boxes
      if (i < steps.length - 1) {
        const ax = bx + boxW;
        s.addShape("rect", {
          x: ax, y: by + boxH / 2 - 0.02, w: stepGap, h: 0.04,
          fill: { color: "4A7090" },
          line: { color: "4A7090" }
        });
      }
    }

    // Bottom note
    s.addText("MS Learn pulls from azure-ai-docs-pr 4× daily  ·  Agents improve docs continuously  ·  MCP server always reflects latest state", {
      x: 0.5, y: 4.0, w: 9, h: 0.4,
      fontSize: 11, color: "6B9AB8", align: "center",
      fontFace: "Calibri", italic: true, margin: 0
    });

    // Agent categories footer
    const cats = ["📋 Audit", "🔧 Heal", "🧪 Test", "🔄 Update", "👁 Review", "🔔 Monitor"];
    let fx = 0.5;
    for (const cat of cats) {
      s.addShape("rect", {
        x: fx, y: 4.55, w: 1.42, h: 0.72,
        fill: { color: C.slate },
        line: { color: C.teal, width: 1 }
      });
      s.addText(cat, {
        x: fx, y: 4.55, w: 1.42, h: 0.72,
        fontSize: 11, color: C.white, align: "center", valign: "middle",
        fontFace: "Calibri", margin: 0
      });
      fx += 1.52;
    }
  }

  // ─────────────────────────────────────────────
  // SLIDE 4: DOCUMENTATION COVERAGE
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };
    addHeaderBar(s, "Documentation Coverage  —  267 MDX Pages");

    // Bar chart data (sorted by page count)
    const sections = [
      { label: "Models",              count: 72 },
      { label: "Agents",              count: 57 },
      { label: "Observability",       count: 24 },
      { label: "Setup",               count: 20 },
      { label: "Security",            count: 20 },
      { label: "Guardrails",          count: 15 },
      { label: "API & SDK",           count: 14 },
      { label: "Developer Exp.",      count: 11 },
      { label: "Manage",              count:  9 },
      { label: "Responsible AI",      count:  8 },
      { label: "Operate",             count:  7 },
      { label: "Best Practices",      count:  5 },
      { label: "Get Started",         count:  4 },
      { label: "Overview",            count:  1 },
    ];

    const chartData = [{
      name: "Pages",
      labels: sections.map(s => s.label),
      values: sections.map(s => s.count)
    }];

    s.addChart(pres.charts.BAR, chartData, {
      x: 0.3, y: 0.85, w: 9.4, h: 4.55,
      barDir: "bar",  // horizontal
      chartColors: ["028090", "00A896", "02C39A", "028090", "00A896", "02C39A",
                    "028090", "00A896", "02C39A", "028090", "00A896", "02C39A",
                    "028090", "00A896"],
      chartArea: { fill: { color: C.offwhite }, roundedCorners: false },
      plotArea: { fill: { color: C.offwhite } },
      catAxisLabelColor: "1E2A35",
      catAxisLabelFontSize: 11,
      valAxisLabelColor: "64748B",
      valAxisLabelFontSize: 10,
      valGridLine: { color: "D4E8EE", size: 0.5 },
      catGridLine: { style: "none" },
      showValue: true,
      dataLabelColor: "1E293B",
      dataLabelFontSize: 10,
      showLegend: false,
      barGapWidthPct: 55,
    });
  }

  // ─────────────────────────────────────────────
  // SLIDE 5: AGENTIC WORKFLOWS
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };
    addHeaderBar(s, "Agentic Workflows  —  25 Autonomous Agents");

    // 6 category cards in a 3×2 grid
    const categories = [
      { icon: FaSearch,       title: "Monitoring",        count: "7 agents", desc: "SDK releases, upstream docs, community discussions, push checks", color: C.teal },
      { icon: FaTools,        title: "Healing & Updating", count: "5 agents", desc: "Daily doc healer, updater, unbloat, post-sync updater, glossary", color: C.seafoam },
      { icon: FaBug,          title: "Testing & QA",      count: "5 agents", desc: "Noob tester, multi-device tester, search testbench, regression gate", color: C.mint },
      { icon: FaEye,          title: "Review & Audit",    count: "4 agents", desc: "PR reviewer, docs auditor, file auditor, post-merge verify", color: C.accent },
      { icon: FaComments,     title: "Slash Commands",    count: "5 agents", desc: "/sdk-check, /check-discussions, /audit-file, /run-noob-test + more", color: C.navyMid },
      { icon: FaExchangeAlt,  title: "Sync & Convert",   count: "4 agents", desc: "docs-vnext sync, diff report, index sync, post-index testbench", color: C.slate },
    ];

    const cols = 3, rows = 2;
    const cardW = 2.95, cardH = 1.75;
    const gapX = 0.22, gapY = 0.22;
    const startX = 0.3, startY = 0.88;

    for (let i = 0; i < categories.length; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const cx = startX + col * (cardW + gapX);
      const cy = startY + row * (cardH + gapY);
      const cat = categories[i];

      addCard(s, cx, cy, cardW, cardH);
      // Left accent bar
      s.addShape("rect", {
        x: cx, y: cy, w: 0.06, h: cardH,
        fill: { color: cat.color },
        line: { color: cat.color }
      });

      const ic = await iconPng(cat.icon, `#${cat.color}`, 256);
      s.addImage({ data: ic, x: cx + 0.18, y: cy + 0.15, w: 0.42, h: 0.42 });

      s.addText(cat.title, {
        x: cx + 0.72, y: cy + 0.12, w: cardW - 0.82, h: 0.34,
        fontSize: 13, bold: true, color: C.dark,
        fontFace: "Trebuchet MS", margin: 0
      });
      s.addText(cat.count, {
        x: cx + 0.72, y: cy + 0.44, w: cardW - 0.82, h: 0.25,
        fontSize: 11, bold: true, color: cat.color,
        fontFace: "Calibri", margin: 0
      });
      s.addText(cat.desc, {
        x: cx + 0.18, y: cy + 0.75, w: cardW - 0.28, h: 0.9,
        fontSize: 10.5, color: C.muted,
        fontFace: "Calibri", margin: 0
      });
    }
  }

  // ─────────────────────────────────────────────
  // SLIDE 6: TRIGGER COVERAGE
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };
    addHeaderBar(s, "Trigger Coverage  —  Event-Driven Workflow Architecture", true);

    const triggers = [
      { icon: FaCog,          label: "schedule",            count: "15", desc: "Hourly to daily cron jobs\nfor continuous monitoring" },
      { icon: FaCodeBranch,   label: "push",                count: "3",  desc: "Validates docs on every\ncommit to main" },
      { icon: FaNetworkWired, label: "workflow_run",         count: "12", desc: "Chain reactions: sync →\ntest → verify" },
      { icon: FaTools,        label: "workflow_dispatch",    count: "25", desc: "Manual trigger on\nevery workflow" },
      { icon: FaComments,     label: "issue_comment",        count: "5",  desc: "Slash commands:\n/sdk-check, /audit-file…" },
      { icon: FaCloud,        label: "repository_dispatch",  count: "2",  desc: "Cross-repo events from\nmicrosoft-foundry/discussions" },
      { icon: FaExchangeAlt,  label: "pull_request",         count: "2",  desc: "PR docs review and\npost-merge validation" },
      { icon: FaRocket,       label: "release",              count: "1",  desc: "SDK new release\ndetection triggers" },
    ];

    const cols = 4, rows = 2;
    const cardW = 2.22, cardH = 1.95;
    const gapX = 0.13, gapY = 0.18;
    const startX = 0.2, startY = 0.88;

    for (let i = 0; i < triggers.length; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const cx = startX + col * (cardW + gapX);
      const cy = startY + row * (cardH + gapY);
      const t = triggers[i];

      s.addShape("rect", {
        x: cx, y: cy, w: cardW, h: cardH,
        fill: { color: C.navyMid },
        line: { color: C.teal, width: 1 }
      });

      const ic = await iconPng(t.icon, `#${C.mint}`, 256);
      s.addImage({ data: ic, x: cx + cardW / 2 - 0.26, y: cy + 0.18, w: 0.52, h: 0.52 });

      s.addText(t.count, {
        x: cx + 0.08, y: cy + 0.72, w: cardW - 0.16, h: 0.52,
        fontSize: 32, bold: true, color: C.mint, align: "center",
        fontFace: "Trebuchet MS", margin: 0
      });
      s.addText(t.label, {
        x: cx + 0.06, y: cy + 1.24, w: cardW - 0.12, h: 0.3,
        fontSize: 10, bold: true, color: C.white, align: "center",
        fontFace: "Calibri", margin: 0
      });
      s.addText(t.desc, {
        x: cx + 0.06, y: cy + 1.52, w: cardW - 0.12, h: 0.38,
        fontSize: 9, color: "7AAEC4", align: "center",
        fontFace: "Calibri", margin: 0
      });
    }
  }

  // ─────────────────────────────────────────────
  // SLIDE 7: QUALITY PIPELINE
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };
    addHeaderBar(s, "Quality Pipeline  —  Multi-Layer Documentation QA");

    // Left: pipeline flow diagram
    const stages = [
      { icon: FaFileAlt,    label: "Source Docs Arrive",         color: C.slate    },
      { icon: FaSearch,     label: "Auditor scans for issues",   color: C.teal     },
      { icon: FaTools,      label: "Daily Healer auto-fixes",    color: C.seafoam  },
      { icon: FaBug,        label: "Noob Tester validates UX",   color: C.mint     },
      { icon: FaMobileAlt,  label: "Multi-Device Test runs",     color: C.accent   },
      { icon: FaCheckCircle,label: "PR Reviewer approves",       color: C.seafoam  },
      { icon: FaRocket,     label: "Published & Live",           color: C.teal     },
    ];

    const colX = 0.3, colW = 3.8;
    const stH = 0.56, stGap = 0.06;
    const startY = 0.9;

    for (let i = 0; i < stages.length; i++) {
      const st = stages[i];
      const sy = startY + i * (stH + stGap);
      addCard(s, colX, sy, colW, stH, i % 2 === 0 ? C.white : C.lightBg);

      const ic = await iconPng(st.icon, `#${st.color}`, 256);
      s.addImage({ data: ic, x: colX + 0.12, y: sy + 0.07, w: 0.38, h: 0.38 });

      s.addText(`${i + 1}. ${st.label}`, {
        x: colX + 0.62, y: sy, w: colW - 0.72, h: stH,
        fontSize: 12, bold: i === 0 || i === stages.length - 1, color: C.dark,
        fontFace: "Calibri", valign: "middle", margin: 0
      });

      if (i < stages.length - 1) {
        s.addShape("rect", {
          x: colX + colW / 2 - 0.02, y: sy + stH, w: 0.04, h: stGap,
          fill: { color: C.teal },
          line: { color: C.teal }
        });
      }
    }

    // Right: details cards
    const details = [
      { title: "Documentation Auditor",     desc: "Deep structural scans across all 267 MDX pages — checks frontmatter, broken links, MDX syntax errors, missing descriptions" },
      { title: "Noob Tester",               desc: "Simulates a first-time developer asking beginner questions. Surfaces gaps in get-started coverage and confusing terminology" },
      { title: "Multi-Device Tester",       desc: "Validates rendering across mobile, tablet, desktop viewports. Catches layout issues before they reach production" },
      { title: "PR Documentation Reviewer", desc: "Reviews every docs PR for accuracy, completeness, and style. Leaves inline suggestions using GitHub review comments" },
    ];

    let dy = 0.9;
    for (const d of details) {
      addCard(s, 4.4, dy, 5.35, 1.1);
      s.addText(d.title, {
        x: 4.6, y: dy + 0.1, w: 5.0, h: 0.35,
        fontSize: 13, bold: true, color: C.teal,
        fontFace: "Trebuchet MS", margin: 0
      });
      s.addText(d.desc, {
        x: 4.6, y: dy + 0.42, w: 5.0, h: 0.62,
        fontSize: 11, color: C.dark,
        fontFace: "Calibri", margin: 0
      });
      dy += 1.18;
    }
  }

  // ─────────────────────────────────────────────
  // SLIDE 8: COMMUNITY INTEGRATION
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };
    addHeaderBar(s, "Community Integration  —  Connected to the Foundry Ecosystem", true);

    // Two main integration cards side by side
    const integrations = [
      {
        icon: FaComments,
        title: "microsoft-foundry/discussions",
        subtitle: "Cross-repo dispatch integration",
        points: [
          "Listens for new discussions via repository_dispatch events",
          "Responds automatically to questions about Foundry docs",
          "Routes complex queries to the right documentation section",
          "/check-discussions slash command for manual sweeps",
          "Discussion Feedback Responder handles in-thread replies",
        ],
        color: C.teal,
      },
      {
        icon: FaGithub,
        title: "foundry-samples monitoring",
        subtitle: "Code sample repo integration",
        points: [
          "Monitors azure-ai-samples for new Foundry code examples",
          "Detects when new samples lack corresponding documentation",
          "Auto-creates tracking issues for undocumented samples",
          "Links code examples to relevant MDX pages",
          "Ensures docs coverage stays aligned with code samples",
        ],
        color: C.seafoam,
      },
    ];

    for (let i = 0; i < integrations.length; i++) {
      const intg = integrations[i];
      const cx = 0.3 + i * 4.85;
      addCard(s, cx, 0.9, 4.6, 4.35, C.navyMid);

      const ic = await iconPng(intg.icon, `#${intg.color}`, 256);
      s.addImage({ data: ic, x: cx + 0.2, y: 1.05, w: 0.55, h: 0.55 });

      s.addText(intg.title, {
        x: cx + 0.88, y: 1.0, w: 3.55, h: 0.38,
        fontSize: 14, bold: true, color: C.white,
        fontFace: "Trebuchet MS", margin: 0
      });
      s.addText(intg.subtitle, {
        x: cx + 0.88, y: 1.36, w: 3.55, h: 0.28,
        fontSize: 10, color: intg.color,
        fontFace: "Calibri", italic: true, margin: 0
      });

      // Separator
      s.addShape("rect", {
        x: cx + 0.18, y: 1.72, w: 4.24, h: 0.03,
        fill: { color: C.slate },
        line: { color: C.slate }
      });

      let py = 1.85;
      for (const pt of intg.points) {
        s.addText("▸  " + pt, {
          x: cx + 0.22, y: py, w: 4.2, h: 0.48,
          fontSize: 11, color: "A8C8D4",
          fontFace: "Calibri", margin: 0
        });
        py += 0.5;
      }
    }
  }

  // ─────────────────────────────────────────────
  // SLIDE 9: SDK MONITORING
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };
    addHeaderBar(s, "SDK Release Monitoring  —  4 Repos Tracked Continuously");

    const sdks = [
      { lang: "Python",     repo: "azure-sdk-for-python",  pkg: "azure-ai-projects",       icon: FaFileAlt, color: C.teal    },
      { lang: "JavaScript", repo: "azure-sdk-for-js",      pkg: "@azure/ai-projects",       icon: FaCodeBranch,       color: C.seafoam },
      { lang: ".NET / C#",  repo: "azure-sdk-for-net",     pkg: "Azure.AI.Projects",        icon: FaLayerGroup,       color: C.mint    },
      { lang: "Java",       repo: "azure-sdk-for-java",    pkg: "azure-ai-projects",        icon: FaCog,              color: C.accent  },
    ];

    for (let i = 0; i < sdks.length; i++) {
      const sdk = sdks[i];
      const cx = 0.3 + (i % 2) * 4.85;
      const cy = 0.9 + Math.floor(i / 2) * 2.35;
      addCard(s, cx, cy, 4.6, 2.15);

      s.addShape("rect", {
        x: cx, y: cy, w: 0.06, h: 2.15,
        fill: { color: sdk.color },
        line: { color: sdk.color }
      });

      const ic = await iconPng(sdk.icon, `#${sdk.color}`, 256);
      s.addImage({ data: ic, x: cx + 0.2, y: cy + 0.2, w: 0.52, h: 0.52 });

      s.addText(sdk.lang, {
        x: cx + 0.86, y: cy + 0.18, w: 3.55, h: 0.38,
        fontSize: 16, bold: true, color: C.dark,
        fontFace: "Trebuchet MS", margin: 0
      });
      s.addText("Repo: " + sdk.repo, {
        x: cx + 0.18, y: cy + 0.78, w: 4.25, h: 0.3,
        fontSize: 11, color: C.muted,
        fontFace: "Calibri", margin: 0
      });
      s.addText("Package: " + sdk.pkg, {
        x: cx + 0.18, y: cy + 1.05, w: 4.25, h: 0.3,
        fontSize: 11, color: C.muted,
        fontFace: "Calibri", margin: 0
      });

      // Detection badges
      const badges = ["Changelog detection", "Docs impact assessment", "Auto-issue creation"];
      let bx = cx + 0.18;
      for (const b of badges) {
        s.addShape("rect", {
          x: bx, y: cy + 1.45, w: 1.32, h: 0.28,
          fill: { color: sdk.color },
          line: { color: sdk.color }
        });
        s.addText(b, {
          x: bx, y: cy + 1.45, w: 1.32, h: 0.28,
          fontSize: 8, color: C.white, align: "center", valign: "middle",
          fontFace: "Calibri", margin: 0
        });
        bx += 1.38;
      }
    }
  }

  // ─────────────────────────────────────────────
  // SLIDE 10: KEY METRICS
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };
    addHeaderBar(s, "Key Metrics  —  Live Numbers from the Repository", true);

    // 2×3 stat grid
    const stats = [
      { n: "267",  label: "MDX Documentation Pages",      icon: FaFileAlt,    color: C.teal    },
      { n: "25",   label: "Agentic GitHub Workflows",      icon: FaRobot,      color: C.seafoam },
      { n: "5",    label: "Slash Command Triggers",        icon: FaComments,   color: C.mint    },
      { n: "12",   label: "Chained workflow_run Events",   icon: FaNetworkWired, color: C.accent },
      { n: "15",   label: "Scheduled Cron Jobs",           icon: FaCog,        color: C.teal    },
      { n: "4",    label: "SDK Repos Monitored",           icon: FaSearch,     color: C.seafoam },
    ];

    const cols = 3, rows = 2;
    const cW = 2.88, cH = 1.88;
    const gX = 0.2, gY = 0.22;
    const sx0 = 0.3, sy0 = 0.88;

    for (let i = 0; i < stats.length; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const cx = sx0 + col * (cW + gX);
      const cy = sy0 + row * (cH + gY);
      const st = stats[i];

      s.addShape("rect", {
        x: cx, y: cy, w: cW, h: cH,
        fill: { color: C.navyMid },
        line: { color: st.color, width: 1.5 }
      });

      const ic = await iconPng(st.icon, `#${st.color}`, 256);
      s.addImage({ data: ic, x: cx + cW - 0.72, y: cy + 0.15, w: 0.52, h: 0.52 });

      s.addText(st.n, {
        x: cx + 0.18, y: cy + 0.18, w: cW - 0.38, h: 0.95,
        fontSize: 52, bold: true, color: st.color,
        fontFace: "Trebuchet MS", valign: "middle", margin: 0
      });
      s.addText(st.label, {
        x: cx + 0.18, y: cy + 1.15, w: cW - 0.28, h: 0.62,
        fontSize: 12, color: "A8C8D4",
        fontFace: "Calibri", valign: "top", margin: 0
      });
    }
  }

  // ─────────────────────────────────────────────
  // SLIDE 11: WHAT'S NEXT
  // ─────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.navy };

    // Dark decorative circles
    s.addShape("ellipse", {
      x: -1.5, y: 3.2, w: 5.5, h: 5.5,
      fill: { color: C.teal, transparency: 88 },
      line: { color: C.teal, transparency: 88 }
    });
    s.addShape("ellipse", {
      x: 7.5, y: -1.5, w: 4.5, h: 4.5,
      fill: { color: C.mint, transparency: 90 },
      line: { color: C.mint, transparency: 90 }
    });

    // Header
    s.addShape("rect", {
      x: 0, y: 0, w: 10, h: 0.72,
      fill: { color: C.teal },
      line: { color: C.teal }
    });
    s.addText("What's Next", {
      x: 0.35, y: 0, w: 9.3, h: 0.72,
      fontSize: 22, bold: true, color: C.white,
      fontFace: "Trebuchet MS", valign: "middle", margin: 0
    });

    const roadmap = [
      { icon: FaArrowRight, title: "Expanded Test Coverage",      desc: "Add semantic search quality tests, link-checker integration, and cross-browser rendering validation to the QA pipeline" },
      { icon: FaArrowRight, title: "Multi-Repo Source Tracking",  desc: "Extend upstream monitoring to track additional MicrosoftDocs repositories beyond azure-ai-docs-pr" },
      { icon: FaArrowRight, title: "Deeper SDK Integration",      desc: "Auto-generate API reference stubs from SDK changelogs and surface code diffs directly in documentation" },
      { icon: FaArrowRight, title: "Docs Health Dashboard",       desc: "Build a live metrics dashboard tracking coverage gaps, staleness scores, and test pass rates over time" },
      { icon: FaArrowRight, title: "Community Q&A Memory",        desc: "Persist resolved discussion answers as curated FAQ pages within the docs-vnext knowledge base" },
    ];

    let ry = 0.9;
    for (let i = 0; i < roadmap.length; i++) {
      const item = roadmap[i];
      s.addShape("rect", {
        x: 0.4, y: ry, w: 9.2, h: 0.8,
        fill: { color: C.navyMid },
        line: { color: i % 2 === 0 ? C.teal : C.seafoam, width: 1 }
      });
      s.addShape("rect", {
        x: 0.4, y: ry, w: 0.05, h: 0.8,
        fill: { color: i % 2 === 0 ? C.teal : C.seafoam },
        line: { color: i % 2 === 0 ? C.teal : C.seafoam }
      });

      const ic = await iconPng(item.icon, i % 2 === 0 ? `#${C.teal}` : `#${C.seafoam}`, 256);
      s.addImage({ data: ic, x: 0.62, y: ry + 0.2, w: 0.38, h: 0.38 });

      s.addText(item.title, {
        x: 1.15, y: ry + 0.08, w: 2.85, h: 0.35,
        fontSize: 13, bold: true, color: C.white,
        fontFace: "Trebuchet MS", margin: 0
      });
      s.addText(item.desc, {
        x: 4.05, y: ry + 0.1, w: 5.38, h: 0.62,
        fontSize: 11, color: "A8C8D4",
        fontFace: "Calibri", margin: 0
      });

      // Divider between title and desc
      s.addShape("rect", {
        x: 4.0, y: ry + 0.18, w: 0.03, h: 0.45,
        fill: { color: C.slate },
        line: { color: C.slate }
      });

      ry += 0.89;
    }
  }

  await pres.writeFile({ fileName: "slides/foundry-docs-overview.pptx" });
  console.log("✅ Deck written to slides/foundry-docs-overview.pptx");
}

buildDeck().catch(e => { console.error(e); process.exit(1); });
