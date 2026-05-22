export const ZonePivot = ({ group, options = [], defaultValue, label = "Choose an experience" }) => {
  const values = options.map((option) => option.id)
  const optionKey = options.map((option) => `${option.id}:${option.title}`).join("|")
  const [activePivot, setActivePivot] = useState(defaultValue || values[0])

  const slugify = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")

  const resolvePivot = () => {
    if (typeof window === "undefined") return defaultValue || values[0]

    const params = new URLSearchParams(window.location.search)
    const requested = params.get("pivots")
    if (requested) {
      const requestedIds = requested.split(",").map((value) => value.trim()).filter(Boolean)
      const match = requestedIds.find((id) => values.includes(id))
      if (match) return match
    }

    const hash = window.location.hash.replace(/^#/, "")
    if (hash) {
      const match = options.find((option) => option.id === hash || slugify(option.title) === hash)
      if (match) return match.id
    }

    try {
      const stored = window.localStorage.getItem(`foundry-zone-pivot:${group}`)
      if (values.includes(stored)) return stored
    } catch {
      return defaultValue || values[0]
    }

    return defaultValue || values[0]
  }

  const publishPivotChange = (value) => {
    if (typeof window === "undefined") return
    window.dispatchEvent(new CustomEvent("foundry-zone-pivot-change", { detail: { group, value } }))
  }

  const syncTableOfContents = () => {
    if (typeof window === "undefined") return

    window.requestAnimationFrame(() => {
      const toc = document.getElementById("table-of-contents-content")
      if (!toc) return

      const links = Array.from(toc.querySelectorAll('a[href^="#"]'))
      for (const link of links) {
        const item = link.closest("li")
        const rawId = link.getAttribute("href")?.slice(1)
        if (!item || !rawId) continue

        let id = rawId
        try {
          id = decodeURIComponent(rawId)
        } catch {
        }

        item.style.display = document.getElementById(id) ? "" : "none"
      }
    })
  }

  useEffect(() => {
    const resolvedPivot = resolvePivot()
    setActivePivot(resolvedPivot)
    publishPivotChange(resolvedPivot)
    window.setTimeout(syncTableOfContents, 0)
  }, [group, defaultValue, values.join("|"), optionKey])

  const selectPivot = (value) => {
    setActivePivot(value)

    if (typeof window !== "undefined") {
      try {
        window.localStorage.setItem(`foundry-zone-pivot:${group}`, value)
      } catch {
      }

      const url = new URL(window.location.href)
      const current = url.searchParams.get("pivots")
      const preserved = current
        ? current.split(",").map((id) => id.trim()).filter((id) => id && !values.includes(id))
        : []
      url.searchParams.set("pivots", [...preserved, value].join(","))
      window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`)
    }

    publishPivotChange(value)
    window.setTimeout(syncTableOfContents, 0)
  }

  if (options.length < 2) return null

  return (
    <div className="not-prose my-6 border-b border-slate-200 pb-3 dark:border-slate-800">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </div>
      <div className="flex flex-wrap gap-2" role="tablist" aria-label={label}>
        {options.map((option) => {
          const selected = option.id === activePivot
          return (
            <button
              key={option.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => selectPivot(option.id)}
              className={`rounded-md border px-3 py-1.5 text-sm font-medium transition ${selected ? "border-slate-900 bg-slate-900 text-white shadow-sm dark:border-slate-100 dark:bg-slate-100 dark:text-slate-950" : "border-slate-200 bg-white text-slate-700 hover:border-slate-400 hover:text-slate-950 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200 dark:hover:border-slate-500"}`}
            >
              {option.title}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export const ZoneContent = ({ group, value, options = [], values = [], defaultValue, children }) => {
  const optionKey = options.map((option) => `${option.id}:${option.title}`).join("|")
  const [activePivot, setActivePivot] = useState(defaultValue || values[0])

  const slugify = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")

  const resolvePivot = () => {
    if (typeof window === "undefined") return defaultValue || values[0]

    const params = new URLSearchParams(window.location.search)
    const requested = params.get("pivots")
    if (requested) {
      const requestedIds = requested.split(",").map((value) => value.trim()).filter(Boolean)
      const match = requestedIds.find((id) => values.includes(id))
      if (match) return match
    }

    const hash = window.location.hash.replace(/^#/, "")
    if (hash) {
      const match = options.find((option) => option.id === hash || slugify(option.title) === hash)
      if (match) return match.id
    }

    try {
      const stored = window.localStorage.getItem(`foundry-zone-pivot:${group}`)
      if (values.includes(stored)) return stored
    } catch {
      return defaultValue || values[0]
    }

    return defaultValue || values[0]
  }

  useEffect(() => {
    setActivePivot(resolvePivot())
  }, [group, defaultValue, values.join("|"), optionKey])

  useEffect(() => {
    const onPivotChange = (event) => {
      if (event.detail?.group === group && values.includes(event.detail.value)) {
        setActivePivot(event.detail.value)
      }
    }

    window.addEventListener("foundry-zone-pivot-change", onPivotChange)
    return () => window.removeEventListener("foundry-zone-pivot-change", onPivotChange)
  }, [group, values.join("|")])

  if (activePivot !== value) return null

  return <>{children}</>
}