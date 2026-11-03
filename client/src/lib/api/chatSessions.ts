import type { ChatSession } from "@/types/chatSession";
import { apiFetch } from "./http";

export async function listChatSessions(projectId: string): Promise<ChatSession[]> {
  const { sessions } = await apiFetch<{ sessions: ChatSession[] }>(
    `/projects/${projectId}/sessions`,
  );
  return sessions;
}

/** Deleting a project's last session leaves a fresh "Session 1" on the server; re-list after. */
export function deleteChatSession(projectId: string, sessionId: string): Promise<void> {
  return apiFetch<void>(`/projects/${projectId}/sessions/${sessionId}`, { method: "DELETE" });
}

export function createChatSession(projectId: string, name?: string): Promise<ChatSession> {
  return apiFetch<ChatSession>(`/projects/${projectId}/sessions`, {
    method: "POST",
    body: JSON.stringify(name ? { name } : {}),
  });
}
