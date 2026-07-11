import assert from "node:assert/strict";
import test from "node:test";

import {
  AuthClient,
  authPathWithNext,
  isOAuthProvider,
  safeRedirectPath,
} from "../packages/core/dist/index.js";

test("safe redirect accepts internal targets and rejects external redirects", () => {
  assert.equal(
    safeRedirectPath("/deliveries/overview?tab=1"),
    "/deliveries/overview?tab=1",
  );
  assert.equal(safeRedirectPath("https://evil.test", "/overview"), "/overview");
  assert.equal(safeRedirectPath("//evil.test", "/overview"), "/overview");
  assert.equal(
    safeRedirectPath("/login?next=/admin", "/overview"),
    "/overview",
  );
});

test("auth paths preserve a safe next target", () => {
  assert.equal(
    authPathWithNext("/login", "/deliveries/overview"),
    "/login?next=%2Fdeliveries%2Foverview",
  );
});

test("the bundled oauth provider set is GitHub, Google and Yandex", () => {
  assert.equal(isOAuthProvider("github"), true);
  assert.equal(isOAuthProvider("google"), true);
  assert.equal(isOAuthProvider("yandex"), true);
  assert.equal(isOAuthProvider("vk"), false);
});

test("authenticated requests refresh once and retry after an expired access cookie", async () => {
  const calls = [];
  const responses = [
    new Response(JSON.stringify({ detail: "expired" }), { status: 401 }),
    new Response(null, { status: 204 }),
    new Response(JSON.stringify({ id: 1, username: "user" }), { status: 200 }),
  ];
  const client = new AuthClient({
    routes: {
      login: "/login",
      register: "/register",
      methods: "/methods",
      me: "/me",
      refresh: "/refresh",
      logout: "/logout",
      passwordResetRequest: "/reset/request",
      passwordResetConfirm: "/reset/confirm",
      emailVerificationCode: "/verify/send",
      emailConfirm: "/verify/confirm",
      oauthCallback: (provider) => `/oauth/${provider}`,
    },
    fetch: async (url, init) => {
      calls.push([url, init?.method]);
      return responses.shift();
    },
  });
  assert.equal((await client.me()).username, "user");
  assert.deepEqual(calls, [
    ["/me", "GET"],
    ["/refresh", "POST"],
    ["/me", "GET"],
  ]);
});
