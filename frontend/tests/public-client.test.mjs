import assert from "node:assert/strict";
import test from "node:test";

import {
  OAuthCallbackError,
  OAuthTokenClient,
  buildOAuthAuthorizationUrl,
  createOAuthAuthorizationRequest,
  derivePkceChallenge,
  generateOAuthState,
  generatePkcePair,
  parseOAuthCallback,
} from "../packages/core/dist/index.js";

test("public-client state and PKCE values have secure base64url shapes", async () => {
  const firstState = generateOAuthState();
  const secondState = generateOAuthState();
  const pkce = await generatePkcePair();

  assert.match(firstState, /^[A-Za-z0-9_-]{43}$/u);
  assert.notEqual(firstState, secondState);
  assert.match(pkce.codeVerifier, /^[A-Za-z0-9_-]{43,128}$/u);
  assert.match(pkce.codeChallenge, /^[A-Za-z0-9_-]{43}$/u);
  assert.equal(pkce.codeChallengeMethod, "S256");
  assert.equal(
    await derivePkceChallenge(
      "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
    ),
    "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
  );
});

test("authorization requests contain OAuth 2.1 code and PKCE parameters", async () => {
  const request = await createOAuthAuthorizationRequest({
    authorizationEndpoint: "https://auth.example.test/oauth/authorize",
    clientId: "desktop-client",
    redirectUri: "com.example.desktop://oauth/callback",
    scope: ["openid", "profile", "offline_access"],
    additionalParameters: { audience: "example-api" },
  });
  const url = new URL(request.authorizationUrl);

  assert.equal(url.origin, "https://auth.example.test");
  assert.equal(url.pathname, "/oauth/authorize");
  assert.equal(url.searchParams.get("response_type"), "code");
  assert.equal(url.searchParams.get("client_id"), "desktop-client");
  assert.equal(
    url.searchParams.get("redirect_uri"),
    "com.example.desktop://oauth/callback",
  );
  assert.equal(url.searchParams.get("scope"), "openid profile offline_access");
  assert.equal(url.searchParams.get("state"), request.state);
  assert.equal(url.searchParams.get("code_challenge"), request.codeChallenge);
  assert.equal(url.searchParams.get("code_challenge_method"), "S256");
  assert.equal(url.searchParams.get("audience"), "example-api");
});

test("OAuth server endpoints require HTTPS or exact loopback HTTP URLs", () => {
  const authorizationUrl = (authorizationEndpoint) =>
    buildOAuthAuthorizationUrl({
      authorizationEndpoint,
      clientId: "desktop-client",
      redirectUri: "com.example.desktop://oauth/callback",
      scope: "profile",
      state: "state",
      codeChallenge: "challenge",
    });
  const fetch = async () => new Response(null, { status: 500 });

  for (const endpoint of [
    "https://auth.example.test/oauth/authorize",
    "http://localhost:8000/oauth/authorize",
    "http://127.0.0.1:8000/oauth/authorize",
    "http://[::1]:8000/oauth/authorize",
  ]) {
    assert.doesNotThrow(() => authorizationUrl(endpoint));
  }
  for (const endpoint of [
    "https://auth.example.test/oauth/token",
    "http://localhost:8000/oauth/token",
    "http://127.0.0.1:8000/oauth/token",
    "http://[::1]:8000/oauth/token",
  ]) {
    assert.doesNotThrow(
      () =>
        new OAuthTokenClient({
          tokenEndpoint: endpoint,
          clientId: "desktop-client",
          fetch,
        }),
    );
  }

  for (const endpoint of [
    "http://auth.example.test/oauth/authorize",
    "ftp://auth.example.test/oauth/authorize",
    "https://user:password@auth.example.test/oauth/authorize",
    "https://auth.example.test/oauth/authorize?audience=api",
    "https://auth.example.test/oauth/authorize?",
    "https://auth.example.test/oauth/authorize#fragment",
    "https://auth.example.test/oauth/authorize#",
    "http://localhost.example.test/oauth/authorize",
  ]) {
    assert.throws(
      () => authorizationUrl(endpoint),
      /oauth_authorization_endpoint_invalid/u,
    );
  }
  for (const endpoint of [
    "http://auth.example.test/oauth/token",
    "ftp://auth.example.test/oauth/token",
    "https://user:password@auth.example.test/oauth/token",
    "https://auth.example.test/oauth/token?tenant=one",
    "https://auth.example.test/oauth/token?",
    "https://auth.example.test/oauth/token#fragment",
    "https://auth.example.test/oauth/token#",
    "http://localhost.example.test/oauth/token",
  ]) {
    assert.throws(
      () =>
        new OAuthTokenClient({
          tokenEndpoint: endpoint,
          clientId: "desktop-client",
          fetch,
        }),
      /oauth_token_endpoint_invalid/u,
    );
  }
});

test("callback parsing rejects state mismatches before accepting results", () => {
  assert.throws(
    () =>
      parseOAuthCallback(
        "com.example.desktop://oauth/callback?code=code-1&state=wrong",
        { expectedState: "expected" },
      ),
    (error) => {
      assert.equal(error instanceof OAuthCallbackError, true);
      assert.equal(error.code, "state_mismatch");
      return true;
    },
  );

  assert.throws(
    () =>
      parseOAuthCallback(
        "com.example.desktop://oauth/callback?error=access_denied&error_description=Denied&state=expected",
        { expectedState: "expected" },
      ),
    (error) => {
      assert.equal(error instanceof OAuthCallbackError, true);
      assert.equal(error.code, "authorization_error");
      assert.equal(error.oauthError, "access_denied");
      assert.equal(error.errorDescription, "Denied");
      return true;
    },
  );

  assert.deepEqual(
    parseOAuthCallback(
      "com.example.desktop://oauth/callback?code=code-1&state=expected",
      {
        expectedState: "expected",
        expectedRedirectUri: "com.example.desktop://oauth/callback",
      },
    ),
    { code: "code-1", state: "expected" },
  );
});

test("callback parsing validates the exact expected redirect URI base", () => {
  const callback =
    "com.example.desktop://oauth/callback?code=code-1&state=expected";

  assert.deepEqual(
    parseOAuthCallback(callback, {
      expectedState: "expected",
      expectedRedirectUri: "com.example.desktop://oauth/callback",
    }),
    { code: "code-1", state: "expected" },
  );

  for (const expectedRedirectUri of [
    "com.example.other://oauth/callback",
    "com.example.desktop://other/callback",
    "com.example.desktop://oauth/callback/",
  ]) {
    assert.throws(
      () =>
        parseOAuthCallback(callback, {
          expectedState: "expected",
          expectedRedirectUri,
        }),
      (error) => {
        assert.equal(error instanceof OAuthCallbackError, true);
        assert.equal(error.code, "redirect_uri_mismatch");
        return true;
      },
    );
  }

  assert.throws(
    () =>
      parseOAuthCallback(new URLSearchParams("code=code-1&state=expected"), {
        expectedState: "expected",
        expectedRedirectUri: "com.example.desktop://oauth/callback",
      }),
    (error) => {
      assert.equal(error instanceof OAuthCallbackError, true);
      assert.equal(error.code, "invalid_callback_url");
      return true;
    },
  );
  assert.throws(
    () =>
      parseOAuthCallback(callback, {
        expectedState: "expected",
        expectedRedirectUri:
          "com.example.desktop://oauth/callback?embedded=true",
      }),
    (error) => {
      assert.equal(error instanceof OAuthCallbackError, true);
      assert.equal(error.code, "invalid_expected_redirect_uri");
      return true;
    },
  );
  assert.throws(
    () =>
      parseOAuthCallback(`${callback}#`, {
        expectedState: "expected",
        expectedRedirectUri: "com.example.desktop://oauth/callback",
      }),
    (error) => {
      assert.equal(error instanceof OAuthCallbackError, true);
      assert.equal(error.code, "invalid_callback_url");
      return true;
    },
  );
});

test("token client submits authorization-code and refresh grants as forms", async () => {
  const calls = [];
  const responses = [
    {
      access_token: "access-1",
      refresh_token: "refresh-1",
      token_type: "Bearer",
      expires_in: 900,
      scope: "openid profile offline_access",
    },
    {
      access_token: "access-2",
      refresh_token: "refresh-2",
      token_type: "Bearer",
    },
  ];
  const client = new OAuthTokenClient({
    tokenEndpoint: "https://auth.example.test/oauth/token",
    clientId: "desktop-client",
    fetch: async (url, init) => {
      calls.push({ url, init });
      return new Response(JSON.stringify(responses.shift()), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  });

  const exchanged = await client.exchangeAuthorizationCode({
    code: "authorization-code",
    redirectUri: "com.example.desktop://oauth/callback",
    codeVerifier: "v".repeat(64),
  });
  const refreshed = await client.refreshToken({
    refreshToken: exchanged.refresh_token,
    scope: ["openid", "profile"],
  });

  assert.equal(exchanged.access_token, "access-1");
  assert.equal(refreshed.access_token, "access-2");
  assert.equal(calls.length, 2);
  for (const call of calls) {
    assert.equal(call.url, "https://auth.example.test/oauth/token");
    assert.equal(call.init.method, "POST");
    assert.equal(call.init.cache, "no-store");
    assert.equal(call.init.credentials, "omit");
    assert.equal(call.init.redirect, "error");
    assert.equal(
      new Headers(call.init.headers).get("content-type"),
      "application/x-www-form-urlencoded",
    );
  }
  assert.deepEqual(
    Object.fromEntries(new URLSearchParams(calls[0].init.body)),
    {
      grant_type: "authorization_code",
      client_id: "desktop-client",
      code: "authorization-code",
      redirect_uri: "com.example.desktop://oauth/callback",
      code_verifier: "v".repeat(64),
    },
  );
  assert.deepEqual(
    Object.fromEntries(new URLSearchParams(calls[1].init.body)),
    {
      grant_type: "refresh_token",
      client_id: "desktop-client",
      refresh_token: "refresh-1",
      scope: "openid profile",
    },
  );
});
