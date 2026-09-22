import type { UploadResponse } from "@/types/document";
import { apiFetch } from "./http";

export function uploadDocument(projectId: string, file: File): Promise<UploadResponse> {
  const body = new FormData();
  body.append("file", file);
  return apiFetch<UploadResponse>(`/projects/${projectId}/documents`, { method: "POST", body });
}
