import assert from "node:assert/strict";
import test from "node:test";

import { authMessages } from "../packages/forms/dist/i18n.js";

function keys(value, prefix = "") {
  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return child && typeof child === "object" ? keys(child, path) : [path];
  });
}

test("Russian and English auth dictionaries have the same complete key set", () => {
  assert.deepEqual(keys(authMessages.ru).sort(), keys(authMessages.en).sort());
});
