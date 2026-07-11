import { safeRedirectPath } from "@orcestr/auth-core";
import { NextResponse, type NextRequest } from "next/server";

export type AuthProxyOptions = {
  accessCookieName?: string;
  refreshCookieName?: string;
  loginPath?: string;
  isProtectedPath: (pathname: string) => boolean;
  resolveVisiblePath?: (request: NextRequest) => string;
};

export function hasAuthSession(
  request: NextRequest,
  options: AuthProxyOptions,
): boolean {
  return (
    request.cookies.has(options.accessCookieName ?? "orcestr_access") ||
    request.cookies.has(options.refreshCookieName ?? "orcestr_refresh")
  );
}

export function authLoginRedirect(
  request: NextRequest,
  options: AuthProxyOptions,
): NextResponse | null {
  const pathname = request.nextUrl.pathname;
  if (!options.isProtectedPath(pathname) || hasAuthSession(request, options)) {
    return null;
  }
  const visiblePath = options.resolveVisiblePath?.(request) ?? pathname;
  const target = safeRedirectPath(`${visiblePath}${request.nextUrl.search}`);
  const url = request.nextUrl.clone();
  url.pathname = options.loginPath ?? "/login";
  url.search = "";
  url.searchParams.set("next", target);
  return NextResponse.redirect(url);
}

export function requestAuthNext(
  request: NextRequest,
  fallback = "/overview",
): string {
  return safeRedirectPath(
    `${request.nextUrl.pathname}${request.nextUrl.search}${request.nextUrl.hash}`,
    fallback,
  );
}
