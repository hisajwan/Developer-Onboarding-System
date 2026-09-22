import { cn } from "@/lib/cn";
import type { UploadState } from "@/types/document";

const STATUS_TEXT: Record<UploadState["status"], string> = {
  uploading: "Uploading...",
  indexed: "Indexed",
  unchanged: "Already indexed",
  error: "Failed",
};

const STATUS_CLASS: Record<UploadState["status"], string> = {
  uploading: "text-muted",
  indexed: "text-primary",
  unchanged: "text-muted",
  error: "text-danger",
};

export function UploadStatusItem({ filename, status, message }: Omit<UploadState, "id">) {
  return (
    <li className="flex flex-col gap-0.5 text-xs">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-ink">{filename}</span>
        <span className={cn("shrink-0 font-medium", STATUS_CLASS[status])}>
          {STATUS_TEXT[status]}
        </span>
      </div>
      {message && <span className="text-muted">{message}</span>}
    </li>
  );
}
