import assert from "node:assert/strict";
import test from "node:test";

import { authMessages } from "../packages/forms/dist/i18n.js";
import { AuthApiError } from "../packages/core/dist/client.js";
import { resolveAuthErrorMessage } from "../packages/forms/dist/i18n.js";

function keys(value, prefix = "") {
  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return child && typeof child === "object" ? keys(child, path) : [path];
  });
}

test("Russian and English auth dictionaries have the same complete key set", () => {
  assert.deepEqual(keys(authMessages.ru).sort(), keys(authMessages.en).sort());
});

test("OAuth provider outages resolve to an actionable localized message", () => {
  const error = new AuthApiError(502, "oauth_provider_unavailable");
  assert.equal(
    resolveAuthErrorMessage(error, authMessages.en),
    "The sign-in provider is temporarily unavailable. Try again in a few minutes.",
  );
  assert.equal(
    resolveAuthErrorMessage(error, authMessages.ru),
    "Сервис входа временно недоступен. Повторите попытку через несколько минут.",
  );
});
