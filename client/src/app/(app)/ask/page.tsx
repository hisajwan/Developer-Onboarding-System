"use client";

import { ChatPanel } from "@/components/organisms/ChatPanel";
import { PageTemplate } from "@/components/templates/PageTemplate";
import { useChatContext } from "../ChatProvider";

export default function AskPage() {
  const { messages, isSending, error, send } = useChatContext();

  return (
    <PageTemplate title="Ask about the codebase">
      <ChatPanel messages={messages} onSend={send} isSending={isSending} error={error} />
    </PageTemplate>
  );
}
