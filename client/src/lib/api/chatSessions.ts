import type { ChatSession } from "@/types/chatSession";
import { apiFetch } from "./http";

export async function listChatSessions(projectId: string): Promise<ChatSession[]> {
  const { sessions } = await apiFetch<{ sessions: ChatSession[] }>(
    `/projects/${projectId}/sessions`,
  );
  return sessions;
}

export function createChatSession(projectId: string, name?: string): Promise<ChatSession> {
  return apiFetch<ChatSession>(`/projects/${projectId}/sessions`, {
    method: "POST",
    body: JSON.stringify(name ? { name } : {}),
  });
}
