"use client";

import { usePathname } from "next/navigation";
import { ProjectDocsPanel } from "@/components/organisms/ProjectDocsPanel";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";

/** Shown in the shared sidebar, but only on the Ask screen — matches the wireframe's placement. */
export function AskDocsSidebar() {
  const pathname = usePathname();
  const { uploads, upload } = useDocumentUpload();

  if (pathname !== "/ask") return null;

  return <ProjectDocsPanel uploads={uploads} onFiles={upload} />;
}
