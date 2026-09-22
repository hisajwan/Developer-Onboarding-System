"use client";

import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";
import { cn } from "@/lib/cn";

interface DocumentDropzoneProps {
  onFiles: (files: FileList) => void;
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
    if (!disabled && event.dataTransfer.files.length) onFiles(event.dataTransfer.files);
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
        accept=".md,.markdown,.txt,.pdf"
        className="hidden"
        disabled={disabled}
        onChange={(event) => {
          if (event.target.files?.length) onFiles(event.target.files);
          event.target.value = "";
        }}
      />
    </div>
  );
}
