import client from "./client";
import type {
  ChatSessionItem,
  ChatResponse,
  SessionHistoryResponse,
} from "../types/api";

export async function listSessions(): Promise<ChatSessionItem[]> {
  const { data } = await client.get<ChatSessionItem[]>("/chat/sessions");
  return data;
}

export async function createSession(): Promise<{
  session_id: string;
  title: string;
}> {
  const { data } = await client.post("/chat/sessions");
  return data;
}

export async function getSessionHistory(
  sessionId: string
): Promise<SessionHistoryResponse> {
  const { data } = await client.get<SessionHistoryResponse>(
    `/chat/sessions/${sessionId}`
  );
  return data;
}

export async function sendMessage(
  sessionId: string,
  message: string,
  selectedRegionContext?: string
): Promise<ChatResponse> {
  const { data } = await client.post<ChatResponse>(`/chat/${sessionId}`, {
    message,
    selected_region_context: selectedRegionContext,
  });
  return data;
}

export async function sendStatelessMessage(
  message: string,
  selectedRegionContext?: string
): Promise<ChatResponse> {
  const { data } = await client.post<ChatResponse>("/chat", {
    message,
    selected_region_context: selectedRegionContext,
  });
  return data;
}
