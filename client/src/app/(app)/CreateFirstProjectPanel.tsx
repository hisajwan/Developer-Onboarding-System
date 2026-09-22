"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { Heading } from "@/components/atoms/Heading";
import { TextInput } from "@/components/atoms/TextInput";
import { DocumentDropzone } from "@/components/molecules/DocumentDropzone";
import { uploadDocument } from "@/lib/api/documents";
import { ApiError } from "@/lib/api/http";
import { useProjectContext } from "./ProjectProvider";

/**
 * Shown instead of the whole app (nav included) until the account has a first project. Needs a
 * name and at least one document together, not a project created empty - the first thing anyone
 * would do in Ask mode is ask about a doc, so start with one already there.
 */
export function CreateFirstProjectPanel() {
  const router = useRouter();
  const { createProject } = useProjectContext();
  const [name, setName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = name.trim() !== "" && files.length > 0 && !isSubmitting;

  function stageFiles(list: FileList) {
    setFiles(Array.from(list));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const project = await createProject(name.trim());
      // Best-effort: the project exists either way once created (there's no way to undo that
      // from here); a document that fails to upload can always be retried from Ask afterwards.
      await Promise.allSettled(files.map((file) => uploadDocument(project.id, file)));
      router.push("/ask");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the project.");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4">
      <Heading>Create your first project</Heading>
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
          <ul className="flex flex-col gap-1 text-xs text-muted">
            {files.map((file) => (
              <li key={file.name} className="truncate">
                {file.name}
              </li>
            ))}
          </ul>
        )}
        {error && (
          <p role="alert" className="text-xs text-danger">
            {error}
          </p>
        )}
        <Button type="submit" disabled={!canSubmit}>
          {isSubmitting ? "Creating..." : "Create project"}
        </Button>
      </form>
    </div>
  );
}
