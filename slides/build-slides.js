"use strict";

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const OUTPUT = path.join(__dirname, "foundry-docs-overview.pptx");

const C = {
  navy: "0B1F33",
  deep: "01363D",
  teal: "028090",
  sea: "00A896",
  mint: "02C39A",
  ice: "EAF7F7",
  pale: "F5FAFB",
  white: "FFFFFF",
  ink: "17333A",
  muted: "58777D",
  line: "C9E2E4",
  amber: "F4B942",
  red: "D95D5D",
};

function walk(dir, predicate) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(full, predicate) : predicate(full) ? [full] : [];
  });
}

function topLevelFiles(dir, extension) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter((name) => name.endsWith(extension))
    .map((name) => path.join(dir, name));
}

function onBlock(file) {
  const text = fs.readFileSync(file, "utf8");
  const match = text.match(/^on:\n([\s\S]*?)(?=^[a-zA-Z][\w-]*:|\n---)/m);
  return match ? match[1] : "";
}

function countTrigger(files, trigger) {
  return files.filter((file) => new RegExp(`^  ${trigger}:`, "m").test(onBlock(file))).length;
}

function collectData() {
  const vnext = walk(path.join(ROOT, "docs-vnext"), (file) => file.endsWith(".mdx"));
  const canonical = walk(path.join(ROOT, "docs"), (file) => file.endsWith(".mdx"));
  const workflows = topLevelFiles(path.join(ROOT, ".github", "workflows"), ".md");
  const sectionMap = new Map();

  for (const file of vnext) {
    const rel = path.relative(path.join(ROOT, "docs-vnext"), file);
    const section = rel.includes(path.sep) ? rel.split(path.sep)[0] : "root";
    sectionMap.set(section, (sectionMap.get(section) || 0) + 1);
  }

  const vnextNames = new Set(vnext.map((file) => path.basename(file)));
  const canonicalNames = new Set(canonical.map((file) => path.basename(file)));
  const shared = [...vnextNames].filter((name) => canonicalNames.has(name)).length;

  return {
    mdxDocs: vnext.length,
    canonicalDocs: canonical.length,
    workflowCount: workflows.length,
    slashCommands: countTrigger(workflows, "slash_command"),
    chains: countTrigger(workflows, "workflow_run"),
    sdkRepos: 4,
    monitoredSurfaces: 5,
    sourceModules: walk(path.join(ROOT, "foundry_docs_mcp"), (file) => file.endsWith(".py")).length,
    scripts: walk(path.join(ROOT, "scripts"), (file) => file.endsWith(".py")).length,
    sections: [...sectionMap.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count),
    onlyVnext: [...vnextNames].filter((name) => !canonicalNames.has(name)).length,
    shared,
    triggers: {
      schedule: countTrigger(workflows, "schedule"),
      dispatch: countTrigger(workflows, "workflow_dispatch"),
      repositoryDispatch: countTrigger(workflows, "repository_dispatch"),
      pullRequest: countTrigger(workflows, "pull_request"),
      issues: countTrigger(workflows, "issues"),
      workflowRun: countTrigger(workflows, "workflow_run"),
      push: countTrigger(workflows, "push"),
    },
  };
}

const DATA = collectData();

const MERGED_DOCS_VNEXT_PRS = [
  23, 28, 46, 50, 93, 95, 96, 146, 148, 150, 152, 456, 489, 507,
];

const EVAL = {
  date: "2026-03-05",
  evaluations: 300,
  models: ["claude-opus-4.6", "gemini-3-pro", "gpt-5.3-codex"],
  rows: [
    { server: "MS Learn", scores: [0.933, 0.882, 0.906], average: 0.908 },
    { server: "Mintlify MCP", scores: [0.949, 0.868, 0.905], average: 0.908 },
    { server: "docs-vnext/", scores: [0.927, 0.879, 0.912], average: 0.906 },
    { server: "docs/ baseline", scores: [0.924, 0.860, 0.931], average: 0.904 },
  ],
  categories: [
    ["agent-development", 0.971, 0.962],
    ["getting-started", 0.887, 0.867],
    ["infra-security", 0.927, 0.918],
    ["observability", 0.802, 0.829],
    ["sdk-api", 0.947, 0.947],
  ],
};

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Foundry-Docs Slide Deck Maintainer";
pptx.company = "Foundry-Docs";
pptx.subject = "Stakeholder overview of Foundry-Docs architecture, automation, and outcomes";
pptx.title = "Foundry-Docs: Agentic Documentation for Microsoft Foundry";
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
    { rect: { x: 0, y: 0, w: 13.333, h: 0.12, fill: { color: C.teal }, line: { color: C.teal } } },
    { line: { x: 0.45, y: 7.12, w: 12.45, h: 0, line: { color: C.line, width: 0.8 } } },
  ],
  slideNumber: { x: 12.35, y: 7.17, w: 0.45, h: 0.18, fontSize: 9, color: C.muted, align: "right" },
});
pptx.defineSlideMaster({
  title: "DARK",
  background: { color: C.navy },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.12, fill: { color: C.mint }, line: { color: C.mint } } },
  ],
  slideNumber: { x: 12.35, y: 7.17, w: 0.45, h: 0.18, fontSize: 9, color: "8DB8BC", align: "right" },
});

const shadow = () => ({ type: "outer", color: "6F9296", opacity: 0.16, blur: 2, angle: 45, distance: 1.5 });

function addTitle(slide, title, kicker, dark = false) {
  if (kicker) {
    slide.addText(kicker.toUpperCase(), {
      x: 0.55, y: 0.34, w: 5.8, h: 0.24, fontSize: 10, bold: true,
      color: dark ? C.mint : C.teal, charSpacing: 1.7, margin: 0,
    });
  }
  slide.addText(title, {
    x: 0.55, y: 0.62, w: 12.15, h: 0.62, fontSize: 30, bold: true,
    color: dark ? C.white : C.navy, margin: 0, breakLine: false,
  });
}

function addFooter(slide, text, dark = false) {
  slide.addText(text, {
    x: 0.55, y: 6.93, w: 11.35, h: 0.2, fontSize: 8.5,
    color: dark ? "8DB8BC" : C.muted, margin: 0,
  });
}

function card(slide, x, y, w, h, title, body, options = {}) {
  const fill = options.fill || C.white;
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: fill },
    line: { color: options.line || C.line, width: 0.8 },
    shadow: options.shadow === false ? undefined : shadow(),
  });
  if (options.accent) {
    slide.addShape(pptx.ShapeType.rect, {
      x, y, w: 0.09, h,
      fill: { color: options.accent }, line: { color: options.accent },
    });
  }
  slide.addText(title, {
    x: x + 0.2, y: y + 0.16, w: w - 0.4, h: 0.33,
    fontSize: options.titleSize || 16, bold: true,
    color: options.titleColor || C.navy, margin: 0,
  });
  slide.addText(body, {
    x: x + 0.2, y: y + 0.58, w: w - 0.4, h: h - 0.72,
    fontSize: options.bodySize || 11.5, color: options.bodyColor || C.ink,
    margin: 0, breakLine: false, valign: "top",
  });
}

function metric(slide, x, y, w, value, label, dark = false) {
  slide.addText(String(value), {
    x, y, w, h: 0.66, fontSize: 34, bold: true, align: "center",
    color: dark ? C.mint : C.teal, margin: 0,
  });
  slide.addText(label, {
    x, y: y + 0.67, w, h: 0.32, fontSize: 10.5, bold: true, align: "center",
    color: dark ? "B8DADD" : C.muted, margin: 0,
  });
}

function pill(slide, x, y, w, text, color = C.teal) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.34, rectRadius: 0.12,
    fill: { color }, line: { color },
  });
  slide.addText(text, {
    x, y: y + 0.03, w, h: 0.22, fontSize: 9.5, bold: true,
    align: "center", color: C.white, margin: 0,
  });
}

function arrow(slide, x, y, w) {
  slide.addShape(pptx.ShapeType.chevron, {
    x, y, w, h: 0.42,
    fill: { color: C.mint }, line: { color: C.mint },
  });
}

// 1. Title
{
  const slide = pptx.addSlide("DARK");
  slide.addShape(pptx.ShapeType.arc, {
    x: 9.1, y: -1.2, w: 5.2, h: 5.2,
    adjustPoint: 0.25, rotate: 25,
    fill: { color: C.teal, transparency: 58 }, line: { color: C.sea, transparency: 50, width: 2 },
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: 10.25, y: 4.35, w: 2.25, h: 2.25,
    fill: { color: C.mint, transparency: 72 }, line: { color: C.mint, transparency: 100 },
  });
  slide.addText("FOUNDRY-DOCS", {
    x: 0.7, y: 1.2, w: 4.3, h: 0.3, fontSize: 12, bold: true,
    color: C.mint, charSpacing: 2.8, margin: 0,
  });
  slide.addText("Agentic Documentation\nfor Microsoft Foundry", {
    x: 0.7, y: 1.68, w: 8.8, h: 1.55, fontSize: 42, bold: true,
    color: C.white, margin: 0, breakLine: false,
  });
  slide.addText("A living documentation system: upstream ingestion, AI-assisted improvement, quality gates, and MCP delivery.", {
    x: 0.72, y: 3.58, w: 8.2, h: 0.58, fontSize: 17, color: "B8DADD", margin: 0,
  });
  metric(slide, 0.72, 5.34, 2, DATA.mdxDocs, "MDX pages", true);
  metric(slide, 2.95, 5.34, 2, DATA.workflowCount, "agent workflows", true);
  metric(slide, 5.18, 5.34, 2, DATA.slashCommands, "slash commands", true);
  metric(slide, 7.41, 5.34, 2, DATA.sdkRepos, "SDK repos", true);
  addFooter(slide, `Live repository snapshot • generated ${new Date().toISOString().slice(0, 10)}`, true);
}

// 2. What is Foundry-Docs
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, "What is Foundry-Docs?", "Platform");
  slide.addText("A dual-server FastMCP documentation platform", {
    x: 0.62, y: 1.45, w: 6.2, h: 0.42, fontSize: 22, bold: true, color: C.teal, margin: 0,
  });
  slide.addText(
    "It extracts Microsoft Learn content, converts it to Mintlify MDX, indexes it locally or in Azure AI Search, and exposes retrieval tools to AI assistants.",
    { x: 0.62, y: 1.98, w: 5.8, h: 1.05, fontSize: 16, color: C.ink, margin: 0, breakLine: false }
  );
  card(slide, 6.78, 1.42, 2.75, 1.65, "foundry_docs_mcp", "Serves canonical docs/\nLocal TF-IDF fallback\nOptional hybrid Azure Search", { accent: C.teal });
  card(slide, 9.75, 1.42, 2.75, 1.65, "foundry_docs_vnext_mcp", "Serves docs-vnext/\nAlternative information architecture\nA/B/C/D comparison surface", { accent: C.mint });
  const tools = [
    ["Search", "Relevant chunks with source paths"],
    ["Retrieve", "Full page content by document path"],
    ["Browse", "Sections and navigation discovery"],
    ["Feedback", "Telemetry-backed relevance signals"],
  ];
  tools.forEach(([name, body], i) => card(slide, 0.62 + i * 3.0, 4.05, 2.68, 1.35, name, body, { accent: i % 2 ? C.sea : C.teal, bodySize: 11 }));
  addFooter(slide, `${DATA.sourceModules} server modules • ${DATA.scripts} ingestion, indexing, and evaluation scripts`);
}

// 3. Architecture
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, "From upstream source to governed answers", "Architecture");
  const nodes = [
    ["MicrosoftDocs", "azure-ai-docs"],
    ["Extract + convert", "scripts/ pipeline"],
    ["docs/ + docs-vnext/", `${DATA.canonicalDocs} + ${DATA.mdxDocs} pages`],
    ["Search indexes", "TF-IDF + Azure hybrid"],
    ["MCP clients", "Assistants and IDEs"],
  ];
  nodes.forEach(([title, body], i) => {
    const x = 0.48 + i * 2.56;
    card(slide, x, 2.0, 2.1, 1.45, title, body, {
      fill: i === 2 ? C.deep : C.white,
      titleColor: i === 2 ? C.white : C.navy,
      bodyColor: i === 2 ? "B8DADD" : C.muted,
      accent: i === 2 ? C.mint : C.teal,
      bodySize: 10.5,
    });
    if (i < nodes.length - 1) arrow(slide, x + 2.18, 2.5, 0.28);
  });
  card(slide, 1.0, 4.45, 3.45, 1.45, "Upstream automation", "Monitor detects a Foundry change, dispatches sync-and-convert, and records the event.", { accent: C.sea });
  card(slide, 4.95, 4.45, 3.45, 1.45, "Agent improvement", "Post-sync updater preserves curated vNext structure while applying relevant source changes.", { accent: C.mint });
  card(slide, 8.9, 4.45, 3.45, 1.45, "Quality + telemetry", "Audits, noob testing, PR review, evals, spans, logs, and feedback close the loop.", { accent: C.teal });
  addFooter(slide, "ServerConfig keeps both MCP servers consistent while separating paths, environment variables, and index names.");
}

// 4. Documentation coverage
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, `Documentation coverage: ${DATA.mdxDocs} pages`, "Content");
  const top = DATA.sections.slice(0, 10);
  const max = Math.max(...top.map((item) => item.count));
  top.forEach((item, i) => {
    const y = 1.45 + i * 0.5;
    slide.addText(item.name.replaceAll("-", " "), {
      x: 0.62, y, w: 2.25, h: 0.24, fontSize: 10.5, color: C.ink, margin: 0,
    });
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 2.9, y: y + 0.01, w: 7.35, h: 0.23, rectRadius: 0.08,
      fill: { color: "DDEDEF" }, line: { color: "DDEDEF" },
    });
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 2.9, y: y + 0.01, w: 7.35 * item.count / max, h: 0.23, rectRadius: 0.08,
      fill: { color: i < 2 ? C.sea : C.teal }, line: { color: i < 2 ? C.sea : C.teal },
    });
    slide.addText(String(item.count), {
      x: 10.42, y: y - 0.02, w: 0.55, h: 0.26, fontSize: 10.5, bold: true, color: C.teal, align: "right", margin: 0,
    });
  });
  card(slide, 11.15, 1.48, 1.55, 1.35, String(DATA.sections.length), "top-level sections", { titleSize: 28, bodySize: 10.5, accent: C.mint });
  card(slide, 11.15, 3.05, 1.55, 1.35, String(DATA.onlyVnext), "vNext-only filenames", { titleSize: 28, bodySize: 10.5, accent: C.sea });
  card(slide, 11.15, 4.62, 1.55, 1.35, String(DATA.shared), "filenames shared with docs/", { titleSize: 28, bodySize: 10.5, accent: C.teal });
  addFooter(slide, "Counts are computed from docs-vnext/**/*.mdx at generation time; chart shows the ten largest top-level sections.");
}

// 5. Agentic workflows
{
  const slide = pptx.addSlide("DARK");
  addTitle(slide, `${DATA.workflowCount} agentic workflows after consolidation`, "Automation estate", true);
  const groups = [
    ["Monitor", "Upstream docs\nSDK releases\nCommunities\nModel catalog", 6, C.teal],
    ["Test", "Docs auditor\nNoob tester\nSearch testbench\nPost-merge verify", 5, C.sea],
    ["Update", "Daily updater\nPost-sync updater\nGlossary\nUnbloat", 7, C.mint],
    ["Operate", "Auto-triage\nDiff reports\nChangelog\nSlide deck", DATA.workflowCount - 18, C.amber],
  ];
  groups.forEach(([name, body, count, color], i) => {
    const x = 0.6 + i * 3.16;
    slide.addShape(pptx.ShapeType.roundRect, {
      x, y: 1.65, w: 2.82, h: 3.55, rectRadius: 0.08,
      fill: { color: "102E42" }, line: { color, width: 1.5 },
    });
    slide.addShape(pptx.ShapeType.ellipse, {
      x: x + 0.96, y: 1.95, w: 0.9, h: 0.9,
      fill: { color }, line: { color },
    });
    slide.addText(String(count), {
      x: x + 0.96, y: 2.12, w: 0.9, h: 0.38, fontSize: 22, bold: true, align: "center", color: C.white, margin: 0,
    });
    slide.addText(name, {
      x: x + 0.2, y: 3.05, w: 2.42, h: 0.4, fontSize: 20, bold: true, align: "center", color, margin: 0,
    });
    slide.addText(body, {
      x: x + 0.28, y: 3.65, w: 2.26, h: 1.15, fontSize: 12, color: "B8DADD", align: "center", margin: 0, breakLine: false,
    });
  });
  pill(slide, 4.64, 5.75, 1.65, `${DATA.slashCommands} slash commands`, C.teal);
  pill(slide, 6.48, 5.75, 1.65, `${DATA.chains} workflow chains`, C.sea);
  addFooter(slide, "Category counts are presentation groupings; total is computed from top-level .github/workflows/*.md files.", true);
}

// 6. Trigger coverage
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, "Event-driven coverage across the documentation lifecycle", "Triggers");
  const t = DATA.triggers;
  const triggers = [
    ["Schedule", t.schedule, "recurring monitoring and maintenance"],
    ["Manual dispatch", t.dispatch, "operator-controlled reruns"],
    ["Slash command", DATA.slashCommands, "issue-comment entry points"],
    ["Pull request", t.pullRequest, "review and post-merge checks"],
    ["Issues", t.issues, "label-driven fixes and triage"],
    ["Workflow chain", t.workflowRun, "sync and index follow-through"],
    ["Repository dispatch", t.repositoryDispatch, "cross-repo community signals"],
    ["Push", t.push, "direct source-change hooks"],
  ];
  triggers.forEach(([name, value, body], i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = 0.55 + col * 3.15;
    const y = 1.55 + row * 2.35;
    card(slide, x, y, 2.82, 1.85, name, body, { accent: value ? C.teal : C.line, bodySize: 10.5 });
    slide.addText(String(value), {
      x: x + 1.78, y: y + 0.18, w: 0.75, h: 0.5, fontSize: 27, bold: true,
      color: value ? C.sea : C.muted, align: "right", margin: 0,
    });
  });
  addFooter(slide, "Trigger counts are parsed only from each workflow's frontmatter on: block, avoiding permission-key false positives.");
}

// 7. Quality pipeline
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, "Three independent lenses protect quality", "Quality pipeline");
  const stages = [
    ["1", "Documentation Auditor", "Accuracy, code examples, external links, terminology, and MDX conventions.", C.teal],
    ["2", "Noob Tester", "Five first-run journeys plus mobile 375x812, tablet 768x1024, and desktop 1440x900 viewport checks.", C.sea],
    ["3", "PR Documentation Reviewer", "Change-aware review on pull request open, synchronize, reopen, and ready-for-review events.", C.mint],
  ];
  stages.forEach(([num, title, body, color], i) => {
    const x = 0.68 + i * 4.17;
    slide.addShape(pptx.ShapeType.ellipse, {
      x: x + 1.34, y: 1.55, w: 0.78, h: 0.78,
      fill: { color }, line: { color },
    });
    slide.addText(num, {
      x: x + 1.34, y: 1.72, w: 0.78, h: 0.3, fontSize: 20, bold: true, color: C.white, align: "center", margin: 0,
    });
    card(slide, x, 2.55, 3.48, 2.55, title, body, { accent: color, bodySize: 13 });
    if (i < stages.length - 1) arrow(slide, x + 3.68, 3.58, 0.28);
  });
  slide.addText("Evidence gate", {
    x: 4.55, y: 5.58, w: 1.4, h: 0.3, fontSize: 12, bold: true, color: C.teal, align: "center", margin: 0,
  });
  slide.addText("The noob tester validates its report before it can publish success; blocked infrastructure is reported separately.", {
    x: 3.1, y: 5.95, w: 4.35, h: 0.55, fontSize: 11, color: C.muted, align: "center", margin: 0,
  });
  addFooter(slide, "Quality checks combine static source inspection, rendered-site behavior, and change-specific review.");
}

// 8. History and impact
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, "docs-vnext history: from experiment to operating system", "History + impact");
  const milestones = [
    ["Mar 1", "#23", "Cloud evaluation unbloated"],
    ["Mar 2", "#28", "35-term glossary created"],
    ["Mar", "#46", "Navigation reflow by product pillar"],
    ["Mar", "#50", "267 endpoints gain 5-language samples"],
    ["Jun-Jul", "#456 / #489 / #507", "Daily glossary, sync, and SDK cleanup"],
    ["Sep", "#1045", "Latest upstream sync in local history"],
  ];
  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 3.0, w: 11.7, h: 0, line: { color: C.teal, width: 3 },
  });
  milestones.forEach(([date, ref, label], i) => {
    const x = 0.72 + i * 2.04;
    const top = i % 2 === 0;
    slide.addShape(pptx.ShapeType.ellipse, {
      x, y: 2.82, w: 0.36, h: 0.36, fill: { color: i === milestones.length - 1 ? C.mint : C.teal },
      line: { color: C.white, width: 1.2 },
    });
    slide.addText(`${date}  ${ref}`, {
      x: x - 0.2, y: top ? 1.75 : 3.42, w: 1.8, h: 0.28, fontSize: 10.5, bold: true, color: C.teal, margin: 0,
    });
    slide.addText(label, {
      x: x - 0.2, y: top ? 2.08 : 3.78, w: 1.8, h: 0.65, fontSize: 10.5, color: C.ink, margin: 0,
    });
  });
  metric(slide, 0.8, 5.35, 2.2, MERGED_DOCS_VNEXT_PRS.length, "verified merged docs-vnext PRs");
  metric(slide, 3.25, 5.35, 2.2, 2, "bot authors verified in deep dives");
  metric(slide, 5.7, 5.35, 2.2, DATA.onlyVnext, "vNext-only filenames");
  metric(slide, 8.15, 5.35, 2.2, DATA.mdxDocs, "current vNext pages");
  metric(slide, 10.6, 5.35, 2.0, DATA.canonicalDocs, "canonical pages");
  addFooter(slide, "PR set comes from approved GitHub search results; author fields for the remaining records were unavailable, so no unsupported human/agent split is claimed.");
}

// 9. Agentic chain deep dive
{
  const slide = pptx.addSlide("DARK");
  addTitle(slide, "Deep dive: a trigger becomes a documentation decision", "Agentic chain in action", true);
  const chain = [
    ["Upstream Docs Monitor", "1 Foundry commit detected\nIssue #54 created"],
    ["sync-and-convert", "Workflow dispatched\nsource content refreshed"],
    ["Post-Sync Updater", "Diffs docs/ vs docs-vnext/\npreserves curated IA"],
    ["Outcome", "Creates a vNext PR\nor noops with evidence"],
  ];
  chain.forEach(([title, body], i) => {
    const x = 0.55 + i * 3.17;
    card(slide, x, 1.55, 2.72, 1.75, title, body, {
      fill: "102E42", line: i === 3 ? C.mint : C.teal,
      titleColor: i === 3 ? C.mint : C.white, bodyColor: "B8DADD",
      accent: i === 3 ? C.mint : C.teal, bodySize: 11,
    });
    if (i < chain.length - 1) arrow(slide, x + 2.82, 2.2, 0.25);
  });
  card(slide, 0.72, 4.08, 5.7, 1.8, "Observed upstream case: #54", "2026-03-05 • blocklist instruction changed in MicrosoftDocs/azure-ai-docs • monitor dispatched sync-and-convert • issue closed after the signal was processed.", {
    fill: "102E42", line: C.sea, titleColor: C.mint, bodyColor: "B8DADD", accent: C.sea, bodySize: 12,
  });
  card(slide, 6.9, 4.08, 5.7, 1.8, "Parallel SDK chain: #53", "Java 2.0.0-beta.2 detected • Index renamed to AIProjectIndex • feature flags removed • DayOfWeek type replaced • docs impact mapped to api-sdk and agents/development.", {
    fill: "102E42", line: C.mint, titleColor: C.mint, bodyColor: "B8DADD", accent: C.mint, bodySize: 12,
  });
  addFooter(slide, "Run IDs and outcomes are verified from issues #54 and #53; duration was not exposed by the approved read interface.", true);
}

// 10. Content improvements
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, "Deep dive: agents make concrete editorial improvements", "Content outcomes");
  card(slide, 0.62, 1.45, 5.85, 4.65, "PR #28 — glossary from zero", "INPUT\nA codebase with fast-moving Foundry, MCP, search, evaluation, and developer-tooling terminology.\n\nAGENT ACTION\nGlossary Maintainer scanned recent changes, organized 16 alphabetical sections, and updated navigation.\n\nOUTPUT\n35 terms • 194 additions • one discoverable reference page", {
    accent: C.sea, bodySize: 13,
  });
  card(slide, 6.86, 1.45, 5.85, 4.65, "PR #23 — remove cloud-evaluation bloat", "BEFORE\nDuplicate intro, four repetitive prerequisite tips, trivial guidance, verbose lists.\n\nAFTER\nConcise reference table and direct prose; technical content and examples preserved.\n\nIMPACT\n-232 words (7%) • -29 lines • -10 bullets (34.5%)", {
    accent: C.mint, bodySize: 13,
  });
  pill(slide, 2.18, 6.34, 2.75, "NEW KNOWLEDGE SURFACE", C.sea);
  pill(slide, 8.38, 6.34, 2.75, "LESS FRICTION, SAME MEANING", C.teal);
  addFooter(slide, "Sources: merged PR descriptions for #28 and #23.");
}

// 11. Evaluation harness
{
  const slide = pptx.addSlide("DARK");
  addTitle(slide, "Evaluation harness: competitive, with targeted upside", "Evidence snapshot", true);
  slide.addText(`${EVAL.evaluations} evaluations • 4 servers • 3 models • report snapshot ${EVAL.date}`, {
    x: 0.58, y: 1.24, w: 6.5, h: 0.3, fontSize: 11, color: "8DB8BC", margin: 0,
  });
  const tableRows = [
    [
      { text: "Server", options: { bold: true, color: C.white, fill: C.teal } },
      ...EVAL.models.map((model) => ({ text: model, options: { bold: true, color: C.white, fill: C.teal, align: "center" } })),
      { text: "Average", options: { bold: true, color: C.white, fill: C.teal, align: "center" } },
    ],
    ...EVAL.rows.map((row) => {
      const selected = row.server === "docs-vnext/";
      const fill = selected ? C.deep : C.white;
      const color = selected ? C.mint : C.ink;
      return [
        { text: row.server, options: { bold: selected, color, fill } },
        ...row.scores.map((score) => ({ text: score.toFixed(3), options: { color, fill, align: "center" } })),
        { text: row.average.toFixed(3), options: { bold: true, color, fill, align: "center" } },
      ];
    }),
  ];
  slide.addTable(tableRows, {
    x: 0.58, y: 1.65, w: 7.2, h: 2.55,
    colW: [1.75, 1.42, 1.3, 1.42, 1.0],
    rowH: 0.48, fontSize: 10.2, fontFace: "Aptos",
    border: { type: "solid", color: C.teal, pt: 0.5 },
    margin: 0.08,
  });
  card(slide, 8.12, 1.65, 4.58, 2.55, "Hypotheses", "H1  MARGINAL  vNext +0.002 vs docs/\nH2  REJECTED  -0.002 vs Mintlify\nH3  REJECTED  -0.002 vs MS Learn\nH4  MIXED  model rankings vary", {
    fill: "102E42", line: C.teal, titleColor: C.mint, bodyColor: "B8DADD", accent: C.mint, bodySize: 12.5,
  });
  slide.addText("Category delta: docs-vnext minus docs/", {
    x: 0.62, y: 4.56, w: 3.2, h: 0.3, fontSize: 13, bold: true, color: C.mint, margin: 0,
  });
  EVAL.categories.forEach(([name, vnext, docs], i) => {
    const delta = vnext - docs;
    const x = 0.62 + i * 2.48;
    card(slide, x, 5.0, 2.2, 1.15, name, `${delta >= 0 ? "+" : ""}${delta.toFixed(3)}`, {
      fill: "102E42", line: delta > 0 ? C.mint : delta < 0 ? C.red : C.muted,
      titleColor: C.white, bodyColor: delta > 0 ? C.mint : delta < 0 ? "FF9D9D" : "B8DADD",
      bodySize: 19, titleSize: 10.5, shadow: false,
    });
  });
  addFooter(slide, "Latest eval issue was blocked by the approved read interface; values shown are the most recent verified snapshot already carried by the deck.", true);
}

// 12. Community integration
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, "Community signals become documentation work", "Community integration");
  const sources = [
    ["Microsoft Foundry discussions", "Cross-repo repository_dispatch\n/check-discussions fallback", C.teal],
    ["foundry-samples activity", "Code and sample changes reveal docs drift and missing examples", C.sea],
    ["Reddit community signals", "Devvit dispatch surfaces recurring questions and pain points", C.mint],
  ];
  sources.forEach(([title, body, color], i) => {
    const x = 0.62 + i * 4.15;
    card(slide, x, 1.55, 3.72, 2.1, title, body, { accent: color, bodySize: 12.5 });
    arrow(slide, x + 1.65, 3.9, 0.42);
  });
  card(slide, 3.9, 4.72, 5.55, 1.45, "Shared decision layer", "Classify signal → map to docs-vnext → create an actionable issue, dispatch a fixer, or noop when evidence is insufficient.", {
    fill: C.deep, line: C.deep, titleColor: C.white, bodyColor: "B8DADD", accent: C.mint, bodySize: 12,
  });
  addFooter(slide, `${DATA.triggers.repositoryDispatch} workflows accept repository_dispatch events for cross-repository signals.`);
}

// 13. SDK monitoring
{
  const slide = pptx.addSlide("DARK");
  addTitle(slide, "SDK monitoring maps releases to documentation impact", "Release intelligence", true);
  const langs = [
    ["Python", "azure-ai-projects"],
    ["JavaScript", "@azure/ai-projects"],
    [".NET", "Azure.AI.Projects"],
    ["Java", "azure-ai-projects"],
  ];
  langs.forEach(([lang, pkg], i) => {
    const x = 0.58 + i * 3.15;
    card(slide, x, 1.55, 2.82, 1.35, lang, pkg, {
      fill: "102E42", line: C.teal, titleColor: C.mint, bodyColor: "B8DADD", accent: C.teal, bodySize: 11,
    });
  });
  card(slide, 0.78, 3.55, 5.6, 2.35, "Detection", "Compare changelog versions against persisted state.\n\nExtract release date, stability, breaking changes, new features, and API changes.\n\nA REST API specification surface is assessed alongside the four SDK repositories.", {
    fill: "102E42", line: C.sea, titleColor: C.white, bodyColor: "B8DADD", accent: C.sea, bodySize: 12,
  });
  card(slide, 6.95, 3.55, 5.6, 2.35, "Example: Java 2.0.0-beta.2", "HIGH  Index → AIProjectIndex\nMEDIUM  FoundryFeaturesOptInKeys constants removed\nLOW  custom DayOfWeek → java.time.DayOfWeek\n\nMapped to api-sdk/ and agents/development/ in issue #53.", {
    fill: "102E42", line: C.mint, titleColor: C.white, bodyColor: "B8DADD", accent: C.mint, bodySize: 12,
  });
  addFooter(slide, `${DATA.sdkRepos} SDK repositories + REST API specification monitoring • 12-hour scheduled cadence`, true);
}

// 14. Key metrics
{
  const slide = pptx.addSlide("LIGHT");
  addTitle(slide, "Key metrics at a glance", "Current state");
  const metrics = [
    [DATA.mdxDocs, "MDX pages", "docs-vnext"],
    [DATA.sections.length, "top-level sections", "information architecture"],
    [DATA.workflowCount, "agentic workflows", "top-level definitions"],
    [DATA.slashCommands, "slash commands", "operator entry points"],
    [DATA.onlyVnext, "vNext-only files", "agent-created or restructured"],
    [MERGED_DOCS_VNEXT_PRS.length, "verified merged PRs", "approved history result"],
    [EVAL.rows.find((row) => row.server === "docs-vnext/").average.toFixed(3), "vNext eval average", EVAL.date],
    [DATA.sdkRepos, "SDK repos", "plus REST API"],
  ];
  metrics.forEach(([value, label, sub], i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = 0.58 + col * 3.15;
    const y = 1.48 + row * 2.45;
    card(slide, x, y, 2.82, 1.95, label, sub, { accent: i % 3 === 0 ? C.mint : C.teal, bodySize: 10.5 });
    slide.addText(String(value), {
      x: x + 0.22, y: y + 0.78, w: 2.35, h: 0.62, fontSize: 31, bold: true, color: C.teal, align: "center", margin: 0,
    });
  });
  addFooter(slide, "Repository metrics are recomputed by this generator; historical and evaluation figures retain source labels.");
}

// 15. What's next
{
  const slide = pptx.addSlide("DARK");
  addTitle(slide, "What's next: turn weak signals into measurable gains", "Roadmap", true);
  const roadmap = [
    ["01", "Close the observability gap", "Use the -0.027 category delta to prioritize task-based tracing, evaluation, and monitoring journeys."],
    ["02", "Increase agentic PR merge yield", "Track detected signal → proposed change → merged outcome, not just workflow activity."],
    ["03", "Expand evaluation scenarios", "Add freshness, cross-page navigation, multi-step troubleshooting, and SDK migration tasks."],
    ["04", "Improve operational evidence", "Persist run duration, outcome, and lineage so chain performance is visible without manual reconstruction."],
  ];
  roadmap.forEach(([num, title, body], i) => {
    const y = 1.42 + i * 1.26;
    slide.addText(num, {
      x: 0.72, y, w: 0.72, h: 0.52, fontSize: 27, bold: true, color: C.mint, margin: 0,
    });
    slide.addText(title, {
      x: 1.62, y: y + 0.02, w: 3.85, h: 0.38, fontSize: 18, bold: true, color: C.white, margin: 0,
    });
    slide.addText(body, {
      x: 5.5, y: y + 0.01, w: 6.65, h: 0.7, fontSize: 12.5, color: "B8DADD", margin: 0,
    });
    if (i < roadmap.length - 1) {
      slide.addShape(pptx.ShapeType.line, {
        x: 1.62, y: y + 0.92, w: 10.55, h: 0, line: { color: "24475A", width: 1 },
      });
    }
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 3.15, y: 6.45, w: 7.05, h: 0.48, rectRadius: 0.1,
    fill: { color: C.teal }, line: { color: C.teal },
  });
  slide.addText("North star: better answers, delivered faster, with evidence.", {
    x: 3.2, y: 6.54, w: 6.95, h: 0.25, fontSize: 13, bold: true, color: C.white, align: "center", margin: 0,
  });
  addFooter(slide, "Foundry-Docs stakeholder overview", true);
}

pptx.writeFile({ fileName: OUTPUT });
