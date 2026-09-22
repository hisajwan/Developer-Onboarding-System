"use client";

import { useCallback, useEffect, useState } from "react";
import { listDocuments } from "@/lib/api/documents";
import type { UploadedDocument } from "@/types/document";

/** The documents already indexed for a project - what survives a reload, unlike upload status. */
export function useProjectDocuments(projectId: string | null) {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Loads on mount and on every project switch, including the first mount after a page reload.
  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!projectId) {
        setDocuments([]);
        return;
      }
      setIsLoading(true);
      try {
        const list = await listDocuments(projectId);
        if (!cancelled) setDocuments(list);
      } catch {
        // A failed load leaves the previous list showing rather than blanking it.
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  // Callable directly too, e.g. right after an upload finishes, without waiting for a re-render.
  const reload = useCallback(async () => {
    if (!projectId) {
      setDocuments([]);
      return;
    }
    setIsLoading(true);
    try {
      setDocuments(await listDocuments(projectId));
    } catch {
      // A failed reload leaves the previous list showing rather than blanking it.
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  return { documents, isLoadingDocuments: isLoading, reload };
}
