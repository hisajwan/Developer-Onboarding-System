"use client";

import { useCallback, useState } from "react";
import { uploadDocument } from "@/lib/api/documents";
import { ApiError } from "@/lib/api/http";
import type { UploadState } from "@/types/document";

function pluralChunks(count: number): string {
  return `${count} chunk${count === 1 ? "" : "s"}`;
}

export function useDocumentUpload() {
  const [uploads, setUploads] = useState<UploadState[]>([]);

  const upload = useCallback(async (files: FileList) => {
    // One at a time: keeps status updates predictable and avoids bursting the backend.
    for (const file of Array.from(files)) {
      const id = crypto.randomUUID();
      setUploads((current) => [...current, { id, filename: file.name, status: "uploading" }]);
      try {
        const response = await uploadDocument(file);
        setUploads((current) =>
          current.map((item) =>
            item.id === id
              ? {
                  ...item,
                  status: response.status,
                  message:
                    response.status === "indexed"
                      ? pluralChunks(response.document.chunk_count)
                      : undefined,
                }
              : item,
          ),
        );
      } catch (err) {
        setUploads((current) =>
          current.map((item) =>
            item.id === id
              ? {
                  ...item,
                  status: "error",
                  message: err instanceof ApiError ? err.message : "Upload failed.",
                }
              : item,
          ),
        );
      }
    }
  }, []);

  return { uploads, upload };
}
