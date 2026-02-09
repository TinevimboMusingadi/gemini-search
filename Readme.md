# Multimodal PDF Search

A full-stack multimodal search engine for PDFs. Index documents with OCR, vision detection (figures, tables, diagrams), and multimodal embeddings. Search with hybrid keyword + semantic retrieval. Research with a Gemini-powered AI agent that summarizes, grounds answers, and lets you ask follow-up questions.

```
Backend:  Python / FastAPI / SQLite / ChromaDB / Gemini / Vertex AI
Frontend: React 18 / TypeScript / Vite / TailwindCSS v4 / react-pdf
```

---

## Architecture

```
gemini-search/
├── src/multimodal_search/       # Python backend
│   ├── api/                     # FastAPI routes
│   │   └── routes/
│   │       ├── search_routes.py # GET/POST /search
│   │       ├── chat.py          # /chat/* session-based agent
│   │       ├── documents.py     # /documents/* listing & detail
│   │       ├── render.py        # /render/* PDF, crop, page images
│   │       └── ingest.py        # POST /ingest/pdf upload
│   ├── core/
│   │   ├── config.py            # Pydantic settings from .env
│   │   ├── database.py          # SQLite schema, FTS5, singleton engine
│   │   ├── memory_db.py         # Chat session persistence (separate DB)
│   │   ├── storage.py           # File storage helpers
│   │   ├── vector_store.py      # ChromaDB / in-memory vector store
│   │   └── schemas/             # Pydantic request/response models
│   ├── agent/
│   │   ├── chains.py            # Gemini agent loop with tool calling
│   │   └── tools/
│   │       └── search_tools.py  # search_local_index, web_search tools
│   ├── indexer/
│   │   └── pipeline.py          # PDF → pages → OCR → detection → embed
│   ├── search/
│   │   └── engine.py            # Keyword (FTS5), semantic, hybrid + RRF
│   └── services/
│       ├── gcp_vision.py        # Google Cloud Vision OCR
│       ├── gemini_client.py     # Gemini API client (detection + chat)
│       ├── vertex_embedder.py   # Vertex AI multimodal embeddings
│       └── web_search.py        # Web search grounding
├── ui/                          # React frontend
│   └── src/
│       ├── pages/
│       │   ├── SearchPage.tsx   # Landing + AI research results
│       │   └── ReaderPage.tsx   # PDF viewer with regions + chat
│       ├── components/
│       │   ├── search/          # SearchBar, AiResponse, ResultCard, ResultsSidebar
│       │   ├── reader/          # PdfViewer, RegionOverlay, DocSidebar, PageNav
│       │   ├── chat/            # ChatInput, ChatPanel, MessageBubble
│       │   ├── layout/          # AppShell, Header
│       │   ├── common/          # Spinner, Modal, ThemeToggle
│       │   └── ingest/          # UploadModal
│       ├── api/                 # Axios client (documents, search, chat, ingest)
│       ├── store/               # Zustand global state
│       └── types/               # TypeScript interfaces
├── scripts/                     # CLI tools (search, chat, inspect, test)
├── tests/                       # Test scaffolding
└── data/                        # Runtime data (pdfs, crops, pages, chroma)
```

### Data Flow

```
PDF Upload
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  Indexer Pipeline                                     │
│                                                       │
│  PDF → Render pages (144 DPI)                        │
│      → Google Cloud Vision OCR (batched)             │
│      → Gemini object detection (bounding boxes)      │
│      → Crop regions from page images                 │
│      → Vertex AI multimodal embeddings (dim=1408)    │
│      → Store in SQLite + ChromaDB                    │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  Search Engine                                        │
│                                                       │
│  Query → Keyword search (FTS5 on text_chunks)        │
│        → Semantic search (cosine on ChromaDB)         │
│        → Reciprocal Rank Fusion (RRF) merge           │
│        → Return ranked results (text + image regions) │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  Gemini Agent                                         │
│                                                       │
│  User query + search results                          │
│      → Gemini 3 Pro (thinking_level=high)            │
│      → Tools: search_local_index, web_search          │
│      → Multi-step tool calling loop (max 10 steps)   │
│      → Session memory (up to 20 messages)            │
│      → Returns summary + sources                     │
└──────────────────────────────────────────────────────┘
```

---

## Databases

### 1. Main Database — `multimodal_search.db` (SQLite)

| Table | Description |
|---|---|
| **documents** | PDF metadata: `id`, `file_hash` (unique), `filename`, `total_pages`, `storage_path` |
| **pages** | Per-page data: `id`, `document_id` (FK), `page_num`, `image_path`, `ocr_text`, `ocr_metadata` |
| **text_chunks** | Chunked OCR text: `id`, `page_id` (FK), `document_id` (FK), `chunk_index`, `text`, `vector_id` |
| **regions** | Detected visual regions: `id`, `page_id` (FK), `document_id` (FK), `label`, bounding box (`box_y0/x0/y1/x1`), `crop_path`, `vector_id` |
| **text_chunks_fts** | FTS5 virtual table over `text_chunks.text` for keyword search |

Triggers keep `text_chunks_fts` in sync on INSERT, UPDATE, DELETE. WAL mode enabled for concurrent reads.

### 2. Chat History Database — `chat_history.db` (SQLite)

| Table | Description |
|---|---|
| **chat_sessions** | Sessions: `id` (UUID), `title`, `created_at` |
| **chat_messages** | Messages: `id` (UUID), `session_id` (FK), `role` (user/model/tool), `content`, `timestamp` |

Separate DB so chat history doesn't interfere with document indexing.

### 3. Vector Store — ChromaDB (or in-memory)

| Setting | Value |
|---|---|
| Collection | `multimodal_embeddings` |
| Dimension | 1408 (Vertex AI multimodal) |
| Similarity | Cosine |
| Persistence | `data/chroma/` (configurable) |

Backends: `chroma` (default, persistent) or `memory` (ephemeral). Set via `VECTOR_STORE_BACKEND` in `.env`.

---

## API Reference

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "ok"}` |

### Search

| Method | Path | Description |
|---|---|---|
| `GET` | `/search?q=...&top_k=20&mode=hybrid` | Search via query params |
| `POST` | `/search` | Search via JSON body: `{"query": "...", "top_k": 20, "mode": "hybrid"}` |

**Modes:** `hybrid` (default), `keyword` (FTS5 only), `semantic` (vector only)

**Response:** `{ "query": "...", "results": [{ "document_id", "document_title", "page_id", "page_num", "result_type" ("text"/"image"), "chunk_id", "region_id", "snippet", "score", "vector_id" }] }`

### Documents

| Method | Path | Description |
|---|---|---|
| `GET` | `/documents` | List all indexed documents |
| `GET` | `/documents/{id}` | Document detail with page list |
| `GET` | `/documents/{id}/pages/{page_num}/regions` | Regions (bounding boxes) for a page |

### Chat (Agent)

| Method | Path | Description |
|---|---|---|
| `GET` | `/chat/sessions` | List all chat sessions |
| `POST` | `/chat/sessions` | Create a new session |
| `GET` | `/chat/sessions/{session_id}` | Get session history (messages) |
| `POST` | `/chat/{session_id}` | Send message to agent in session |
| `POST` | `/chat` | Stateless chat (no session persistence) |

**Request:** `{ "message": "...", "selected_region_context": "optional region info" }`
**Response:** `{ "reply": "...", "sources": [...] }`

### Render (File Serving)

| Method | Path | Description |
|---|---|---|
| `GET` | `/render/pdf/{document_id}` | Serve raw PDF (for client-side pdf.js) |
| `GET` | `/render/crop/{document_id}/{region_id}` | Serve cropped region image (PNG) |
| `GET` | `/render/page/{document_id}/{page_num}` | Serve rendered page image (PNG) |

### Ingest

| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest/pdf` | Upload PDF (multipart). Returns `{ "document_id", "status": "indexed" }` |

---

## Frontend

### Tech Stack

| Package | Version | Purpose |
|---|---|---|
| React | 19.2 | UI framework |
| TypeScript | 5.9 | Type safety |
| Vite | 7.3 | Build tool + dev server |
| TailwindCSS | 4.1 | Utility-first CSS |
| react-pdf | 9.2 | PDF rendering via pdf.js |
| react-router-dom | 7.13 | Client-side routing |
| zustand | 5.0 | State management |
| axios | 1.13 | HTTP client |

### Pages & Routes

| Route | Page | Description |
|---|---|---|
| `/` or `/search` | SearchPage | Landing with search input + AI research results |
| `/reader` | ReaderPage | PDF viewer with document sidebar |
| `/reader/:documentId` | ReaderPage | PDF viewer for a specific document |

### Search Page

**Landing state:** Centered search input with suggestion chips and an animated ticker showing currently indexed documents. Clean monochrome design (black/white/grey/silver).

**Results state:** Two-panel layout:
- **Left:** AI research response — the agent analyzes search results and renders a flowing markdown summary with headings, lists, bold text, and action buttons (share, thumbs up/down, new research). Embedded "Ask anything" follow-up input for continued conversation.
- **Right:** Sources sidebar — compact cards with colored document icons, titles, snippets, page numbers. Collapsible with "Show all" button.

### Reader Page

Three-panel layout:
- **Left sidebar:** Document tree showing all indexed PDFs with page counts. Click to open.
- **Center:** PDF rendered client-side via react-pdf (pdf.js). Region bounding boxes overlaid on pages. Click a region to select it for chat context.
- **Right:** Chat panel with Gemini agent. Session-based with message history.

### Theme

Dark mode by default (Cursor-inspired). Light mode toggle available. CSS custom properties:

| Token | Dark | Light |
|---|---|---|
| `--color-bg` | `#0a0a0a` | `#ffffff` |
| `--color-surface` | `#141414` | `#f5f5f5` |
| `--color-surface-2` | `#1c1c1c` | `#ebebeb` |
| `--color-border` | `#262626` | `#e0e0e0` |
| `--color-text` | `#fafafa` | `#171717` |
| `--color-text-secondary` | `#a1a1aa` | `#525252` |
| `--color-accent` | `#3b82f6` | `#3b82f6` |

---

## Setup

### 1. Environment & Keys

Create `.env` in the project root:

```env
# GCP (for Vertex AI embeddings and optional Vision ADC)
GOOGLE_APPLICATION_CREDENTIALS=key/your-service-account.json
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# Google Cloud Vision (API key or use ADC above)
GOOGLE_API_KEY=your-vision-api-key

# Gemini (from AI Studio: https://aistudio.google.com/apikey)
GEMINI_API_KEY=your-gemini-api-key

# Vector store
VECTOR_STORE_BACKEND=chroma
```

**Test API connectivity:**

```bash
python scripts/test_google_apis.py
```

### 2. Install Backend

```bash
cd gemini-search
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -e . --timeout 600
# or: pip install -r requirements.txt --timeout 600 && pip install -e . --no-deps
```

### 3. Index PDFs

```bash
python run_index.py path/to/file.pdf
# or a directory:
python run_index.py data/
```

This creates the SQLite DB, crops, and ChromaDB vectors.

### 4. Run Backend

```bash
# Windows PowerShell:
$env:PYTHONPATH = "src"
$env:PYTHONUNBUFFERED = "1"
python -m uvicorn multimodal_search.main:app --host 0.0.0.0 --port 8000

# Linux/Mac:
PYTHONPATH=src PYTHONUNBUFFERED=1 uvicorn multimodal_search.main:app --host 0.0.0.0 --port 8000
```

Health check: `http://localhost:8000/health`

### 5. Install & Run Frontend

```bash
cd ui
npm install
npm run dev
```

Opens at `http://localhost:5173`. The Vite dev server proxies `/api` to `http://localhost:8000`.

---

## CLI Scripts

| Script | Description |
|---|---|
| `scripts/search_cli.py` | Interactive search from terminal |
| `scripts/chat_cli.py` | Interactive chat with the agent |
| `scripts/inspect_db.py` | Dump database tables and sample rows |
| `scripts/reindex_embeddings.py` | Re-embed all chunks/regions without re-indexing |
| `scripts/test_google_apis.py` | Test Vision, Gemini, Vertex connectivity |
| `scripts/test_agent_grounding.py` | Test agent tool calling and grounding |
| `scripts/test_agent_memory.py` | Test agent session memory |
| `scripts/test_search_and_chroma.py` | Test search engine + ChromaDB |

---

## Agent

The Gemini agent (`agent/chains.py`) uses a multi-step tool-calling loop:

1. User sends a message (optionally with selected region context)
2. Agent calls Gemini 3 Pro with `thinking_level=high`
3. If Gemini requests a tool call:
   - **`search_local_index`**: Runs hybrid/keyword/semantic search on the local PDF database
   - **`web_search`**: Searches the web for additional grounding
4. Tool results are fed back to Gemini for the next step
5. Loop continues (max 10 steps) until Gemini returns a final text response
6. All messages are persisted in `chat_history.db` for session continuity (up to 20 messages of context)

---

## Troubleshooting

**"Database is locked"** — The indexer and API share `multimodal_search.db`. WAL mode and a 60s timeout handle most cases. If it persists, stop the API, run the indexer, then restart.

**Backend takes 90-120s to start** — Google Cloud SDK imports are slow on first load. This is normal. Set `PYTHONUNBUFFERED=1` to see logs during startup.

**`npm install` hangs on Windows** — Use `npm install 2>&1 | Out-String` in PowerShell to capture output, or try `npm install --prefer-offline`.

**Search returns no results** — Ensure the backend is running on port 8000. Check `http://localhost:8000/documents` to verify documents are indexed. Try keyword mode first.

**Vertex AI deprecation warning** — The `vertexai` SDK shows a deprecation notice for `_model_garden_models`. This is cosmetic and does not affect functionality.

---

## Data Directory

```
data/
├── pdfs/
│   ├── 1/                     # Document ID folders
│   │   └── filename.pdf       # Stored PDF copy
│   └── 2/
├── crops/
│   ├── 1/                     # Document ID folders
│   │   ├── region_1.png       # Cropped region images
│   │   ├── region_2.png
│   │   └── ...
│   └── 2/
├── pages/                     # Rendered page images (if stored)
└── chroma/                    # ChromaDB persistent vector store
    └── multimodal_embeddings/ # Collection data
```

---
