/* ── TypeScript interfaces matching the backend Pydantic schemas ── */

// ---------- Documents ----------

export interface DocumentListItem {
  id: number;
  filename: string;
  total_pages: number;
  storage_path?: string;
}

export interface PageSummary {
  id: number;
  page_num: number;
  has_image: boolean;
  has_ocr_text: boolean;
}

export interface DocumentDetail {
  id: number;
  filename: string;
  total_pages: number;
  storage_path?: string;
  pages: PageSummary[];
}

// ---------- Regions ----------

export interface RegionDetail {
  id: number;
  page_id: number;
  label: string;
  box_y0: number;
  box_x0: number;
  box_y1: number;
  box_x1: number;
  crop_path?: string;
  vector_id?: string;
}

// ---------- Search ----------

export type SearchMode = "hybrid" | "keyword" | "semantic";

export interface SearchRequest {
  query: string;
  top_k?: number;
  mode?: SearchMode;
}

export interface SearchResultItem {
  document_id: number;
  document_title: string;
  page_id: number;
  page_num: number;
  result_type: "text" | "image";
  chunk_id?: number;
  region_id?: number;
  snippet: string;
  score: number;
  vector_id?: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
}

// ---------- Chat ----------

export interface ChatRequest {
  message: string;
  selected_region_context?: string;
}

export interface ChatResponse {
  reply: string;
  sources: unknown[];
}

export interface ChatSessionItem {
  session_id: string;
  title?: string;
  created_at: string;
}

export interface MessageSchema {
  role: string;
  content: string;
  timestamp: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  messages: MessageSchema[];
}

// ---------- Ingest ----------

export interface IngestResponse {
  document_id: number;
  status: string;
}
