import { Heading } from "@/components/atoms/Heading";
import { DocumentDropzone } from "@/components/molecules/DocumentDropzone";
import { IndexedDocItem } from "@/components/molecules/IndexedDocItem";
import { UploadStatusItem } from "@/components/molecules/UploadStatusItem";
import type { UploadedDocument, UploadState } from "@/types/document";

interface ProjectDocsPanelProps {
  documents: UploadedDocument[];
  isLoadingDocuments?: boolean;
  uploads: UploadState[];
  onFiles: (files: File[]) => void;
  onDelete: (filename: string) => Promise<void>;
}

export function ProjectDocsPanel({
  documents,
  isLoadingDocuments,
  uploads,
  onFiles,
  onDelete,
}: ProjectDocsPanelProps) {
  // Uploads that just finished are already in `documents` too (it's reloaded after each one) -
  // only show ones still in flight or failed here, so a finished upload isn't listed twice.
  const inFlight = uploads.filter((item) => item.status === "uploading" || item.status === "error");

  return (
    <div className="flex flex-col gap-3">
      <Heading as="h2">Project docs</Heading>
      <DocumentDropzone onFiles={onFiles} />
      {inFlight.length > 0 && (
        <ul className="flex flex-col gap-2" aria-live="polite">
          {inFlight.map((item) => (
            <UploadStatusItem
              key={item.id}
              filename={item.filename}
              status={item.status}
              message={item.message}
            />
          ))}
        </ul>
      )}
      {isLoadingDocuments && documents.length === 0 ? (
        <p className="text-xs text-muted">Loading documents...</p>
      ) : documents.length > 0 ? (
        <ul className="flex max-h-64 flex-col gap-2 overflow-y-auto">
          {documents.map((document) => (
            <IndexedDocItem key={document.filename} document={document} onDelete={onDelete} />
          ))}
        </ul>
      ) : (
        inFlight.length === 0 && <p className="text-xs text-muted">No documents yet.</p>
      )}
    </div>
  );
}
