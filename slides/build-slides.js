"use strict";

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaArrowRight,
  FaBell,
  FaBook,
  FaBolt,
  FaChartLine,
  FaCheckCircle,
  FaCode,
  FaCodeBranch,
  FaComments,
  FaDatabase,
  FaEye,
  FaFlask,
  FaGithub,
  FaMobileAlt,
  FaRobot,
  FaSearch,
  FaServer,
  FaShieldAlt,
  FaSyncAlt,
  FaTools,
  FaUsers,
} = require("react-icons/fa");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(__dirname, "foundry-docs-overview.pptx");

const C = {
  navy: "092D3A",
  teal: "028090",
  sea: "00A896",
  mint: "02C39A",
  ice: "EAF7F7",
  pale: "F6FBFB",
  white: "FFFFFF",
  ink: "16343C",
  muted: "5D7880",
  line: "CBE3E5",
  amber: "E4A11B",
  red: "C94C4C",
  green: "168B6A",
};

function walk(dir, predicate) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(full, predicate);
    return predicate(full) ? [full] : [];
  });
}

function relNames(dir, extension) {
  return walk(dir, (file) => file.endsWith(extension)).map((file) => path.relative(dir, file));
}

function read(file) {
  return fs.readFileSync(file, "utf8");
}

function countByTopDirectory(files) {
  const counts = new Map();
  for (const file of files) {
    const top = file.split(path.sep)[0];
    counts.set(top, (counts.get(top) || 0) + 1);
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

function extractOnBlock(content) {
  const start = content.indexOf("\non:\n");
  if (start < 0) return "";
  const remainder = content.slice(start + 5);
  const end = remainder.indexOf("\npermissions:");
  return end >= 0 ? remainder.slice(0, end) : remainder;
}

function triggerCount(workflows, trigger) {
  const pattern = new RegExp(`^  ${trigger}:`, "m");
  return workflows.filter(({ content }) => pattern.test(extractOnBlock(content))).length;
}

function basenameDelta(left, right) {
  const rightCounts = new Map();
  for (const file of right) {
    const name = path.basename(file);
    rightCounts.set(name, (rightCounts.get(name) || 0) + 1);
  }
  let delta = 0;
  for (const file of left) {
    const name = path.basename(file);
    const remaining = rightCounts.get(name) || 0;
    if (remaining > 0) rightCounts.set(name, remaining - 1);
    else delta += 1;
  }
  return delta;
}

const vnextFiles = relNames(path.join(ROOT, "docs-vnext"), ".mdx");
const canonicalFiles = relNames(path.join(ROOT, "docs"), ".mdx");
const workflowAssets = relNames(path.join(ROOT, ".github", "workflows"), ".md");
const workflowFiles = workflowAssets
  .filter((file) => !file.includes(path.sep))
  .map((file) => ({ file, content: read(path.join(ROOT, ".github", "workflows", file)) }));
const glossary = read(path.join(ROOT, "docs-vnext", "reference", "glossary.mdx"));

const DATA = {
  asOf: "31 Aug 2026",
  mdxDocs: vnextFiles.length,
  canonicalDocs: canonicalFiles.length,
  sections: countByTopDirectory(vnextFiles),
  workflowDefinitions: workflowFiles.length,
  workflowAssets: workflowAssets.length,
  slashCommands: triggerCount(workflowFiles, "slash_command"),
  workflowChains: triggerCount(workflowFiles, "workflow_run"),
  triggers: [
    ["Schedule", triggerCount(workflowFiles, "schedule")],
    ["Manual dispatch", triggerCount(workflowFiles, "workflow_dispatch")],
    ["Pull request", triggerCount(workflowFiles, "pull_request")],
    ["Issues", triggerCount(workflowFiles, "issues")],
    ["Repository dispatch", triggerCount(workflowFiles, "repository_dispatch")],
    ["Workflow run", triggerCount(workflowFiles, "workflow_run")],
    ["Slash command", triggerCount(workflowFiles, "slash_command")],
  ],
  sourceModules: relNames(path.join(ROOT, "foundry_docs_mcp"), ".py").length,
  scripts: relNames(path.join(ROOT, "scripts"), ".py").length,
  glossaryTerms: (glossary.match(/^### /gm) || []).length,
  onlyVnext: basenameDelta(vnextFiles, canonicalFiles),
  sharedBasenames: vnextFiles.length - basenameDelta(vnextFiles, canonicalFiles),
  sdkRepos: 4,
};

const HISTORY = {
  asOf: "27 Aug 2026",
  mergedDocsVnextPrs: 14,
  botMergedPrs: 12,
  humanMergedPrs: 2,
  openDocsVnextPrs: 2,
};

const EVAL = {
  issue: 640,
  date: "28 Jul 2026",
  total: 100,
  model: "claude-sonnet-4.6",
  servers: [
    ["MS Learn", 0.873, 0.32],
    ["FastMCP docs-vnext/", 0.863, 0.36],
    ["FastMCP docs/", 0.855, 0.48],
    ["Mintlify MCP", 0.843, 0.48],
  ],
  hypotheses: [
    ["H1", "MARGINAL", "docs-vnext beats docs/ by +0.008", C.amber],
    ["H2", "MARGINAL", "docs-vnext beats Mintlify by +0.020", C.amber],
    ["H3", "REJECTED", "docs-vnext trails MS Learn by -0.010", C.red],
    ["H4", "SUPPORTED", "Ranking is consistent for the executed model", C.green],
  ],
  categories: [
    ["Agent development", 0.823, 0.823],
    ["Getting started", 0.827, 0.857],
    ["Infrastructure & security", 0.913, 0.947],
    ["Observability & evaluation", 0.767, 0.767],
    ["SDK & API", 0.947, 0.920],
  ],
};

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Foundry-Docs Slide Deck Maintainer";
pptx.subject = "Stakeholder overview of the foundry-docs agentic documentation platform";
pptx.title = "Foundry-Docs: Agentic Documentation for Microsoft Foundry";
pptx.company = "foundry-docs";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "en-US",
};
pptx.defineSlideMaster({
  title: "LIGHT",
  background: { color: C.pale },
  objects: [
    { rect: { x: 0, y: 0, w: 0.12, h: 7.5, fill: { color: C.teal }, line: { transparency: 100 } } },
    { text: { text: "FOUNDRY-DOCS", options: { x: 0.45, y: 7.14, w: 2, h: 0.18, fontSize: 8, color: C.muted, bold: true, margin: 0 } } },
  ],
  slideNumber: { x: 12.5, y: 7.12, w: 0.35, h: 0.18, fontSize: 8, color: C.muted, align: "right", margin: 0 },
});
pptx.defineSlideMaster({
  title: "DARK",
  background: { color: C.navy },
  objects: [
    { rect: { x: 0, y: 7.34, w: 13.333, h: 0.16, fill: { color: C.mint }, line: { transparency: 100 } } },
    { text: { text: "FOUNDRY-DOCS", options: { x: 0.45, y: 7.06, w: 2, h: 0.18, fontSize: 8, color: "9FCED2", bold: true, margin: 0 } } },
  ],
  slideNumber: { x: 12.5, y: 7.04, w: 0.35, h: 0.18, fontSize: 8, color: "9FCED2", align: "right", margin: 0 },
});

const shadow = () => ({ type: "outer", color: "17343B", opacity: 0.12, blur: 4, angle: 45, distance: 2 });

async function iconData(Icon, color = C.white) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Icon, { color: `#${color}`, size: "256" }),
  );
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return `data:image/png;base64,${png.toString("base64")}`;
}

function title(slide, text, subtitle, dark = false) {
  slide.addText(text, {
    x: 0.48, y: 0.34, w: 12.15, h: 0.5,
    fontSize: 32, bold: true, color: dark ? C.white : C.navy, margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 0.93, w: 12, h: 0.28,
      fontSize: 12.5, color: dark ? "A9D5D7" : C.muted, margin: 0,
    });
  }
}

function card(slide, x, y, w, h, options = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: options.fill || C.white },
    line: { color: options.line || C.line, width: options.lineWidth || 1 },
    shadow: options.shadow === false ? undefined : shadow(),
  });
}

function metric(slide, x, y, w, value, label, dark = false, sub = "") {
  slide.addText(String(value), {
    x, y, w, h: 0.48, fontSize: 27, bold: true,
    color: dark ? C.mint : C.teal, align: "center", margin: 0,
  });
  slide.addText(label, {
    x, y: y + 0.54, w, h: 0.24, fontSize: 11.5, bold: true,
    color: dark ? C.white : C.ink, align: "center", margin: 0,
  });
  if (sub) {
    slide.addText(sub, {
      x, y: y + 0.84, w, h: 0.22, fontSize: 9.5,
      color: dark ? "A9D5D7" : C.muted, align: "center", margin: 0,
    });
  }
}

function label(slide, text, x, y, w, fill = C.teal, color = C.white) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.34, fill: { color: fill }, line: { transparency: 100 },
  });
  slide.addText(text, {
    x, y: y + 0.05, w, h: 0.18, fontSize: 9.5, bold: true,
    color, align: "center", margin: 0, breakLine: false,
  });
}

function bulletText(items) {
  return items.map((text) => ({
    text,
    options: { bullet: { indent: 14 }, hanging: 3, breakLine: true },
  }));
}

async function build() {
  const icons = {};
  for (const [name, Icon] of Object.entries({
    arrow: FaArrowRight, bell: FaBell, book: FaBook, bolt: FaBolt,
    chart: FaChartLine, check: FaCheckCircle, code: FaCode, branch: FaCodeBranch,
    comments: FaComments, database: FaDatabase, eye: FaEye, flask: FaFlask,
    github: FaGithub, mobile: FaMobileAlt, robot: FaRobot, search: FaSearch,
    server: FaServer, shield: FaShieldAlt, sync: FaSyncAlt, tools: FaTools, users: FaUsers,
  })) {
    icons[name] = await iconData(Icon);
  }

  // 1. Title
  {
    const s = pptx.addSlide("DARK");
    s.addShape(pptx.ShapeType.ellipse, {
      x: 9.25, y: 0.15, w: 3.8, h: 3.8, fill: { color: C.teal, transparency: 55 }, line: { transparency: 100 },
    });
    s.addShape(pptx.ShapeType.ellipse, {
      x: 10.8, y: 3.9, w: 2.2, h: 2.2, fill: { color: C.sea, transparency: 38 }, line: { transparency: 100 },
    });
    s.addText("Foundry-Docs", {
      x: 0.65, y: 1.45, w: 8.7, h: 0.8, fontSize: 46, bold: true, color: C.white, margin: 0,
    });
    s.addText("Agentic Documentation for Microsoft Foundry", {
      x: 0.68, y: 2.45, w: 9.4, h: 0.58, fontSize: 25, color: C.mint, margin: 0,
    });
    s.addText("A live content pipeline, dual-mode MCP retrieval, and autonomous quality loops.", {
      x: 0.7, y: 3.28, w: 8.9, h: 0.45, fontSize: 16, color: "CAE4E6", margin: 0,
    });
    card(s, 0.68, 4.5, 8.7, 1.25, { fill: "0D4653", line: "23606B", shadow: false });
    metric(s, 0.95, 4.72, 1.6, DATA.mdxDocs, "MDX pages", true);
    metric(s, 2.85, 4.72, 1.8, DATA.workflowDefinitions, "agent workflows", true);
    metric(s, 4.95, 4.72, 1.45, DATA.sdkRepos, "SDK repos", true);
    metric(s, 6.75, 4.72, 2.1, `+${(EVAL.servers[1][1] - EVAL.servers[2][1]).toFixed(3)}`, "vnext eval lift", true);
    s.addText(`Current repository + verified GitHub data | ${DATA.asOf}`, {
      x: 0.7, y: 6.35, w: 7.8, h: 0.28, fontSize: 11, color: "9FCED2", margin: 0,
    });
  }

  // 2. What is Foundry-Docs
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "What is Foundry-Docs?", "One platform, two documentation variants, five MCP tools per server.");
    const items = [
      ["Extract", "Pull Microsoft Foundry content from MicrosoftDocs/azure-ai-docs.", "sync"],
      ["Transform", "Convert Microsoft Learn markdown into Mintlify-ready MDX.", "code"],
      ["Retrieve", "Serve local TF-IDF search or Azure AI Search hybrid retrieval.", "search"],
      ["Improve", "Use agentic workflows to audit, test, review, and update docs-vnext.", "robot"],
    ];
    items.forEach(([head, body, icon], i) => {
      const y = 1.45 + i * 1.25;
      card(s, 0.55, y, 7.25, 0.98);
      s.addShape(pptx.ShapeType.ellipse, {
        x: 0.8, y: y + 0.18, w: 0.58, h: 0.58, fill: { color: C.teal }, line: { transparency: 100 },
      });
      s.addImage({ data: icons[icon], x: 0.95, y: y + 0.33, w: 0.28, h: 0.28 });
      s.addText(head, { x: 1.62, y: y + 0.15, w: 1.25, h: 0.28, fontSize: 16, bold: true, color: C.navy, margin: 0 });
      s.addText(body, { x: 2.85, y: y + 0.15, w: 4.55, h: 0.55, fontSize: 13.5, color: C.ink, margin: 0 });
    });
    card(s, 8.15, 1.45, 4.55, 4.75, { fill: C.navy, line: C.navy });
    s.addImage({ data: icons.server, x: 9.77, y: 1.85, w: 1.3, h: 1.3 });
    s.addText("FastMCP service surface", {
      x: 8.5, y: 3.25, w: 3.85, h: 0.35, fontSize: 20, bold: true, color: C.white, align: "center", margin: 0,
    });
    s.addText(bulletText([
      "search_docs",
      "get_doc",
      "list_sections",
      "get_section",
      "submit_feedback",
    ]), {
      x: 8.95, y: 3.9, w: 3.1, h: 1.55, fontSize: 14, color: "D9EEEE",
      breakLine: false, paraSpaceAfterPt: 8, margin: 0,
    });
    label(s, "docs/", 8.65, 5.65, 1.45, C.teal);
    label(s, "docs-vnext/", 10.45, 5.65, 1.75, C.sea);
  }

  // 3. Architecture
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "Architecture: source to stakeholder answer", "The same factory serves canonical and experimental content; agents operate around the content boundary.");
    const nodes = [
      ["MicrosoftDocs\nazure-ai-docs", "github"],
      ["Manifest +\ndownload", "database"],
      ["Learn MD to\nMintlify MDX", "code"],
      ["docs/ +\ndocs-vnext/", "book"],
      ["Local TF-IDF or\nAzure hybrid", "search"],
      ["FastMCP\nclients", "server"],
    ];
    nodes.forEach(([text, icon], i) => {
      const x = 0.48 + i * 2.08;
      card(s, x, 2.0, 1.65, 1.72, { fill: i === 3 ? C.ice : C.white });
      s.addShape(pptx.ShapeType.ellipse, {
        x: x + 0.52, y: 2.25, w: 0.62, h: 0.62, fill: { color: i === 3 ? C.sea : C.teal }, line: { transparency: 100 },
      });
      s.addImage({ data: icons[icon], x: x + 0.68, y: 2.41, w: 0.3, h: 0.3 });
      s.addText(text, { x: x + 0.12, y: 3.02, w: 1.41, h: 0.48, fontSize: 12.5, bold: true, color: C.ink, align: "center", margin: 0 });
      if (i < nodes.length - 1) {
        s.addImage({ data: icons.arrow, x: x + 1.72, y: 2.66, w: 0.28, h: 0.28 });
      }
    });
    card(s, 1.05, 4.62, 11.1, 1.32, { fill: C.navy, line: C.navy });
    s.addImage({ data: icons.robot, x: 1.42, y: 4.95, w: 0.58, h: 0.58 });
    s.addText("Agent improvement plane", { x: 2.25, y: 4.83, w: 2.5, h: 0.3, fontSize: 18, bold: true, color: C.mint, margin: 0 });
    s.addText("Monitors create evidence -> fixers update docs-vnext -> reviewers enforce MDX quality -> eval measures retrieval outcomes.", {
      x: 2.25, y: 5.23, w: 8.9, h: 0.42, fontSize: 14, color: C.white, margin: 0,
    });
    s.addText(`${DATA.sourceModules} server modules | ${DATA.scripts} pipeline and evaluation scripts`, {
      x: 8.45, y: 6.35, w: 3.7, h: 0.25, fontSize: 11, color: C.muted, align: "right", margin: 0,
    });
  }

  // 4. Coverage
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "Documentation coverage", `${DATA.mdxDocs} MDX pages across ${DATA.sections.length} top-level content areas.`);
    const top = DATA.sections.slice(0, 10);
    const max = top[0].count;
    top.forEach((section, i) => {
      const col = i < 5 ? 0 : 1;
      const row = i % 5;
      const x = 0.72 + col * 6.2;
      const y = 1.48 + row * 0.92;
      const barW = 4.4 * section.count / max;
      s.addText(section.name.replaceAll("-", " "), {
        x, y, w: 1.75, h: 0.22, fontSize: 11.5, bold: true, color: C.ink, margin: 0,
      });
      s.addShape(pptx.ShapeType.roundRect, {
        x: x + 1.8, y: y + 0.02, w: 4.2, h: 0.25, fill: { color: "DCEEEF" }, line: { transparency: 100 },
      });
      s.addShape(pptx.ShapeType.roundRect, {
        x: x + 1.8, y: y + 0.02, w: Math.max(0.2, barW), h: 0.25,
        fill: { color: col ? C.sea : C.teal }, line: { transparency: 100 },
      });
      s.addText(String(section.count), {
        x: x + 5.38, y: y - 0.02, w: 0.62, h: 0.22, fontSize: 11.5, bold: true, color: C.teal, align: "right", margin: 0,
      });
    });
    card(s, 0.72, 6.15, 12.0, 0.63, { fill: C.ice, shadow: false });
    s.addText(`${DATA.onlyVnext} filenames only in docs-vnext | ${DATA.sharedBasenames} filenames shared with docs/ | ${DATA.canonicalDocs} canonical MDX pages`, {
      x: 0.98, y: 6.35, w: 11.45, h: 0.22, fontSize: 12.5, bold: true, color: C.navy, align: "center", margin: 0,
    });
  }

  // 5. Agentic workflows
  {
    const s = pptx.addSlide("DARK");
    title(s, "Agentic workflows", `${DATA.workflowDefinitions} executable workflow definitions; ${DATA.workflowAssets} markdown assets including shared prompts.`, true);
    const groups = [
      ["MONITOR", "Upstream docs\nSDK releases\nCommunity + Reddit", "bell", C.teal],
      ["TEST", "Docs auditor\nNoob tester\nSearch testbench", "flask", C.sea],
      ["UPDATE", "Post-sync updater\nGlossary + changelog\nUnbloat + catalog", "sync", C.mint],
      ["GOVERN", "PR docs reviewer\nAuto-triage\nPost-merge verify", "shield", "2B6572"],
    ];
    groups.forEach(([head, body, icon, fill], i) => {
      const x = 0.62 + i * 3.14;
      card(s, x, 1.63, 2.72, 3.68, { fill, line: fill });
      s.addShape(pptx.ShapeType.ellipse, {
        x: x + 0.9, y: 2.02, w: 0.92, h: 0.92, fill: { color: C.navy, transparency: 8 }, line: { transparency: 100 },
      });
      s.addImage({ data: icons[icon], x: x + 1.13, y: 2.25, w: 0.46, h: 0.46 });
      s.addText(head, { x: x + 0.25, y: 3.18, w: 2.22, h: 0.28, fontSize: 17, bold: true, color: C.white, align: "center", margin: 0 });
      s.addText(body, { x: x + 0.3, y: 3.7, w: 2.12, h: 1.15, fontSize: 14, color: C.white, align: "center", breakLine: false, margin: 0, valign: "mid" });
    });
    metric(s, 2.05, 5.82, 2.2, DATA.slashCommands, "slash commands", true);
    metric(s, 5.55, 5.82, 2.2, DATA.workflowChains, "workflow_run chains", true);
    metric(s, 9.05, 5.82, 2.2, DATA.workflowDefinitions, "post-consolidation", true);
  }

  // 6. Trigger coverage
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "Trigger coverage", "Scheduled maintenance, event-driven response, human control, and chained verification coexist.");
    const max = Math.max(...DATA.triggers.map(([, count]) => count));
    DATA.triggers.forEach(([name, count], i) => {
      const y = 1.48 + i * 0.68;
      s.addText(name, { x: 0.72, y, w: 1.75, h: 0.23, fontSize: 12.5, bold: true, color: C.ink, margin: 0 });
      s.addShape(pptx.ShapeType.roundRect, {
        x: 2.55, y: y + 0.01, w: 7.85, h: 0.28, fill: { color: "DCEEEF" }, line: { transparency: 100 },
      });
      s.addShape(pptx.ShapeType.roundRect, {
        x: 2.55, y: y + 0.01, w: Math.max(0.22, 7.85 * count / max), h: 0.28,
        fill: { color: i % 2 ? C.sea : C.teal }, line: { transparency: 100 },
      });
      s.addText(String(count), { x: 10.55, y: y - 0.03, w: 0.48, h: 0.25, fontSize: 13, bold: true, color: C.teal, align: "right", margin: 0 });
    });
    card(s, 11.25, 1.48, 1.45, 4.7, { fill: C.navy, line: C.navy });
    s.addImage({ data: icons.bolt, x: 11.7, y: 1.92, w: 0.55, h: 0.55 });
    s.addText("EVENT\nDRIVEN", { x: 11.38, y: 2.72, w: 1.18, h: 0.75, fontSize: 17, bold: true, color: C.mint, align: "center", margin: 0 });
    s.addText("Detect\nAnalyze\nAct\nVerify", { x: 11.42, y: 3.8, w: 1.1, h: 1.35, fontSize: 14, color: C.white, align: "center", breakLine: false, margin: 0 });
  }

  // 7. Quality pipeline
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "Quality pipeline", "Three complementary gates test correctness, usability, and change quality.");
    const stages = [
      ["1", "Documentation Auditor", "Source + link accuracy", ["Code examples", "External links", "Terminology"], "eye"],
      ["2", "Noob Tester", "First-use experience", ["5 required journeys", "Desktop + mobile viewports", "Evidence validator"], "mobile"],
      ["3", "PR Docs Reviewer", "Change-time quality", ["MDX syntax", "Diataxis fit", "Style + accuracy"], "check"],
    ];
    stages.forEach(([num, head, sub, bullets, icon], i) => {
      const x = 0.62 + i * 4.18;
      card(s, x, 1.55, 3.72, 4.7, { fill: i === 1 ? C.ice : C.white });
      label(s, `GATE ${num}`, x + 0.3, 1.86, 0.9, i === 1 ? C.sea : C.teal);
      s.addShape(pptx.ShapeType.ellipse, {
        x: x + 2.75, y: 1.78, w: 0.62, h: 0.62, fill: { color: C.navy }, line: { transparency: 100 },
      });
      s.addImage({ data: icons[icon], x: x + 2.92, y: 1.95, w: 0.28, h: 0.28 });
      s.addText(head, { x: x + 0.3, y: 2.72, w: 3.0, h: 0.35, fontSize: 18, bold: true, color: C.navy, margin: 0 });
      s.addText(sub, { x: x + 0.3, y: 3.18, w: 3.0, h: 0.25, fontSize: 12.5, color: C.muted, margin: 0 });
      s.addText(bulletText(bullets), {
        x: x + 0.35, y: 3.78, w: 2.95, h: 1.45, fontSize: 14, color: C.ink, paraSpaceAfterPt: 10, margin: 0,
      });
      s.addText(i === 1 ? "Real site + source cross-check" : "Repository evidence", {
        x: x + 0.3, y: 5.58, w: 3.0, h: 0.25, fontSize: 10.5, bold: true, color: C.teal, align: "center", margin: 0,
      });
    });
  }

  // 8. History and impact
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "docs-vnext history & impact", `Verified GitHub PR history through ${HISTORY.asOf}; repository coverage through ${DATA.asOf}.`);
    card(s, 0.58, 1.38, 3.15, 4.95, { fill: C.navy, line: C.navy });
    metric(s, 0.9, 1.75, 2.5, HISTORY.mergedDocsVnextPrs, "merged docs-vnext PRs", true);
    metric(s, 0.9, 3.12, 2.5, `${HISTORY.botMergedPrs}/${HISTORY.humanMergedPrs}`, "bot / human authored", true);
    metric(s, 0.9, 4.49, 2.5, HISTORY.openDocsVnextPrs, "open docs-vnext PRs", true);
    const milestones = [
      ["01 Mar", "PR #23", "First traced agentic content PR", "Unbloat cloud evaluation"],
      ["02 Mar", "PR #28", "Glossary created from zero", "35 terms in one run"],
      ["04 Mar", "PR #46", "Navigation reflow", "Product-pillar structure"],
      ["28 Jul", `Issue #${EVAL.issue}`, "Evaluation report", "docs-vnext +0.008 vs docs/"],
    ];
    milestones.forEach(([date, ref, head, sub], i) => {
      const y = 1.48 + i * 1.16;
      s.addShape(pptx.ShapeType.ellipse, {
        x: 4.15, y: y + 0.1, w: 0.34, h: 0.34, fill: { color: i === 3 ? C.mint : C.teal }, line: { transparency: 100 },
      });
      if (i < milestones.length - 1) {
        s.addShape(pptx.ShapeType.line, { x: 4.32, y: y + 0.42, w: 0, h: 0.84, line: { color: C.line, width: 2 } });
      }
      s.addText(date, { x: 4.72, y, w: 0.8, h: 0.22, fontSize: 11, bold: true, color: C.teal, margin: 0 });
      s.addText(ref, { x: 5.52, y, w: 0.9, h: 0.22, fontSize: 11, bold: true, color: C.navy, margin: 0 });
      s.addText(head, { x: 6.5, y, w: 3.05, h: 0.24, fontSize: 14.5, bold: true, color: C.ink, margin: 0 });
      s.addText(sub, { x: 6.5, y: y + 0.36, w: 3.2, h: 0.23, fontSize: 11.5, color: C.muted, margin: 0 });
    });
    card(s, 9.95, 1.48, 2.7, 4.62, { fill: C.ice, shadow: false });
    metric(s, 10.22, 1.85, 2.15, DATA.mdxDocs, "total MDX pages");
    metric(s, 10.22, 3.22, 2.15, DATA.onlyVnext, "vnext-only names");
    metric(s, 10.22, 4.59, 2.15, DATA.glossaryTerms, "current glossary terms");
    s.addText("Automation issues are ephemeral evidence: monitors create them, downstream agents act, and expiry/close rules resolve stale signals.", {
      x: 4.15, y: 6.37, w: 8.5, h: 0.4, fontSize: 11.5, color: C.muted, italic: true, margin: 0,
    });
  }

  // 9. Chain deep dive
  {
    const s = pptx.addSlide("DARK");
    title(s, "Deep dive: agentic chain in action", "Two real detections show how monitoring becomes routed documentation work.", true);
    s.addText("UPSTREAM DOCS CHAIN", { x: 0.62, y: 1.38, w: 3.1, h: 0.28, fontSize: 15, bold: true, color: C.mint, margin: 0 });
    const upstream = [
      ["Upstream Docs Monitor", "Every 12h", "bell"],
      ["Issue #54", "1 Foundry commit", "github"],
      ["sync-and-convert", "Dispatched", "sync"],
      ["Post-Sync Updater", "PR or evidence-based noop", "robot"],
    ];
    upstream.forEach(([head, sub, icon], i) => {
      const x = 0.62 + i * 3.06;
      card(s, x, 1.88, 2.5, 1.55, { fill: "123E49", line: "2A5A64", shadow: false });
      s.addImage({ data: icons[icon], x: x + 0.2, y: 2.18, w: 0.42, h: 0.42 });
      s.addText(head, { x: x + 0.78, y: 2.08, w: 1.48, h: 0.4, fontSize: 13.5, bold: true, color: C.white, margin: 0 });
      s.addText(sub, { x: x + 0.78, y: 2.58, w: 1.48, h: 0.36, fontSize: 10.5, color: "A9D5D7", margin: 0 });
      if (i < upstream.length - 1) s.addImage({ data: icons.arrow, x: x + 2.62, y: 2.45, w: 0.28, h: 0.28 });
    });
    s.addText("Issue created about 3 minutes after the monitor run timestamp; downstream work is deliberately data-dependent.", {
      x: 0.7, y: 3.62, w: 11.8, h: 0.28, fontSize: 11.5, color: "A9D5D7", margin: 0,
    });
    s.addText("SDK RELEASE CHAIN", { x: 0.62, y: 4.32, w: 3.1, h: 0.28, fontSize: 15, bold: true, color: C.mint, margin: 0 });
    card(s, 0.62, 4.82, 12.05, 1.55, { fill: C.teal, line: C.teal });
    const sdkItems = [
      ["SDK Release Monitor", "4 SDK repos + REST"],
      ["Issue #53", "Java 2.0.0-beta.2"],
      ["Breaking changes", "Index -> AIProjectIndex"],
      ["Impact routing", "api-sdk + agent development"],
    ];
    sdkItems.forEach(([head, sub], i) => {
      const x = 0.92 + i * 2.95;
      s.addText(head, { x, y: 5.12, w: 2.3, h: 0.28, fontSize: 13.5, bold: true, color: C.white, align: "center", margin: 0 });
      s.addText(sub, { x, y: 5.58, w: 2.3, h: 0.24, fontSize: 10.5, color: "D8F3F0", align: "center", margin: 0 });
      if (i < sdkItems.length - 1) s.addImage({ data: icons.arrow, x: x + 2.5, y: 5.37, w: 0.24, h: 0.24 });
    });
  }

  // 10. Content improvements
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "Deep dive: content improvements", "Two merged agent PRs demonstrate net-new reference content and targeted simplification.");
    card(s, 0.62, 1.45, 5.95, 4.95);
    label(s, "PR #28 | GLOSSARY MAINTAINER", 0.95, 1.77, 2.35, C.sea);
    s.addText("From zero to 35 terms", { x: 0.95, y: 2.38, w: 4.9, h: 0.36, fontSize: 22, bold: true, color: C.navy, margin: 0 });
    s.addText("One weekly scan converted project vocabulary into a navigable reference surface.", {
      x: 0.95, y: 2.88, w: 5.0, h: 0.48, fontSize: 13.5, color: C.ink, margin: 0,
    });
    s.addText(bulletText([
      "194 additions across glossary + navigation",
      "16 alphabetical sections",
      "Foundry, MCP, retrieval, evaluation, and tooling terms",
      "Generated from the prior seven days of repository change",
    ]), {
      x: 1.0, y: 3.62, w: 5.05, h: 1.8, fontSize: 13.5, color: C.ink, paraSpaceAfterPt: 8, margin: 0,
    });
    card(s, 6.8, 1.45, 5.9, 4.95, { fill: C.ice });
    label(s, "PR #23 | DOCUMENTATION UNBLOAT", 7.12, 1.77, 2.8, C.teal);
    s.addText("Less repetition, same technical signal", { x: 7.12, y: 2.38, w: 5.0, h: 0.36, fontSize: 22, bold: true, color: C.navy, margin: 0 });
    const beforeAfter = [
      ["Words", "3,412", "3,180", "-7%"],
      ["Bullets", "29", "19", "-34.5%"],
      ["Lines", "913", "884", "-3%"],
    ];
    beforeAfter.forEach(([name, before, after, delta], i) => {
      const y = 3.08 + i * 0.72;
      s.addText(name, { x: 7.15, y, w: 1.0, h: 0.23, fontSize: 12, bold: true, color: C.ink, margin: 0 });
      s.addText(before, { x: 8.25, y, w: 0.85, h: 0.23, fontSize: 12, color: C.muted, align: "right", margin: 0 });
      s.addImage({ data: icons.arrow, x: 9.28, y: y + 0.01, w: 0.22, h: 0.22 });
      s.addText(after, { x: 9.7, y, w: 0.85, h: 0.23, fontSize: 12, bold: true, color: C.teal, margin: 0 });
      label(s, delta, 11.15, y - 0.05, 0.9, C.sea);
    });
    s.addText("Removed duplicate paragraphs, four repetitive prerequisite tips, a trivial tip, and redundant list structures.", {
      x: 7.15, y: 5.45, w: 4.95, h: 0.45, fontSize: 12.5, color: C.ink, margin: 0,
    });
  }

  // 11. Evaluation
  {
    const s = pptx.addSlide("DARK");
    title(s, "Evaluation harness results", `Issue #${EVAL.issue}: ${EVAL.total} evaluations across 4 servers and 1 executed model (${EVAL.date}).`, true);
    s.addText("Latest run executed one model; the configured three-model matrix was not present in this report.", {
      x: 0.62, y: 1.24, w: 7.2, h: 0.28, fontSize: 11.5, color: "A9D5D7", italic: true, margin: 0,
    });
    const headers = ["Server", EVAL.model, "Pass rate"];
    headers.forEach((h, i) => s.addText(h, {
      x: [0.7, 4.5, 6.1][i], y: 1.72, w: [3.5, 1.35, 1.2][i], h: 0.25,
      fontSize: 11, bold: true, color: C.mint, align: i ? "center" : "left", margin: 0,
    }));
    EVAL.servers.forEach(([name, score, pass], i) => {
      const y = 2.15 + i * 0.68;
      const fill = i === 1 ? "145967" : "103E49";
      card(s, 0.62, y, 6.8, 0.5, { fill, line: fill, shadow: false });
      s.addText(`${i + 1}. ${name}`, { x: 0.85, y: y + 0.13, w: 3.4, h: 0.2, fontSize: 12.5, bold: i < 2, color: C.white, margin: 0 });
      s.addText(score.toFixed(3), { x: 4.5, y: y + 0.13, w: 1.35, h: 0.2, fontSize: 12.5, bold: true, color: i === 1 ? C.mint : C.white, align: "center", margin: 0 });
      s.addText(`${Math.round(pass * 100)}%`, { x: 6.12, y: y + 0.13, w: 1.0, h: 0.2, fontSize: 12.5, color: C.white, align: "center", margin: 0 });
    });
    EVAL.hypotheses.forEach(([id, status, detail, color], i) => {
      const y = 5.08 + i * 0.45;
      label(s, `${id} ${status}`, 0.68, y, 1.55, color);
      s.addText(detail, { x: 2.45, y: y + 0.04, w: 4.8, h: 0.2, fontSize: 11.5, color: C.white, margin: 0 });
    });
    card(s, 7.75, 1.72, 4.92, 4.98, { fill: C.white, line: C.white });
    s.addText("Category delta: vnext - docs", { x: 8.05, y: 2.02, w: 4.2, h: 0.3, fontSize: 17, bold: true, color: C.navy, margin: 0 });
    EVAL.categories.forEach(([name, docs, vnext], i) => {
      const y = 2.65 + i * 0.67;
      const delta = vnext - docs;
      s.addText(name, { x: 8.05, y, w: 2.5, h: 0.22, fontSize: 11.5, color: C.ink, margin: 0 });
      s.addShape(pptx.ShapeType.roundRect, {
        x: 10.72, y: y + 0.01, w: 1.05, h: 0.25, fill: { color: "E2ECEE" }, line: { transparency: 100 },
      });
      const width = Math.min(1.05, Math.abs(delta) / 0.04);
      s.addShape(pptx.ShapeType.roundRect, {
        x: 10.72, y: y + 0.01, w: Math.max(0.05, width), h: 0.25,
        fill: { color: delta >= 0 ? C.sea : C.red }, line: { transparency: 100 },
      });
      s.addText(`${delta >= 0 ? "+" : ""}${delta.toFixed(3)}`, {
        x: 11.9, y: y - 0.01, w: 0.52, h: 0.22, fontSize: 11.5, bold: true,
        color: delta >= 0 ? C.green : C.red, align: "right", margin: 0,
      });
    });
    s.addText("Largest gains: infrastructure/security (+0.034) and getting-started (+0.030). Weak spot: observability remains flat at 0.767.", {
      x: 8.05, y: 6.15, w: 4.2, h: 0.35, fontSize: 10.8, color: C.muted, margin: 0,
    });
  }

  // 12. Community
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "Community integration", "External signals enter through controlled dispatch events and become scoped documentation evidence.");
    const sources = [
      ["Microsoft Foundry discussions", "repository_dispatch", "Discussion payload + labels", "comments"],
      ["foundry-samples changes", "scheduled/update agents", "Code and sample drift", "github"],
      ["Reddit community signals", "repository_dispatch", "Real-world confusion and gaps", "users"],
    ];
    sources.forEach(([head, trigger, output, icon], i) => {
      const y = 1.55 + i * 1.55;
      card(s, 0.62, y, 5.55, 1.18);
      s.addShape(pptx.ShapeType.ellipse, {
        x: 0.95, y: y + 0.27, w: 0.62, h: 0.62, fill: { color: i === 0 ? C.teal : i === 1 ? C.sea : C.navy }, line: { transparency: 100 },
      });
      s.addImage({ data: icons[icon], x: 1.11, y: y + 0.43, w: 0.3, h: 0.3 });
      s.addText(head, { x: 1.82, y: y + 0.22, w: 3.85, h: 0.27, fontSize: 15.5, bold: true, color: C.navy, margin: 0 });
      s.addText(`${trigger} -> ${output}`, { x: 1.82, y: y + 0.67, w: 3.85, h: 0.23, fontSize: 11.5, color: C.muted, margin: 0 });
    });
    s.addImage({ data: icons.arrow, x: 6.5, y: 3.25, w: 0.62, h: 0.62 });
    card(s, 7.45, 1.55, 5.2, 4.28, { fill: C.navy, line: C.navy });
    s.addText("Signal routing", { x: 7.85, y: 1.95, w: 4.35, h: 0.36, fontSize: 22, bold: true, color: C.mint, align: "center", margin: 0 });
    s.addText(bulletText([
      "Classify doc gap, error, request, or SDK signal",
      "Map the signal to affected docs-vnext pages",
      "Create a time-bounded issue only when action is justified",
      "Noop when evidence does not support documentation impact",
    ]), {
      x: 8.02, y: 2.72, w: 4.05, h: 2.1, fontSize: 14, color: C.white, paraSpaceAfterPt: 10, margin: 0,
    });
    label(s, "HIGH-SIGNAL INPUTS ONLY", 8.75, 5.18, 2.6, C.sea);
  }

  // 13. SDK monitoring
  {
    const s = pptx.addSlide("DARK");
    title(s, "SDK monitoring", "Four language repositories plus the REST specification are checked every 12 hours.", true);
    const langs = [
      ["Python", "azure-sdk-for-python"],
      ["JavaScript / TypeScript", "azure-sdk-for-js"],
      [".NET", "azure-sdk-for-net"],
      ["Java", "azure-sdk-for-java"],
    ];
    langs.forEach(([lang, repo], i) => {
      const x = 0.62 + i * 3.12;
      card(s, x, 1.62, 2.72, 1.42, { fill: "123E49", line: "2A5A64", shadow: false });
      s.addText(lang, { x: x + 0.22, y: 1.92, w: 2.28, h: 0.28, fontSize: 16, bold: true, color: C.mint, align: "center", margin: 0 });
      s.addText(repo, { x: x + 0.2, y: 2.42, w: 2.32, h: 0.22, fontSize: 10.5, color: C.white, align: "center", margin: 0 });
    });
    card(s, 0.62, 3.58, 12.05, 2.45, { fill: C.teal, line: C.teal });
    s.addText("DETECTED EXAMPLE", { x: 0.95, y: 3.92, w: 2.0, h: 0.25, fontSize: 12, bold: true, color: "CFF6EE", margin: 0 });
    s.addText("Java 2.0.0-beta.2", { x: 0.95, y: 4.37, w: 3.1, h: 0.4, fontSize: 25, bold: true, color: C.white, margin: 0 });
    s.addText("Issue #53 | 05 Mar 2026", { x: 0.98, y: 4.95, w: 2.8, h: 0.25, fontSize: 11.5, color: "D8F3F0", margin: 0 });
    const changes = [
      ["HIGH", "Index renamed to AIProjectIndex"],
      ["MEDIUM", "FoundryFeaturesOptInKeys constants removed"],
      ["LOW", "Custom DayOfWeek replaced by java.time.DayOfWeek"],
    ];
    changes.forEach(([level, text], i) => {
      const y = 3.98 + i * 0.64;
      label(s, level, 4.55, y, 0.95, i === 0 ? C.red : i === 1 ? C.amber : C.green);
      s.addText(text, { x: 5.75, y: y + 0.05, w: 5.85, h: 0.24, fontSize: 13, color: C.white, margin: 0 });
    });
    s.addText("Monitor -> changelog diff -> breaking-change analysis -> docs impact map -> issue or noop", {
      x: 4.55, y: 5.55, w: 7.25, h: 0.28, fontSize: 11.5, color: "D8F3F0", italic: true, margin: 0,
    });
  }

  // 14. Key metrics
  {
    const s = pptx.addSlide("LIGHT");
    title(s, "Key metrics", `Current repository inventory plus verified GitHub and evaluation snapshots.`);
    const metrics = [
      [DATA.mdxDocs, "MDX pages", "docs-vnext"],
      [DATA.workflowDefinitions, "agent workflows", "top-level definitions"],
      [DATA.slashCommands, "slash commands", "human-invoked"],
      [DATA.workflowChains, "workflow chains", "workflow_run"],
      [HISTORY.mergedDocsVnextPrs, "merged vnext PRs", `${HISTORY.botMergedPrs} bot-authored`],
      [DATA.onlyVnext, "vnext-only names", "vs canonical docs"],
      [EVAL.servers[1][1].toFixed(3), "vnext eval score", EVAL.model],
      [`+${(EVAL.servers[1][1] - EVAL.servers[2][1]).toFixed(3)}`, "lift vs docs/", `Issue #${EVAL.issue}`],
    ];
    metrics.forEach(([value, head, sub], i) => {
      const col = i % 4;
      const row = Math.floor(i / 4);
      const x = 0.62 + col * 3.12;
      const y = 1.52 + row * 2.55;
      card(s, x, y, 2.72, 2.05, { fill: row ? C.ice : C.white });
      metric(s, x + 0.2, y + 0.32, 2.32, value, head, false, sub);
    });
    s.addText(`Inventory calculated by slides/build-slides.js at build time | GitHub history as of ${HISTORY.asOf} | Eval ${EVAL.date}`, {
      x: 0.62, y: 6.75, w: 12.0, h: 0.23, fontSize: 10.5, color: C.muted, align: "center", margin: 0,
    });
  }

  // 15. Next
  {
    const s = pptx.addSlide("DARK");
    title(s, "What's next", "Focus automation where measured user outcomes show the largest opportunity.", true);
    const roadmap = [
      ["01", "Close the observability gap", "Expand evaluation and tracing coverage; current category score is flat at 0.767.", "chart"],
      ["02", "Increase agentic PR yield", "Turn more validated monitor signals into merge-ready, tightly scoped changes.", "branch"],
      ["03", "Restore full eval breadth", "Run the intended multi-model matrix and track category-level confidence over time.", "flask"],
    ];
    roadmap.forEach(([num, head, body, icon], i) => {
      const y = 1.52 + i * 1.62;
      label(s, num, 0.72, y + 0.12, 0.62, i === 0 ? C.red : i === 1 ? C.sea : C.teal);
      s.addImage({ data: icons[icon], x: 1.72, y: y + 0.03, w: 0.55, h: 0.55 });
      s.addText(head, { x: 2.62, y, w: 4.1, h: 0.36, fontSize: 20, bold: true, color: C.white, margin: 0 });
      s.addText(body, { x: 2.62, y: y + 0.52, w: 6.35, h: 0.45, fontSize: 13.5, color: "BFDADD", margin: 0 });
      s.addShape(pptx.ShapeType.line, { x: 2.62, y: y + 1.16, w: 6.55, h: 0, line: { color: "315560", width: 1 } });
    });
    card(s, 9.65, 1.52, 2.85, 4.7, { fill: C.teal, line: C.teal });
    s.addImage({ data: icons.robot, x: 10.55, y: 2.05, w: 1.05, h: 1.05 });
    s.addText("SUSTAINABLE\nDOC OPS", { x: 9.95, y: 3.45, w: 2.25, h: 0.8, fontSize: 21, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText("Evidence in\nQuality gates\nMeasured outcomes", {
      x: 10.0, y: 4.68, w: 2.15, h: 0.95, fontSize: 13.5, color: "D8F3F0", align: "center", margin: 0,
    });
    s.addText(`foundry-docs | ${DATA.asOf}`, { x: 0.72, y: 6.63, w: 4.0, h: 0.25, fontSize: 11, color: "9FCED2", margin: 0 });
  }

  await pptx.writeFile({ fileName: OUT });
  console.log(JSON.stringify({
    output: path.relative(ROOT, OUT),
    slides: 15,
    data: DATA,
    history: HISTORY,
    evaluation: { issue: EVAL.issue, date: EVAL.date, total: EVAL.total, model: EVAL.model },
  }, null, 2));
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
