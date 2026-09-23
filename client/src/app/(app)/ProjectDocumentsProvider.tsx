"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api/documents";
import { ApiError } from "@/lib/api/http";
import { pluralChunks } from "@/lib/format";
import type { UploadedDocument, UploadState } from "@/types/document";
import { useProjectContext } from "./ProjectProvider";

interface ProjectDocumentsContextValue {
  documents: UploadedDocument[];
  isLoadingDocuments: boolean;
  uploads: UploadState[];
  /**
   * `projectId` defaults to whichever project is current. Pass it explicitly right after
   * creating a project: the function reference a caller already holds was captured on a render
   * where the new project didn't exist yet, so it would otherwise still act on the old (or no)
   * project - see CreateProjectScreen, which is exactly this case.
   */
  uploadFiles: (files: File[], projectId?: string) => Promise<void>;
  deleteFile: (filename: string, projectId?: string) => Promise<void>;
  reloadDocuments: (projectId?: string) => Promise<void>;
}

const ProjectDocumentsContext = createContext<ProjectDocumentsContextValue | null>(null);

/**
 * The current project's documents, shared by every consumer - the docs panel and the
 * create-project screen's own upload both read and write this same state, instead of each
 * keeping their own. That sharing is what fixes docs not showing up right after creating a
 * project and landing on Ask: without it, the docs panel's own fetch could run (and find nothing
 * indexed yet) before the creation screen's upload had finished.
 */
export function ProjectDocumentsProvider({ children }: { children: ReactNode }) {
  const { currentProjectId } = useProjectContext();
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [uploads, setUploads] = useState<UploadState[]>([]);
  // Every fetch of the document list (whether from the effect below or an explicit reload) claims
  // the next number and only commits its result if it's still the most recently *issued* one by
  // the time it resolves - otherwise a slow, now-stale fetch (e.g. the effect's own reload, fired
  // the instant the project changes) could overwrite a newer one that resolves first.
  const latestRequestRef = useRef(0);

  const fetchAndCommit = useCallback(async (targetId: string) => {
    const requestId = ++latestRequestRef.current;
    setIsLoadingDocuments(true);
    try {
      const list = await listDocuments(targetId);
      if (latestRequestRef.current === requestId) setDocuments(list);
    } catch {
      // A failed load/reload leaves the previous list showing rather than blanking it.
    } finally {
      if (latestRequestRef.current === requestId) setIsLoadingDocuments(false);
    }
  }, []);

  const reloadDocuments = useCallback(
    async (projectId?: string) => {
      const targetId = projectId ?? currentProjectId;
      if (!targetId) {
        latestRequestRef.current += 1; // invalidates any fetch still in flight
        setDocuments([]);
        return;
      }
      await fetchAndCommit(targetId);
    },
    [currentProjectId, fetchAndCommit],
  );

  // Loads on mount and on every project switch, including the first mount after a page reload.
  useEffect(() => {
    function run() {
      if (!currentProjectId) {
        latestRequestRef.current += 1;
        setDocuments([]);
        return;
      }
      fetchAndCommit(currentProjectId);
    }
    run();
  }, [currentProjectId, fetchAndCommit]);

  const uploadFiles = useCallback(
    async (files: File[], projectId?: string) => {
      const targetId = projectId ?? currentProjectId;
      if (!targetId) return;
      // Collected rather than thrown immediately, so one bad file doesn't stop the rest from
      // uploading - but still surfaced at the end (see below), so a caller that specifically
      // needs to know knows. Without this, a failed upload was previously silent to anyone
      // awaiting uploadFiles: it only ever showed up in the `uploads` status list, which a caller
      // like CreateProjectScreen never looks at before navigating away.
      const failures: string[] = [];
      // One at a time: keeps status updates predictable and avoids bursting the backend.
      for (const file of files) {
        const id = crypto.randomUUID();
        setUploads((current) => [...current, { id, filename: file.name, status: "uploading" }]);
        try {
          const response = await uploadDocument(targetId, file);
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
          const message = err instanceof ApiError ? err.message : "Upload failed.";
          failures.push(`${file.name} (${message})`);
          setUploads((current) =>
            current.map((item) =>
              item.id === id ? { ...item, status: "error", message } : item,
            ),
          );
        }
      }
      await reloadDocuments(targetId);
      if (failures.length > 0) {
        throw new Error(`Could not upload: ${failures.join(", ")}`);
      }
    },
    [currentProjectId, reloadDocuments],
  );

  const deleteFile = useCallback(
    async (filename: string, projectId?: string) => {
      const targetId = projectId ?? currentProjectId;
      if (!targetId) return;
      await deleteDocument(targetId, filename);
      await reloadDocuments(targetId);
    },
    [currentProjectId, reloadDocuments],
  );

  return (
    <ProjectDocumentsContext.Provider
      value={{ documents, isLoadingDocuments, uploads, uploadFiles, deleteFile, reloadDocuments }}
    >
      {children}
    </ProjectDocumentsContext.Provider>
  );
}

export function useProjectDocumentsContext(): ProjectDocumentsContextValue {
  const context = useContext(ProjectDocumentsContext);
  if (!context) {
    throw new Error("useProjectDocumentsContext must be used within ProjectDocumentsProvider.");
  }
  return context;
}
