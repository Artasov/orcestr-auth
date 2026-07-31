"use client";

import { Button, Checkbox, Flex, Link, Modal, Text } from "@orcestr/ui";
import { useCallback, useId, useRef, useState, type ReactNode } from "react";

import { useAuthMessages } from "./i18n.js";

export type AuthLegalDocument = {
  id: string;
  title: string;
  version: string;
  href: string;
  required?: boolean;
  acceptance: Record<string, unknown>;
  description?: ReactNode;
};

export type AuthLegalConsentOptions = {
  enabled?: boolean;
  documents: readonly AuthLegalDocument[];
  title?: ReactNode;
  description?: ReactNode;
  confirmLabel?: ReactNode;
  cancelLabel?: ReactNode;
  payloadKey?: string;
  buildPayload?: (
    documents: readonly AuthLegalDocument[],
  ) => Record<string, unknown>;
};

export type AuthLegalConsentDialogProps = {
  open: boolean;
  options: AuthLegalConsentOptions;
  selectedDocumentIds: ReadonlySet<string>;
  onDocumentChange: (documentId: string, checked: boolean) => void;
  onConfirm: () => void;
  onOpenChange: (open: boolean) => void;
};

type LegalAction = (
  acceptedDocuments: readonly AuthLegalDocument[],
) => void | Promise<void>;

export function buildAuthLegalPayload(
  options: AuthLegalConsentOptions | undefined,
  documents: readonly AuthLegalDocument[],
): Record<string, unknown> {
  if (!options) return {};
  if (options.buildPayload) return options.buildPayload(documents);
  return {
    [options.payloadKey ?? "accepted_legal_documents"]: documents.map(
      (document) => document.acceptance,
    ),
  };
}

export function useAuthLegalConsent(options?: AuthLegalConsentOptions) {
  const [open, setOpen] = useState(false);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<string>>(
    () => new Set(),
  );
  const pendingAction = useRef<LegalAction | null>(null);
  const documents = options?.documents ?? [];
  const enabled = options?.enabled !== false && documents.length > 0;

  const request = useCallback(
    (action: LegalAction) => {
      if (!enabled) {
        void action([]);
        return;
      }
      pendingAction.current = action;
      setSelectedDocumentIds(new Set());
      setOpen(true);
    },
    [enabled],
  );

  const onOpenChange = useCallback((nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) pendingAction.current = null;
  }, []);

  const onDocumentChange = useCallback(
    (documentId: string, checked: boolean) => {
      setSelectedDocumentIds((current) => {
        const next = new Set(current);
        if (checked) next.add(documentId);
        else next.delete(documentId);
        return next;
      });
    },
    [],
  );

  const onConfirm = useCallback(() => {
    const action = pendingAction.current;
    if (!action) return;
    const acceptedDocuments = documents.filter((document) =>
      selectedDocumentIds.has(document.id),
    );
    pendingAction.current = null;
    setOpen(false);
    void action(acceptedDocuments);
  }, [documents, selectedDocumentIds]);

  return {
    request,
    dialog: options ? (
      <AuthLegalConsentDialog
        open={open}
        options={options}
        selectedDocumentIds={selectedDocumentIds}
        onDocumentChange={onDocumentChange}
        onConfirm={onConfirm}
        onOpenChange={onOpenChange}
      />
    ) : null,
  };
}

export function AuthLegalConsentDialog({
  open,
  options,
  selectedDocumentIds,
  onDocumentChange,
  onConfirm,
  onOpenChange,
}: AuthLegalConsentDialogProps) {
  const copy = useAuthMessages().legal;
  const titleId = useId();
  const descriptionId = useId();
  const requiredAccepted = options.documents
    .filter((document) => document.required !== false)
    .every((document) => selectedDocumentIds.has(document.id));

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      maxWidth={520}
      ariaLabelledBy={titleId}
      ariaDescribedBy={descriptionId}
    >
      <Modal.Header>
        <Text id={titleId} fw={700} fs={20}>
          {options.title ?? copy.title}
        </Text>
      </Modal.Header>
      <Modal.Body>
        <Flex col g="3">
          <Text id={descriptionId} tone="neutral">
            {options.description ?? copy.description}
          </Text>
          {options.documents.map((document) => (
            <Flex key={`${document.id}:${document.version}`} g="2">
              <Checkbox
                checked={selectedDocumentIds.has(document.id)}
                onCheckedChange={(checked) =>
                  onDocumentChange(document.id, checked)
                }
                aria-label={`${copy.acceptPrefix} ${document.title}`}
              />
              <Flex col g="1">
                <Text>
                  {copy.acceptPrefix}{" "}
                  <Link href={document.href} target="_blank" rel="noreferrer">
                    {document.title}
                  </Link>
                  {document.required === false ? ` (${copy.optional})` : ""}
                </Text>
                <Text fs={12} tone="neutral">
                  {copy.version}: {document.version}
                </Text>
                {document.description ? (
                  <Text fs={12} tone="neutral">
                    {document.description}
                  </Text>
                ) : null}
              </Flex>
            </Flex>
          ))}
        </Flex>
      </Modal.Body>
      <Modal.Footer>
        <Flex g="2" j="e">
          <Button type="button" v="soft" onClick={() => onOpenChange(false)}>
            {options.cancelLabel ?? copy.cancel}
          </Button>
          <Button
            type="button"
            disabled={!requiredAccepted}
            onClick={onConfirm}
          >
            {options.confirmLabel ?? copy.confirm}
          </Button>
        </Flex>
      </Modal.Footer>
    </Modal>
  );
}
