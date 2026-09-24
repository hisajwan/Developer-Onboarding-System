import { Markdown } from "@/components/atoms/Markdown";
import { cn } from "@/lib/cn";
import type { ChatMessage } from "@/types/chat";

export function MessageBubble({ role, content, source }: Omit<ChatMessage, "id">) {
  const isUser = role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-xl rounded-xl px-4 py-3 text-sm",
          isUser ? "bg-primary text-primary-contrast" : "bg-bubble text-ink",
        )}
      >
        {isUser ? (
          // What the user typed, as typed: line breaks and pasted code kept.
          <p className="whitespace-pre-wrap break-words">{content}</p>
        ) : (
          <Markdown>{content}</Markdown>
        )}
        {source && <p className="mt-2 text-xs text-muted">Source: {source}</p>}
      </div>
    </div>
  );
}
