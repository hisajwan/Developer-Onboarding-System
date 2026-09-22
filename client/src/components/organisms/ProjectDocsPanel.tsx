import { Heading } from "@/components/atoms/Heading";
import { DocumentDropzone } from "@/components/molecules/DocumentDropzone";
import { UploadStatusItem } from "@/components/molecules/UploadStatusItem";
import type { UploadState } from "@/types/document";

interface ProjectDocsPanelProps {
  uploads: UploadState[];
  onFiles: (files: FileList) => void;
}

export function ProjectDocsPanel({ uploads, onFiles }: ProjectDocsPanelProps) {
  return (
    <div className="flex flex-col gap-3">
      <Heading as="h2">Project docs</Heading>
      <DocumentDropzone onFiles={onFiles} />
      {uploads.length > 0 && (
        <ul className="flex flex-col gap-2" aria-live="polite">
          {uploads.map((item) => (
            <UploadStatusItem
              key={item.id}
              filename={item.filename}
              status={item.status}
              message={item.message}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
