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
  // Fluent UI System Icons (Microsoft, MIT) — monochrome filled SVGs
  // Source: github.com/microsoft/fluentui-system-icons
  const FI = ({ d, tip, vb = 16 }) => (
    <svg className="shrink-0" width="14" height="14" viewBox={`0 0 ${vb} ${vb}`} fill="currentColor" aria-hidden="true">
      <title>{tip}</title>
      <path d={d} />
    </svg>
  )

  const MODALITY_ICON = {
    text: { d: "M4.5 5C4.22386 5 4 5.22386 4 5.5C4 5.77614 4.22386 6 4.5 6H11.5C11.7761 6 12 5.77614 12 5.5C12 5.22386 11.7761 5 11.5 5H4.5ZM4 8.5C4 8.22386 4.22386 8 4.5 8H11.5C11.7761 8 12 8.22386 12 8.5C12 8.77614 11.7761 9 11.5 9H4.5C4.22386 9 4 8.77614 4 8.5ZM4.5 11C4.22386 11 4 11.2239 4 11.5C4 11.7761 4.22386 12 4.5 12H8.5C8.77614 12 9 11.7761 9 11.5C9 11.2239 8.77614 11 8.5 11H4.5Z", tip: "Text" },
    image: { d: "M2 4.5C2 3.11929 3.11929 2 4.5 2H11.5C12.8807 2 14 3.11929 14 4.5V11.5C14 12.8807 12.8807 14 11.5 14H4.5C3.11929 14 2 12.8807 2 11.5V4.5ZM10.4979 6.50414C11.0514 6.50414 11.5 6.0555 11.5 5.50207C11.5 4.94864 11.0514 4.5 10.4979 4.5C9.94449 4.5 9.49585 4.94864 9.49585 5.50207C9.49585 6.0555 9.94449 6.50414 10.4979 6.50414Z", tip: "Image" },
    audio: { d: "M8.69435 2.03934C8.87957 2.11749 8.99998 2.29898 8.99998 2.50001V13.5C8.99998 13.701 8.87957 13.8825 8.69435 13.9607C8.50913 14.0388 8.29428 14.0046 8.14282 13.872L4.72179 10.9H2.49998C2.22384 10.9 1.99998 10.6761 1.99998 10.4V5.60001C1.99998 5.32387 2.22384 5.10001 2.49998 5.10001H4.72179L8.14282 2.12803C8.29428 1.99543 8.50913 1.96119 8.69435 2.03934Z", tip: "Audio" },
    video: { d: "M3.5 3C2.11929 3 1 4.11929 1 5.5V10.5C1 11.8807 2.11929 13 3.5 13H8.5C9.88071 13 11 11.8807 11 10.5V5.5C11 4.11929 9.88071 3 8.5 3H3.5Z", tip: "Video" },
    code: { d: "M9.80307 3.04322C10.0554 3.15537 10.1691 3.45085 10.0569 3.70319L6.05691 12.7032C5.94477 12.9555 5.64928 13.0692 5.39694 12.957C5.14461 12.8449 5.03095 12.5494 5.14309 12.2971L9.14309 3.29706C9.25524 3.04472 9.55073 2.93107 9.80307 3.04322Z", tip: "Code" },
  }

  const TASK_ICON = {
    "chat-completion": { d: "M8 2C4.68629 2 2 4.68629 2 8C2 9.82141 2.82675 11.4438 4.12602 12.5102L2.57602 14.424C2.30894 14.7539 2.54558 15.2354 2.96568 15.2093L7.04813 14.9544C7.36208 14.9848 7.67915 15 8 15C11.3137 15 14 12.3137 14 9C14 5.68629 11.3137 2 8 2Z", tip: "Chat Completions" },
    responses: { d: "M6.35355 3.64645C6.54882 3.84171 6.54882 4.15829 6.35355 4.35355L3.70711 7H8.5C11.5376 7 14 9.46243 14 12.5C14 12.7761 13.7761 13 13.5 13C13.2239 13 13 12.7761 13 12.5C13 10.0147 10.9853 8 8.5 8H3.70711L6.35355 10.6464C6.54882 10.8417 6.54882 11.1583 6.35355 11.3536C6.15829 11.5488 5.84171 11.5488 5.64645 11.3536L2.14645 7.85355C1.95118 7.65829 1.95118 7.34171 2.14645 7.14645L5.64645 3.64645C5.84171 3.45118 6.15829 3.45118 6.35355 3.64645Z", tip: "Responses API" },
    embeddings: { d: "M2 4.5C2 3.11929 3.11929 2 4.5 2H11.5C12.8807 2 14 3.11929 14 4.5V11.5C14 12.8807 12.8807 14 11.5 14H4.5C3.11929 14 2 12.8807 2 11.5V4.5ZM4.5 3C3.67157 3 3 3.67157 3 4.5V5H7.5V3H4.5ZM8.5 3V10H13V4.5C13 3.67157 12.3284 3 11.5 3H8.5Z", tip: "Embeddings" },
    "text-to-image": { d: "M2 4.5C2 3.11929 3.11929 2 4.5 2H11.5C12.8807 2 14 3.11929 14 4.5V11.5C14 12.8807 12.8807 14 11.5 14H4.5C3.11929 14 2 12.8807 2 11.5V4.5Z", tip: "Image Generation" },
    "text-generation": { d: "M4.5 5C4.22386 5 4 5.22386 4 5.5C4 5.77614 4.22386 6 4.5 6H11.5C11.7761 6 12 5.77614 12 5.5C12 5.22386 11.7761 5 11.5 5H4.5Z", tip: "Text Generation" },
    "speech-to-text": { d: "M5.5 4.5C5.5 3.11929 6.61929 2 8 2C9.38071 2 10.5 3.11929 10.5 4.5V8C10.5 9.38071 9.38071 10.5 8 10.5C6.61929 10.5 5.5 9.38071 5.5 8V4.5Z", tip: "Speech-to-Text" },
    "text-to-speech": { d: "M8.69435 2.03934C8.87957 2.11749 8.99998 2.29898 8.99998 2.50001V13.5C8.99998 13.701 8.87957 13.8825 8.69435 13.9607C8.50913 14.0388 8.29428 14.0046 8.14282 13.872L4.72179 10.9H2.49998C2.22384 10.9 1.99998 10.6761 1.99998 10.4V5.60001C1.99998 5.32387 2.22384 5.10001 2.49998 5.10001H4.72179L8.14282 2.12803C8.29428 1.99543 8.50913 1.96119 8.69435 2.03934Z", tip: "Text-to-Speech" },
    "video-generation": { d: "M3.5 3C2.11929 3 1 4.11929 1 5.5V10.5C1 11.8807 2.11929 13 3.5 13H8.5C9.88071 13 11 11.8807 11 10.5V5.5C11 4.11929 9.88071 3 8.5 3H3.5Z", tip: "Video Generation" },
    "audio-generation": { d: "M8.69435 2.03934C8.87957 2.11749 8.99998 2.29898 8.99998 2.50001V13.5C8.99998 13.701 8.87957 13.8825 8.69435 13.9607C8.50913 14.0388 8.29428 14.0046 8.14282 13.872L4.72179 10.9H2.49998C2.22384 10.9 1.99998 10.6761 1.99998 10.4V5.60001C1.99998 5.32387 2.22384 5.10001 2.49998 5.10001H4.72179L8.14282 2.12803C8.29428 1.99543 8.50913 1.96119 8.69435 2.03934Z", tip: "Audio Generation" },
  }

  const CAP_ICON = {
    reasoning: { d: "M5.70049 3.94804C5.92703 2.81534 6.92158 2 8.07672 2C8.86031 2 9.55704 2.37193 10 2.94888C10.443 2.37193 11.1397 2 11.9233 2C13.0784 2 14.073 2.81534 14.2995 3.94804L14.4249 4.57508L14.8311 4.65632C16.0922 4.90854 17 6.01586 17 7.30196V7.5C17 8.22648 16.6901 8.88058 16.1954 9.33735C17.2649 9.86867 18 10.9723 18 12.2475C18 13.7835 16.9244 15.1075 15.425 15.4247L15.3879 15.6102C15.1099 16.9998 13.8899 18 12.4728 18C11.4417 18 10.5332 17.4751 10 16.6779C9.46679 17.4751 8.5583 18 7.52721 18C6.11013 18 4.89005 16.9998 4.61214 15.6102L4.57504 15.4247C3.07561 15.1075 2 13.7835 2 12.2475C2 10.9723 2.73508 9.86867 3.80465 9.33735C3.30987 8.88058 3 8.22648 3 7.5V7.30196C3 6.01586 3.90778 4.90854 5.16891 4.65632L5.57508 4.57508L5.70049 3.94804Z", tip: "Reasoning", vb: 20 },
    streaming: { d: "M4.91447 1.71442C5.04078 1.29055 5.43053 1 5.87282 1H10.2786C10.9768 1 11.4601 1.69737 11.2149 2.35112L10.2216 5H12.2511C12.8791 5 13.229 5.72572 12.8379 6.21709L6.23096 14.5173C5.37726 15.5898 3.66907 14.7047 4.05299 13.3888L5.33338 9H3.74951C3.24769 9 2.88743 8.51673 3.03074 8.03581L4.91447 1.71442Z", tip: "Streaming" },
    "tool-calling": { d: "M6.99952 5C6.99952 2.79086 8.79038 1 10.9995 1C11.5083 1 11.996 1.09525 12.4457 1.26951C12.6994 1.36796 12.8246 1.65042 12.7262 1.90409C12.6277 2.15777 12.3453 2.28301 12.0916 2.18456C11.7522 2.05282 11.3841 1.98214 10.9995 1.98214C9.33203 1.98214 7.98167 3.3325 7.98167 5C7.98167 6.6675 9.33203 8.01786 10.9995 8.01786C12.667 8.01786 14.0174 6.6675 14.0174 5C14.0174 4.72386 14.2412 4.5 14.5174 4.5C14.7935 4.5 15.0174 4.72386 15.0174 5C15.0174 7.20914 13.2086 9 10.9995 9C8.79038 9 6.99952 7.20914 6.99952 5Z", tip: "Tool Calling" },
    "fine-tuning": { d: "M13.5 1C13.7761 1 14 1.22386 14 1.5V2H14.5C14.7761 2 15 2.22386 15 2.5C15 2.77614 14.7761 3 14.5 3H14V3.5C14 3.77614 13.7761 4 13.5 4C13.2239 4 13 3.77614 13 3.5V3H12.5C12.2239 3 12 2.77614 12 2.5C12 2.22386 12.2239 2 12.5 2H13V1.5C13 1.22386 13.2239 1 13.5 1Z", tip: "Fine-tuning" },
    agentsV2: { d: "M8.5 1.5C8.5 1.22386 8.27614 1 8 1C7.72386 1 7.5 1.22386 7.5 1.5V2H5.5C4.67157 2 4 2.67157 4 3.5V5.5C4 7.70914 5.79086 9.5 8 9.5C10.2091 9.5 12 7.70914 12 5.5V3.5C12 2.67157 11.3284 2 10.5 2H8.5V1.5Z", tip: "Agents" },
    agents: { d: "M8.5 1.5C8.5 1.22386 8.27614 1 8 1C7.72386 1 7.5 1.22386 7.5 1.5V2H5.5C4.67157 2 4 2.67157 4 3.5V5.5C4 7.70914 5.79086 9.5 8 9.5C10.2091 9.5 12 7.70914 12 5.5V3.5C12 2.67157 11.3284 2 10.5 2H8.5V1.5Z", tip: "Agents (v1)" },
    assistants: { d: "M8 2C4.68629 2 2 4.68629 2 8C2 9.82141 2.82675 11.4438 4.12602 12.5102L2.57602 14.424C2.30894 14.7539 2.54558 15.2354 2.96568 15.2093L7.04813 14.9544C7.36208 14.9848 7.67915 15 8 15C11.3137 15 14 12.3137 14 9C14 5.68629 11.3137 2 8 2Z", tip: "Assistants" },
  }

  const TOOL_ICON = {
    web_search: { d: "M8 14C11.3137 14 14 11.3137 14 8C14 4.68629 11.3137 2 8 2C4.68629 2 2 4.68629 2 8C2 11.3137 4.68629 14 8 14Z", tip: "Web Search" },
    file_search: { d: "M5 1C3.89543 1 3 1.89543 3 3V13C3 14.1046 3.89543 15 5 15H11C12.1046 15 13 14.1046 13 13V5L9 1H5Z", tip: "File Search" },
    code_interpreter: { d: "M9.80307 3.04322C10.0554 3.15537 10.1691 3.45085 10.0569 3.70319L6.05691 12.7032C5.94477 12.9555 5.64928 13.0692 5.39694 12.957C5.14461 12.8449 5.03095 12.5494 5.14309 12.2971L9.14309 3.29706C9.25524 3.04472 9.55073 2.93107 9.80307 3.04322Z", tip: "Code Interpreter" },
    mcp: { d: "M6.01323 6.77501C5.52723 6.28801 4.73223 6.28801 4.24523 6.77501C3.75923 7.26201 3.75923 8.05701 4.24523 8.54401L7.45623 11.755C7.94323 12.242 8.73823 12.242 9.22523 11.755C9.71223 11.268 9.71223 10.473 9.22523 9.98601L6.01323 6.77501Z", tip: "MCP" },
    browser_automation: { d: "M1 3.5C1 2.11929 2.11929 1 3.5 1H10.5C11.8807 1 13 2.11929 13 3.5V12.5C13 13.8807 11.8807 15 10.5 15H3.5C2.11929 15 1 13.8807 1 12.5V3.5Z", tip: "Computer Use" },
    function: { d: "M9.80307 3.04322C10.0554 3.15537 10.1691 3.45085 10.0569 3.70319L6.05691 12.7032C5.94477 12.9555 5.64928 13.0692 5.39694 12.957C5.14461 12.8449 5.03095 12.5494 5.14309 12.2971L9.14309 3.29706C9.25524 3.04472 9.55073 2.93107 9.80307 3.04322Z", tip: "Functions" },
    azure_ai_search: { d: "M11.0195 11.7266C10.0658 12.5217 8.83875 13 7.5 13C4.46243 13 2 10.5376 2 7.5C2 4.46243 4.46243 2 7.5 2C10.5376 2 13 4.46243 13 7.5C13 8.83875 12.5217 10.0658 11.7266 11.0195L14.3536 13.6464C14.5488 13.8417 14.5488 14.1583 14.3536 14.3536C14.1583 14.5488 13.8417 14.5488 13.6464 14.3536L11.0195 11.7266Z", tip: "Azure AI Search" },
    bing_grounding: { d: "M11.0195 11.7266C10.0658 12.5217 8.83875 13 7.5 13C4.46243 13 2 10.5376 2 7.5C2 4.46243 4.46243 2 7.5 2C10.5376 2 13 4.46243 13 7.5C13 8.83875 12.5217 10.0658 11.7266 11.0195L14.3536 13.6464C14.5488 13.8417 14.5488 14.1583 14.3536 14.3536C14.1583 14.5488 13.8417 14.5488 13.6464 14.3536L11.0195 11.7266Z", tip: "Bing Grounding" },
    bing_custom_search: { d: "M11.0195 11.7266C10.0658 12.5217 8.83875 13 7.5 13C4.46243 13 2 10.5376 2 7.5C2 4.46243 4.46243 2 7.5 2C10.5376 2 13 4.46243 13 7.5C13 8.83875 12.5217 10.0658 11.7266 11.0195L14.3536 13.6464C14.5488 13.8417 14.5488 14.1583 14.3536 14.3536C14.1583 14.5488 13.8417 14.5488 13.6464 14.3536L11.0195 11.7266Z", tip: "Bing Custom Search" },
    sharepoint_grounding: { d: "M4.5 5C4.22386 5 4 5.22386 4 5.5C4 5.77614 4.22386 6 4.5 6H11.5C11.7761 6 12 5.77614 12 5.5C12 5.22386 11.7761 5 11.5 5H4.5ZM4 8.5C4 8.22386 4.22386 8 4.5 8H11.5C11.7761 8 12 8.22386 12 8.5C12 8.77614 11.7761 9 11.5 9H4.5C4.22386 9 4 8.77614 4 8.5Z", tip: "SharePoint" },
    fabric_dataagent: { d: "M2 4.5C2 3.11929 3.11929 2 4.5 2H11.5C12.8807 2 14 3.11929 14 4.5V11.5C14 12.8807 12.8807 14 11.5 14H4.5C3.11929 14 2 12.8807 2 11.5V4.5Z", tip: "Fabric Data Agent" },
    openapi: { d: "M9.80307 3.04322C10.0554 3.15537 10.1691 3.45085 10.0569 3.70319L6.05691 12.7032C5.94477 12.9555 5.64928 13.0692 5.39694 12.957C5.14461 12.8449 5.03095 12.5494 5.14309 12.2971L9.14309 3.29706C9.25524 3.04472 9.55073 2.93107 9.80307 3.04322Z", tip: "OpenAPI" },
    image_generation: { d: "M2 4.5C2 3.11929 3.11929 2 4.5 2H11.5C12.8807 2 14 3.11929 14 4.5V11.5C14 12.8807 12.8807 14 11.5 14H4.5C3.11929 14 2 12.8807 2 11.5V4.5Z", tip: "Image Generation" },
    a2a_preview: { d: "M6.35355 3.64645C6.54882 3.84171 6.54882 4.15829 6.35355 4.35355L3.70711 7H8.5C11.5376 7 14 9.46243 14 12.5C14 12.7761 13.7761 13 13.5 13C13.2239 13 13 12.7761 13 12.5C13 10.0147 10.9853 8 8.5 8H3.70711L6.35355 10.6464C6.54882 10.8417 6.54882 11.1583 6.35355 11.3536C6.15829 11.5488 5.84171 11.5488 5.64645 11.3536L2.14645 7.85355C1.95118 7.65829 1.95118 7.34171 2.14645 7.14645L5.64645 3.64645C5.84171 3.45118 6.15829 3.45118 6.35355 3.64645Z", tip: "A2A" },
    azure_function: { d: "M9.80307 3.04322C10.0554 3.15537 10.1691 3.45085 10.0569 3.70319L6.05691 12.7032C5.94477 12.9555 5.64928 13.0692 5.39694 12.957C5.14461 12.8449 5.03095 12.5494 5.14309 12.2971L9.14309 3.29706C9.25524 3.04472 9.55073 2.93107 9.80307 3.04322Z", tip: "Azure Function" },
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
                    <div className="p-4">
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
                            <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 leading-tight line-clamp-2 min-h-[2.5rem]">
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

                      {/* Description — clamp when collapsed, full when expanded */}
                      <p className={`text-xs leading-snug text-zinc-600 dark:text-zinc-400 ${isExpanded ? "mb-2 max-h-24 overflow-y-auto" : "line-clamp-2 mb-2"}`} style={{minHeight: "2rem"}}>
                        {m.summary || "No description available."}
                      </p>

                      {/* Specs row — context + output (always rendered for alignment) */}
                      <div className="flex items-center gap-2 text-[11px] text-zinc-500 dark:text-zinc-400 mb-2 tabular-nums" style={{minHeight: "1.25rem"}}>
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

                      {/* Icon strip — modalities, tasks, capabilities, tools */}
                      <div className="flex flex-wrap items-center gap-1">
                        {/* Input modalities */}
                        {m.inputModalities?.map((mod) => (
                          <span key={`in-${mod}`} title={`Input: ${mod}`}
                            className="inline-flex items-center justify-center w-6 h-6 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
                            {MODALITY_ICON[mod] ? <FI {...MODALITY_ICON[mod]} /> : <span className="text-[10px]">{mod.slice(0,2)}</span>}
                          </span>
                        ))}
                        {/* Output modalities (only if different from input) */}
                        {m.outputModalities?.filter((mod) => !m.inputModalities?.includes(mod)).map((mod) => (
                          <span key={`out-${mod}`} title={`Output: ${mod}`}
                            className="inline-flex items-center justify-center w-6 h-6 rounded bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400">
                            {MODALITY_ICON[mod] ? <FI {...MODALITY_ICON[mod]} /> : <span className="text-[10px]">{mod.slice(0,2)}</span>}
                          </span>
                        ))}
                        {/* Separator */}
                        {(m.inputModalities?.length > 0 || m.outputModalities?.length > 0) && (m.tasks?.length > 0 || m.capabilities?.length > 0) && (
                          <span className="w-px h-4 bg-zinc-200 dark:bg-zinc-700 mx-0.5" />
                        )}
                        {/* Tasks (top 3) */}
                        {(m.tasks || []).slice(0, 3).map((t) => {
                          const ti = TASK_ICON[t]
                          return ti ? (
                            <span key={t} title={ti.tip}
                              className="inline-flex items-center justify-center w-6 h-6 rounded bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400">
                              <FI {...ti} />
                            </span>
                          ) : null
                        })}
                        {/* Capabilities (top 4) */}
                        {(m.capabilities || []).slice(0, 4).map((c) => {
                          const ci = CAP_ICON[c]
                          return ci ? (
                            <span key={c} title={ci.tip}
                              className="inline-flex items-center justify-center w-6 h-6 rounded bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400">
                              <FI {...ci} />
                            </span>
                          ) : null
                        })}
                        {/* Overflow count */}
                        {((m.tasks || []).length + (m.capabilities || []).length) > 7 && (
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-zinc-100 dark:bg-zinc-800 text-[10px] text-zinc-400">
                            +{(m.tasks || []).length + (m.capabilities || []).length - 7}
                          </span>
                        )}
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
                                      {ti && <FI {...ti} />}
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
