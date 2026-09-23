"use client";

import { ProjectDocsPanel } from "@/components/organisms/ProjectDocsPanel";
import { useProjectDocumentsContext } from "./ProjectDocumentsProvider";
import { useProjectContext } from "./ProjectProvider";

/** Shown alongside every module (Dashboard, Ask, Code review) once a project is active. */
export function ProjectDocsSidebar() {
  const { currentProjectId, isCreateScreenOpen } = useProjectContext();
  const { documents, isLoadingDocuments, uploads, uploadFiles, deleteFile } =
    useProjectDocumentsContext();

  // Hidden while creating a project: this panel reflects whatever project was current *before*
  // that screen opened (which is now deselected - see ProjectProvider), so showing it here would
  // look like those documents belong to the project being created.
  if (isCreateScreenOpen) return null;
  if (!currentProjectId) return null; // the page itself prompts for a project in this state

  return (
    <ProjectDocsPanel
      documents={documents}
      isLoadingDocuments={isLoadingDocuments}
      uploads={uploads}
      onFiles={uploadFiles}
      onDelete={deleteFile}
    />
  );
}
