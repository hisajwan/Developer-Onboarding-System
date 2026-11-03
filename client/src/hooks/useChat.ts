"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getChatHistory, sendChatMessage } from "@/lib/api/chat";
import type { ChatMessage } from "@/types/chat";

/**
 * `sessionId` is `null` while a draft is open: the chat starts empty, and the first message sent
 * creates the session (through `ensureSession`) before it is sent. With no project, sending is a
 * no-op.
 */
export function useChat(
  projectId: string | null,
  sessionId: string | null,
  ensureSession: (beforeSwitch: (sessionId: string) => void) => Promise<string>,
) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // A session just created from a draft: its history is the message being sent right now, so
  // reloading it would only wipe that message off the screen.
  const createdFromDraftRef = useRef<string | null>(null);

  // Reloads the saved conversation whenever the selected session changes, including on the first
  // mount after a page reload - this is what makes the chat survive a refresh, not just a nav.
  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      if (sessionId && sessionId === createdFromDraftRef.current) {
        createdFromDraftRef.current = null;
        return;
      }
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
            source: message.sources.join(", ") || undefined,
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
      if (!projectId) return;
      setError(null);
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "user", content: text },
      ]);
      setIsSending(true);
      try {
        const targetId =
          sessionId ??
          (await ensureSession((createdId) => {
            createdFromDraftRef.current = createdId;
          }));
        const response = await sendChatMessage(projectId, targetId, text);
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
    [projectId, sessionId, ensureSession],
  );

  return { messages, isLoadingHistory, isSending, error, send };
}
