import * as React from "react";
import { Modal } from "./modal";
import { Button } from "./button";

export function Dialog({
  isOpen,
  onClose,
  title,
  description,
  children,
  actionText,
  onAction,
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="flex flex-col space-y-4">
        <div>
          <h2 className="text-xl font-semibold">{title}</h2>
          {description && (
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        <div className="py-2">{children}</div>
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          {actionText && <Button onClick={onAction}>{actionText}</Button>}
        </div>
      </div>
    </Modal>
  );
}
