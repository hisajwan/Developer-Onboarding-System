import type { ChatHistoryResponse, ChatResponse } from "@/types/api";
import { apiFetch } from "./http";

export function sendChatMessage(
  projectId: string,
  sessionId: string,
  message: string,
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(`/projects/${projectId}/sessions/${sessionId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function getChatHistory(projectId: string, sessionId: string): Promise<ChatHistoryResponse> {
  return apiFetch<ChatHistoryResponse>(`/projects/${projectId}/sessions/${sessionId}/chat/history`);
}
