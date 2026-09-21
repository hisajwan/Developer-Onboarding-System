import { ChatComposer } from "@/components/molecules/ChatComposer";
import { MessageBubble } from "@/components/molecules/MessageBubble";
import type { ChatMessage } from "@/types/chat";

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  isSending: boolean;
  error: string | null;
}

export function ChatPanel({ messages, onSend, isSending, error }: ChatPanelProps) {
  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto" aria-live="polite">
        {messages.map(({ id, ...message }) => (
          <MessageBubble key={id} {...message} />
        ))}
        {isSending && <p className="text-xs text-muted">Thinking...</p>}
        {error && (
          <p role="alert" className="text-xs text-danger">
            {error}
          </p>
        )}
      </div>
      <ChatComposer onSend={onSend} disabled={isSending} />
    </div>
  );
}
