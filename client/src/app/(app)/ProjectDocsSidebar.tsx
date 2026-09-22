"use client";

import { usePathname } from "next/navigation";
import { useCallback } from "react";
import { ProjectDocsPanel } from "@/components/organisms/ProjectDocsPanel";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";
import { useProjectDocuments } from "@/hooks/useProjectDocuments";
import { useProjectContext } from "./ProjectProvider";

const PATHS_WITH_DOCS_PANEL = ["/ask", "/code-review"];

/**
 * Shown in the shared sidebar on any screen that works from the project's docs (Ask, Code
 * review) — not the Dashboard, which has nothing to upload to.
 */
export function ProjectDocsSidebar() {
  const pathname = usePathname();
  const { currentProjectId } = useProjectContext();
  const { documents, isLoadingDocuments, reload } = useProjectDocuments(currentProjectId);
  const { uploads, upload } = useDocumentUpload(currentProjectId);

  const uploadAndRefresh = useCallback(
    async (files: FileList) => {
      await upload(files);
      await reload();
    },
    [upload, reload],
  );

  if (!PATHS_WITH_DOCS_PANEL.includes(pathname)) return null;
  if (!currentProjectId) return null; // the page itself prompts for a project in this state

  return (
    <ProjectDocsPanel
      documents={documents}
      isLoadingDocuments={isLoadingDocuments}
      uploads={uploads}
      onFiles={uploadAndRefresh}
    />
  );
}
