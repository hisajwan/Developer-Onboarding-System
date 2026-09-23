"use client";

import { useCallback, useEffect, useState } from "react";
import { getChatHistory, sendChatMessage } from "@/lib/api/chat";
import type { ChatMessage } from "@/types/chat";

/**
 * Either id `null` while no project/session is selected yet - chat stays empty and sending is a
 * no-op until both exist.
 */
export function useChat(projectId: string | null, sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reloads the saved conversation whenever the selected session changes, including on the first
  // mount after a page reload - this is what makes the chat survive a refresh, not just a nav.
  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      if (!projectId || !sessionId) {
        setMessages([]);
        return;
      }
      setIsLoadingHistory(true);
      try {
        const history = await getChatHistory(projectId, sessionId);
        if (cancelled) return;
        setMessages(
          history.messages.map((message) => ({
            id: crypto.randomUUID(),
            role: message.role,
            content: message.content,
          })),
        );
      } catch {
        // A failed history load starts the session with an empty (not broken) chat.
      } finally {
        if (!cancelled) setIsLoadingHistory(false);
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [projectId, sessionId]);

  const send = useCallback(
    async (text: string) => {
      if (!projectId || !sessionId) return;
      setError(null);
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "user", content: text },
      ]);
      setIsSending(true);
      try {
        const response = await sendChatMessage(projectId, sessionId, text);
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
    [projectId, sessionId],
  );

  return { messages, isLoadingHistory, isSending, error, send };
}
