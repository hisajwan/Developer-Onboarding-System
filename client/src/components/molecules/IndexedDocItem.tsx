"use client";

import { useState } from "react";
import { pluralChunks } from "@/lib/format";
import type { UploadedDocument } from "@/types/document";

interface IndexedDocItemProps {
  document: UploadedDocument;
  onDelete: (filename: string) => Promise<void>;
}

export function IndexedDocItem({ document, onDelete }: IndexedDocItemProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    setError(null);
    setIsDeleting(true);
    try {
      await onDelete(document.filename);
    } catch {
      setError("Could not remove this document.");
      setIsDeleting(false);
    }
    // No `finally` reset of isDeleting on success: the item is about to be removed from the list
    // entirely once the parent reloads, so there is nothing left to un-disable.
  }

  return (
    <li className="flex flex-col gap-0.5 text-xs">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-ink">{document.filename}</span>
        <span className="flex shrink-0 items-center gap-2">
          <span className="text-muted">{pluralChunks(document.chunk_count)}</span>
          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
            aria-label={`Remove ${document.filename}`}
            title={`Remove ${document.filename}`}
            className="text-muted hover:text-danger disabled:cursor-not-allowed disabled:opacity-50"
          >
            ×
          </button>
        </span>
      </div>
      {error && <span className="text-danger">{error}</span>}
    </li>
  );
}
