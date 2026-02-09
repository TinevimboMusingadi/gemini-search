import client from "./client";
import type { SearchResponse, SearchMode } from "../types/api";

export async function search(
  query: string,
  mode: SearchMode = "hybrid",
  topK: number = 20
): Promise<SearchResponse> {
  const { data } = await client.post<SearchResponse>("/search", {
    query,
    mode,
    top_k: topK,
  });
  return data;
}
