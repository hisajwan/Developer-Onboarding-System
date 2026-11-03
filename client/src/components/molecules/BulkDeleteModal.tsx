"use client";

import { useState, type ReactNode } from "react";
import { Button } from "@/components/atoms/Button";
import { ConfirmDeleteDialog } from "@/components/molecules/ConfirmDeleteDialog";
import { Modal } from "@/components/molecules/Modal";

export interface BulkDeleteItem {
  id: string;
  label: string;
  /** A short extra line, e.g. "current". */
  detail?: string;
}

interface BulkDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  items: BulkDeleteItem[];
  /** Singular and plural, e.g. ["project", "projects"]. */
  noun: [string, string];
  /** What else goes with each deleted item, shown in the confirmation. */
  consequence: ReactNode;
  /** Deletes the chosen ids; the modal closes once it resolves, and shows the error if not. */
  onDelete: (ids: string[]) => Promise<void>;
}

/**
 * Lists every item with a checkbox. "Delete selected" opens a confirmation naming exactly what
 * will go; only confirming that deletes anything.
 */
export function BulkDeleteModal({
  isOpen,
  onClose,
  title,
  items,
  noun,
  consequence,
  onDelete,
}: BulkDeleteModalProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  // Only ids still in the list count (an item may have gone since it was ticked).
  const chosen = items.filter((item) => selected.has(item.id));
  const allChosen = items.length > 0 && chosen.length === items.length;
  const [one, many] = noun;

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected(allChosen ? new Set() : new Set(items.map((item) => item.id)));
  }

  function close() {
    setSelected(new Set());
    setIsConfirmOpen(false);
    onClose();
  }

  async function confirmDelete() {
    await onDelete(chosen.map((item) => item.id));
    close();
  }

  return (
    <>
      <Modal isOpen={isOpen} onClose={close} title={title}>
        <div className="flex flex-col gap-4">
          {items.length === 0 ? (
            <p className="text-sm text-muted">Nothing to manage yet.</p>
          ) : (
            <>
              <label className="flex items-center gap-2 border-b border-border pb-2 text-xs font-medium text-muted">
                <input type="checkbox" checked={allChosen} onChange={toggleAll} />
                Select all
              </label>
              <ul className="flex max-h-72 flex-col gap-1 overflow-y-auto">
                {items.map((item) => (
                  <li key={item.id}>
                    <label className="flex cursor-pointer items-center gap-2 rounded-md px-1 py-1.5 text-sm hover:bg-surface">
                      <input
                        type="checkbox"
                        checked={selected.has(item.id)}
                        onChange={() => toggle(item.id)}
                      />
                      <span className="text-ink">{item.label}</span>
                      {item.detail && <span className="text-xs text-muted">{item.detail}</span>}
                    </label>
                  </li>
                ))}
              </ul>
            </>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={close}>
              Close
            </Button>
            <Button
              variant="danger"
              disabled={chosen.length === 0}
              onClick={() => setIsConfirmOpen(true)}
            >
              Delete selected{chosen.length > 0 ? ` (${chosen.length})` : ""}
            </Button>
          </div>
        </div>
      </Modal>
      <ConfirmDeleteDialog
        isOpen={isConfirmOpen}
        onClose={() => setIsConfirmOpen(false)}
        title={`Delete ${chosen.length === 1 ? one : many}`}
        confirmLabel={`Delete ${chosen.length} ${chosen.length === 1 ? one : many}`}
        onConfirm={confirmDelete}
      >
        <p>Delete {chosen.length === 1 ? `this ${one}` : `these ${chosen.length} ${many}`}?</p>
        <ul className="mt-2 list-disc pl-5">
          {chosen.map((item) => (
            <li key={item.id} className="font-medium">
              {item.label}
            </li>
          ))}
        </ul>
        <p className="mt-2 text-muted">{consequence}</p>
      </ConfirmDeleteDialog>
    </>
  );
}
