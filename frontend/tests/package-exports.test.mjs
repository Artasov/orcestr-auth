import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import test from "node:test";

import * as core from "../packages/core/dist/index.js";
import * as react from "../packages/react/dist/index.js";

test("headless public package barrels load in one consumer runtime", async () => {
  assert.equal(typeof core.AuthClient, "function");
  assert.equal(typeof core.safeRedirectPath, "function");
  assert.equal(typeof react.AuthProvider, "function");
  assert.equal(typeof react.useCurrentUser, "function");
  await access(new URL("../packages/forms/dist/index.js", import.meta.url));
  await access(new URL("../packages/forms/dist/index.d.ts", import.meta.url));
  await access(new URL("../packages/next/dist/index.js", import.meta.url));
  await access(new URL("../packages/next/dist/index.d.ts", import.meta.url));
});
