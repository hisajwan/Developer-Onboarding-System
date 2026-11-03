"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { createChatSession, deleteChatSession, listChatSessions } from "@/lib/api/chatSessions";
import { readStored, writeStored } from "@/lib/storage";
import type { ChatSession } from "@/types/chatSession";
import { useProjectContext } from "./ProjectProvider";

interface ChatSessionContextValue {
  sessions: ChatSession[];
  /** `null` while a draft is open (or before anything has loaded). */
  currentSessionId: string | null;
  /** A new, unsaved conversation: it becomes a real session when its first question is sent. */
  isDraft: boolean;
  /** The name the draft will get once it is saved. */
  draftName: string;
  isLoading: boolean;
  selectSession: (sessionId: string) => void;
  /** Opens an empty draft; nothing is created on the server yet. */
  startDraft: () => void;
  /**
   * The id to send the next message to: the current session, or - for a draft - a session created
   * now. `beforeSwitch` runs with the new id before it becomes current, so the chat can keep the
   * message it is sending instead of reloading an empty history.
   */
  ensureSession: (beforeSwitch?: (sessionId: string) => void) => Promise<string>;
  /** Deletes these sessions and their messages; a project always keeps at least one. */
  deleteSessions: (sessionIds: string[]) => Promise<void>;
}

const ChatSessionContext = createContext<ChatSessionContextValue | null>(null);

// Project ids are unique per owner, so the project id alone scopes this to one user's project.
function lastSessionKey(projectId: string): string {
  return `last-chat-session:${projectId}`;
}

/** "Session N" one past the highest number in use, so a name isn't reused after a deletion. */
function nextSessionName(sessions: ChatSession[]): string {
  const numbers = sessions
    .map((session) => /^Session (\d+)$/.exec(session.name)?.[1])
    .filter((n): n is string => n !== undefined)
    .map(Number);
  return `Session ${Math.max(sessions.length, ...numbers) + 1}`;
}

/**
 * A project's conversation threads. Every project starts with one ("Session 1", created
 * server-side alongside the project itself); this tracks which one is active, opens drafts for new
 * ones, and deletes them. Reloads whenever the active project changes, reopening the session that
 * was last open in that project (remembered in this browser) if it still exists.
 */
export function ChatSessionProvider({ children }: { children: ReactNode }) {
  const { currentProjectId } = useProjectContext();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isDraft, setIsDraft] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsDraft(false);
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
      setIsDraft(false); // leaving a draft discards it; it was never saved
      setCurrentSessionId(sessionId);
      if (currentProjectId) writeStored(lastSessionKey(currentProjectId), sessionId);
    },
    [currentProjectId],
  );

  const startDraft = useCallback(() => {
    setIsDraft(true);
    setCurrentSessionId(null);
  }, []);

  const ensureSession = useCallback(
    async (beforeSwitch?: (sessionId: string) => void) => {
      if (!currentProjectId) throw new Error("No project selected.");
      if (currentSessionId) return currentSessionId;
      const session = await createChatSession(currentProjectId, nextSessionName(sessions));
      beforeSwitch?.(session.id);
      setSessions((current) => [...current, session]);
      setIsDraft(false);
      setCurrentSessionId(session.id);
      writeStored(lastSessionKey(currentProjectId), session.id);
      return session.id;
    },
    [currentProjectId, currentSessionId, sessions],
  );

  const deleteSessions = useCallback(
    async (sessionIds: string[]) => {
      if (!currentProjectId) throw new Error("No project selected.");
      try {
        for (const sessionId of sessionIds) {
          await deleteChatSession(currentProjectId, sessionId);
        }
      } finally {
        // Re-list even after a part-way failure: deleting the last session makes the server
        // start a fresh "Session 1", and the list should show what is actually left.
        const list = await listChatSessions(currentProjectId);
        setSessions(list);
        if (!isDraft && !list.some((session) => session.id === currentSessionId)) {
          const next = list[0];
          setCurrentSessionId(next?.id ?? null);
          if (next) writeStored(lastSessionKey(currentProjectId), next.id);
        }
      }
    },
    [currentProjectId, currentSessionId, isDraft],
  );

  return (
    <ChatSessionContext.Provider
      value={{
        sessions,
        currentSessionId,
        isDraft,
        draftName: nextSessionName(sessions),
        isLoading,
        selectSession,
        startDraft,
        ensureSession,
        deleteSessions,
      }}
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
