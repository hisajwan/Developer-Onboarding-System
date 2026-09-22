"use client";

import { ChatPanel } from "@/components/organisms/ChatPanel";
import { PageTemplate } from "@/components/templates/PageTemplate";
import { ChatSessionSwitcher } from "../ChatSessionSwitcher";
import { useChatContext } from "../ChatProvider";
import { useProjectContext } from "../ProjectProvider";

export default function AskPage() {
  const { messages, isLoadingHistory, isSending, error, send } = useChatContext();
  const { currentProjectId, isLoading: isLoadingProjects } = useProjectContext();

  if (!currentProjectId) {
    return (
      <PageTemplate title="Ask about the codebase">
        <p className="text-sm text-muted">
          {isLoadingProjects
            ? "Loading your projects…"
            : "Create a project (see the sidebar) before asking a question."}
        </p>
      </PageTemplate>
    );
  }

  return (
    <PageTemplate title="Ask about the codebase">
      <div className="flex h-full flex-col gap-4">
        <div className="flex justify-end">
          <ChatSessionSwitcher />
        </div>
        <div className="min-h-0 flex-1">
          <ChatPanel
            messages={messages}
            onSend={send}
            isSending={isSending}
            isLoadingHistory={isLoadingHistory}
            error={error}
          />
        </div>
      </div>
    </PageTemplate>
  );
}
