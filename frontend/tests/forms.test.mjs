import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

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
  assert.match(login, /oauthButtons\?: OAuthButtonsOptions/);
  assert.match(register, /oauthButtons\?: OAuthButtonsOptions/);
});
