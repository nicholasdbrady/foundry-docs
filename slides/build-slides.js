/**
 * Foundry-Docs Stakeholder Slide Deck
 * Built with PptxGenJS — Run #13
 * Palette: Teal Trust (028090 / 00A896 / 02C39A)
 */

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// ─── Icon helpers ────────────────────────────────────────────────────────────
const {
  FaRobot, FaBook, FaCodeBranch, FaSync, FaChartLine, FaShieldAlt,
  FaSearch, FaComments, FaPython, FaGithub, FaNetworkWired, FaDatabase,
  FaCheckCircle, FaExclamationTriangle, FaBolt, FaArrowRight,
  FaUsers, FaMicrophone, FaCode, FaFlask, FaLayerGroup, FaCogs,
  FaRocket, FaStar, FaTrophy, FaEye, FaTerminal, FaFileAlt,
  FaCloud, FaBoxOpen, FaLink, FaChevronRight,
} = require("react-icons/fa");
const { MdAutoAwesome, MdUpdate, MdBugReport, MdSpeed } = require("react-icons/md");

function svgIcon(IconComp, color = "#FFFFFF", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComp, { color, size: String(size) })
  );
}
async function icon64(IconComp, color = "#FFFFFF", size = 256) {
  const svg = svgIcon(IconComp, color, size);
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// ─── Palette ──────────────────────────────────────────────────────────────────
const C = {
  teal:       "028090",  // primary dark teal
  seafoam:    "00A896",  // secondary
  mint:       "02C39A",  // accent
  midnight:   "012F38",  // darkest bg
  slate:      "045D6E",  // mid dark
  ice:        "E0F4F7",  // light bg
  offwhite:   "F5FAFA",  // slide bg
  white:      "FFFFFF",
  textDark:   "0D2B33",
  textMid:    "1A5C6B",
  textLight:  "CCE8EE",
  muted:      "64748B",
  coral:      "F96167",  // warning/highlight
  gold:       "F4C430",  // star/badge
};

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.12 });

// ─── Main ─────────────────────────────────────────────────────────────────────
async function buildDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
  pres.author  = "Foundry-Docs Slide Agent";
  pres.title   = "Foundry-Docs: Agentic Documentation for Microsoft Foundry";
  pres.subject = "Stakeholder Overview — Run #13";

  // ── SLIDE 1: Title ──────────────────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.midnight };

    // Left accent bar
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: 7.5, fill: { color: C.mint }, line: { color: C.mint } });

    // Decorative top-right shape
    s.addShape(pres.shapes.RECTANGLE, { x: 9.5, y: 0, w: 3.8, h: 2.2, fill: { color: C.slate }, line: { color: C.slate } });
    s.addShape(pres.shapes.RECTANGLE, { x: 10.5, y: 0, w: 2.8, h: 1.4, fill: { color: C.teal }, line: { color: C.teal } });

    // Robot icon top right
    const botIcon = await icon64(FaRobot, "#" + C.mint, 300);
    s.addImage({ data: botIcon, x: 11.0, y: 0.35, w: 1.5, h: 1.5 });

    // Title
    s.addText("Foundry-Docs", {
      x: 0.5, y: 1.6, w: 9.5, h: 1.2,
      fontSize: 52, bold: true, color: C.white,
      fontFace: "Calibri", margin: 0,
    });
    // Subtitle
    s.addText("Agentic Documentation for Microsoft Foundry", {
      x: 0.5, y: 2.8, w: 10, h: 0.65,
      fontSize: 22, color: C.mint, fontFace: "Calibri", margin: 0,
    });

    // Divider
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.55, w: 7.5, h: 0.04, fill: { color: C.seafoam }, line: { color: C.seafoam } });

    // Stats row
    const stats = [
      { n: "274", label: "MDX Docs" },
      { n: "22",  label: "AI Workflows" },
      { n: "24",  label: "Merged PRs" },
      { n: "0.900", label: "Eval Score" },
    ];
    stats.forEach((st, i) => {
      const x = 0.5 + i * 3.1;
      s.addText(st.n, { x, y: 3.75, w: 2.8, h: 0.8, fontSize: 36, bold: true, color: C.mint, fontFace: "Calibri", margin: 0 });
      s.addText(st.label, { x, y: 4.5, w: 2.8, h: 0.35, fontSize: 13, color: C.textLight, fontFace: "Calibri", margin: 0 });
    });

    // Footer
    s.addText("Workflow Run #13  ·  March 2026  ·  nicholasdbrady/foundry-docs", {
      x: 0.5, y: 6.9, w: 12, h: 0.35,
      fontSize: 10, color: C.textLight, fontFace: "Calibri", margin: 0,
    });
  }

  // ── SLIDE 2: What is Foundry-Docs ──────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    // Header bar
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("What is Foundry-Docs?", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    // Left column: description
    s.addText([
      { text: "An agentic documentation system", options: { bold: true, color: C.teal, fontSize: 18, breakLine: true } },
      { text: " ", options: { fontSize: 8, breakLine: true } },
      { text: "foundry-docs is a GitHub repository that combines a FastMCP documentation server with a fleet of 22 AI-powered workflows to keep Microsoft Foundry's developer documentation continuously up-to-date, accurate, and high quality.", options: { fontSize: 14, color: C.textDark, breakLine: true } },
      { text: " ", options: { fontSize: 10, breakLine: true } },
      { text: "Docs are authored in Mintlify MDX format under ", options: { fontSize: 13, color: C.muted } },
      { text: "docs-vnext/", options: { fontSize: 13, color: C.teal, bold: true } },
      { text: " and served via a FastMCP server for AI model consumption.", options: { fontSize: 13, color: C.muted, breakLine: true } },
    ], { x: 0.4, y: 1.0, w: 5.8, h: 3.5, valign: "top", fontFace: "Calibri" });

    // Right column: 4 pillar cards
    const pillars = [
      { icon: FaBook,         title: "MCP Server",       desc: "FastMCP serves 274 MDX docs to AI models via the Model Context Protocol" },
      { icon: FaRobot,        title: "Agentic Workflows", desc: "22 gh-aw workflows monitor, audit, and improve docs automatically" },
      { icon: FaSync,         title: "Upstream Sync",    desc: "Continuous monitoring of MicrosoftDocs/azure-ai-docs-pr for changes" },
      { icon: FaChartLine,    title: "Eval Harness",     desc: "4-server × 3-model benchmarks track docs quality against competitors" },
    ];

    for (let i = 0; i < pillars.length; i++) {
      const row = Math.floor(i / 2);
      const col = i % 2;
      const x = 6.6 + col * 3.3;
      const y = 1.0 + row * 2.8;
      const p = pillars[i];

      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 3.1, h: 2.5, fill: { color: C.white }, line: { color: C.ice }, shadow: makeShadow() });
      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 3.1, h: 0.06, fill: { color: C.mint }, line: { color: C.mint } });

      const icn = await icon64(p.icon, "#" + C.teal, 200);
      s.addImage({ data: icn, x: x + 0.15, y: y + 0.2, w: 0.45, h: 0.45 });

      s.addText(p.title, { x: x + 0.7, y: y + 0.2, w: 2.3, h: 0.45, fontSize: 14, bold: true, color: C.textDark, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addText(p.desc, { x: x + 0.1, y: y + 0.75, w: 2.9, h: 1.65, fontSize: 11, color: C.muted, fontFace: "Calibri", margin: 0, valign: "top" });
    }

    // Footer
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 3: Architecture ───────────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Architecture: docs/ → docs-vnext Pipeline", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    // Pipeline boxes
    const boxes = [
      { x: 0.3,  label: "MicrosoftDocs\nazure-ai-docs-pr", sub: "Upstream source\n(MS Learn)" },
      { x: 3.2,  label: "docs/\n(canonical)", sub: "274 MDX files\nsync'd weekly" },
      { x: 6.1,  label: "docs-vnext/\n(agent-improved)", sub: "13 new files\n261 shared" },
      { x: 9.0,  label: "FastMCP\nServer", sub: "MCP protocol\nfor AI models" },
      { x: 11.7, label: "AI Models\n& Agents", sub: "Claude, GPT-5\nGemini" },
    ];

    const colors = [C.slate, C.teal, C.seafoam, C.mint, "028090"];
    boxes.forEach((b, i) => {
      const bx = b.x;
      const by = 1.3;
      const bw = 2.6;
      const bh = 1.8;
      s.addShape(pres.shapes.RECTANGLE, { x: bx, y: by, w: bw, h: bh, fill: { color: colors[i] }, line: { color: colors[i] }, shadow: makeShadow() });
      s.addText(b.label, { x: bx + 0.05, y: by + 0.2, w: bw - 0.1, h: 0.9, fontSize: 13, bold: true, color: C.white, fontFace: "Calibri", align: "center", margin: 0, valign: "middle" });
      s.addText(b.sub, { x: bx + 0.05, y: by + 1.1, w: bw - 0.1, h: 0.6, fontSize: 10, color: C.textLight, fontFace: "Calibri", align: "center", margin: 0, valign: "middle" });

      // Arrow between boxes
      if (i < boxes.length - 1) {
        const arrowX = bx + bw + 0.05;
        s.addShape(pres.shapes.RECTANGLE, { x: arrowX, y: by + 0.82, w: 0.22, h: 0.14, fill: { color: C.muted }, line: { color: C.muted } });
      }
    });

    // Workflow feedback arrows (below)
    s.addShape(pres.shapes.RECTANGLE, { x: 3.2, y: 3.4, w: 6.5, h: 0.04, fill: { color: C.coral }, line: { color: C.coral } });
    s.addText("⟵  AI Workflows continuously improve docs-vnext (audit, update, unbloat, glossary...)", {
      x: 3.2, y: 3.5, w: 9.5, h: 0.4, fontSize: 11, color: C.coral, fontFace: "Calibri", margin: 0, italic: true,
    });

    // Eval feedback
    s.addShape(pres.shapes.RECTANGLE, { x: 6.1, y: 4.15, w: 6.5, h: 0.04, fill: { color: C.gold }, line: { color: C.gold } });
    s.addText("⟵  Eval harness measures quality: docs-vnext 0.900 vs docs/ 0.894 (+0.006 delta)", {
      x: 6.1, y: 4.25, w: 7, h: 0.4, fontSize: 11, color: "8B6914", fontFace: "Calibri", margin: 0, italic: true,
    });

    // Community inputs box
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 4.8, w: 4.0, h: 2.3, fill: { color: C.ice }, line: { color: C.seafoam }, shadow: makeShadow() });
    s.addText("Community Signals", { x: 0.4, y: 4.85, w: 3.8, h: 0.35, fontSize: 12, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });
    s.addText([
      { text: "• Reddit monitoring (microsoft-foundry)", options: { bullet: false, breakLine: true } },
      { text: "• GitHub Discussions dispatch", options: { bullet: false, breakLine: true } },
      { text: "• foundry-samples repo watch", options: { bullet: false, breakLine: true } },
      { text: "• SDK release detection (4 repos)", options: { bullet: false } },
    ], { x: 0.4, y: 5.3, w: 3.7, h: 1.6, fontSize: 11, color: C.textDark, fontFace: "Calibri", margin: 0 });

    // Quality gates box
    s.addShape(pres.shapes.RECTANGLE, { x: 4.6, y: 4.8, w: 4.0, h: 2.3, fill: { color: C.ice }, line: { color: C.seafoam }, shadow: makeShadow() });
    s.addText("Quality Gates", { x: 4.7, y: 4.85, w: 3.8, h: 0.35, fontSize: 12, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });
    s.addText([
      { text: "• docs-auditor (accuracy + links)", options: { bullet: false, breakLine: true } },
      { text: "• docs-noob-tester (UX perspective)", options: { bullet: false, breakLine: true } },
      { text: "• pr-docs-reviewer (MDX quality)", options: { bullet: false, breakLine: true } },
      { text: "• post-merge-docs-verify", options: { bullet: false } },
    ], { x: 4.7, y: 5.3, w: 3.7, h: 1.6, fontSize: 11, color: C.textDark, fontFace: "Calibri", margin: 0 });

    // Output box
    s.addShape(pres.shapes.RECTANGLE, { x: 8.9, y: 4.8, w: 4.1, h: 2.3, fill: { color: C.ice }, line: { color: C.seafoam }, shadow: makeShadow() });
    s.addText("Outputs", { x: 9.0, y: 4.85, w: 3.9, h: 0.35, fontSize: 12, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });
    s.addText([
      { text: "• Stakeholder slide decks", options: { bullet: false, breakLine: true } },
      { text: "• Weekly diff reports", options: { bullet: false, breakLine: true } },
      { text: "• Eval scorecards", options: { bullet: false, breakLine: true } },
      { text: "• Auto-fixed PRs", options: { bullet: false } },
    ], { x: 9.0, y: 5.3, w: 3.8, h: 1.6, fontSize: 11, color: C.textDark, fontFace: "Calibri", margin: 0 });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 4: Documentation Coverage ─────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Documentation Coverage: 274 MDX Pages", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    // Section data (from live find)
    const sections = [
      { name: "models",                count: 72, pct: 72/274 },
      { name: "agents",                count: 57, pct: 57/274 },
      { name: "observability",         count: 24, pct: 24/274 },
      { name: "setup",                 count: 20, pct: 20/274 },
      { name: "security",              count: 20, pct: 20/274 },
      { name: "api-sdk",               count: 17, pct: 17/274 },
      { name: "guardrails",            count: 15, pct: 15/274 },
      { name: "developer-experience",  count: 11, pct: 11/274 },
      { name: "manage",                count:  9, pct:  9/274 },
      { name: "responsible-ai",        count:  8, pct:  8/274 },
      { name: "operate",               count:  7, pct:  7/274 },
      { name: "best-practices",        count:  5, pct:  5/274 },
      { name: "get-started",           count:  4, pct:  4/274 },
      { name: "overview + reference",  count:  5, pct:  5/274 },
    ];

    const barColors = [C.teal, C.seafoam, C.mint, C.slate, "028090", C.seafoam, C.teal, C.mint];

    sections.forEach((sec, i) => {
      const row = Math.floor(i / 2);
      const col = i % 2;
      const x = col === 0 ? 0.3 : 6.9;
      const y = 1.0 + row * 0.77;
      const maxW = 5.8;
      const barW = Math.max(0.1, sec.pct * maxW);
      const bCol = barColors[i % barColors.length];

      s.addText(sec.name, { x, y, w: 2.4, h: 0.45, fontSize: 11, bold: false, color: C.textDark, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addShape(pres.shapes.RECTANGLE, { x: x + 2.5, y: y + 0.1, w: maxW, h: 0.25, fill: { color: C.ice }, line: { color: C.ice } });
      s.addShape(pres.shapes.RECTANGLE, { x: x + 2.5, y: y + 0.1, w: barW, h: 0.25, fill: { color: bCol }, line: { color: bCol } });
      s.addText(String(sec.count), { x: x + 2.5 + maxW + 0.1, y, w: 0.5, h: 0.45, fontSize: 11, bold: true, color: C.teal, fontFace: "Calibri", margin: 0, valign: "middle" });
    });

    // Summary callout
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 7.0, w: 12.7, h: 0.0, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("274 total MDX pages  ·  13 new files created by agents (not in canonical docs/)  ·  261 files shared with docs/", {
      x: 0.3, y: 6.85, w: 12.7, h: 0.35, fontSize: 11, color: C.muted, fontFace: "Calibri", margin: 0, italic: true, align: "center",
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 5: Agentic Workflows ──────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("22 Agentic Workflows", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    const categories = [
      {
        icon: FaEye, title: "Monitoring & Detection", color: C.slate,
        items: ["docs-upstream-monitor", "sdk-release-monitor", "reddit-community-monitor", "community-discussions-monitor", "dependabot-docs-check"],
      },
      {
        icon: FaFlask, title: "Quality & Testing", color: C.teal,
        items: ["docs-auditor", "docs-noob-tester", "pr-docs-reviewer", "post-merge-docs-verify", "post-index-sync-testbench", "docs-vnext-diff-report"],
      },
      {
        icon: MdUpdate, title: "Content Updating", color: C.seafoam,
        items: ["post-sync-updater", "daily-doc-updater", "docs-vnext-sync", "unbloat-docs", "glossary-maintainer", "label-ops-docs-fix"],
      },
      {
        icon: FaBolt, title: "Slash Commands & Dispatch", color: C.mint,
        items: ["audit-file (/audit)", "search-test (/search-test)", "auto-triage-issues", "discussion-responder", "slide-deck-maintainer"],
      },
    ];

    for (let i = 0; i < categories.length; i++) {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = 0.3 + col * 6.5;
      const y = 0.95 + row * 3.05;
      const cat = categories[i];

      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 6.1, h: 2.8, fill: { color: C.white }, line: { color: C.ice }, shadow: makeShadow() });
      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 6.1, h: 0.5, fill: { color: cat.color }, line: { color: cat.color } });

      const icn = await icon64(cat.icon, "#" + C.white, 200);
      s.addImage({ data: icn, x: x + 0.1, y: y + 0.08, w: 0.35, h: 0.35 });
      s.addText(cat.title, { x: x + 0.55, y: y + 0.05, w: 5.4, h: 0.42, fontSize: 14, bold: true, color: C.white, fontFace: "Calibri", margin: 0, valign: "middle" });

      const textItems = cat.items.map((itm, idx) => ({
        text: itm,
        options: { bullet: true, fontSize: 11, color: C.textDark, breakLine: idx < cat.items.length - 1 },
      }));
      s.addText(textItems, { x: x + 0.15, y: y + 0.6, w: 5.8, h: 2.1, fontFace: "Calibri", margin: 0, valign: "top" });
    }

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 6: Trigger Coverage ───────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.midnight };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.slate }, line: { color: C.slate } });
    s.addText("Event-Driven Trigger Coverage", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    const triggers = [
      { icon: FaCogs,        name: "schedule",              desc: "Cron-based daily, weekly,\nevery 8h / 12h runs", count: "8 workflows" },
      { icon: FaBolt,        name: "slash_command",         desc: "/audit, /search-test,\n/check-discussions, /unbloat", count: "7 workflows" },
      { icon: FaCodeBranch,  name: "pull_request",          desc: "PR review, post-merge\nverification", count: "3 workflows" },
      { icon: FaNetworkWired,name: "workflow_run",          desc: "Chain triggers: sync →\nupdate → testbench", count: "3 workflows" },
      { icon: FaComments,    name: "issues / discussion",   desc: "Issue labeled, discussion\ncomment, community dispatch", count: "4 workflows" },
      { icon: FaEye,         name: "reaction",              desc: "\"eyes\" / \"rocket\" reactions\nto trigger on-demand audits", count: "2 workflows" },
      { icon: FaRobot,       name: "repository_dispatch",   desc: "Cross-repo triggers from\nDevvit app, foundry-samples", count: "2 workflows" },
      { icon: FaTerminal,    name: "workflow_dispatch",     desc: "Manual on-demand\nexecution for all workflows", count: "22 workflows" },
    ];

    for (let i = 0; i < triggers.length; i++) {
      const col = i % 4;
      const row = Math.floor(i / 4);
      const x = 0.3 + col * 3.2;
      const y = 1.05 + row * 2.85;
      const t = triggers[i];

      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 3.0, h: 2.6, fill: { color: C.slate }, line: { color: C.seafoam }, shadow: makeShadow() });

      const icn = await icon64(t.icon, "#" + C.mint, 200);
      s.addImage({ data: icn, x: x + 0.15, y: y + 0.2, w: 0.5, h: 0.5 });

      s.addText(t.name, { x: x + 0.75, y: y + 0.2, w: 2.1, h: 0.5, fontSize: 12, bold: true, color: C.mint, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addText(t.desc, { x: x + 0.1, y: y + 0.85, w: 2.8, h: 1.0, fontSize: 10, color: C.textLight, fontFace: "Calibri", margin: 0 });
      s.addText(t.count, { x: x + 0.1, y: y + 1.95, w: 2.8, h: 0.45, fontSize: 10, bold: true, color: C.seafoam, fontFace: "Calibri", margin: 0 });
    }

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.slate }, line: { color: C.slate } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.textLight, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 7: Quality Pipeline ────────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Quality Pipeline", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    const stages = [
      {
        num: "1",
        icon: FaSearch,
        title: "docs-auditor",
        subtitle: "Automated Accuracy Check",
        color: C.teal,
        points: [
          "Validates code examples against real SDK APIs",
          "Checks all external links (404 detection)",
          "Verifies MDX frontmatter and Mintlify syntax",
          "Creates labeled issues for every failure",
          "Triggered weekly + on every docs PR",
        ],
      },
      {
        num: "2",
        icon: FaUsers,
        title: "docs-noob-tester",
        subtitle: "New User Perspective Testing",
        color: C.seafoam,
        points: [
          "Simulates a first-time Foundry developer",
          "Follows getting-started flow end-to-end",
          "Tests across desktop, tablet, mobile viewports",
          "Scores confusing steps and missing prerequisites",
          "Posts report to GitHub Discussions for review",
        ],
      },
      {
        num: "3",
        icon: FaCodeBranch,
        title: "pr-docs-reviewer",
        subtitle: "Pull Request Quality Gate",
        color: C.mint,
        points: [
          "Reviews every docs-vnext PR automatically",
          "Checks MDX syntax, frontmatter, Mintlify compliance",
          "Flags style issues: GitHub alerts → Mintlify callouts",
          "Ensures Diátaxis framework alignment",
          "Posts inline review comments on the PR",
        ],
      },
    ];

    for (let i = 0; i < stages.length; i++) {
      const x = 0.3 + i * 4.3;
      const st = stages[i];

      // Main card
      s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 4.0, h: 5.9, fill: { color: C.white }, line: { color: C.ice }, shadow: makeShadow() });
      // Color header
      s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 4.0, h: 1.15, fill: { color: st.color }, line: { color: st.color } });

      // Number badge
      s.addShape(pres.shapes.OVAL, { x: x + 0.15, y: 1.05, w: 0.55, h: 0.55, fill: { color: C.midnight }, line: { color: C.midnight } });
      s.addText(st.num, { x: x + 0.15, y: 1.05, w: 0.55, h: 0.55, fontSize: 16, bold: true, color: C.white, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });

      const icn = await icon64(st.icon, "#" + C.white, 200);
      s.addImage({ data: icn, x: x + 3.35, y: 1.08, w: 0.45, h: 0.45 });

      s.addText(st.title, { x: x + 0.82, y: 1.03, w: 2.5, h: 0.5, fontSize: 15, bold: true, color: C.white, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addText(st.subtitle, { x: x + 0.1, y: 1.55, w: 3.8, h: 0.45, fontSize: 10, color: C.white, fontFace: "Calibri", margin: 0, align: "center", italic: true });

      const bullets = st.points.map((p, idx) => ({
        text: p,
        options: { bullet: true, fontSize: 11, color: C.textDark, breakLine: idx < st.points.length - 1 },
      }));
      s.addText(bullets, { x: x + 0.15, y: 2.2, w: 3.7, h: 4.4, fontFace: "Calibri", margin: 0, valign: "top" });

      // Arrow between stages
      if (i < stages.length - 1) {
        const arrowX = x + 4.1;
        s.addShape(pres.shapes.RECTANGLE, { x: arrowX, y: 3.3, w: 0.2, h: 0.12, fill: { color: C.seafoam }, line: { color: C.seafoam } });
        s.addText("→", { x: arrowX - 0.05, y: 3.15, w: 0.35, h: 0.4, fontSize: 18, color: C.seafoam, fontFace: "Calibri", margin: 0 });
      }
    }

    // post-merge note
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 7.0, w: 12.7, h: 0.0 });
    s.addText("+ post-merge-docs-verify runs after every PR merge  ·  post-index-sync-testbench validates search quality after index updates", {
      x: 0.3, y: 6.88, w: 12.7, h: 0.3, fontSize: 10, color: C.muted, fontFace: "Calibri", margin: 0, italic: true, align: "center",
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 8: docs-vnext History & Impact ────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("docs-vnext: History & Impact", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    // Left: timeline
    s.addText("Milestone Timeline", { x: 0.3, y: 0.95, w: 6.5, h: 0.4, fontSize: 14, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });

    const milestones = [
      { date: "Feb 2026", event: "PR #2: Agentic workflows + docs-vnext strategy launched" },
      { date: "Feb 24",   event: "PR #19: First AI-generated stakeholder slide deck created" },
      { date: "Mar 02",   event: "PR #28: Glossary created — 35 terms across 16 sections (agent-generated)" },
      { date: "Mar 02",   event: "PR #23: docs-vnext unbloat — cloud-evaluation.mdx cleaned of duplicate paragraphs" },
      { date: "Mar 04",   event: "PR #46: Navigation reflow to product-pillar structure" },
      { date: "Mar 05",   event: "Eval harness launched — 4-server × 3-model quality benchmarks" },
      { date: "Mar 07",   event: "PR #50: Full 5-language SDK samples + 267 API endpoint examples" },
      { date: "Mar 08",   event: "Eval Report #68: docs-vnext 0.900 vs docs/ 0.894 (+0.006)" },
    ];

    // Timeline line
    s.addShape(pres.shapes.RECTANGLE, { x: 1.0, y: 1.4, w: 0.04, h: 5.5, fill: { color: C.seafoam }, line: { color: C.seafoam } });

    milestones.forEach((m, i) => {
      const y = 1.42 + i * 0.68;
      // Dot
      s.addShape(pres.shapes.OVAL, { x: 0.82, y: y - 0.02, w: 0.38, h: 0.38, fill: { color: i === milestones.length - 1 ? C.mint : C.teal }, line: { color: C.white } });
      s.addText(m.date, { x: 1.55, y: y - 0.05, w: 1.5, h: 0.35, fontSize: 10, bold: true, color: C.teal, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addText(m.event, { x: 3.15, y: y - 0.05, w: 3.5, h: 0.45, fontSize: 10, color: C.textDark, fontFace: "Calibri", margin: 0, valign: "middle" });
    });

    // Right: metric cards
    const metrics = [
      { n: "24", label: "Merged PRs Total",       sub: "4 agentic · 20 human" },
      { n: "10+", label: "Upstream Detections",   sub: "azure-ai-docs-pr changes caught" },
      { n: "18+", label: "Automation Issues",     sub: "closed and resolved" },
      { n: "13",  label: "New Agent-Created Files", sub: "not in canonical docs/" },
    ];

    metrics.forEach((m, i) => {
      const row = Math.floor(i / 2);
      const col = i % 2;
      const x = 6.9 + col * 3.1;
      const y = 1.05 + row * 3.1;
      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.9, h: 2.8, fill: { color: C.white }, line: { color: C.ice }, shadow: makeShadow() });
      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.9, h: 0.06, fill: { color: C.mint }, line: { color: C.mint } });
      s.addText(m.n, { x, y: y + 0.35, w: 2.9, h: 1.1, fontSize: 52, bold: true, color: C.teal, fontFace: "Calibri", align: "center", margin: 0 });
      s.addText(m.label, { x: x + 0.1, y: y + 1.5, w: 2.7, h: 0.5, fontSize: 12, bold: true, color: C.textDark, fontFace: "Calibri", align: "center", margin: 0 });
      s.addText(m.sub, { x: x + 0.1, y: y + 2.05, w: 2.7, h: 0.55, fontSize: 10, color: C.muted, fontFace: "Calibri", align: "center", margin: 0 });
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 9: Deep Dive: Agentic Chain ───────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.midnight };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.slate }, line: { color: C.slate } });
    s.addText("Deep Dive: Agentic Chain in Action", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    // Chain A: Upstream Sync
    s.addText("Chain A — Upstream Docs Monitor → Sync → Update", {
      x: 0.3, y: 0.9, w: 12.7, h: 0.4, fontSize: 14, bold: true, color: C.mint, fontFace: "Calibri", margin: 0,
    });

    const chainA = [
      { step: "1", label: "docs-upstream-monitor", detail: "Detects commit in\nMicrosoftDocs/azure-ai-docs-pr", trigger: "schedule: every 8h" },
      { step: "2", label: "Creates Issue #54", detail: "\"Upstream Foundry Docs\nChanges Detected — 2026-03-05\"", trigger: "→ dispatch" },
      { step: "3", label: "docs-vnext-sync\n(Sync and Convert)", detail: "Syncs & converts\nraw docs to MDX", trigger: "workflow_run" },
      { step: "4", label: "post-sync-updater", detail: "Analyzes changes,\ncreates docs-vnext PR", trigger: "workflow_run" },
    ];

    chainA.forEach((step, i) => {
      const x = 0.3 + i * 3.2;
      s.addShape(pres.shapes.RECTANGLE, { x, y: 1.4, w: 2.9, h: 2.0, fill: { color: C.slate }, line: { color: C.seafoam }, shadow: makeShadow() });
      s.addShape(pres.shapes.OVAL, { x: x + 0.1, y: 1.5, w: 0.45, h: 0.45, fill: { color: C.mint }, line: { color: C.mint } });
      s.addText(step.step, { x: x + 0.1, y: 1.5, w: 0.45, h: 0.45, fontSize: 13, bold: true, color: C.midnight, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
      s.addText(step.label, { x: x + 0.1, y: 2.05, w: 2.7, h: 0.55, fontSize: 11, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });
      s.addText(step.detail, { x: x + 0.1, y: 2.65, w: 2.7, h: 0.6, fontSize: 10, color: C.textLight, fontFace: "Calibri", margin: 0 });
      s.addText(step.trigger, { x: x + 0.1, y: 3.25, w: 2.7, h: 0.3, fontSize: 9, color: C.seafoam, fontFace: "Calibri", margin: 0, italic: true });

      if (i < chainA.length - 1) {
        s.addText("→", { x: x + 2.95, y: 2.15, w: 0.3, h: 0.4, fontSize: 16, color: C.mint, fontFace: "Calibri", margin: 0 });
      }
    });

    // Chain B: SDK Release
    s.addText("Chain B — SDK Release Monitor", {
      x: 0.3, y: 3.85, w: 9, h: 0.35, fontSize: 14, bold: true, color: C.gold, fontFace: "Calibri", margin: 0,
    });

    const chainB = [
      { step: "1", label: "sdk-release-monitor", detail: "Monitors 4 SDK repos:\nPython, JS, .NET, Java", trigger: "schedule: every 12h" },
      { step: "2", label: "Issue #53 Created", detail: "Java 2.0.0-beta.2\nbreaking changes assessed", trigger: "→ github issue" },
      { step: "3", label: "label-ops-docs-fix", detail: "Applies sdk-update label,\ncreates fix PR automatically", trigger: "issues: [labeled]" },
    ];

    chainB.forEach((step, i) => {
      const x = 0.3 + i * 4.2;
      s.addShape(pres.shapes.RECTANGLE, { x, y: 4.3, w: 3.9, h: 2.0, fill: { color: C.slate }, line: { color: C.gold }, shadow: makeShadow() });
      s.addShape(pres.shapes.OVAL, { x: x + 0.1, y: 4.4, w: 0.45, h: 0.45, fill: { color: C.gold }, line: { color: C.gold } });
      s.addText(step.step, { x: x + 0.1, y: 4.4, w: 0.45, h: 0.45, fontSize: 13, bold: true, color: C.midnight, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
      s.addText(step.label, { x: x + 0.65, y: 4.4, w: 3.1, h: 0.55, fontSize: 11, bold: true, color: C.white, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addText(step.detail, { x: x + 0.1, y: 5.0, w: 3.7, h: 0.65, fontSize: 10, color: C.textLight, fontFace: "Calibri", margin: 0 });
      s.addText(step.trigger, { x: x + 0.1, y: 5.7, w: 3.7, h: 0.3, fontSize: 9, color: C.gold, fontFace: "Calibri", margin: 0, italic: true });

      if (i < chainB.length - 1) {
        s.addText("→", { x: x + 4.0, y: 5.1, w: 0.3, h: 0.4, fontSize: 16, color: C.gold, fontFace: "Calibri", margin: 0 });
      }
    });

    // Issue #53 callout box
    s.addShape(pres.shapes.RECTANGLE, { x: 9.1, y: 4.1, w: 4.0, h: 2.4, fill: { color: C.slate }, line: { color: C.gold }, shadow: makeShadow() });
    s.addText("Issue #53 — SDK Release Detected", { x: 9.2, y: 4.15, w: 3.8, h: 0.4, fontSize: 11, bold: true, color: C.gold, fontFace: "Calibri", margin: 0 });
    s.addText([
      { text: "📦 Azure AI Projects SDK v2", options: { bold: true, breakLine: true } },
      { text: "Java 2.0.0-beta.2\n", options: { breakLine: true } },
      { text: "Breaking changes detected:", options: { bold: true, breakLine: true } },
      { text: "• API surface changes in agents client\n• Docs impact: 3 pages need update\n• Auto-labeled: sdk-update", options: {} },
    ], { x: 9.2, y: 4.6, w: 3.7, h: 1.75, fontSize: 10, color: C.textLight, fontFace: "Calibri", margin: 0 });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.slate }, line: { color: C.slate } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.textLight, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 10: Deep Dive: Content Improvements ────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Deep Dive: Content Improvements", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    // ─ Example A: Glossary (PR #28)
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.95, w: 6.0, h: 5.9, fill: { color: C.white }, line: { color: C.ice }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.95, w: 6.0, h: 0.55, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("PR #28 — Glossary Creation", { x: 0.4, y: 0.98, w: 5.8, h: 0.48, fontSize: 14, bold: true, color: C.white, fontFace: "Calibri", margin: 0, valign: "middle" });

    s.addText("glossary-maintainer (Monday scan)", { x: 0.4, y: 1.6, w: 5.7, h: 0.3, fontSize: 11, color: C.muted, fontFace: "Calibri", margin: 0, italic: true });

    s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 2.0, w: 2.5, h: 0.32, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("BEFORE", { x: 0.4, y: 2.0, w: 2.5, h: 0.32, fontSize: 10, bold: true, color: C.muted, fontFace: "Calibri", align: "center", margin: 0, valign: "middle" });
    s.addShape(pres.shapes.RECTANGLE, { x: 3.1, y: 2.0, w: 2.5, h: 0.32, fill: { color: C.mint }, line: { color: C.mint } });
    s.addText("AFTER", { x: 3.1, y: 2.0, w: 2.5, h: 0.32, fontSize: 10, bold: true, color: C.midnight, fontFace: "Calibri", align: "center", margin: 0, valign: "middle" });

    s.addText("No glossary existed.\nTerms like MCP, FastMCP, RAG,\nHybrid Search, A2A, Hosted Agent\nwere undefined and inconsistent\nacross 274 doc pages.", {
      x: 0.4, y: 2.4, w: 2.5, h: 2.0, fontSize: 11, color: C.textDark, fontFace: "Calibri", margin: 0,
    });

    s.addText("docs-vnext/glossary.mdx created:\n✓ 35 terms defined\n✓ 16 alphabetical sections\n✓ Covers Core Foundry, MCP,\n  Search, Agent Tools\n✓ Added to navigation as\n  \"Reference\" section", {
      x: 3.1, y: 2.4, w: 2.5, h: 2.3, fontSize: 11, color: C.textDark, fontFace: "Calibri", margin: 0,
    });

    // Sample terms
    s.addText("Sample terms added:", { x: 0.4, y: 4.7, w: 5.6, h: 0.3, fontSize: 10, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });
    const terms = ["Agent · MCP Gateway (MCPG) · FastMCP · RAG · Hybrid Search", "Embeddings · HNSW · Semantic Reranking · Code Interpreter"];
    terms.forEach((t, i) => {
      s.addText(t, { x: 0.4, y: 5.05 + i * 0.35, w: 5.7, h: 0.3, fontSize: 10, color: C.muted, fontFace: "Calibri", margin: 0, italic: true });
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 6.55, w: 5.7, h: 0.22, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("Zero-to-done in one workflow run  ·  First-ever glossary for the project", {
      x: 0.4, y: 6.55, w: 5.7, h: 0.22, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0, align: "center", italic: true,
    });

    // ─ Example B: Unbloat (PR #23)
    s.addShape(pres.shapes.RECTANGLE, { x: 6.8, y: 0.95, w: 6.2, h: 5.9, fill: { color: C.white }, line: { color: C.ice }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: 6.8, y: 0.95, w: 6.2, h: 0.55, fill: { color: C.seafoam }, line: { color: C.seafoam } });
    s.addText("PR #23 — Unbloat: cloud-evaluation.mdx", { x: 6.9, y: 0.98, w: 6.0, h: 0.48, fontSize: 14, bold: true, color: C.white, fontFace: "Calibri", margin: 0, valign: "middle" });

    s.addText("unbloat-docs workflow", { x: 6.9, y: 1.6, w: 6.0, h: 0.3, fontSize: 11, color: C.muted, fontFace: "Calibri", margin: 0, italic: true });

    // Bloat types table
    const bloatRows = [
      ["Bloat Type", "Detail"],
      ["Duplicate paragraph", "Restated evaluator info already covered 2 paragraphs earlier"],
      ["Repetitive tip boxes", "4 identical \"Before you begin\" callouts removed (covered at top)"],
      ["Trivial tips", "\"To add another run, use the same method\" — obvious to developers"],
      ["Redundant prerequisites", "Re-listed SDK install in each section despite top-level install step"],
    ];
    const colW = [2.5, 3.4];
    bloatRows.forEach((row, ri) => {
      const y = 2.05 + ri * 0.62;
      const isHeader = ri === 0;
      row.forEach((cell, ci) => {
        const cx = 6.85 + (ci === 0 ? 0 : colW[0] + 0.1);
        s.addShape(pres.shapes.RECTANGLE, {
          x: cx, y, w: colW[ci], h: 0.55,
          fill: { color: isHeader ? C.seafoam : (ri % 2 === 0 ? C.ice : C.white) },
          line: { color: C.ice },
        });
        s.addText(cell, {
          x: cx + 0.05, y: y + 0.02, w: colW[ci] - 0.1, h: 0.51,
          fontSize: isHeader ? 10 : 9,
          bold: isHeader, color: isHeader ? C.white : C.textDark,
          fontFace: "Calibri", margin: 0, valign: "middle",
        });
      });
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 6.85, y: 6.5, w: 6.0, h: 0.25, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("Result: clearer doc, same technical content, reduced reading burden for developers", {
      x: 6.85, y: 6.5, w: 6.0, h: 0.25, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0, align: "center", italic: true,
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 11: Evaluation Harness Results ─────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Evaluation Harness — 2026-03-08  ·  300 Scenarios", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    // Scoreboard table
    s.addText("Server × Model Scoreboard", { x: 0.3, y: 0.9, w: 7, h: 0.35, fontSize: 13, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });

    const scoreHeaders = ["Server", "claude-opus-4.6", "gemini-3-pro", "gpt-5.3-codex", "Average"];
    const scoreData = [
      ["MS Learn (Control A) 🥇", "0.949", "0.877", "0.905", "0.911"],
      ["Mintlify MCP (Control B) 🥈", "0.937", "0.860", "0.911", "0.903"],
      ["FastMCP docs-vnext (Treatment) 🥉", "0.937", "0.861", "0.900", "0.900"],
      ["FastMCP docs/ (Control C)", "0.939", "0.844", "0.900", "0.894"],
    ];
    const colWs = [3.5, 1.6, 1.6, 1.6, 1.4];
    const tableX = 0.3;

    // Header row
    let cx = tableX;
    scoreHeaders.forEach((h, ci) => {
      s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 1.28, w: colWs[ci], h: 0.42, fill: { color: C.teal }, line: { color: C.white } });
      s.addText(h, { x: cx + 0.05, y: 1.28, w: colWs[ci] - 0.1, h: 0.42, fontSize: 9, bold: true, color: C.white, fontFace: "Calibri", margin: 0, valign: "middle", align: ci > 0 ? "center" : "left" });
      cx += colWs[ci];
    });

    // Data rows
    scoreData.forEach((row, ri) => {
      const y = 1.72 + ri * 0.5;
      const isTreatment = ri === 2;
      cx = tableX;
      row.forEach((cell, ci) => {
        const isAvg = ci === 4;
        const bgColor = isTreatment ? "E0F9F7" : (ri % 2 === 0 ? C.ice : C.white);
        s.addShape(pres.shapes.RECTANGLE, { x: cx, y, w: colWs[ci], h: 0.48, fill: { color: bgColor }, line: { color: C.ice } });
        s.addText(cell, {
          x: cx + 0.05, y, w: colWs[ci] - 0.1, h: 0.48,
          fontSize: ci === 0 ? 10 : 11,
          bold: isAvg || isTreatment,
          color: isAvg ? C.teal : C.textDark,
          fontFace: "Calibri", margin: 0, valign: "middle",
          align: ci > 0 ? "center" : "left",
        });
        cx += colWs[ci];
      });
    });

    // Hypothesis results
    s.addText("Hypothesis Testing Results", { x: 0.3, y: 3.8, w: 9.5, h: 0.35, fontSize: 13, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });

    const hyps = [
      { id: "H1", result: "⚠️ MARGINAL", color: C.gold, desc: "docs-vnext (0.900) vs docs/ (0.894) — delta +0.006. Treatment outperforms control." },
      { id: "H2", result: "❌ REJECTED", color: C.coral, desc: "FastMCP docs-vnext (0.900) vs Mintlify MCP (0.903) — delta -0.003. Mintlify MCP slightly ahead." },
      { id: "H3", result: "❌ REJECTED", color: C.coral, desc: "FastMCP docs-vnext (0.900) vs MS Learn (0.911) — delta -0.011. MS Learn leads on structured content." },
      { id: "H4", result: "⚠️ MIXED", color: C.gold, desc: "Rankings shift by model. Consistent leader: MS Learn. docs-vnext beats docs/ in 2/3 models." },
    ];

    hyps.forEach((h, i) => {
      const y = 4.2 + i * 0.6;
      s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y, w: 1.6, h: 0.48, fill: { color: h.color }, line: { color: h.color } });
      s.addText(`${h.id}: ${h.result}`, { x: 0.35, y, w: 1.5, h: 0.48, fontSize: 9, bold: true, color: C.midnight, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
      s.addText(h.desc, { x: 2.1, y: y + 0.04, w: 7.0, h: 0.4, fontSize: 10, color: C.textDark, fontFace: "Calibri", margin: 0, valign: "middle" });
    });

    // Category breakdown chart (right side)
    s.addText("Category Breakdown", { x: 9.3, y: 0.9, w: 3.7, h: 0.35, fontSize: 13, bold: true, color: C.teal, fontFace: "Calibri", margin: 0 });

    const categories = [
      { cat: "agent-development",    vnext: 0.964, docs: 0.973 },
      { cat: "sdk-api",              vnext: 0.947, docs: 0.929 },
      { cat: "observability-eval",   vnext: 0.844, docs: 0.811 },
      { cat: "getting-started",      vnext: 0.824, docs: 0.822 },
      { cat: "infra-security",       vnext: 0.918, docs: 0.936 },
    ];

    categories.forEach((cat, i) => {
      const y = 1.3 + i * 1.1;
      s.addText(cat.cat, { x: 9.3, y, w: 3.7, h: 0.28, fontSize: 9, bold: true, color: C.textDark, fontFace: "Calibri", margin: 0 });

      const maxW = 3.5;
      const vnextW = cat.vnext * maxW;
      const docsW = cat.docs * maxW;

      s.addShape(pres.shapes.RECTANGLE, { x: 9.3, y: y + 0.3, w: vnextW, h: 0.22, fill: { color: C.mint }, line: { color: C.mint } });
      s.addText(`vnext: ${cat.vnext}`, { x: 9.3 + vnextW + 0.05, y: y + 0.3, w: 1.2, h: 0.22, fontSize: 8, color: C.teal, fontFace: "Calibri", margin: 0, valign: "middle" });

      s.addShape(pres.shapes.RECTANGLE, { x: 9.3, y: y + 0.56, w: docsW, h: 0.22, fill: { color: C.muted }, line: { color: C.muted } });
      s.addText(`docs: ${cat.docs}`, { x: 9.3 + docsW + 0.05, y: y + 0.56, w: 1.2, h: 0.22, fontSize: 8, color: C.muted, fontFace: "Calibri", margin: 0, valign: "middle" });
    });

    // Legend
    s.addShape(pres.shapes.RECTANGLE, { x: 9.3, y: 6.85, w: 0.25, h: 0.15, fill: { color: C.mint }, line: { color: C.mint } });
    s.addText("docs-vnext", { x: 9.6, y: 6.83, w: 1.2, h: 0.2, fontSize: 9, color: C.teal, fontFace: "Calibri", margin: 0 });
    s.addShape(pres.shapes.RECTANGLE, { x: 10.9, y: 6.85, w: 0.25, h: 0.15, fill: { color: C.muted }, line: { color: C.muted } });
    s.addText("docs/", { x: 11.2, y: 6.83, w: 0.9, h: 0.2, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  300 eval scenarios  ·  4 servers  ·  3 models  ·  Issue #68", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 12: Community Integration ─────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Community Integration", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    const sources = [
      {
        icon: FaComments, color: C.teal,
        title: "Microsoft Foundry Discussions",
        trigger: "repository_dispatch → community-discussions-monitor",
        detail: [
          "Devvit app dispatches community discussion events",
          "discussion-responder workflow analyzes new comments",
          "Creates actionable GitHub issues for documentation gaps",
          "Responds to Noob Test report threads with fix PRs",
          "/check-discussions slash command for manual checks",
        ],
      },
      {
        icon: FaGithub, color: C.seafoam,
        title: "foundry-samples Monitoring",
        trigger: "repository_dispatch / dependabot-docs-check",
        detail: [
          "Monitors foundry-samples repo for new examples",
          "Detects when example code diverges from docs",
          "dependabot-docs-check catches SDK version updates",
          "Triggered when Dependabot PRs update azure-ai-projects",
          "Creates issues linking affected documentation pages",
        ],
      },
      {
        icon: FaMicrophone, color: C.mint,
        title: "Reddit Community Signals",
        trigger: "repository_dispatch (reddit-foundry-mention)",
        detail: [
          "Devvit app monitors r/AZURE and r/microsoftfabric",
          "Detects posts mentioning Microsoft Foundry / Azure AI",
          "reddit-community-monitor workflow analyzes sentiment",
          "Identifies documentation gaps from user pain points",
          "/check-reddit slash command for manual analysis",
        ],
      },
    ];

    for (let i = 0; i < sources.length; i++) {
      const x = 0.3 + i * 4.3;
      const src = sources[i];

      s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 4.1, h: 5.9, fill: { color: C.white }, line: { color: C.ice }, shadow: makeShadow() });
      s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 4.1, h: 1.15, fill: { color: src.color }, line: { color: src.color } });

      const icn = await icon64(src.icon, "#" + C.white, 200);
      s.addImage({ data: icn, x: x + 0.15, y: 1.05, w: 0.55, h: 0.55 });

      s.addText(src.title, { x: x + 0.82, y: 1.02, w: 3.1, h: 0.65, fontSize: 13, bold: true, color: C.white, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addText(src.trigger, { x: x + 0.1, y: 2.15, w: 3.9, h: 0.4, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0, italic: true });

      const bullets = src.detail.map((d, idx) => ({
        text: d,
        options: { bullet: true, fontSize: 11, color: C.textDark, breakLine: idx < src.detail.length - 1 },
      }));
      s.addText(bullets, { x: x + 0.15, y: 2.6, w: 3.8, h: 3.9, fontFace: "Calibri", margin: 0, valign: "top" });
    }

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 13: SDK Monitoring ─────────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.midnight };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.slate }, line: { color: C.slate } });
    s.addText("SDK Release Monitoring — 4 Repos Tracked", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    const sdks = [
      { lang: "Python",     pkg: "azure-ai-projects", color: C.teal,    latest: "v2.x" },
      { lang: "JavaScript", pkg: "azure-ai-projects", color: C.seafoam, latest: "v2.x" },
      { lang: ".NET / C#",  pkg: "azure-ai-projects", color: C.mint,    latest: "v2.x" },
      { lang: "Java",       pkg: "azure-ai-projects", color: C.gold,    latest: "v2.0.0-beta.2" },
    ];

    sdks.forEach((sdk, i) => {
      const x = 0.3 + i * 3.2;
      s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 3.0, h: 2.5, fill: { color: C.slate }, line: { color: sdk.color }, shadow: makeShadow() });
      s.addShape(pres.shapes.RECTANGLE, { x, y: 0.95, w: 3.0, h: 0.06, fill: { color: sdk.color }, line: { color: sdk.color } });
      s.addText(sdk.lang, { x: x + 0.1, y: 1.1, w: 2.8, h: 0.45, fontSize: 16, bold: true, color: sdk.color, fontFace: "Calibri", margin: 0 });
      s.addText(sdk.pkg, { x: x + 0.1, y: 1.6, w: 2.8, h: 0.3, fontSize: 9, color: C.textLight, fontFace: "Calibri", margin: 0, italic: true });
      s.addText(sdk.latest, { x: x + 0.1, y: 2.0, w: 2.8, h: 0.35, fontSize: 12, bold: false, color: C.white, fontFace: "Calibri", margin: 0 });
      if (sdk.lang === "Java") {
        s.addShape(pres.shapes.RECTANGLE, { x: x + 0.1, y: 2.45, w: 2.0, h: 0.28, fill: { color: C.gold }, line: { color: C.gold } });
        s.addText("🔔 Breaking Changes", { x: x + 0.12, y: 2.45, w: 2.0, h: 0.28, fontSize: 9, bold: true, color: C.midnight, fontFace: "Calibri", margin: 0, valign: "middle" });
      }
    });

    // Detection workflow
    s.addText("Detection & Response Pipeline", { x: 0.3, y: 3.65, w: 12, h: 0.38, fontSize: 14, bold: true, color: C.mint, fontFace: "Calibri", margin: 0 });

    const steps = [
      { n: "1", t: "Monitor Repos", d: "sdk-release-monitor checks\nGitHub releases every 12h" },
      { n: "2", t: "Detect Release", d: "Compares against last known\nversion stored in cache" },
      { n: "3", t: "Analyze Impact", d: "AI assesses breaking changes,\nbeta vs stable, docs affected" },
      { n: "4", t: "Create Issue", d: "Labels: sdk-update, sdk-release\nIncludes changelog summary" },
      { n: "5", t: "Auto-Fix PR", d: "label-ops-docs-fix triggers\nwhen sdk-update applied" },
    ];

    steps.forEach((st, i) => {
      const x = 0.3 + i * 2.52;
      s.addShape(pres.shapes.RECTANGLE, { x, y: 4.1, w: 2.35, h: 2.8, fill: { color: C.slate }, line: { color: C.seafoam }, shadow: makeShadow() });
      s.addShape(pres.shapes.OVAL, { x: x + 0.85, y: 4.18, w: 0.55, h: 0.55, fill: { color: C.mint }, line: { color: C.mint } });
      s.addText(st.n, { x: x + 0.85, y: 4.18, w: 0.55, h: 0.55, fontSize: 14, bold: true, color: C.midnight, fontFace: "Calibri", align: "center", valign: "middle", margin: 0 });
      s.addText(st.t, { x: x + 0.1, y: 4.82, w: 2.15, h: 0.5, fontSize: 11, bold: true, color: C.white, fontFace: "Calibri", margin: 0, align: "center" });
      s.addText(st.d, { x: x + 0.1, y: 5.38, w: 2.15, h: 1.3, fontSize: 9, color: C.textLight, fontFace: "Calibri", margin: 0, align: "center" });

      if (i < steps.length - 1) {
        s.addText("→", { x: x + 2.38, y: 5.25, w: 0.25, h: 0.4, fontSize: 14, color: C.mint, fontFace: "Calibri", margin: 0 });
      }
    });

    // Example issue
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 7.0, w: 12.7, h: 0.0 });
    s.addText("Example: Issue #53 — \"📦 Azure AI Projects SDK v2 Release Detected — Java 2.0.0-beta.2\" with breaking changes + docs impact assessment", {
      x: 0.3, y: 6.88, w: 12.7, h: 0.28, fontSize: 9, color: C.seafoam, fontFace: "Calibri", margin: 0, italic: true, align: "center",
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.slate }, line: { color: C.slate } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.textLight, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 14: Key Metrics ────────────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.offwhite };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Key Metrics — Workflow Run #13", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    const metrics = [
      { n: "274",   label: "MDX Documentation Pages",   sub: "across 14 content sections",          icon: FaFileAlt,   color: C.teal },
      { n: "22",    label: "Agentic Workflows",          sub: "monitoring, quality, updating, slash", icon: FaRobot,     color: C.seafoam },
      { n: "7",     label: "Slash Commands",             sub: "/audit /search-test /unbloat +more",  icon: FaTerminal,  color: C.mint },
      { n: "3",     label: "Workflow Chains",            sub: "trigger-to-result automated pipelines", icon: FaLink,     color: C.slate },
      { n: "0.900", label: "Eval Score (docs-vnext)",   sub: "+0.006 vs docs/ · 300 scenarios",     icon: FaChartLine, color: C.teal },
      { n: "24",    label: "Merged Pull Requests",       sub: "4 agentic-generated · 20 human",      icon: FaCodeBranch,color: C.seafoam },
      { n: "10+",   label: "Upstream Detections",       sub: "azure-ai-docs-pr changes caught",     icon: FaEye,       color: C.mint },
      { n: "35",    label: "Glossary Terms",             sub: "created from zero in one run",         icon: FaBook,      color: C.slate },
      { n: "4",     label: "SDK Repos Tracked",          sub: "Python · JS · .NET · Java",           icon: FaBoxOpen,   color: C.teal },
    ];

    for (let i = 0; i < metrics.length; i++) {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const x = 0.3 + col * 4.3;
      const y = 0.95 + row * 2.05;
      const m = metrics[i];

      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 4.0, h: 1.85, fill: { color: C.white }, line: { color: C.ice }, shadow: makeShadow() });
      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h: 1.85, fill: { color: m.color }, line: { color: m.color } });

      const icn = await icon64(m.icon, "#" + m.color, 200);
      s.addImage({ data: icn, x: x + 0.2, y: y + 0.18, w: 0.5, h: 0.5 });

      s.addText(m.n, { x: x + 0.85, y: y + 0.12, w: 3.0, h: 0.75, fontSize: 38, bold: true, color: m.color, fontFace: "Calibri", margin: 0 });
      s.addText(m.label, { x: x + 0.85, y: y + 0.9, w: 3.0, h: 0.38, fontSize: 11, bold: true, color: C.textDark, fontFace: "Calibri", margin: 0 });
      s.addText(m.sub, { x: x + 0.85, y: y + 1.3, w: 3.0, h: 0.38, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
    }

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.ice }, line: { color: C.ice } });
    s.addText("Data gathered live from repo  ·  March 2026  ·  Run #13", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.muted, fontFace: "Calibri", margin: 0 });
  }

  // ── SLIDE 15: What's Next ────────────────────────────────────────────────────
  {
    const s = pres.addSlide();
    s.background = { color: C.midnight };

    // Header
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 13.3, h: 0.8, fill: { color: C.slate }, line: { color: C.slate } });
    s.addText("What's Next", { x: 0.4, y: 0.1, w: 12, h: 0.6, fontSize: 26, bold: true, color: C.white, fontFace: "Calibri", margin: 0 });

    // Left accent
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.8, w: 0.15, h: 6.35, fill: { color: C.mint }, line: { color: C.mint } });

    const roadmap = [
      {
        n: "01", icon: FaChartLine, color: C.mint,
        title: "Improve Observability Docs Coverage",
        body: "The eval harness identified observability-evaluation as a weak category (0.844 docs-vnext, vs 0.853 MS Learn). Priority: expand tracing, evaluation SDK, and monitoring docs. Add code examples for cloud vs local evaluation scenarios and remote eval job submission.",
        tag: "Eval weak spot",
      },
      {
        n: "02", icon: FaRocket, color: C.seafoam,
        title: "Increase Agentic PR Merge Rate",
        body: "Currently 4 of 24 merged PRs (17%) are agentic. Goal: improve PR quality so more agent-generated PRs pass review without manual edits. Add PR self-review loop: agent generates PR, auditor validates, submits only if passing. Target: 40% agentic by Q2.",
        tag: "Efficiency",
      },
      {
        n: "03", icon: FaFlask, color: C.gold,
        title: "Expand Eval Scenarios",
        body: "Current eval: 300 scenarios across 5 categories. Gaps: guardrails, security, fine-tuning, responsible-ai not yet tested. Add 150 new scenarios for uncovered sections. Validate that agent-created content (glossary, SDK samples) boosts targeted category scores.",
        tag: "Quality",
      },
    ];

    for (let i = 0; i < roadmap.length; i++) {
      const x = 0.4 + i * 4.2;
      const r = roadmap[i];

      s.addShape(pres.shapes.RECTANGLE, { x, y: 1.0, w: 4.0, h: 5.7, fill: { color: C.slate }, line: { color: r.color }, shadow: makeShadow() });

      // Number
      s.addShape(pres.shapes.RECTANGLE, { x, y: 1.0, w: 4.0, h: 0.06, fill: { color: r.color }, line: { color: r.color } });
      s.addText(r.n, { x: x + 0.12, y: 1.15, w: 0.6, h: 0.6, fontSize: 22, bold: true, color: r.color, fontFace: "Calibri", margin: 0 });

      // Tag
      s.addShape(pres.shapes.RECTANGLE, { x: x + 2.7, y: 1.18, w: 1.15, h: 0.3, fill: { color: r.color }, line: { color: r.color } });
      s.addText(r.tag, { x: x + 2.7, y: 1.18, w: 1.15, h: 0.3, fontSize: 9, bold: true, color: C.midnight, fontFace: "Calibri", align: "center", margin: 0, valign: "middle" });

      const icn = await icon64(r.icon, "#" + r.color, 200);
      s.addImage({ data: icn, x: x + 0.15, y: 1.85, w: 0.55, h: 0.55 });

      s.addText(r.title, { x: x + 0.85, y: 1.82, w: 3.0, h: 0.65, fontSize: 13, bold: true, color: C.white, fontFace: "Calibri", margin: 0, valign: "middle" });
      s.addText(r.body, { x: x + 0.1, y: 2.55, w: 3.8, h: 3.9, fontSize: 11, color: C.textLight, fontFace: "Calibri", margin: 0, valign: "top" });
    }

    // Bottom tagline
    s.addText("Agentic documentation: continuously learning, continuously improving.", {
      x: 0.4, y: 6.9, w: 12.5, h: 0.4, fontSize: 14, bold: true, color: C.mint, fontFace: "Calibri", align: "center", margin: 0,
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 7.15, w: 13.3, h: 0.35, fill: { color: C.slate }, line: { color: C.slate } });
    s.addText("foundry-docs  ·  nicholasdbrady/foundry-docs  ·  Run #13", { x: 0.4, y: 7.17, w: 12, h: 0.3, fontSize: 9, color: C.textLight, fontFace: "Calibri", margin: 0 });
  }

  // Write file
  await pres.writeFile({ fileName: "slides/foundry-docs-overview.pptx" });
  console.log("✅ Deck written to slides/foundry-docs-overview.pptx");
}

buildDeck().catch(e => { console.error(e); process.exit(1); });
