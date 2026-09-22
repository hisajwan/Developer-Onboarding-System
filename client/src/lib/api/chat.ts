import type { ChatHistoryResponse, ChatResponse } from "@/types/api";
import { apiFetch } from "./http";

export function sendChatMessage(projectId: string, message: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(`/projects/${projectId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function getChatHistory(projectId: string): Promise<ChatHistoryResponse> {
  return apiFetch<ChatHistoryResponse>(`/projects/${projectId}/chat/history`);
}
