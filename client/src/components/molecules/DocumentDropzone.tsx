"use client";

import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";
import { cn } from "@/lib/cn";

interface DocumentDropzoneProps {
  /**
   * A plain array, not the DOM's own FileList - `event.target.files`/`dataTransfer.files` are
   * *live* objects tied to the input element, and get cleared the moment its value is reset
   * (right after this fires, so the input can accept the same file again later). Snapshotting
   * into a real array here, before that reset, means no caller can be bitten by acting on it
   * after the fact (e.g. inside a state updater callback, which React doesn't run inline - see
   * the "nothing shows up" bug this exact gap caused in CreateProjectScreen).
   */
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

export function DocumentDropzone({ onFiles, disabled }: DocumentDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  function browse() {
    if (!disabled) inputRef.current?.click();
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragOver(false);
    if (!disabled && event.dataTransfer.files.length) onFiles(Array.from(event.dataTransfer.files));
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      browse();
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Drop files or browse to upload project docs"
      aria-disabled={disabled}
      onClick={browse}
      onKeyDown={handleKeyDown}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      className={cn(
        "flex h-24 cursor-pointer items-center justify-center rounded-lg border border-dashed",
        "border-border px-3 text-center text-xs text-muted transition",
        isDragOver && "border-primary bg-primary-soft",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      Drop files or browse
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".md,.markdown,.txt,.pdf,.png,.jpg,.jpeg,.webp"
        className="hidden"
        disabled={disabled}
        onChange={(event) => {
          if (event.target.files?.length) onFiles(Array.from(event.target.files));
          event.target.value = "";
        }}
      />
    </div>
  );
}
