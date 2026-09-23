"use client";

import { useEffect, useRef, type MouseEvent, type ReactNode } from "react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

/** A native `<dialog>`-backed modal: gets ESC-to-close, focus trapping and a backdrop for free. */
export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isOpen && !dialog.open) dialog.showModal();
    if (!isOpen && dialog.open) dialog.close();
  }, [isOpen]);

  function handleBackdropClick(event: MouseEvent<HTMLDialogElement>) {
    if (event.target === dialogRef.current) onClose();
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onCancel={onClose}
      onClick={handleBackdropClick}
      // Browsers only center a <dialog> horizontally by default (it's anchored to the top
      // vertically) - `fixed inset-0 m-auto` plus a bounded height is the standard way to get
      // true centering in both directions out of an absolutely/fixed-positioned box.
      className="fixed inset-0 m-auto h-fit max-h-[85vh] w-full max-w-sm overflow-y-auto rounded-xl border border-border bg-canvas p-6 backdrop:bg-ink/40"
    >
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-sm font-bold text-ink">{title}</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="text-lg leading-none text-muted hover:text-ink"
        >
          ×
        </button>
      </div>
      <div className="mt-4">{children}</div>
    </dialog>
  );
}
