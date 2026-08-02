import assert from "node:assert/strict";
import test from "node:test";

import {
  AuthClient,
  AuthSessionManager,
  authPathWithNext,
  isOAuthProvider,
  safeRedirectPath,
} from "../packages/core/dist/index.js";
import { ApiError } from "@orcestr/core";

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
    safeRedirectPath("/dashboard/overview?tab=1"),
    "/dashboard/overview?tab=1",
  );
  assert.equal(safeRedirectPath("https://evil.test", "/overview"), "/overview");
  assert.equal(safeRedirectPath("//evil.test", "/overview"), "/overview");
  assert.equal(safeRedirectPath("/%5cevil.test", "/overview"), "/overview");
  assert.equal(safeRedirectPath("/%2f%2fevil.test", "/overview"), "/overview");
  assert.equal(
    safeRedirectPath("/login?next=/admin", "/overview"),
    "/overview",
  );
});

test("auth paths preserve a safe next target", () => {
  assert.equal(
    authPathWithNext("/login", "/dashboard/overview"),
    "/login?next=%2Fdashboard%2Foverview",
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

test("parallel unauthorized requests share one in-flight refresh", async () => {
  let refreshCalls = 0;
  let authenticated = false;
  const session = new AuthSessionManager({
    execute: async () =>
      authenticated
        ? new Response(null, { status: 204 })
        : new Response(null, { status: 401 }),
    refresh: async () => {
      refreshCalls += 1;
      await new Promise((resolve) => setTimeout(resolve, 5));
      authenticated = true;
      return new Response(null, { status: 204 });
    },
  });

  const results = await Promise.all([
    session.request("/first"),
    session.request("/second"),
  ]);
  assert.equal(refreshCalls, 1);
  assert.deepEqual(
    results.map(({ response }) => response.status),
    [204, 204],
  );
});

test("public login errors and forbidden responses never trigger refresh", async () => {
  let refreshCalls = 0;
  const session = new AuthSessionManager({
    execute: async () => new Response(null, { status: 403 }),
    refresh: async () => {
      refreshCalls += 1;
      return new Response(null, { status: 204 });
    },
  });
  const forbidden = await session.request("/forbidden");
  assert.equal(forbidden.response.status, 403);
  assert.equal(refreshCalls, 0);

  const calls = [];
  const client = new AuthClient({
    routes,
    fetch: async (url) => {
      calls.push(url);
      return new Response(
        JSON.stringify({
          error: {
            code: "invalid_credentials",
            message: "Invalid username or password.",
          },
        }),
        { status: 401 },
      );
    },
  });
  await assert.rejects(client.login("user", "wrong"));
  assert.deepEqual(calls, ["/login"]);
});

test("login includes action metadata without allowing it to replace credentials", async () => {
  let body;
  const client = new AuthClient({
    routes,
    fetch: async (_url, init) => {
      body = JSON.parse(init.body);
      return new Response(
        JSON.stringify({ user: { id: 1, username: "real-user" } }),
        { status: 200 },
      );
    },
  });

  await client.login("real-user", "real-password", {
    username: "forged-user",
    accepted_legal_documents: [{ document_slug: "terms", version: "2" }],
  });

  assert.deepEqual(body, {
    username: "real-user",
    password: "real-password",
    accepted_legal_documents: [{ document_slug: "terms", version: "2" }],
  });
});

test("failed refresh is reported without retrying the protected request", async () => {
  let requestCalls = 0;
  let refreshCalls = 0;
  const session = new AuthSessionManager({
    execute: async () => {
      requestCalls += 1;
      return new Response(null, { status: 401 });
    },
    refresh: async () => {
      refreshCalls += 1;
      return new Response(null, { status: 401 });
    },
  });
  const result = await session.request("/protected");
  assert.equal(result.response.status, 401);
  assert.equal(result.refreshFailed, true);
  assert.equal(requestCalls, 1);
  assert.equal(refreshCalls, 1);
});

test("structured API errors preserve their code and human-readable message", async () => {
  const client = new AuthClient({
    routes,
    fetch: async () =>
      new Response(
        JSON.stringify({
          error: {
            code: "authentication_required",
            message: "Authentication required",
          },
        }),
        { status: 401 },
      ),
  });

  await assert.rejects(client.login("user", "secret"), (error) => {
    assert.equal(error instanceof ApiError, true);
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
  assert.deepEqual(entries.find((entry) => entry[0] === "%cRequest data:")[2], {
    username: "user",
    password: "[redacted]",
  });
});
