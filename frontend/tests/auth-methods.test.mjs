import assert from "node:assert/strict";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuthMethods } from "../packages/react/dist/index.js";
import { AuthI18nProvider, AuthMethodsStatus, LoginForm, RegisterForm, OAuthButtons } from "../packages/forms/dist/index.js";

test("useAuthMethods stays pending during SSR without reading window or requesting an incorrect origin", () => {
  const queryClient = new QueryClient();
  let requested = false;
  let state;
  function Probe() {
    state = useAuthMethods();
    return null;
  }
  renderToStaticMarkup(createElement(QueryClientProvider, {client: queryClient},
    createElement(AuthProvider, {client: {
      routes: {methods: "/auth/methods/"},
      methods: () => {requested = true; throw new Error("unexpected request");},
    }}, createElement(Probe))));
  assert.equal(state.isPending, true);
  assert.equal(state.fetchStatus, "idle");
  assert.equal(requested, false);
  queryClient.clear();
});

test("AuthMethodsStatus renders loading and retryable error states", () => {
  const loading = renderToStaticMarkup(createElement(AuthMethodsStatus, {methodsPending: true}));
  assert.match(loading, /role="status"/);
  assert.match(loading, /Loading/);
  const failed = renderToStaticMarkup(createElement(AuthI18nProvider, {locale: "ru"},
    createElement(AuthMethodsStatus, {methodsError: new Error("failed"), onRetryMethods: () => undefined})));
  assert.match(failed, /role="alert"/);
  assert.match(failed, /Повторить/);
  assert.equal(renderToStaticMarkup(createElement(AuthMethodsStatus)), "");
});

test("OAuthButtons renders only allowed providers with configured client IDs", () => {
  const html = renderToStaticMarkup(createElement(OAuthButtons, {
    providers: ["google", "github"],
    clientIds: {google: "public-google-client-id", github: " "},
  }));
  assert.match(html, /Google/);
  assert.doesNotMatch(html, /GitHub/);
});

for (const Form of [LoginForm, RegisterForm]) {
  test(`${Form.name} disables submission and OAuth while methods are pending or failed`, () => {
    for (const status of [{methodsPending: true}, {methodsError: new Error("failed")}]) {
      const queryClient = new QueryClient();
      const html = renderToStaticMarkup(createElement(QueryClientProvider, {client: queryClient},
        createElement(AuthProvider, {client: {}}, createElement(Form, {
          methods: {allowed_oauth_providers: ["google"], oauth_client_ids: {google: "public-id"}},
          ...status,
        }))));
      const buttons = [...html.matchAll(/<button\b[^>]*>[\s\S]*?<\/button>/g)].map(([button]) => button);
      const submit = buttons.find((button) => button.includes('type="submit"'));
      const google = buttons.find((button) => button.includes("Google"));
      assert.match(submit, /disabled=""/);
      assert.match(google, /disabled=""/);
      queryClient.clear();
    }
  });
}
