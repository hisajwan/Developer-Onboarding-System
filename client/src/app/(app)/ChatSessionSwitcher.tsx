"use client";

import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { Select } from "@/components/atoms/Select";
import { SettingsButton } from "@/components/atoms/SettingsButton";
import { BulkDeleteModal } from "@/components/molecules/BulkDeleteModal";
import { useChatSessionContext } from "./ChatSessionProvider";

const DRAFT_VALUE = "__draft__";

/**
 * Ask mode's conversation switcher: manage (delete) sessions from the gear, pick one, or open a
 * draft for a new one - the draft only becomes a real session when its first question is sent.
 */
export function ChatSessionSwitcher() {
  const {
    sessions,
    currentSessionId,
    isDraft,
    draftName,
    selectSession,
    startDraft,
    deleteSessions,
  } = useChatSessionContext();
  const [isManageOpen, setIsManageOpen] = useState(false);

  return (
    <div className="flex items-center gap-2">
      <SettingsButton label="Manage sessions" onClick={() => setIsManageOpen(true)} />
      {(sessions.length > 0 || isDraft) && (
        <Select
          value={isDraft ? DRAFT_VALUE : (currentSessionId ?? "")}
          onChange={(event) => {
            if (event.target.value !== DRAFT_VALUE) selectSession(event.target.value);
          }}
          aria-label="Conversation"
        >
          {sessions.map((session) => (
            <option key={session.id} value={session.id}>
              {session.name}
            </option>
          ))}
          {isDraft && <option value={DRAFT_VALUE}>{draftName} (new)</option>}
        </Select>
      )}
      <Button
        type="button"
        variant="ghost"
        onClick={startDraft}
        disabled={isDraft}
        className="text-xs"
      >
        + New session
      </Button>
      <BulkDeleteModal
        isOpen={isManageOpen}
        onClose={() => setIsManageOpen(false)}
        title="Manage sessions"
        noun={["session", "sessions"]}
        items={sessions.map((session) => ({
          id: session.id,
          label: session.name,
          detail: session.id === currentSessionId ? "open now" : undefined,
        }))}
        consequence="Their messages are deleted with them. If none are left, a new, empty Session 1 is started."
        onDelete={deleteSessions}
      />
    </div>
  );
}
