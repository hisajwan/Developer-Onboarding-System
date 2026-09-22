"use client";

import { ChatPanel } from "@/components/organisms/ChatPanel";
import { PageTemplate } from "@/components/templates/PageTemplate";
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
      <ChatPanel
        messages={messages}
        onSend={send}
        isSending={isSending}
        isLoadingHistory={isLoadingHistory}
        error={error}
      />
    </PageTemplate>
  );
}
