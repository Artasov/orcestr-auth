const PKCE_CHALLENGE_METHOD = "S256" as const;
const OAUTH_STATE_BYTES = 32;
const PKCE_VERIFIER_BYTES = 64;

const AUTHORIZATION_PARAMETER_NAMES = new Set([
  "response_type",
  "client_id",
  "redirect_uri",
  "scope",
  "state",
  "code_challenge",
  "code_challenge_method",
]);

export type OAuthScope = string | readonly string[];

export type OAuthPkcePair = {
  codeVerifier: string;
  codeChallenge: string;
  codeChallengeMethod: typeof PKCE_CHALLENGE_METHOD;
};

export type BuildOAuthAuthorizationUrlOptions = {
  authorizationEndpoint: string | URL;
  clientId: string;
  redirectUri: string;
  scope: OAuthScope;
  state: string;
  codeChallenge: string;
  additionalParameters?: Readonly<Record<string, string>>;
};

export type CreateOAuthAuthorizationRequestOptions = Omit<
  BuildOAuthAuthorizationUrlOptions,
  "state" | "codeChallenge"
>;

export type OAuthAuthorizationRequest = OAuthPkcePair & {
  authorizationUrl: string;
  state: string;
};

/**
 * Generates an opaque, cryptographically secure state value. The caller owns
 * its lifecycle and must keep it until the authorization callback is handled.
 */
export function generateOAuthState(): string {
  return randomBase64Url(OAUTH_STATE_BYTES);
}

/**
 * Derives the RFC 7636 S256 challenge for an existing PKCE verifier.
 */
export async function derivePkceChallenge(
  codeVerifier: string,
): Promise<string> {
  if (!/^[A-Za-z0-9._~-]{43,128}$/u.test(codeVerifier)) {
    throw new Error("oauth_pkce_verifier_invalid");
  }
  const digest = await webCrypto().subtle.digest(
    "SHA-256",
    new TextEncoder().encode(codeVerifier),
  );
  return base64Url(new Uint8Array(digest));
}

/**
 * Creates a cryptographically secure PKCE verifier and its S256 challenge.
 */
export async function generatePkcePair(): Promise<OAuthPkcePair> {
  const codeVerifier = randomBase64Url(PKCE_VERIFIER_BYTES);
  return {
    codeVerifier,
    codeChallenge: await derivePkceChallenge(codeVerifier),
    codeChallengeMethod: PKCE_CHALLENGE_METHOD,
  };
}

/**
 * Builds an OAuth 2.1 authorization-code URL for a public client. Security
 * parameters cannot be replaced through additionalParameters.
 */
export function buildOAuthAuthorizationUrl(
  options: BuildOAuthAuthorizationUrlOptions,
): string {
  requireValue(options.clientId, "oauth_client_id_missing");
  requireValue(options.redirectUri, "oauth_redirect_uri_missing");
  requireValue(options.state, "oauth_state_missing");
  requireValue(options.codeChallenge, "oauth_pkce_challenge_missing");

  const scope = normalizeScope(options.scope);
  const url = secureOAuthEndpoint(
    options.authorizationEndpoint,
    "authorization",
  );
  for (const [name, value] of Object.entries(
    options.additionalParameters ?? {},
  )) {
    if (AUTHORIZATION_PARAMETER_NAMES.has(name)) {
      throw new Error(`oauth_authorization_parameter_reserved:${name}`);
    }
    url.searchParams.set(name, value);
  }

  url.searchParams.set("response_type", "code");
  url.searchParams.set("client_id", options.clientId);
  url.searchParams.set("redirect_uri", options.redirectUri);
  url.searchParams.set("scope", scope);
  url.searchParams.set("state", options.state);
  url.searchParams.set("code_challenge", options.codeChallenge);
  url.searchParams.set("code_challenge_method", PKCE_CHALLENGE_METHOD);
  return url.toString();
}

/**
 * Generates state and PKCE material and returns it together with the URL. The
 * SDK intentionally does not persist any of these values.
 */
export async function createOAuthAuthorizationRequest(
  options: CreateOAuthAuthorizationRequestOptions,
): Promise<OAuthAuthorizationRequest> {
  const state = generateOAuthState();
  const pkce = await generatePkcePair();
  return {
    ...pkce,
    state,
    authorizationUrl: buildOAuthAuthorizationUrl({
      ...options,
      state,
      codeChallenge: pkce.codeChallenge,
    }),
  };
}

export type OAuthCallbackErrorCode =
  | "authorization_error"
  | "duplicate_parameter"
  | "invalid_callback_url"
  | "invalid_expected_redirect_uri"
  | "missing_code"
  | "missing_state"
  | "redirect_uri_mismatch"
  | "state_mismatch";

export class OAuthCallbackError extends Error {
  readonly code: OAuthCallbackErrorCode;
  readonly oauthError?: string;
  readonly errorDescription?: string;
  readonly errorUri?: string;
  readonly parameter?: string;

  constructor(
    code: OAuthCallbackErrorCode,
    options: {
      oauthError?: string;
      errorDescription?: string;
      errorUri?: string;
      parameter?: string;
    } = {},
  ) {
    super(callbackErrorMessage(code));
    this.name = "OAuthCallbackError";
    this.code = code;
    this.oauthError = options.oauthError;
    this.errorDescription = options.errorDescription;
    this.errorUri = options.errorUri;
    this.parameter = options.parameter;
  }
}

export type ParseOAuthCallbackOptions = {
  expectedState: string;
  expectedRedirectUri?: string | URL;
};

export type OAuthAuthorizationCodeCallback = {
  code: string;
  state: string;
};

/**
 * Parses an authorization callback, validates its state and surfaces protocol
 * errors as OAuthCallbackError. State is checked before provider errors.
 */
export function parseOAuthCallback(
  callback: string | URL | URLSearchParams,
  options: ParseOAuthCallbackOptions,
): OAuthAuthorizationCodeCallback {
  requireValue(options.expectedState, "oauth_expected_state_missing");
  if (options.expectedRedirectUri !== undefined) {
    validateCallbackRedirectUri(callback, options.expectedRedirectUri);
  }
  const parameters = callbackParameters(callback);
  const state = singleCallbackParameter(parameters, "state");
  if (!state) throw new OAuthCallbackError("missing_state");
  if (state !== options.expectedState) {
    throw new OAuthCallbackError("state_mismatch");
  }

  if (parameters.has("error")) {
    throw new OAuthCallbackError("authorization_error", {
      oauthError:
        singleCallbackParameter(parameters, "error") || "unknown_error",
      errorDescription:
        singleCallbackParameter(parameters, "error_description") || undefined,
      errorUri:
        singleCallbackParameter(parameters, "error_uri") || undefined,
    });
  }

  const code = singleCallbackParameter(parameters, "code");
  if (!code) throw new OAuthCallbackError("missing_code");
  return { code, state };
}

export type OAuthFetch = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

export type OAuthTokenResponse = {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in?: number;
  scope?: string;
  [extension: string]: unknown;
};

export type OAuthAuthorizationCodeGrant = {
  code: string;
  redirectUri: string;
  codeVerifier: string;
};

export type OAuthRefreshTokenGrant = {
  refreshToken: string;
  scope?: OAuthScope;
};

export type OAuthTokenClientOptions = {
  tokenEndpoint: string | URL;
  clientId: string;
  fetch?: OAuthFetch;
};

export type OAuthTokenErrorCode =
  | "invalid_token_response"
  | "token_endpoint_error";

export class OAuthTokenError extends Error {
  readonly code: OAuthTokenErrorCode;
  readonly status: number;
  readonly oauthError?: string;
  readonly errorDescription?: string;
  readonly errorUri?: string;

  constructor(
    code: OAuthTokenErrorCode,
    options: {
      status: number;
      oauthError?: string;
      errorDescription?: string;
      errorUri?: string;
    },
  ) {
    super(
      code === "token_endpoint_error"
        ? "The OAuth token endpoint rejected the request."
        : "The OAuth token endpoint returned an invalid response.",
    );
    this.name = "OAuthTokenError";
    this.code = code;
    this.status = options.status;
    this.oauthError = options.oauthError;
    this.errorDescription = options.errorDescription;
    this.errorUri = options.errorUri;
  }
}

/**
 * Stateless OAuth 2.1 public-client token transport. It never persists or
 * refreshes tokens implicitly; applications own their token storage policy.
 */
export class OAuthTokenClient {
  readonly tokenEndpoint: string;
  readonly clientId: string;
  private readonly fetchImplementation: OAuthFetch;

  constructor(options: OAuthTokenClientOptions) {
    this.tokenEndpoint = secureOAuthEndpoint(
      options.tokenEndpoint,
      "token",
    ).toString();
    requireValue(options.clientId, "oauth_client_id_missing");
    this.clientId = options.clientId;

    if (options.fetch) {
      this.fetchImplementation = options.fetch;
    } else if (typeof globalThis.fetch === "function") {
      this.fetchImplementation = globalThis.fetch.bind(globalThis);
    } else {
      throw new Error("oauth_fetch_unavailable");
    }
  }

  exchangeAuthorizationCode(
    grant: OAuthAuthorizationCodeGrant,
  ): Promise<OAuthTokenResponse> {
    requireValue(grant.code, "oauth_authorization_code_missing");
    requireValue(grant.redirectUri, "oauth_redirect_uri_missing");
    requireValue(grant.codeVerifier, "oauth_pkce_verifier_missing");
    return this.requestToken(
      new URLSearchParams({
        grant_type: "authorization_code",
        client_id: this.clientId,
        code: grant.code,
        redirect_uri: grant.redirectUri,
        code_verifier: grant.codeVerifier,
      }),
    );
  }

  refreshToken(grant: OAuthRefreshTokenGrant): Promise<OAuthTokenResponse> {
    requireValue(grant.refreshToken, "oauth_refresh_token_missing");
    const parameters = new URLSearchParams({
      grant_type: "refresh_token",
      client_id: this.clientId,
      refresh_token: grant.refreshToken,
    });
    if (grant.scope !== undefined) {
      parameters.set("scope", normalizeScope(grant.scope));
    }
    return this.requestToken(parameters);
  }

  private async requestToken(
    parameters: URLSearchParams,
  ): Promise<OAuthTokenResponse> {
    const response = await this.fetchImplementation(this.tokenEndpoint, {
      method: "POST",
      cache: "no-store",
      credentials: "omit",
      redirect: "error",
      headers: {
        accept: "application/json",
        "content-type": "application/x-www-form-urlencoded",
      },
      body: parameters.toString(),
    });
    const payload = await responseJson(response);

    if (!response.ok) {
      throw new OAuthTokenError("token_endpoint_error", {
        status: response.status,
        oauthError: stringProperty(payload, "error"),
        errorDescription: stringProperty(payload, "error_description"),
        errorUri: stringProperty(payload, "error_uri"),
      });
    }
    if (!isTokenResponse(payload)) {
      throw new OAuthTokenError("invalid_token_response", {
        status: response.status,
      });
    }
    return payload;
  }
}

function webCrypto(): Crypto {
  if (
    !globalThis.crypto ||
    typeof globalThis.crypto.getRandomValues !== "function" ||
    !globalThis.crypto.subtle
  ) {
    throw new Error("oauth_crypto_unavailable");
  }
  return globalThis.crypto;
}

function randomBase64Url(byteLength: number): string {
  const bytes = new Uint8Array(byteLength);
  webCrypto().getRandomValues(bytes);
  return base64Url(bytes);
}

function base64Url(bytes: Uint8Array): string {
  let result = "";
  for (let index = 0; index < bytes.length; index += 3) {
    const first = bytes[index] ?? 0;
    const second = bytes[index + 1];
    const third = bytes[index + 2];
    const value =
      (first << 16) | ((second ?? 0) << 8) | (third ?? 0);
    result += BASE64_URL_ALPHABET[(value >> 18) & 63];
    result += BASE64_URL_ALPHABET[(value >> 12) & 63];
    if (second !== undefined) {
      result += BASE64_URL_ALPHABET[(value >> 6) & 63];
    }
    if (third !== undefined) {
      result += BASE64_URL_ALPHABET[value & 63];
    }
  }
  return result;
}

const BASE64_URL_ALPHABET =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

type OAuthEndpointKind = "authorization" | "token";

function secureOAuthEndpoint(
  endpoint: string | URL,
  kind: OAuthEndpointKind,
): URL {
  const errorCode = `oauth_${kind}_endpoint_invalid`;
  let url: URL;
  try {
    url = new URL(endpoint);
  } catch {
    throw new Error(errorCode);
  }

  const secureTransport =
    url.protocol === "https:" ||
    (url.protocol === "http:" && isLoopbackHostname(url.hostname));
  const hasEmbeddedParameters =
    url.href.includes("?") || url.href.includes("#");
  if (
    !secureTransport ||
    url.username !== "" ||
    url.password !== "" ||
    hasEmbeddedParameters
  ) {
    throw new Error(errorCode);
  }
  return url;
}

function isLoopbackHostname(hostname: string): boolean {
  return (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "[::1]"
  );
}

function requireValue(value: string, errorCode: string): void {
  if (!value.trim()) throw new Error(errorCode);
}

function normalizeScope(scope: OAuthScope): string {
  return typeof scope === "string"
    ? scope.trim()
    : scope.map((entry) => entry.trim()).filter(Boolean).join(" ");
}

function callbackParameters(
  callback: string | URL | URLSearchParams,
): URLSearchParams {
  if (callback instanceof URLSearchParams) {
    return new URLSearchParams(callback);
  }
  if (callback instanceof URL) return new URLSearchParams(callback.search);
  try {
    return new URLSearchParams(new URL(callback).search);
  } catch {
    return new URLSearchParams(callback.startsWith("?") ? callback.slice(1) : callback);
  }
}

function validateCallbackRedirectUri(
  callback: string | URL | URLSearchParams,
  expectedRedirectUri: string | URL,
): void {
  const expected = parseExpectedRedirectUri(expectedRedirectUri);
  const actual = parseCallbackUrl(callback);
  if (
    actual.protocol !== expected.protocol ||
    actual.username !== expected.username ||
    actual.password !== expected.password ||
    actual.hostname !== expected.hostname ||
    actual.port !== expected.port ||
    actual.pathname !== expected.pathname
  ) {
    throw new OAuthCallbackError("redirect_uri_mismatch");
  }
}

function parseExpectedRedirectUri(expectedRedirectUri: string | URL): URL {
  let expected: URL;
  try {
    expected = new URL(expectedRedirectUri);
  } catch {
    throw new OAuthCallbackError("invalid_expected_redirect_uri");
  }
  if (
    expected.username !== "" ||
    expected.password !== "" ||
    expected.href.includes("?") ||
    expected.href.includes("#")
  ) {
    throw new OAuthCallbackError("invalid_expected_redirect_uri");
  }
  return expected;
}

function parseCallbackUrl(callback: string | URL | URLSearchParams): URL {
  if (callback instanceof URLSearchParams) {
    throw new OAuthCallbackError("invalid_callback_url");
  }
  let actual: URL;
  try {
    actual = new URL(callback);
  } catch {
    throw new OAuthCallbackError("invalid_callback_url");
  }
  if (
    actual.username !== "" ||
    actual.password !== "" ||
    actual.href.includes("#")
  ) {
    throw new OAuthCallbackError("invalid_callback_url");
  }
  return actual;
}

function singleCallbackParameter(
  parameters: URLSearchParams,
  name: string,
): string | null {
  const values = parameters.getAll(name);
  if (values.length > 1) {
    throw new OAuthCallbackError("duplicate_parameter", { parameter: name });
  }
  return values[0] ?? null;
}

function callbackErrorMessage(code: OAuthCallbackErrorCode): string {
  switch (code) {
    case "authorization_error":
      return "The authorization server returned an OAuth error.";
    case "duplicate_parameter":
      return "The OAuth callback contains a duplicate parameter.";
    case "invalid_callback_url":
      return "The OAuth callback URL is invalid.";
    case "invalid_expected_redirect_uri":
      return "The expected OAuth redirect URI is invalid.";
    case "missing_code":
      return "The OAuth callback does not contain an authorization code.";
    case "missing_state":
      return "The OAuth callback does not contain state.";
    case "redirect_uri_mismatch":
      return "The OAuth callback URL does not match the expected redirect URI.";
    case "state_mismatch":
      return "The OAuth callback state does not match the authorization request.";
  }
}

async function responseJson(response: Response): Promise<unknown> {
  const body = await response.text();
  if (!body) return undefined;
  try {
    return JSON.parse(body) as unknown;
  } catch {
    return undefined;
  }
}

function isTokenResponse(value: unknown): value is OAuthTokenResponse {
  if (!isRecord(value)) return false;
  if (
    typeof value.access_token !== "string" ||
    !value.access_token ||
    typeof value.token_type !== "string" ||
    !value.token_type
  ) {
    return false;
  }
  if (
    value.refresh_token !== undefined &&
    typeof value.refresh_token !== "string"
  ) {
    return false;
  }
  if (
    value.expires_in !== undefined &&
    (typeof value.expires_in !== "number" ||
      !Number.isFinite(value.expires_in) ||
      value.expires_in < 0)
  ) {
    return false;
  }
  return value.scope === undefined || typeof value.scope === "string";
}

function stringProperty(value: unknown, name: string): string | undefined {
  if (!isRecord(value)) return undefined;
  const property = value[name];
  return typeof property === "string" ? property : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
