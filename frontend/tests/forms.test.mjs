import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  createAuthLegalConsentStorageRecord,
  hasCurrentRequiredAuthLegalConsent,
  parseAuthLegalConsentStorage,
  restoreAcceptedAuthLegalDocuments,
} from "../packages/forms/dist/legalConsentStorage.js";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");

test("auth navigation uses the semantic Orcestr UI Link", () => {
  const login = read("../packages/forms/src/LoginForm.tsx");
  const register = read("../packages/forms/src/RegisterForm.tsx");

  assert.match(login, /import \{ Button, Flex, Link \} from "@orcestr\/ui"/);
  assert.match(login, /<Link href=\{forgotPasswordHref\} fs=\{14\}>/);
  assert.match(login, /<Link href=\{registerHref\} fs=\{14\}>/);
  assert.doesNotMatch(login, /<a href=/);
  assert.match(register, /<Link href=\{loginHref\} fs=\{14\}>/);
  assert.doesNotMatch(register, /<a href=/);
});

test("OAuth provider buttons support shared and provider-specific components", () => {
  const buttons = read("../packages/forms/src/OAuthButtons.tsx");
  const login = read("../packages/forms/src/LoginForm.tsx");
  const register = read("../packages/forms/src/RegisterForm.tsx");

  assert.match(buttons, /export type OAuthProviderButtonProps/);
  assert.match(buttons, /buttonComponent\?: OAuthProviderButtonComponent/);
  assert.match(buttons, /buttonComponents\?: Partial</);
  assert.match(
    buttons,
    /buttonComponents\?\.\[provider\] \?\?[\s\S]*buttonComponent \?\?[\s\S]*DefaultOAuthProviderButton/,
  );
  assert.match(buttons, /direction\?: "row" \| "column"/);
  assert.match(buttons, /placement\?: OAuthButtonsPlacement/);
  assert.match(buttons, /"after-submit"/);
  assert.match(login, /oauthButtons\?: OAuthButtonsOptions/);
  assert.match(register, /oauthButtons\?: OAuthButtonsOptions/);
});

test("login, registration and OAuth share the versioned legal consent gate", () => {
  const legal = read("../packages/forms/src/LegalConsent.tsx");
  const oauth = read("../packages/forms/src/OAuthButtons.tsx");
  const login = read("../packages/forms/src/LoginForm.tsx");
  const register = read("../packages/forms/src/RegisterForm.tsx");

  assert.match(legal, /export type AuthLegalDocument/);
  assert.match(legal, /version: string/);
  assert.match(legal, /required\?: boolean/);
  assert.match(legal, /acceptance: Record<string, unknown>/);
  assert.match(legal, /selectedDocumentIds/);
  assert.match(legal, /requiredAccepted/);
  assert.match(legal, /selectAllOnFirstDocumentCheck\?: boolean/);
  assert.match(legal, /documentId === documents\[0\]\?\.id/);
  assert.match(legal, /readAuthLegalConsentStorage/);
  assert.match(legal, /writeAuthLegalConsentStorage/);
  assert.match(oauth, /callbackPayload/);
  assert.match(login, /legal\.request/);
  assert.match(login, /buildAuthLegalPayload/);
  assert.match(register, /legal\.request/);
  assert.match(register, /buildAuthLegalPayload/);
});

test("legal consent storage restores only matching document versions", () => {
  const documents = [
    { id: "terms", version: "2", required: true },
    { id: "privacy", version: "4", required: true },
    { id: "marketing", version: "1", required: false },
  ];
  const record = createAuthLegalConsentStorageRecord(documents.slice(0, 2));

  assert.equal(hasCurrentRequiredAuthLegalConsent(documents, record), true);
  assert.deepEqual(
    restoreAcceptedAuthLegalDocuments(documents, record).map(({ id }) => id),
    ["terms", "privacy"],
  );
  assert.equal(
    hasCurrentRequiredAuthLegalConsent(
      documents.map((document) =>
        document.id === "privacy" ? { ...document, version: "5" } : document,
      ),
      record,
    ),
    false,
  );
});

test("legal consent storage rejects malformed or unsupported records", () => {
  assert.equal(parseAuthLegalConsentStorage(null), null);
  assert.equal(parseAuthLegalConsentStorage("not-json"), null);
  assert.equal(
    parseAuthLegalConsentStorage(
      JSON.stringify({ schemaVersion: 2, acceptedDocuments: [] }),
    ),
    null,
  );
  assert.equal(
    parseAuthLegalConsentStorage(
      JSON.stringify({
        schemaVersion: 1,
        acceptedDocuments: [{ id: "terms" }],
      }),
    ),
    null,
  );
});
