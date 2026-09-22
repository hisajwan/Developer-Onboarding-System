export interface UploadedDocument {
  filename: string;
  chunk_count: number;
  indexed_at: string;
}

export interface UploadResponse {
  document: UploadedDocument;
  status: "indexed" | "unchanged";
  chunks_embedded: number;
}

export interface UploadState {
  id: string;
  filename: string;
  status: "uploading" | "indexed" | "unchanged" | "error";
  message?: string;
}
