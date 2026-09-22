import type { DocumentListResponse, UploadedDocument, UploadResponse } from "@/types/document";
import { apiFetch } from "./http";

export function uploadDocument(projectId: string, file: File): Promise<UploadResponse> {
  const body = new FormData();
  body.append("file", file);
  return apiFetch<UploadResponse>(`/projects/${projectId}/documents`, { method: "POST", body });
}

export async function listDocuments(projectId: string): Promise<UploadedDocument[]> {
  const { documents } = await apiFetch<DocumentListResponse>(`/projects/${projectId}/documents`);
  return documents;
}

export function deleteDocument(projectId: string, filename: string): Promise<void> {
  return apiFetch<void>(`/projects/${projectId}/documents/${encodeURIComponent(filename)}`, {
    method: "DELETE",
  });
}
