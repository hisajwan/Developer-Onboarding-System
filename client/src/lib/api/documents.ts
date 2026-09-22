import type { UploadResponse } from "@/types/document";
import { apiFetch } from "./http";

export function uploadDocument(file: File): Promise<UploadResponse> {
  const body = new FormData();
  body.append("file", file);
  return apiFetch<UploadResponse>("/documents", { method: "POST", body });
}
