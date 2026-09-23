"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { Select } from "@/components/atoms/Select";
import { Textarea } from "@/components/atoms/Textarea";
import { SNIPPET_LANGUAGES } from "@/config/review";
import type { SnippetLanguage } from "@/types/review";

interface CodeReviewFormProps {
  onSubmit: (code: string, language: SnippetLanguage) => void;
  isReviewing?: boolean;
}

export function CodeReviewForm({ onSubmit, isReviewing }: CodeReviewFormProps) {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState<SnippetLanguage>("tsx");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!code.trim() || isReviewing) return;
    onSubmit(code, language);
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
      <div className="flex items-center gap-3">
        <Select
          value={language}
          onChange={(event) => setLanguage(event.target.value as SnippetLanguage)}
          aria-label="Language"
          disabled={isReviewing}
        >
          {SNIPPET_LANGUAGES.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
        <Button type="submit" disabled={isReviewing || !code.trim()}>
          {isReviewing ? "Reviewing…" : "Review"}
        </Button>
      </div>
    </form>
  );
}
