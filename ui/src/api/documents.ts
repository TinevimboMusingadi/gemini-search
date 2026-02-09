import client from "./client";
import type {
  DocumentListItem,
  DocumentDetail,
  RegionDetail,
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getDocuments(): Promise<DocumentListItem[]> {
  const { data } = await client.get<DocumentListItem[]>("/documents");
  return data;
}

export async function getDocument(
  documentId: number
): Promise<DocumentDetail> {
  const { data } = await client.get<DocumentDetail>(
    `/documents/${documentId}`
  );
  return data;
}

export async function getPageRegions(
  documentId: number,
  pageNum: number
): Promise<RegionDetail[]> {
  const { data } = await client.get<RegionDetail[]>(
    `/documents/${documentId}/pages/${pageNum}/regions`
  );
  return data;
}

/** URL to fetch the raw PDF for client-side rendering */
export function getPdfUrl(documentId: number): string {
  return `${API_BASE}/render/pdf/${documentId}`;
}

/** URL for a crop image */
export function getCropUrl(documentId: number, regionId: number): string {
  return `${API_BASE}/render/crop/${documentId}/${regionId}`;
}

/** URL for a page image */
export function getPageImageUrl(documentId: number, pageNum: number): string {
  return `${API_BASE}/render/page/${documentId}/${pageNum}`;
}
