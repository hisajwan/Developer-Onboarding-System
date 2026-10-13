"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { createChatSession, listChatSessions } from "@/lib/api/chatSessions";
import { readStored, writeStored } from "@/lib/storage";
import type { ChatSession } from "@/types/chatSession";
import { useProjectContext } from "./ProjectProvider";

interface ChatSessionContextValue {
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  selectSession: (sessionId: string) => void;
  createSession: () => Promise<ChatSession>;
}

const ChatSessionContext = createContext<ChatSessionContextValue | null>(null);

// Project ids are unique per owner, so the project id alone scopes this to one user's project.
function lastSessionKey(projectId: string): string {
  return `last-chat-session:${projectId}`;
}

/**
 * A project's conversation threads. Every project starts with one ("Session 1", created
 * server-side alongside the project itself); this just tracks which one is active and lets Ask
 * mode start a new one. Reloads whenever the active project changes, reopening the session that
 * was last open in that project (remembered in this browser) if it still exists.
 */
export function ChatSessionProvider({ children }: { children: ReactNode }) {
  const { currentProjectId } = useProjectContext();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!currentProjectId) {
        setSessions([]);
        setCurrentSessionId(null);
        return;
      }
      setIsLoading(true);
      try {
        const list = await listChatSessions(currentProjectId);
        if (cancelled) return;
        setSessions(list);
        const remembered = readStored(lastSessionKey(currentProjectId));
        const reopened = list.find((session) => session.id === remembered) ?? list[0];
        setCurrentSessionId(reopened?.id ?? null);
      } catch {
        // Leaves sessions empty; Ask mode's own empty state covers this.
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [currentProjectId]);

  const selectSession = useCallback(
    (sessionId: string) => {
      setCurrentSessionId(sessionId);
      if (currentProjectId) writeStored(lastSessionKey(currentProjectId), sessionId);
    },
    [currentProjectId],
  );

  const createSession = useCallback(async () => {
    if (!currentProjectId) throw new Error("No project selected.");
    const ordinal = sessions.length + 1;
    const session = await createChatSession(currentProjectId, `Session ${ordinal}`);
    setSessions((current) => [...current, session]);
    setCurrentSessionId(session.id);
    writeStored(lastSessionKey(currentProjectId), session.id);
    return session;
  }, [currentProjectId, sessions.length]);

  return (
    <ChatSessionContext.Provider
      value={{ sessions, currentSessionId, isLoading, selectSession, createSession }}
    >
      {children}
    </ChatSessionContext.Provider>
  );
}

export function useChatSessionContext(): ChatSessionContextValue {
  const context = useContext(ChatSessionContext);
  if (!context) throw new Error("useChatSessionContext must be used within ChatSessionProvider.");
  return context;
}
