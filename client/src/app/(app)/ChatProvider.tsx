"use client";

import { createContext, useContext, type ReactNode } from "react";
import { useChat } from "@/hooks/useChat";
import { useChatSessionContext } from "./ChatSessionProvider";
import { useProjectContext } from "./ProjectProvider";

type ChatContextValue = ReturnType<typeof useChat>;

const ChatContext = createContext<ChatContextValue | null>(null);

/**
 * Holds Ask mode's chat state at the layout level, so it survives navigating to another screen
 * and back — a page component alone would remount and lose it. Scoped to whatever project and
 * session ProjectProvider/ChatSessionProvider say are current, and reloads that session's saved
 * history on every switch.
 */
export function ChatProvider({ children }: { children: ReactNode }) {
  const { currentProjectId } = useProjectContext();
  const { currentSessionId } = useChatSessionContext();
  const chat = useChat(currentProjectId, currentSessionId);
  return <ChatContext.Provider value={chat}>{children}</ChatContext.Provider>;
}

export function useChatContext(): ChatContextValue {
  const chat = useContext(ChatContext);
  if (!chat) throw new Error("useChatContext must be used within ChatProvider.");
  return chat;
}
