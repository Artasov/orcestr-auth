import { safeInternalPath } from "@orcestr/core";

const AUTH_LOOP_PATH =
  /^\/(?:[a-z]{2}\/)?(?:login|register|forgot-password|reset-password|auth(?:\/|$))/u;

export function safeRedirectPath(
  value: string | null | undefined,
  fallback = "/overview",
): string {
  const safePath = safeInternalPath(value, fallback);
  const url = new URL(safePath, "http://orcestr.internal");
  return AUTH_LOOP_PATH.test(url.pathname) ? fallback : safePath;
}

export function authPathWithNext(
  pathname: "/login" | "/register" | "/forgot-password" | "/reset-password",
  value: string | null | undefined,
  fallback = "/overview",
): string {
  return `${pathname}?next=${encodeURIComponent(safeRedirectPath(value, fallback))}`;
}

export function currentLocationNext(fallback = "/overview"): string {
  if (typeof window === "undefined") return fallback;
  return safeRedirectPath(
    `${window.location.pathname}${window.location.search}${window.location.hash}`,
    fallback,
  );
}
