import client from "./client";
import type { IngestResponse } from "../types/api";

export async function uploadPdf(
  file: File,
  onProgress?: (pct: number) => void
): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);

  const { data } = await client.post<IngestResponse>("/ingest/pdf", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
  return data;
}
