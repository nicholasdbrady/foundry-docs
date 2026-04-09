export const ModelCatalog = () => {
  const PAGE_SIZE = 50
  const [models, setModels] = useState([])
  const [publisherIcons, setPublisherIcons] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [activeFilters, setActiveFilters] = useState({})
  const [sortBy, setSortBy] = useState("newest")
  const [groupBy, setGroupBy] = useState("none")
  const [expandedModel, setExpandedModel] = useState(null)
  const [copiedId, setCopiedId] = useState(null)
  const [openDropdown, setOpenDropdown] = useState(null)
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)
  const [hfLoaded, setHfLoaded] = useState(false)
  const [hfLoading, setHfLoading] = useState(false)
  const [viewMode, setViewMode] = useState("cards")

  useEffect(() => {
    fetch("/static/data/models-core.json")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setModels(data.models || [])
        setPublisherIcons(data.publisherIcons || {})
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const loadHuggingFace = () => {
    if (hfLoaded || hfLoading) return
    setHfLoading(true)
    fetch("/static/data/models-huggingface.json")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setModels((prev) => [...prev, ...(data.models || [])])
        setHfLoaded(true)
        setHfLoading(false)
      })
      .catch(() => {
        setHfLoading(false)
      })
  }

  const DEPLOY_LABELS = {
    "aoai-deployment": "Azure OpenAI",
    "batch-enabled": "Batch",
    "maas-inference": "Serverless API",
    "maap-inference": "Managed Compute",
  }
  const TASK_LABELS = {
    "chat-completion": "Chat",
    responses: "Responses",
    embeddings: "Embeddings",
    "text-to-image": "Image Gen",
    "image-to-image": "Image Edit",
    "audio-generation": "Audio Gen",
    "speech-to-text": "Speech-to-Text",
    "text-to-speech": "Text-to-Speech",
    "video-generation": "Video Gen",
    "automatic-speech-recognition": "ASR",
  }
  const CAP_LABELS = {
    agentsV2: "Agents",
    agents: "Agents (v1)",
    reasoning: "Reasoning",
    streaming: "Streaming",
    "tool-calling": "Tool Calling",
    "fine-tuning": "Fine-tuning",
    assistants: "Assistants",
  }
  const SKU_LABELS = {
    GlobalStandard: "Global Standard",
    Standard: "Standard",
    DataZoneStandard: "Data Zone Standard",
    GlobalBatch: "Global Batch",
    DataZoneBatch: "Data Zone Batch",
    ProvisionedManaged: "Provisioned Managed",
    GlobalProvisionedManaged: "Global Provisioned Managed",
    DataZoneProvisionedManaged: "Data Zone Provisioned",
    DeveloperTier: "Developer Tier",
  }
  // Lucide Icons (ISC license) — uniform stroke-based, 24×24 viewBox
  // Source: lucide.dev — all icons use identical stroke width, linecap, linejoin
  const LI = ({ children, tip }) => (
    <svg className="shrink-0" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <title>{tip}</title>
      {children}
    </svg>
  )

  // ── Modality icons ──
  const MODALITY_ICON = {
    text: { tip: "Text", el: <><path d="M21 5H3" /><path d="M15 12H3" /><path d="M17 19H3" /></> },
    image: { tip: "Image", el: <><rect width="18" height="18" x="3" y="3" rx="2" ry="2" /><circle cx="9" cy="9" r="2" /><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" /></> },
    audio: { tip: "Audio", el: <><path d="M2 13a2 2 0 0 0 2-2V7a2 2 0 0 1 4 0v13a2 2 0 0 0 4 0V4a2 2 0 0 1 4 0v13a2 2 0 0 0 4 0v-4a2 2 0 0 1 2-2" /></> },
    video: { tip: "Video", el: <><path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5" /><rect x="2" y="6" width="14" height="12" rx="2" /></> },
    code: { tip: "Code", el: <><path d="m18 16 4-4-4-4" /><path d="m6 8-4 4 4 4" /><path d="m14.5 4-5 16" /></> },
  }

  // ── Task/endpoint icons ──
  const TASK_ICON = {
    "chat-completion": { tip: "Chat Completions", el: <><path d="M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z" /><path d="M7 11h10" /><path d="M7 15h6" /><path d="M7 7h8" /></> },
    responses: { tip: "Responses API", el: <><path d="M20 18v-2a4 4 0 0 0-4-4H4" /><path d="m9 17-5-5 5-5" /></> },
    embeddings: { tip: "Embeddings", el: <><rect width="18" height="18" x="3" y="3" rx="2" /><path d="M3 9h18" /><path d="M3 15h18" /><path d="M9 3v18" /><path d="M15 3v18" /></> },
    "text-to-image": { tip: "Image Generation", el: <><path d="M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z" /><path d="M20 2v4" /><path d="M22 4h-4" /><circle cx="4" cy="20" r="2" /></> },
    "text-generation": { tip: "Text Generation", el: <><path d="M21 5H3" /><path d="M15 12H3" /><path d="M17 19H3" /></> },
    "speech-to-text": { tip: "Speech-to-Text", el: <><path d="M12 19v3" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><rect x="9" y="2" width="6" height="13" rx="3" /></> },
    "text-to-speech": { tip: "Text-to-Speech", el: <><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z" /><path d="M16 9a5 5 0 0 1 0 6" /><path d="M19.364 18.364a9 9 0 0 0 0-12.728" /></> },
    "video-generation": { tip: "Video Generation", el: <><path d="m12.296 3.464 3.02 3.956" /><path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3z" /><path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><path d="m6.18 5.276 3.1 3.899" /></> },
    "audio-generation": { tip: "Audio Generation", el: <><path d="M2 13a2 2 0 0 0 2-2V7a2 2 0 0 1 4 0v13a2 2 0 0 0 4 0V4a2 2 0 0 1 4 0v13a2 2 0 0 0 4 0v-4a2 2 0 0 1 2-2" /></> },
  }

  // ── Capability icons ──
  const CAP_ICON = {
    reasoning: { tip: "Reasoning", el: <><path d="M12 18V5" /><path d="M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4" /><path d="M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5" /><path d="M17.997 5.125a4 4 0 0 1 2.526 5.77" /><path d="M18 18a4 4 0 0 0 2-7.464" /><path d="M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517" /><path d="M6 18a4 4 0 0 1-2-7.464" /><path d="M6.003 5.125a4 4 0 0 0-2.526 5.77" /></> },
    streaming: { tip: "Streaming", el: <><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" /></> },
    "tool-calling": { tip: "Tool Calling", el: <><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z" /></> },
    "fine-tuning": { tip: "Fine-tuning", el: <><path d="M10 5H3" /><path d="M12 19H3" /><path d="M14 3v4" /><path d="M16 17v4" /><path d="M21 12h-9" /><path d="M21 19h-5" /><path d="M21 5h-7" /><path d="M8 10v4" /><path d="M8 12H3" /></> },
    agentsV2: { tip: "Agents", el: <><path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" /></> },
    agents: { tip: "Agents (v1)", el: <><path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" /></> },
    assistants: { tip: "Assistants", el: <><path d="M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z" /><path d="M7 11h10" /><path d="M7 15h6" /><path d="M7 7h8" /></> },
  }

  // ── Tool icons (expanded view) ──
  const TOOL_ICON = {
    web_search: { tip: "Web Search", el: <><circle cx="12" cy="12" r="10" /><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" /><path d="M2 12h20" /></> },
    file_search: { tip: "File Search", el: <><path d="M10.7 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v4.1" /><path d="m21 21-1.9-1.9" /><circle cx="17" cy="17" r="3" /></> },
    code_interpreter: { tip: "Code Interpreter", el: <><path d="M12 19h8" /><path d="m4 17 6-6-6-6" /></> },
    mcp: { tip: "MCP", el: <><path d="M17 19a1 1 0 0 1-1-1v-2a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2a1 1 0 0 1-1 1z" /><path d="M17 21v-2" /><path d="M19 14V6.5a1 1 0 0 0-7 0v11a1 1 0 0 1-7 0V10" /><path d="M21 21v-2" /><path d="M3 5V3" /><path d="M4 10a2 2 0 0 1-2-2V6a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2a2 2 0 0 1-2 2z" /><path d="M7 5V3" /></> },
    browser_automation: { tip: "Computer Use", el: <><path d="m9 10 2 2 4-4" /><rect width="20" height="14" x="2" y="3" rx="2" /><path d="M12 17v4" /><path d="M8 21h8" /></> },
    function: { tip: "Functions", el: <><rect width="18" height="18" x="3" y="3" rx="2" ry="2" /><path d="M9 17c2 0 2.8-1 2.8-2.8V10c0-2 1-3.3 3.2-3" /><path d="M9 11.2h5.7" /></> },
    azure_ai_search: { tip: "Azure AI Search", el: <><path d="m21 21-4.34-4.34" /><circle cx="11" cy="11" r="8" /></> },
    bing_grounding: { tip: "Bing Grounding", el: <><path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z" /><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12" /><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17" /></> },
    bing_custom_search: { tip: "Bing Custom Search", el: <><path d="m21 21-4.34-4.34" /><circle cx="11" cy="11" r="8" /></> },
    sharepoint_grounding: { tip: "SharePoint", el: <><path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z" /><path d="M14 2v5a1 1 0 0 0 1 1h5" /><path d="M10 9H8" /><path d="M16 13H8" /><path d="M16 17H8" /></> },
    fabric_dataagent: { tip: "Fabric Data Agent", el: <><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5V19A9 3 0 0 0 21 19V5" /><path d="M3 12A9 3 0 0 0 21 12" /></> },
    openapi: { tip: "OpenAPI", el: <><path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1" /><path d="M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1" /></> },
    image_generation: { tip: "Image Generation", el: <><rect width="18" height="18" x="3" y="3" rx="2" ry="2" /><circle cx="9" cy="9" r="2" /><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" /></> },
    a2a_preview: { tip: "A2A", el: <><path d="M8 3 4 7l4 4" /><path d="M4 7h16" /><path d="m16 21 4-4-4-4" /><path d="M20 17H4" /></> },
    azure_function: { tip: "Azure Function", el: <><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" /></> },
  }

  const LIFECYCLE_LABELS = {
    "generally-available": "Generally Available",
    "preview": "Preview",
  }

  const facetConfig = [
    { key: "publisher", label: "Provider" },
    { key: "lifecycleStatus", label: "Lifecycle" },
    { key: "tasks", label: "Task" },
    { key: "capabilities", label: "Capability" },
    { key: "deploymentTypes", label: "Deployment" },
    { key: "_skuTypes", label: "SKU Type", derived: true },
    { key: "_regions", label: "Region", derived: true },
  ]

  // Helper to extract derived facet values from nested regions dict
  const getModelFacetValues = (m, key) => {
    if (key === "_skuTypes") return Object.keys(m.regions || {})
    if (key === "_regions") {
      const allRegions = new Set()
      for (const regions of Object.values(m.regions || {})) {
        for (const r of regions) allRegions.add(r)
      }
      return [...allRegions]
    }
    const val = m[key]
    return Array.isArray(val) ? val : val ? [val] : []
  }

  const formatLabel = (key, value) => {
    if (key === "deploymentTypes") return DEPLOY_LABELS[value] || value
    if (key === "tasks") return TASK_LABELS[value] || value
    if (key === "capabilities") return CAP_LABELS[value] || value
    if (key === "_skuTypes") return SKU_LABELS[value] || value
    if (key === "lifecycleStatus") return LIFECYCLE_LABELS[value] || value
    return value
  }

  const formatNumber = (n) => {
    if (!n) return null
    if (n >= 1000000) return `${(n / 1000000).toFixed(n % 1000000 === 0 ? 0 : 1)}M`
    if (n >= 1000) return `${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}K`
    return String(n)
  }

  const filteredModels = useMemo(() => {
    let result = models
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        (m) =>
          m.displayName?.toLowerCase().includes(q) ||
          m.publisher?.toLowerCase().includes(q) ||
          m.summary?.toLowerCase().includes(q) ||
          m.id?.toLowerCase().includes(q) ||
          m.keywords?.some((k) => k.toLowerCase().includes(q))
      )
    }
    for (const [key, values] of Object.entries(activeFilters)) {
      if (values && values.length > 0) {
        result = result.filter((m) => {
          const mVals = getModelFacetValues(m, key)
          return values.some((v) => mVals.includes(v))
        })
      }
    }
    result = [...result].sort((a, b) => {
      if (sortBy === "newest") {
        const da = Date.parse(a.createdAt) || 0
        const db = Date.parse(b.createdAt) || 0
        if (da !== db) return db - da
        return (a.displayName || "").localeCompare(b.displayName || "")
      }
      if (sortBy === "name") return (a.displayName || "").localeCompare(b.displayName || "")
      if (sortBy === "context") return (b.contextWindow || 0) - (a.contextWindow || 0)
      if (sortBy === "publisher") return (a.publisher || "").localeCompare(b.publisher || "")
      return 0
    })
    return result
  }, [models, searchQuery, activeFilters, sortBy])

  // Reset pagination when filters, search, or sort change
  useEffect(() => {
    setVisibleCount(PAGE_SIZE)
  }, [searchQuery, activeFilters, sortBy, groupBy])

  // Facet counts computed from filtered results (excluding the facet's own filter)
  const facetCounts = useMemo(() => {
    const counts = {}
    for (const f of facetConfig) {
      const otherFilters = { ...activeFilters }
      delete otherFilters[f.key]
      let subset = models
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        subset = subset.filter(
          (m) =>
            m.displayName?.toLowerCase().includes(q) ||
            m.publisher?.toLowerCase().includes(q) ||
            m.summary?.toLowerCase().includes(q) ||
            m.id?.toLowerCase().includes(q) ||
            m.keywords?.some((k) => k.toLowerCase().includes(q))
        )
      }
      for (const [key, values] of Object.entries(otherFilters)) {
        if (values && values.length > 0) {
          subset = subset.filter((m) => {
            const mVals = getModelFacetValues(m, key)
            return values.some((v) => mVals.includes(v))
          })
        }
      }
      const map = {}
      for (const m of subset) {
        const vals = getModelFacetValues(m, f.key)
        for (const v of vals) {
          if (v) map[v] = (map[v] || 0) + 1
        }
      }
      counts[f.key] = Object.entries(map)
        .sort((a, b) => b[1] - a[1])
        .map(([value, count]) => ({ value, count }))
    }
    return counts
  }, [models, searchQuery, activeFilters])

  const groupedModels = useMemo(() => {
    const paginated = filteredModels.slice(0, visibleCount)
    if (groupBy === "none") return [{ label: null, models: paginated }]
    const groups = {}
    for (const m of paginated) {
      const key = m.publisher || "Other"
      if (!groups[key]) groups[key] = []
      groups[key].push(m)
    }
    return Object.entries(groups)
      .sort((a, b) => b[1].length - a[1].length)
      .map(([label, models]) => ({ label, models }))
  }, [filteredModels, groupBy, visibleCount])

  const toggleFilter = (facetKey, value) => {
    setActiveFilters((prev) => {
      const current = prev[facetKey] || []
      const next = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value]
      return { ...prev, [facetKey]: next }
    })
  }

  const clearFilters = () => {
    setActiveFilters({})
    setSearchQuery("")
  }

  const copyModelId = (e, id) => {
    e.stopPropagation()
    navigator.clipboard.writeText(id).then(() => {
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 1500)
    }).catch(() => {})
  }

  const hasActiveFilters =
    searchQuery || Object.values(activeFilters).some((v) => v && v.length > 0)

  const modelKey = (m) => `${m.publisher}-${m.id}`

  if (loading) {
    return (
      <div className="not-prose">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mt-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 p-5 animate-pulse">
              <div className="h-4 bg-zinc-200 dark:bg-zinc-700 rounded w-3/4 mb-3" />
              <div className="h-3 bg-zinc-200 dark:bg-zinc-700 rounded w-1/2 mb-4" />
              <div className="h-3 bg-zinc-200 dark:bg-zinc-700 rounded w-full mb-2" />
              <div className="h-3 bg-zinc-200 dark:bg-zinc-700 rounded w-5/6" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="not-prose rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30 p-5">
        <p className="text-red-700 dark:text-red-400 text-sm">Failed to load model catalog: {error}</p>
      </div>
    )
  }

  return (
    <div className="not-prose px-6 lg:px-10 xl:px-16 pb-10">
      {/* Search + Controls bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search models…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 pl-9 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Search models"
          />
          <svg className="absolute left-3 top-2.5 h-4 w-4 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <div className="flex gap-2">
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 text-xs"
            aria-label="Sort models">
            <option value="newest">Sort: Newest</option>
            <option value="name">Sort: Name</option>
            <option value="publisher">Sort: Provider</option>
            <option value="context">Sort: Context Window</option>
          </select>
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}
            className="px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 text-xs"
            aria-label="Group models">
            <option value="none">Group: None</option>
            <option value="publisher">Group: Provider</option>
          </select>
          {/* View toggle */}
          <div className="inline-flex rounded-lg border border-zinc-200 dark:border-zinc-700 overflow-hidden" role="radiogroup" aria-label="View mode">
            <button
              onClick={() => setViewMode("cards")}
              aria-label="Card view"
              aria-checked={viewMode === "cards"}
              role="radio"
              className={`px-2.5 py-2 transition-colors ${viewMode === "cards" ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100" : "bg-white dark:bg-zinc-900 text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300"}`}
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode("list")}
              aria-label="List view"
              aria-checked={viewMode === "list"}
              role="radio"
              className={`px-2.5 py-2 border-l border-zinc-200 dark:border-zinc-700 transition-colors ${viewMode === "list" ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100" : "bg-white dark:bg-zinc-900 text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300"}`}
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <line x1="3" y1="5" x2="21" y2="5" />
                <line x1="3" y1="10" x2="21" y2="10" />
                <line x1="3" y1="15" x2="21" y2="15" />
                <line x1="3" y1="20" x2="21" y2="20" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Horizontal filter bar */}
      <div className="flex flex-wrap gap-2 mb-4">
        {facetConfig.map((facet) => {
          const isOpen = openDropdown === facet.key
          const activeVals = activeFilters[facet.key] || []
          const items = facetCounts[facet.key] || []
          return (
            <div key={facet.key} className="relative">
              <button
                onClick={() => setOpenDropdown(isOpen ? null : facet.key)}
                aria-label={`Filter by ${facet.label}${activeVals.length > 0 ? `, ${activeVals.length} selected` : ""}`}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                  activeVals.length > 0
                    ? "bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300"
                    : "bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800"
                }`}
              >
                {facet.label}
                {activeVals.length > 0 && (
                  <span className="bg-blue-500 text-white text-[10px] rounded-full px-1.5 py-0.5 leading-none">{activeVals.length}</span>
                )}
                <svg className={`h-3 w-3 transition-transform ${isOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {isOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setOpenDropdown(null)} />
                  <div className="absolute top-full left-0 mt-1 z-20 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg shadow-lg p-2 min-w-[200px] max-h-[300px] overflow-y-auto">
                    {items.map(({ value, count }) => {
                      const isActive = activeVals.includes(value)
                      return (
                        <button key={value} onClick={() => toggleFilter(facet.key, value)}
                          aria-label={`${isActive ? "Remove" : "Add"} ${formatLabel(facet.key, value)} filter`}
                          className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors text-left ${
                            isActive
                              ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium"
                              : "text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                          }`}>
                          <span className="truncate">{formatLabel(facet.key, value)}</span>
                          <span className="text-zinc-400 dark:text-zinc-500 ml-3 tabular-nums">{count}</span>
                        </button>
                      )
                    })}
                  </div>
                </>
              )}
            </div>
          )
        })}
        {hasActiveFilters && (
          <button onClick={clearFilters}
            aria-label="Clear all filters"
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors">
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Clear filters
          </button>
        )}
      </div>

      {/* Active filter pills */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {Object.entries(activeFilters).map(([key, values]) =>
            (values || []).map((v) => (
              <button key={`${key}-${v}`} onClick={() => toggleFilter(key, v)}
                aria-label={`Remove ${formatLabel(key, v)} filter`}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800/50 transition-colors">
                {formatLabel(key, v)}
                <svg className="h-2.5 w-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            ))
          )}
        </div>
      )}

      {/* Results count + HuggingFace toggle */}
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs text-zinc-500 dark:text-zinc-400">
          Showing {Math.min(visibleCount, filteredModels.length)} of {filteredModels.length} model{filteredModels.length !== 1 ? "s" : ""}
          {hasActiveFilters ? " matching filters" : ""}
        </div>
        {!hfLoaded && (
          <button
            onClick={loadHuggingFace}
            disabled={hfLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50"
          >
            {hfLoading ? (
              <>
                <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Loading…
              </>
            ) : (
              <>
                <span>🤗</span>
                Include Hugging Face models (10,000+)
              </>
            )}
          </button>
        )}
        {hfLoaded && (
          <span className="text-xs text-green-600 dark:text-green-400">🤗 Hugging Face models loaded</span>
        )}
      </div>

      {/* Empty state */}
      {filteredModels.length === 0 ? (
        <div className="text-center py-16 text-zinc-500 dark:text-zinc-400">
          <p className="text-sm mb-2">No models match your filters.</p>
          <button onClick={clearFilters} className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
            Clear all filters
          </button>
        </div>
      ) : (
        /* Model cards or list — grouped or flat */
        groupedModels.map((group) => (
          <div key={group.label || "all"} className="mb-6">
            {group.label && (
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-3 pb-2 border-b border-zinc-200 dark:border-zinc-800">
                {group.label}
                <span className="ml-2 text-xs font-normal text-zinc-400">{group.models.length}</span>
              </h3>
            )}

            {viewMode === "list" ? (
              /* ── List view ── */
              <div className="border border-zinc-200 dark:border-zinc-700 rounded-xl overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-zinc-50 dark:bg-zinc-800/60 text-left text-zinc-500 dark:text-zinc-400">
                      <th className="px-4 py-2.5 font-medium">Model</th>
                      <th className="px-4 py-2.5 font-medium hidden sm:table-cell">Provider</th>
                      <th className="px-4 py-2.5 font-medium hidden md:table-cell">Task</th>
                      <th className="px-4 py-2.5 font-medium hidden lg:table-cell">Context</th>
                      <th className="px-4 py-2.5 font-medium hidden lg:table-cell">Deployment</th>
                      <th className="px-4 py-2.5 font-medium w-16">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                    {group.models.map((m) => (
                      <tr key={modelKey(m)}
                        className="bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 cursor-pointer transition-colors"
                        onClick={() => setExpandedModel(expandedModel === modelKey(m) ? null : modelKey(m))}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            {publisherIcons[m.publisher] && (
                              <img src={`data:image/svg+xml;base64,${publisherIcons[m.publisher]}`} alt="" className="w-5 h-5 rounded bg-zinc-100 dark:bg-zinc-800 p-0.5 shrink-0" />
                            )}
                            <div className="min-w-0">
                              <div className="font-medium text-zinc-900 dark:text-zinc-100 truncate">{m.displayName}</div>
                              <code className="text-[10px] text-zinc-400 dark:text-zinc-500 font-mono">{m.id}</code>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400 hidden sm:table-cell">{m.publisher}</td>
                        <td className="px-4 py-3 hidden md:table-cell">
                          <div className="flex flex-wrap gap-1">
                            {(m.tasks || []).slice(0, 2).map((t) => (
                              <span key={t} className="px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-[10px] font-medium">
                                {TASK_LABELS[t] || t}
                              </span>
                            ))}
                            {(m.tasks || []).length > 2 && <span className="text-zinc-400 text-[10px]">+{m.tasks.length - 2}</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400 hidden lg:table-cell tabular-nums">
                          {m.contextWindow ? formatNumber(m.contextWindow) : "—"}
                        </td>
                        <td className="px-4 py-3 hidden lg:table-cell">
                          <div className="flex flex-wrap gap-1">
                            {(m.deploymentTypes || []).slice(0, 2).map((d) => (
                              <span key={d} className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 text-[10px]">
                                {DEPLOY_LABELS[d] || d}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {m.lifecycleStatus === "preview" && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">Preview</span>
                          )}
                          {m.lifecycleStatus === "generally-available" && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300">GA</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              /* ── Card view ── */
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {group.models.map((m) => {
                const isExpanded = expandedModel === modelKey(m)

                return (
                  <div key={modelKey(m)}
                    className={`rounded-xl border bg-white dark:bg-zinc-900 transition-all duration-200 cursor-pointer ${
                      isExpanded
                        ? "border-blue-300 dark:border-blue-700 shadow-sm"
                        : "border-zinc-200 dark:border-zinc-700 hover:border-zinc-300 dark:hover:border-zinc-600 hover:shadow-sm"
                    }`}
                    onClick={() => setExpandedModel(isExpanded ? null : modelKey(m))}
                    role="button" tabIndex={0}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setExpandedModel(isExpanded ? null : modelKey(m)) } }}
                    aria-expanded={isExpanded}>
                    <div className="p-4 flex flex-col" style={{minHeight: "14rem"}}>
                      {/* Header row with icon */}
                      <div className="flex items-start gap-3 mb-2">
                        {publisherIcons[m.publisher] && (
                          <img
                            src={`data:image/svg+xml;base64,${publisherIcons[m.publisher]}`}
                            alt={`${m.publisher} icon`}
                            className="shrink-0 w-8 h-8 mt-0.5 rounded-lg bg-zinc-100 dark:bg-zinc-800 p-1.5"
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 leading-tight line-clamp-2" style={{minHeight: "1.25rem"}}>
                              {m.displayName}
                            </h3>
                            <div className="flex items-center gap-1.5 shrink-0">
                              {m.lifecycleStatus === "preview" && (
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">Preview</span>
                              )}
                              {m.lifecycleStatus === "generally-available" && (
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300">GA</span>
                              )}
                              <svg className={`h-4 w-4 text-zinc-400 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
                                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>
                          </div>
                          <div className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                            {m.publisher} · v{m.latestVersion}
                          </div>
                        </div>
                      </div>

                      {/* Model ID + copy */}
                      <div className="flex items-center gap-2 mb-2">
                        <code className="text-[10px] text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded font-mono truncate">
                          {m.id}
                        </code>
                        <button onClick={(e) => copyModelId(e, m.id)} aria-label={`Copy model ID ${m.id}`} title="Copy model ID"
                          className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors shrink-0">
                          {copiedId === m.id ? (
                            <svg className="h-3.5 w-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          ) : (
                            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          )}
                        </button>
                      </div>

                      {/* Description — flex-1 to fill remaining space */}
                      <div className="flex-1 mb-2" style={{minHeight: "2.5rem"}}>
                        <p className={`text-xs text-zinc-500 dark:text-zinc-400 ${isExpanded ? "max-h-24 overflow-y-auto" : "line-clamp-2"}`} style={{lineHeight: "1.4"}}>
                          {m.summary || "\u00A0"}
                        </p>
                      </div>

                      {/* Specs row — context + output */}
                      <div className="flex items-center gap-2 text-[11px] text-zinc-500 dark:text-zinc-400 mb-2 tabular-nums" style={{minHeight: "1rem"}}>
                        {m.contextWindow && <span>{formatNumber(m.contextWindow)} ctx</span>}
                        {m.contextWindow && m.maxOutputTokens && <span className="text-zinc-300 dark:text-zinc-600">·</span>}
                        {m.maxOutputTokens && <span>{formatNumber(m.maxOutputTokens)} out</span>}
                        {m.license && m.license !== "custom" && (
                          <>
                            {(m.contextWindow || m.maxOutputTokens) && <span className="text-zinc-300 dark:text-zinc-600">·</span>}
                            <span className="uppercase tracking-wider text-[10px]">{m.license}</span>
                          </>
                        )}
                      </div>

                      {/* Icon strip — modalities, tasks, capabilities */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        {m.inputModalities?.map((mod) => {
                          const mi = MODALITY_ICON[mod]
                          return mi ? (
                            <span key={`in-${mod}`} title={mi.tip}
                              className="inline-flex items-center justify-center w-5 h-5 text-zinc-500 dark:text-zinc-400">
                              <LI tip={mi.tip}>{mi.el}</LI>
                            </span>
                          ) : null
                        })}
                        {m.outputModalities?.filter((mod) => !m.inputModalities?.includes(mod)).map((mod) => {
                          const mi = MODALITY_ICON[mod]
                          return mi ? (
                            <span key={`out-${mod}`} title={`Output: ${mi.tip}`}
                              className="inline-flex items-center justify-center w-5 h-5 text-zinc-500 dark:text-zinc-400">
                              <LI tip={mi.tip}>{mi.el}</LI>
                            </span>
                          ) : null
                        })}
                        {(m.inputModalities?.length > 0 || m.outputModalities?.length > 0) && (m.tasks?.length > 0 || m.capabilities?.length > 0) && (
                          <span className="w-px h-3.5 bg-zinc-300 dark:bg-zinc-600 mx-0.5" />
                        )}
                        {(m.tasks || []).slice(0, 3).map((t) => {
                          const ti = TASK_ICON[t]
                          return ti ? (
                            <span key={t} title={ti.tip}
                              className="inline-flex items-center justify-center w-5 h-5 text-zinc-500 dark:text-zinc-400">
                              <LI tip={ti.tip}>{ti.el}</LI>
                            </span>
                          ) : null
                        })}
                        {(m.tasks?.length > 0 && m.capabilities?.length > 0) && (
                          <span className="w-px h-3.5 bg-zinc-300 dark:bg-zinc-600 mx-0.5" />
                        )}
                        {(m.capabilities || []).slice(0, 4).map((c) => {
                          const ci = CAP_ICON[c]
                          return ci ? (
                            <span key={c} title={ci.tip}
                              className="inline-flex items-center justify-center w-5 h-5 text-zinc-500 dark:text-zinc-400">
                              <LI tip={ci.tip}>{ci.el}</LI>
                            </span>
                          ) : null
                        })}
                      </div>
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="px-4 pb-4 pt-0">
                        <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800">
                          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                            {m.deploymentTypes?.length > 0 && (
                              <div>
                                <span className="text-zinc-400 dark:text-zinc-500 block mb-0.5">Deployment</span>
                                <span className="text-zinc-700 dark:text-zinc-300">{m.deploymentTypes.map((d) => DEPLOY_LABELS[d] || d).join(", ")}</span>
                              </div>
                            )}
                            {m.inputModalities?.length > 0 && (
                              <div>
                                <span className="text-zinc-400 dark:text-zinc-500 block mb-0.5">Input</span>
                                <span className="text-zinc-700 dark:text-zinc-300">{m.inputModalities.join(", ")}</span>
                              </div>
                            )}
                            {m.outputModalities?.length > 0 && (
                              <div>
                                <span className="text-zinc-400 dark:text-zinc-500 block mb-0.5">Output</span>
                                <span className="text-zinc-700 dark:text-zinc-300">{m.outputModalities.join(", ")}</span>
                              </div>
                            )}
                            {m.trainingDataDate && (
                              <div>
                                <span className="text-zinc-400 dark:text-zinc-500 block mb-0.5">Training data</span>
                                <span className="text-zinc-700 dark:text-zinc-300">{m.trainingDataDate}</span>
                              </div>
                            )}
                            {m.languages?.length > 0 && m.languages[0] && (
                              <div>
                                <span className="text-zinc-400 dark:text-zinc-500 block mb-0.5">Languages</span>
                                <span className="text-zinc-700 dark:text-zinc-300">{m.languages.join(", ")}</span>
                              </div>
                            )}
                            {m.versions?.length > 1 && (
                              <div>
                                <span className="text-zinc-400 dark:text-zinc-500 block mb-0.5">Versions</span>
                                <span className="text-zinc-700 dark:text-zinc-300">{m.versions.join(", ")}</span>
                              </div>
                            )}
                          </div>
                          {m.toolsSupported?.length > 0 && (
                            <div className="mt-3">
                              <span className="text-xs text-zinc-400 dark:text-zinc-500 block mb-1">Tools</span>
                              <div className="flex flex-wrap gap-1">
                                {m.toolsSupported.map((t) => {
                                  const ti = TOOL_ICON[t]
                                  return (
                                    <span key={t} title={ti?.tip || t}
                                      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                                      {ti && <LI tip={ti.tip}>{ti.el}</LI>}
                                      {ti?.tip || t}
                                    </span>
                                  )
                                })}
                              </div>
                            </div>
                          )}
                          {m.regions && Object.keys(m.regions).length > 0 && (
                            <div className="mt-3">
                              <span className="text-xs text-zinc-400 dark:text-zinc-500 block mb-1">Region availability</span>
                              <div className="flex flex-wrap gap-1">
                                {Object.entries(m.regions).map(([sku, regions]) => (
                                  <span key={sku} className="px-1.5 py-0.5 rounded text-[11px] bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                                    {SKU_LABELS[sku] || sku}: {regions.includes("all") ? "All regions" : `${regions.length} region${regions.length !== 1 ? "s" : ""}`}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {m.pricingLink && (
                            <a href={m.pricingLink} target="_blank" rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 mt-3 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-800/40 transition-colors"
                              onClick={(e) => e.stopPropagation()}>
                              View pricing
                              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </a>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            )}
          </div>
        ))
      )}

      {/* Show More button */}
      {filteredModels.length > visibleCount && (
        <div className="flex justify-center mt-6 mb-4">
          <button
            onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
            className="px-6 py-2.5 rounded-lg text-sm font-medium border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
          >
            Show more ({Math.min(PAGE_SIZE, filteredModels.length - visibleCount)} of {filteredModels.length - visibleCount} remaining)
          </button>
        </div>
      )}
    </div>
  )
}
