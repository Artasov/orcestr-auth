export const DEFAULT_AUTH_LEGAL_CONSENT_STORAGE_KEY =
  "@orcestr/auth-forms:legal-consent";

export type AuthLegalDocumentVersion = {
  id: string;
  version: string;
  required?: boolean;
};

export type AuthLegalConsentStorageOptions = {
  key?: string;
};

export type StoredAuthLegalDocumentVersion = {
  id: string;
  version: string;
};

export type AuthLegalConsentStorageRecord = {
  schemaVersion: 1;
  acceptedDocuments: StoredAuthLegalDocumentVersion[];
};

function isStoredDocument(value: unknown): value is StoredAuthLegalDocumentVersion {
  if (!value || typeof value !== "object") return false;
  const document = value as Record<string, unknown>;
  return typeof document.id === "string" && typeof document.version === "string";
}

export function parseAuthLegalConsentStorage(
  value: string | null,
): AuthLegalConsentStorageRecord | null {
  if (!value) return null;
  try {
    const parsed: unknown = JSON.parse(value);
    if (!parsed || typeof parsed !== "object") return null;
    const record = parsed as Record<string, unknown>;
    if (
      record.schemaVersion !== 1 ||
      !Array.isArray(record.acceptedDocuments) ||
      !record.acceptedDocuments.every(isStoredDocument)
    ) {
      return null;
    }
    return {
      schemaVersion: 1,
      acceptedDocuments: record.acceptedDocuments,
    };
  } catch {
    return null;
  }
}

export function createAuthLegalConsentStorageRecord(
  documents: readonly AuthLegalDocumentVersion[],
): AuthLegalConsentStorageRecord {
  return {
    schemaVersion: 1,
    acceptedDocuments: documents.map(({ id, version }) => ({ id, version })),
  };
}

function containsDocumentVersion(
  record: AuthLegalConsentStorageRecord,
  document: AuthLegalDocumentVersion,
) {
  return record.acceptedDocuments.some(
    (accepted) =>
      accepted.id === document.id && accepted.version === document.version,
  );
}

export function restoreAcceptedAuthLegalDocuments<
  TDocument extends AuthLegalDocumentVersion,
>(
  documents: readonly TDocument[],
  record: AuthLegalConsentStorageRecord | null,
): TDocument[] {
  if (!record) return [];
  return documents.filter((document) => containsDocumentVersion(record, document));
}

export function hasCurrentRequiredAuthLegalConsent(
  documents: readonly AuthLegalDocumentVersion[],
  record: AuthLegalConsentStorageRecord | null,
): boolean {
  if (!record) return false;
  return documents
    .filter((document) => document.required !== false)
    .every((document) => containsDocumentVersion(record, document));
}

function resolveBrowserStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function readAuthLegalConsentStorage(
  options: false | AuthLegalConsentStorageOptions | undefined,
): AuthLegalConsentStorageRecord | null {
  if (options === false) return null;
  const storage = resolveBrowserStorage();
  if (!storage) return null;
  try {
    return parseAuthLegalConsentStorage(
      storage.getItem(options?.key ?? DEFAULT_AUTH_LEGAL_CONSENT_STORAGE_KEY),
    );
  } catch {
    return null;
  }
}

export function writeAuthLegalConsentStorage(
  options: false | AuthLegalConsentStorageOptions | undefined,
  record: AuthLegalConsentStorageRecord,
): void {
  if (options === false) return;
  const storage = resolveBrowserStorage();
  if (!storage) return;
  try {
    storage.setItem(
      options?.key ?? DEFAULT_AUTH_LEGAL_CONSENT_STORAGE_KEY,
      JSON.stringify(record),
    );
  } catch {
    // Storage can be unavailable in privacy modes or full. Consent still proceeds.
  }
}
