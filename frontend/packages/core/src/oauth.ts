import { safeRedirectPath } from "./redirects.js";
import type { OAuthProvider } from "./client.js";

export type StoredOAuthState = {
  state: string;
  returnTo: string;
  createdAt: number;
};

const STATE_TTL_MS = 10 * 60 * 1000;

export function isOAuthProvider(value: string): value is OAuthProvider {
  return value === "github" || value === "google" || value === "yandex";
}

export function oauthRedirectUri(
  provider: OAuthProvider,
  origin?: string,
): string {
  const resolvedOrigin =
    origin ?? (typeof window === "undefined" ? "" : window.location.origin);
  return resolvedOrigin
    ? `${resolvedOrigin}/auth/oauth/${provider}/callback`
    : "";
}

export function createOAuthState(
  provider: OAuthProvider,
  next: string,
): string {
  assertBrowser();
  const state = randomBase64Url(24);
  const stored: StoredOAuthState = {
    state,
    returnTo: safeRedirectPath(next),
    createdAt: Date.now(),
  };
  sessionStorage.setItem(
    `orcestr_auth_state_${provider}`,
    JSON.stringify(stored),
  );
  return state;
}

export function consumeOAuthState(
  provider: OAuthProvider,
): StoredOAuthState | null {
  if (typeof window === "undefined") return null;
  const key = `orcestr_auth_state_${provider}`;
  const raw = sessionStorage.getItem(key);
  sessionStorage.removeItem(key);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<StoredOAuthState>;
    if (
      typeof parsed.state !== "string" ||
      typeof parsed.returnTo !== "string" ||
      typeof parsed.createdAt !== "number" ||
      Date.now() - parsed.createdAt > STATE_TTL_MS
    ) {
      return null;
    }
    return {
      state: parsed.state,
      returnTo: safeRedirectPath(parsed.returnTo),
      createdAt: parsed.createdAt,
    };
  } catch {
    return null;
  }
}

export function consumeOAuthCodeVerifier(
  provider: OAuthProvider,
): string | null {
  if (typeof window === "undefined") return null;
  const key = `orcestr_auth_verifier_${provider}`;
  const value = sessionStorage.getItem(key);
  sessionStorage.removeItem(key);
  return value;
}

export async function buildOAuthAuthorizeUrl(options: {
  provider: OAuthProvider;
  clientId: string;
  next: string;
  redirectUri?: string;
}): Promise<string> {
  const { provider, clientId, next } = options;
  if (!clientId.trim()) throw new Error("oauth_client_id_missing");
  const redirectUri = options.redirectUri ?? oauthRedirectUri(provider);
  if (!redirectUri) throw new Error("oauth_redirect_uri_missing");
  const state = createOAuthState(provider, next);
  const verifier = randomBase64Url(48);
  sessionStorage.setItem(`orcestr_auth_verifier_${provider}`, verifier);
  const challenge = await sha256Base64Url(verifier);
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });
  if (provider === "google") {
    params.set("scope", "openid email profile");
    params.set("prompt", "select_account");
    return `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  }
  if (provider === "github") {
    params.set("scope", "read:user user:email");
    return `https://github.com/login/oauth/authorize?${params}`;
  }
  params.set("scope", "login:email login:info");
  return `https://oauth.yandex.ru/authorize?${params}`;
}

function assertBrowser(): void {
  if (typeof window === "undefined" || !globalThis.crypto) {
    throw new Error("oauth_browser_required");
  }
}

function randomBase64Url(length: number): string {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return base64Url(bytes);
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary)
    .replace(/\+/gu, "-")
    .replace(/\//gu, "_")
    .replace(/=+$/u, "");
}

async function sha256Base64Url(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return base64Url(new Uint8Array(digest));
}
