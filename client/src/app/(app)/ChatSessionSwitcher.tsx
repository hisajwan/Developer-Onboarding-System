"use client";

import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { useChatSessionContext } from "./ChatSessionProvider";

/** Ask mode's own conversation switcher: pick among this project's sessions, or start a new one. */
export function ChatSessionSwitcher() {
  const { sessions, currentSessionId, selectSession, createSession } = useChatSessionContext();
  const [isCreating, setIsCreating] = useState(false);

  async function handleNewSession() {
    setIsCreating(true);
    try {
      await createSession();
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      {sessions.length > 0 && (
        <select
          value={currentSessionId ?? ""}
          onChange={(event) => selectSession(event.target.value)}
          aria-label="Conversation"
          className="rounded-md border border-border bg-canvas px-2 py-1 text-xs outline-none focus:border-primary"
        >
          {sessions.map((session) => (
            <option key={session.id} value={session.id}>
              {session.name}
            </option>
          ))}
        </select>
      )}
      <Button
        type="button"
        variant="ghost"
        onClick={handleNewSession}
        disabled={isCreating}
        className="text-xs"
      >
        {isCreating ? "Creating…" : "+ New session"}
      </Button>
    </div>
  );
}
