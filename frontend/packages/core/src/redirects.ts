const MAX_REDIRECT_LENGTH = 2048;
const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f]/u;
const AUTH_LOOP_PATH =
  /^\/(?:[a-z]{2}\/)?(?:login|register|forgot-password|reset-password|auth(?:\/|$))/u;

export function safeRedirectPath(
  value: string | null | undefined,
  fallback = "/overview",
): string {
  if (
    !value ||
    value.length > MAX_REDIRECT_LENGTH ||
    CONTROL_CHARACTERS.test(value) ||
    !value.startsWith("/") ||
    value.startsWith("//") ||
    value.includes("\\")
  ) {
    return fallback;
  }
  try {
    const url = new URL(value, "http://localhost");
    if (AUTH_LOOP_PATH.test(url.pathname)) return fallback;
    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return fallback;
  }
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
