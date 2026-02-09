# Multimodal PDF Search Backend

Python (FastAPI) backend for a multimodal search engine over PDFs: OCR, vision detection (figures/tables/diagrams), text and image embeddings, hybrid search, and a Gemini agent with local + web search.

## Architecture

- **API** (`src/multimodal_search/api`): Ingest, search, chat, render endpoints.
- **Core** (`src/multimodal_search/core`): Config, SQLite DB, storage, schemas, vector store.
- **Services**: GCP Vision (OCR), Gemini (detection + chat), Vertex (embeddings), web search (grounding).
- **Indexer**: PDF → pages → OCR (batched) → Gemini detection → crops → embeddings → DB + vector store.
- **Search**: Hybrid keyword (FTS5) + vector, RRF merge.
- **Agent**: Gemini with tools: search local index, web search.

## Setup

### 1. Environment and keys

See `context_file/key_and_env_context.md`. Summary:

**Test Google APIs (Vision, Gemini, Vertex)** before indexing:

```bash
python scripts/test_google_apis.py
```

Shows PASS/FAIL for each. Fix any FAIL before running the indexer.

- **GCP (Vertex, optional Vision ADC):** Set in `.env`:
  - `GOOGLE_APPLICATION_CREDENTIALS` = path to service account JSON (e.g. `key/my-sa.json`)
  - `GCP_PROJECT_ID`, `GCP_LOCATION=us-central1`
- **Vision:** Either use ADC above or set `GOOGLE_API_KEY` for the REST client.
- **Gemini:** Get key from [AI Studio](https://aistudio.google.com/apikey), set `GEMINI_API_KEY`.

### 2. Install

```bash
cd gemini-search
pip install -e .
```

If the download times out (e.g. `ReadTimeoutError` on grpcio or PyPI), use a longer timeout and retry:

```bash
pip install -e . --timeout 600
```

**Alternative: install via requirements.txt** (often better with flaky networks or file locks, since deps install one-by-one):

```bash
pip install -r requirements.txt --timeout 600
pip install -e . --no-deps
```

**Install troubleshooting**

- **`ReadTimeoutError` (e.g. on grpcio)**  
  Network or PyPI is slow. Retry with `pip install -e . --timeout 600`. If it still fails, try again later or on a different network; no need to install that package manually.

- **`WinError 32: The process cannot access the file ... (e.g. sympy\...\calculus.py)`**  
  Another process is using a file in `.venv` (e.g. another `pip install` or Python from the same venv). Fix: close all other terminals that use this project’s venv, stop any running app/IDE Python, then run `pip install -e .` again in a single terminal. You do **not** need to install packages manually.

### 3. Run API

```bash
uvicorn multimodal_search.main:app --reload
```

- Health: `GET /health`
- Ingest: `POST /ingest/pdf` (multipart file)
- Search: `GET /search?q=...&top_k=20` or `POST /search` with `{"query":"...","top_k":20}`
- Chat: `POST /chat` with `{"message":"...", "selected_region_context": null}`
- Render crop: `GET /render/crop/{document_id}/{region_id}`

### 4. Index PDFs (CLI)

From project root (with `.env` set for GCP/Gemini/Vertex if you use them):

```bash
python run_index.py path/to/file.pdf
# or a directory of PDFs
python run_index.py path/to/directory
```

Or after install: `run-index path/to/file.pdf`

Logs print to stdout (INFO by default). For per-step detail (OCR batches, regions, embeddings), set `LOG_LEVEL=DEBUG` before running (PowerShell: `$env:LOG_LEVEL="DEBUG"`; cmd: `set LOG_LEVEL=DEBUG`).

**"Database is locked"** — The indexer and the API share the same SQLite file. The DB is configured with a 30s busy timeout and WAL mode so you can run the indexer while the API is running. If you still see lock errors, stop the API (Ctrl+C), run the indexer, then start the API again.

### 5. Quick run: index then backend

1. **Index a PDF** (creates DB, crops, vector store):

   ```bash
   python run_index.py data
   ```
   (or a single file, e.g. `data/MAZ_Newsletter_January_2024.pdf`)

2. **Start the API**:

   ```bash
   uvicorn multimodal_search.main:app --reload
   ```

3. Try: `GET http://127.0.0.1:8000/health`, then`GET http://127.0.0.1:8000/search?q=...&top_k=10`, or `POST /chat` with a message. 

## Data

- SQLite: `multimodal_search.db` (project root by default).
- PDFs and crops: `data/pdfs/`, `data/crops/` (configurable via env / `core/config.py`).
- **Vector store:** Default is in-memory. For a local persistent store, set in `.env`:
  - `VECTOR_STORE_BACKEND=chroma`
  - Optionally `CHROMA_PERSIST_DIR=data/chroma` (default). ChromaDB will persist under that directory.

## Logging

The app logs at INFO by default. Set `LOG_LEVEL=DEBUG` or configure logging to see per-step detail (e.g. pipeline, search, agent).
