import assert from "node:assert/strict";
import test from "node:test";

import {
  AuthApiError,
  AuthClient,
  authPathWithNext,
  isOAuthProvider,
  safeRedirectPath,
} from "../packages/core/dist/index.js";

const routes = {
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
};

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
    routes,
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

test("structured API errors preserve their code and human-readable message", async () => {
  const client = new AuthClient({
    routes,
    fetch: async () =>
      new Response(
        JSON.stringify({
          error: { code: "authentication_required", message: "Authentication required" },
        }),
        { status: 401 },
      ),
  });

  await assert.rejects(client.login("user", "secret"), (error) => {
    assert.equal(error instanceof AuthApiError, true);
    assert.equal(error.code, "authentication_required");
    assert.equal(error.message, "Authentication required");
    return true;
  });
});

test("auth request logging redacts sensitive payload fields", async () => {
  const entries = [];
  const output = {
    log: (...args) => entries.push(args),
    error: () => {},
    warn: () => {},
    groupCollapsed: () => {},
    groupEnd: () => {},
  };
  const client = new AuthClient({
    routes,
    logging: { console: output, logRequestsTime: false },
    fetch: async () =>
      new Response(JSON.stringify({ user: { id: 1, username: "user" } }), {
        status: 200,
      }),
  });

  await client.login("user", "secret");
  assert.deepEqual(
    entries.find((entry) => entry[0] === "%cRequest data:")[2],
    { username: "user", password: "[redacted]" },
  );
});
