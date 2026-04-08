export const ModelCatalog = () => {
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [activeFilters, setActiveFilters] = useState({})
  const [sortBy, setSortBy] = useState("name")
  const [expandedModel, setExpandedModel] = useState(null)

  useEffect(() => {
    fetch("/static/data/models.json")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setModels(data.models || [])
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const facetConfig = useMemo(
    () => [
      { key: "publisher", label: "Provider" },
      { key: "tasks", label: "Task" },
      { key: "capabilities", label: "Capability" },
      { key: "deploymentTypes", label: "Deployment" },
    ],
    []
  )

  const facetCounts = useMemo(() => {
    const counts = {}
    for (const f of facetConfig) {
      const map = {}
      for (const m of models) {
        const vals = Array.isArray(m[f.key]) ? m[f.key] : [m[f.key]]
        for (const v of vals) {
          if (v) map[v] = (map[v] || 0) + 1
        }
      }
      counts[f.key] = Object.entries(map)
        .sort((a, b) => b[1] - a[1])
        .map(([value, count]) => ({ value, count }))
    }
    return counts
  }, [models, facetConfig])

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
          const mVal = m[key]
          if (Array.isArray(mVal)) {
            return values.some((v) => mVal.includes(v))
          }
          return values.includes(mVal)
        })
      }
    }

    result = [...result].sort((a, b) => {
      if (sortBy === "name")
        return (a.displayName || "").localeCompare(b.displayName || "")
      if (sortBy === "context")
        return (b.contextWindow || 0) - (a.contextWindow || 0)
      if (sortBy === "publisher")
        return (a.publisher || "").localeCompare(b.publisher || "")
      return 0
    })

    return result
  }, [models, searchQuery, activeFilters, sortBy])

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

  const hasActiveFilters =
    searchQuery ||
    Object.values(activeFilters).some((v) => v && v.length > 0)

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

  const formatLabel = (key, value) => {
    if (key === "deploymentTypes") return DEPLOY_LABELS[value] || value
    if (key === "tasks") return TASK_LABELS[value] || value
    if (key === "capabilities") return CAP_LABELS[value] || value
    return value
  }

  const formatNumber = (n) => {
    if (!n) return "—"
    if (n >= 1000000) return `${(n / 1000000).toFixed(n % 1000000 === 0 ? 0 : 1)}M`
    if (n >= 1000) return `${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}K`
    return String(n)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-zinc-500 dark:text-zinc-400 text-sm">
          Loading model catalog…
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30 p-4">
        <p className="text-red-700 dark:text-red-400 text-sm">
          Failed to load model catalog: {error}
        </p>
      </div>
    )
  }

  return (
    <div className="not-prose">
      {/* Search + Sort bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search models by name, provider, or keyword…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2.5 pl-10 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            aria-label="Search models"
          />
          <svg
            className="absolute left-3 top-3 h-4 w-4 text-zinc-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 text-sm"
          aria-label="Sort models"
        >
          <option value="name">Sort: Name</option>
          <option value="publisher">Sort: Provider</option>
          <option value="context">Sort: Context Window</option>
        </select>
      </div>

      {/* Active filter pills + clear */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2 mb-4 items-center">
          {Object.entries(activeFilters).map(([key, values]) =>
            (values || []).map((v) => (
              <button
                key={`${key}-${v}`}
                onClick={() => toggleFilter(key, v)}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800/50 transition-colors"
              >
                {formatLabel(key, v)}
                <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            ))
          )}
          <button
            onClick={clearFilters}
            className="text-xs text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 underline"
          >
            Clear all
          </button>
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Faceted sidebar */}
        <div className="lg:w-56 shrink-0 space-y-5">
          {facetConfig.map((facet) => (
            <div key={facet.key}>
              <h4 className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider mb-2">
                {facet.label}
              </h4>
              <div className="space-y-1">
                {(facetCounts[facet.key] || []).slice(0, 12).map(({ value, count }) => {
                  const isActive = (activeFilters[facet.key] || []).includes(value)
                  return (
                    <button
                      key={value}
                      onClick={() => toggleFilter(facet.key, value)}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors text-left ${
                        isActive
                          ? "bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 font-medium"
                          : "text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                      }`}
                      aria-pressed={isActive}
                    >
                      <span className="truncate">{formatLabel(facet.key, value)}</span>
                      <span className="text-zinc-400 dark:text-zinc-500 ml-2 tabular-nums">
                        {count}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Model cards grid */}
        <div className="flex-1 min-w-0">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-3">
            {filteredModels.length} model{filteredModels.length !== 1 ? "s" : ""}
            {hasActiveFilters ? " matching filters" : ""}
          </div>

          {filteredModels.length === 0 ? (
            <div className="text-center py-12 text-zinc-500 dark:text-zinc-400">
              <p className="text-sm">No models match your filters.</p>
              <button
                onClick={clearFilters}
                className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Clear all filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filteredModels.map((m) => (
                <div
                  key={`${m.publisher}-${m.id}`}
                  className="rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-4 hover:border-zinc-300 dark:hover:border-zinc-600 transition-colors cursor-pointer"
                  onClick={() =>
                    setExpandedModel(
                      expandedModel === `${m.publisher}-${m.id}`
                        ? null
                        : `${m.publisher}-${m.id}`
                    )
                  }
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault()
                      setExpandedModel(
                        expandedModel === `${m.publisher}-${m.id}`
                          ? null
                          : `${m.publisher}-${m.id}`
                      )
                    }
                  }}
                  aria-expanded={expandedModel === `${m.publisher}-${m.id}`}
                >
                  {/* Card header */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                        {m.displayName}
                      </h3>
                      <p className="text-xs text-zinc-500 dark:text-zinc-400">
                        {m.publisher} · v{m.latestVersion}
                      </p>
                    </div>
                    {m.isPreview && (
                      <span className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">
                        Preview
                      </span>
                    )}
                  </div>

                  {/* Summary */}
                  <p className="text-xs text-zinc-600 dark:text-zinc-400 line-clamp-2 mb-3">
                    {m.summary || "No description available."}
                  </p>

                  {/* Spec row */}
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-zinc-500 dark:text-zinc-400 mb-2">
                    {m.contextWindow && (
                      <span title="Context window">
                        📐 {formatNumber(m.contextWindow)} ctx
                      </span>
                    )}
                    {m.maxOutputTokens && (
                      <span title="Max output tokens">
                        📝 {formatNumber(m.maxOutputTokens)} out
                      </span>
                    )}
                    {m.versions && m.versions.length > 1 && (
                      <span title="Available versions">
                        📦 {m.versions.length} versions
                      </span>
                    )}
                  </div>

                  {/* Capability tags */}
                  <div className="flex flex-wrap gap-1">
                    {m.tasks?.slice(0, 3).map((t) => (
                      <span
                        key={t}
                        className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                      >
                        {TASK_LABELS[t] || t}
                      </span>
                    ))}
                    {m.capabilities?.slice(0, 3).map((c) => (
                      <span
                        key={c}
                        className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300"
                      >
                        {CAP_LABELS[c] || c}
                      </span>
                    ))}
                  </div>

                  {/* Expanded details */}
                  {expandedModel === `${m.publisher}-${m.id}` && (
                    <div className="mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800 space-y-2">
                      {m.deploymentTypes?.length > 0 && (
                        <div className="text-xs">
                          <span className="text-zinc-500 dark:text-zinc-400 font-medium">
                            Deployment:{" "}
                          </span>
                          <span className="text-zinc-700 dark:text-zinc-300">
                            {m.deploymentTypes
                              .map((d) => DEPLOY_LABELS[d] || d)
                              .join(", ")}
                          </span>
                        </div>
                      )}
                      {m.inputModalities?.length > 0 && (
                        <div className="text-xs">
                          <span className="text-zinc-500 dark:text-zinc-400 font-medium">
                            Input:{" "}
                          </span>
                          <span className="text-zinc-700 dark:text-zinc-300">
                            {m.inputModalities.join(", ")}
                          </span>
                        </div>
                      )}
                      {m.outputModalities?.length > 0 && (
                        <div className="text-xs">
                          <span className="text-zinc-500 dark:text-zinc-400 font-medium">
                            Output:{" "}
                          </span>
                          <span className="text-zinc-700 dark:text-zinc-300">
                            {m.outputModalities.join(", ")}
                          </span>
                        </div>
                      )}
                      {m.toolsSupported?.length > 0 && (
                        <div className="text-xs">
                          <span className="text-zinc-500 dark:text-zinc-400 font-medium">
                            Tools:{" "}
                          </span>
                          <span className="text-zinc-700 dark:text-zinc-300">
                            {m.toolsSupported.slice(0, 8).join(", ")}
                            {m.toolsSupported.length > 8 &&
                              ` +${m.toolsSupported.length - 8} more`}
                          </span>
                        </div>
                      )}
                      {m.regions && Object.keys(m.regions).length > 0 && (
                        <div className="text-xs">
                          <span className="text-zinc-500 dark:text-zinc-400 font-medium">
                            Regions:{" "}
                          </span>
                          <span className="text-zinc-700 dark:text-zinc-300">
                            {Object.entries(m.regions)
                              .map(
                                ([sku, regions]) =>
                                  `${sku} (${regions.length} regions)`
                              )
                              .join(", ")}
                          </span>
                        </div>
                      )}
                      {m.pricingLink && (
                        <a
                          href={m.pricingLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline mt-1"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View pricing →
                        </a>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
