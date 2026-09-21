import type { ChatResponse } from "@/types/api";
import { apiFetch } from "./http";

export function sendChatMessage(message: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
