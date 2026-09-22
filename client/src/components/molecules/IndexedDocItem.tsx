import { pluralChunks } from "@/lib/format";
import type { UploadedDocument } from "@/types/document";

export function IndexedDocItem({ document }: { document: UploadedDocument }) {
  return (
    <li className="flex items-center justify-between gap-2 text-xs">
      <span className="truncate text-ink">{document.filename}</span>
      <span className="shrink-0 text-muted">{pluralChunks(document.chunk_count)}</span>
    </li>
  );
}
