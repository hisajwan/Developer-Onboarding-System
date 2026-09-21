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
        <p>{content}</p>
        {source && <p className="mt-1 text-xs text-muted">Source: {source}</p>}
      </div>
    </div>
  );
}
