import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { authMessages } from "../packages/forms/dist/i18n.js";
import { ApiError } from "@orcestr/core";
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

test("frontend auth dictionaries match the shared backend code contract", async () => {
  const contract = JSON.parse(
    await readFile(
      new URL("../../contracts/auth-error-codes.json", import.meta.url),
      "utf8",
    ),
  );
  assert.deepEqual(
    Object.keys(authMessages.en.errors).sort(),
    [...contract].sort(),
  );
  assert.deepEqual(
    Object.keys(authMessages.ru.errors).sort(),
    [...contract].sort(),
  );
});

test("OAuth provider outages resolve to an actionable localized message", () => {
  const error = new ApiError(502, {
    code: "oauth_provider_unavailable",
    message: "Provider unavailable.",
  });
  assert.equal(
    resolveAuthErrorMessage(error, authMessages.en),
    "The sign-in provider is temporarily unavailable. Try again in a few minutes.",
  );
  assert.equal(
    resolveAuthErrorMessage(error, authMessages.ru),
    "Сервис входа временно недоступен. Повторите попытку через несколько минут.",
  );
});

test("invalid credentials resolve from the stable code in both locales", () => {
  const error = new ApiError(401, {
    code: "invalid_credentials",
    message: "Invalid username or password.",
  });
  assert.equal(
    resolveAuthErrorMessage(error, authMessages.en),
    "Invalid email, username or password.",
  );
  assert.equal(
    resolveAuthErrorMessage(error, authMessages.ru),
    "Неверный email, логин или пароль.",
  );
});

test("unknown codes use the selected locale fallback", () => {
  const error = new ApiError(418, {
    code: "unknown_auth_error",
    message: "Do not render this server message.",
  });
  assert.equal(
    resolveAuthErrorMessage(error, authMessages.en),
    authMessages.en.common.error,
  );
  assert.equal(
    resolveAuthErrorMessage(error, authMessages.ru),
    authMessages.ru.common.error,
  );
});
