"use client";

import { useRouter } from "next/navigation";
import { useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { Heading } from "@/components/atoms/Heading";
import { TextInput } from "@/components/atoms/TextInput";
import { DocumentDropzone } from "@/components/molecules/DocumentDropzone";
import { ApiError } from "@/lib/api/http";
import { useProjectDocumentsContext } from "./ProjectDocumentsProvider";
import { useProjectContext } from "./ProjectProvider";

/**
 * Creating a project needs a name and at least one document together, not a project created
 * empty - the first thing anyone would do in Ask mode is ask about a doc, so start with one
 * already there. Shown full-page for the very first project (nothing to cancel back to), or
 * opened over the current screen for any project after that (see ProjectSwitcher's "+").
 */
export function CreateProjectScreen() {
  const router = useRouter();
  const { projects, createProject, closeCreateScreen } = useProjectContext();
  const { uploadFiles } = useProjectDocumentsContext();
  const [name, setName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Once the project itself exists, a failed *upload* is shown as a recoverable warning rather
  // than a blocking error - there's no way to undo the project creation, so the only useful next
  // step is letting the user retry the upload from Ask, not getting stuck on this screen.
  const [uploadWarning, setUploadWarning] = useState<string | null>(null);
  // A synchronous guard against a double-click firing handleSubmit twice before the `disabled`
  // state (which only takes effect on the next render) has a chance to catch it - that would
  // create two projects and split the staged files' upload across whichever one "wins" last.
  const isSubmittingRef = useRef(false);

  const canCancel = projects.length > 0;
  const canSubmit = name.trim() !== "" && files.length > 0 && !isSubmitting;

  function stageFiles(newFiles: File[]) {
    // Adds to whatever's already staged, so dropping/selecting in more than one go works - a
    // browser's own multi-select within a single drop or dialog already returns every file at
    // once, so this only matters across separate drops.
    setFiles((current) => {
      const added = newFiles.filter(
        (file) => !current.some((existing) => existing.name === file.name && existing.size === file.size),
      );
      return [...current, ...added];
    });
  }

  function removeStagedFile(name: string) {
    setFiles((current) => current.filter((file) => file.name !== name));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit || isSubmittingRef.current) return;
    isSubmittingRef.current = true;
    setError(null);
    setUploadWarning(null);
    setIsSubmitting(true);
    try {
      const project = await createProject(name.trim());
      try {
        // Passing project.id explicitly matters: uploadFiles here is the reference this
        // component held *before* the project existed, so without it the upload would still act
        // on whatever project (or none) was current before this call - see
        // ProjectDocumentsProvider.
        await uploadFiles(files, project.id);
        router.push("/ask");
      } catch (uploadErr) {
        // The project was created either way; only the document(s) need retrying.
        isSubmittingRef.current = false;
        setIsSubmitting(false);
        setUploadWarning(
          uploadErr instanceof Error ? uploadErr.message : "Some documents could not be uploaded.",
        );
      }
    } catch (err) {
      isSubmittingRef.current = false;
      setIsSubmitting(false);
      setError(err instanceof ApiError ? err.message : "Could not create the project.");
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4">
      <Heading>{canCancel ? "Create a project" : "Create your first project"}</Heading>
      <p className="text-sm text-muted">
        Give it a name and at least one document to get started - you can add more later.
      </p>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-xs font-medium">
          Project name
          <TextInput value={name} onChange={(event) => setName(event.target.value)} autoFocus />
        </label>
        <div className="flex flex-col gap-1 text-xs font-medium">
          Documents
          <DocumentDropzone onFiles={stageFiles} />
        </div>
        {files.length > 0 && (
          <ul className="flex flex-col gap-1 rounded-md border border-border bg-surface p-2 text-xs">
            {files.map((file) => (
              <li key={file.name} className="flex items-center justify-between gap-2">
                <span className="truncate text-ink">{file.name}</span>
                <button
                  type="button"
                  onClick={() => removeStagedFile(file.name)}
                  aria-label={`Remove ${file.name}`}
                  className="shrink-0 text-danger hover:underline"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
        {error && (
          <p role="alert" className="text-xs text-danger">
            {error}
          </p>
        )}
        {uploadWarning && (
          <div className="flex flex-col gap-2 rounded-md border border-danger bg-danger-soft p-3 text-xs text-danger">
            <p role="alert">{uploadWarning}</p>
            <p>The project was created - you can upload the document(s) again from Ask.</p>
            <Button type="button" onClick={() => router.push("/ask")} className="w-fit">
              Continue to Ask
            </Button>
          </div>
        )}
        <div className="flex gap-2">
          <Button type="submit" disabled={!canSubmit} className="flex-1">
            {isSubmitting ? "Creating..." : "Create project"}
          </Button>
          {canCancel && (
            <Button type="button" variant="ghost" onClick={closeCreateScreen} disabled={isSubmitting}>
              Cancel
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
