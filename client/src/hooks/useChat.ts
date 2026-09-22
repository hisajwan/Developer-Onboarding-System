"use client";

import { useCallback, useEffect, useState } from "react";
import { getChatHistory, sendChatMessage } from "@/lib/api/chat";
import type { ChatMessage } from "@/types/chat";

/** `null` while no project is selected yet - chat stays empty and sending is a no-op. */
export function useChat(projectId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reloads the saved conversation whenever the selected project changes, including on the first
  // mount after a page reload - this is what makes the chat survive a refresh, not just a nav.
  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      if (!projectId) {
        setMessages([]);
        return;
      }
      setIsLoadingHistory(true);
      try {
        const history = await getChatHistory(projectId);
        if (cancelled) return;
        setMessages(
          history.messages.map((message) => ({
            id: crypto.randomUUID(),
            role: message.role,
            content: message.content,
          })),
        );
      } catch {
        // A failed history load starts the project with an empty (not broken) chat.
      } finally {
        if (!cancelled) setIsLoadingHistory(false);
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const send = useCallback(
    async (text: string) => {
      if (!projectId) return;
      setError(null);
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "user", content: text },
      ]);
      setIsSending(true);
      try {
        const response = await sendChatMessage(projectId, text);
        setMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: response.reply,
            source: response.sources.join(", ") || undefined,
          },
        ]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong.");
      } finally {
        setIsSending(false);
      }
    },
    [projectId],
  );

  return { messages, isLoadingHistory, isSending, error, send };
}
