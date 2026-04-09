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
  const MODALITY_ICONS = { text: "Aa", image: "◩", audio: "♪", video: "▶" }

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
                const allBadges = [
                  ...(m.tasks || []).map((t) => ({ label: TASK_LABELS[t] || t, color: "emerald" })),
                  ...(m.capabilities || []).map((c) => ({ label: CAP_LABELS[c] || c, color: "purple" })),
                ]
                const visibleBadges = allBadges.slice(0, 4)
                const overflowCount = allBadges.length - 4

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
                    <div className="p-5">
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
                            <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 leading-tight">
                              {m.displayName}
                            </h3>
                            <div className="flex items-center gap-1.5 shrink-0">
                              {m.lifecycleStatus === "preview" && (
                                <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">Preview</span>
                              )}
                              {m.lifecycleStatus === "generally-available" && (
                                <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300">GA</span>
                              )}
                              <svg className={`h-4 w-4 text-zinc-400 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
                                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>
                          </div>
                          <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                            {m.publisher} · v{m.latestVersion}
                          </div>
                        </div>
                      </div>

                      {/* Model ID + copy */}
                      <div className="flex items-center gap-2 mb-3">
                        <code className="text-[11px] text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded font-mono">
                          {m.id}
                        </code>
                        <button onClick={(e) => copyModelId(e, m.id)} aria-label={`Copy model ID ${m.id}`} title="Copy model ID"
                          className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
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

                      {/* Summary */}
                      <p className="text-xs text-zinc-600 dark:text-zinc-400 line-clamp-2 mb-3 min-h-[2rem]">
                        {m.summary || "No description available."}
                      </p>

                      {/* Specs row */}
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500 dark:text-zinc-400 mb-2.5">
                        {m.contextWindow && <span>{formatNumber(m.contextWindow)} context</span>}
                        {m.contextWindow && m.maxOutputTokens && <span className="text-zinc-300 dark:text-zinc-600">·</span>}
                        {m.maxOutputTokens && <span>{formatNumber(m.maxOutputTokens)} output</span>}
                        {(m.contextWindow || m.maxOutputTokens) && m.inputModalities?.length > 0 && <span className="text-zinc-300 dark:text-zinc-600">·</span>}
                        {m.inputModalities?.map((mod) => (
                          <span key={mod} className="inline-flex items-center gap-0.5" title={`Input: ${mod}`}>
                            <span className="text-[10px] font-mono text-zinc-400">{MODALITY_ICONS[mod] || mod}</span>
                          </span>
                        ))}
                        {m.license && m.license !== "custom" && (
                          <>
                            <span className="text-zinc-300 dark:text-zinc-600">·</span>
                            <span className="uppercase tracking-wider text-[10px]">{m.license}</span>
                          </>
                        )}
                      </div>

                      {/* Badges */}
                      <div className="flex flex-wrap gap-1">
                        {visibleBadges.map((b) => (
                          <span key={b.label}
                            className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                              b.color === "emerald"
                                ? "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                                : "bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300"
                            }`}>
                            {b.label}
                          </span>
                        ))}
                        {overflowCount > 0 && (
                          <span className="px-1.5 py-0.5 rounded text-xs text-zinc-400 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-800">
                            +{overflowCount}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="px-5 pb-5 pt-0">
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
                              <span className="text-xs text-zinc-400 dark:text-zinc-500 block mb-1">Supported tools</span>
                              <div className="flex flex-wrap gap-1">
                                {m.toolsSupported.map((t) => (
                                  <span key={t} className="px-1.5 py-0.5 rounded text-[11px] bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">{t}</span>
                                ))}
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
