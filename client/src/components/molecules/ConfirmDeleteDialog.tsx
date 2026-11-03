"use client";

import { useState, type ReactNode } from "react";
import { Button } from "@/components/atoms/Button";
import { Modal } from "@/components/molecules/Modal";
import { ApiError } from "@/lib/api/http";

interface ConfirmDeleteDialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  /** What will be lost, in plain words. */
  children: ReactNode;
  confirmLabel: string;
  /** Called on confirm; the dialog closes once it resolves and shows the error if it throws. */
  onConfirm: () => Promise<void>;
}

/** A "are you sure?" step before deleting something, with the delete button in danger red. */
export function ConfirmDeleteDialog({
  isOpen,
  onClose,
  title,
  children,
  confirmLabel,
  onConfirm,
}: ConfirmDeleteDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm() {
    setError(null);
    setIsDeleting(true);
    try {
      await onConfirm();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete. Try again.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <div className="flex flex-col gap-4">
        <div className="text-sm text-ink">{children}</div>
        <p className="text-xs text-muted">This can&apos;t be undone.</p>
        {error && (
          <p role="alert" className="text-xs text-danger">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={isDeleting}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleConfirm} disabled={isDeleting}>
            {isDeleting ? "Deleting…" : confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
