"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { TextInput } from "@/components/atoms/TextInput";

interface ChatComposerProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatComposer({ onSend, disabled }: ChatComposerProps) {
  const [text, setText] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <TextInput
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Ask about the codebase..."
        aria-label="Your question"
      />
      <Button type="submit" disabled={disabled || !text.trim()}>
        Send
      </Button>
    </form>
  );
}
