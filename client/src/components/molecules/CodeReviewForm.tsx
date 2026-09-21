"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { Textarea } from "@/components/atoms/Textarea";

interface CodeReviewFormProps {
  onSubmit: (code: string) => void;
  initialCode?: string;
  disabled?: boolean;
}

export function CodeReviewForm({ onSubmit, initialCode = "", disabled }: CodeReviewFormProps) {
  const [code, setCode] = useState(initialCode);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!code.trim()) return;
    onSubmit(code);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-start gap-3">
      <Textarea
        value={code}
        onChange={(event) => setCode(event.target.value)}
        placeholder="Paste a React or TypeScript snippet to review..."
        aria-label="Code to review"
        rows={10}
        spellCheck={false}
        className="font-mono text-xs"
      />
      <Button type="submit" disabled={disabled || !code.trim()}>
        Review
      </Button>
    </form>
  );
}
