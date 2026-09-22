"use client";

import { usePathname } from "next/navigation";
import { ProjectDocsPanel } from "@/components/organisms/ProjectDocsPanel";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";
import { useProjectContext } from "./ProjectProvider";

/** Shown in the shared sidebar, but only on the Ask screen — matches the wireframe's placement. */
export function AskDocsSidebar() {
  const pathname = usePathname();
  const { currentProjectId } = useProjectContext();
  const { uploads, upload } = useDocumentUpload(currentProjectId);

  if (pathname !== "/ask") return null;
  if (!currentProjectId) return null; // AskPage itself prompts for a project in this state

  return <ProjectDocsPanel uploads={uploads} onFiles={upload} />;
}
