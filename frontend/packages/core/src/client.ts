import {
  formatPayload,
  formatTime,
  formatUrl,
  resolveLogOptions,
  type CutieLogOptions,
} from "cutie-logs";
import { ApiClient } from "@orcestr/core";
import { AuthSessionManager } from "./session.js";

export type AuthUser = {
  id: number | string;
  username: string;
  email?: string | null;
  email_verified?: boolean;
  is_active?: boolean;
  [key: string]: unknown;
};

export type AuthMethods = {
  email_password_allowed: boolean;
  allowed_oauth_providers: OAuthProvider[];
  oauth_client_ids?: Partial<Record<OAuthProvider, string>>;
  country_known?: boolean;
  allowed_email_domains: string[];
};

export type OAuthProvider = "github" | "google" | "yandex";

export type AuthClientRoutes = {
  login: string;
  register: string;
  methods: string;
  me: string;
  refresh: string;
  logout: string;
  passwordResetRequest: string;
  passwordResetConfirm: string;
  emailVerificationCode: string;
  emailConfirm: string;
  oauthCallback: (provider: OAuthProvider) => string;
};

export type AuthClientOptions = {
  routes: AuthClientRoutes;
  fetch?: typeof globalThis.fetch;
  logging?: boolean | CutieLogOptions;
};

export class AuthClient<TUser extends AuthUser = AuthUser> {
  readonly routes: AuthClientRoutes;
  private readonly fetcher: typeof globalThis.fetch;
  private readonly logging: ReturnType<typeof resolveLogOptions> | null;
  private readonly api: ApiClient;
  private readonly session: AuthSessionManager;

  constructor(options: AuthClientOptions) {
    this.routes = options.routes;
    this.fetcher = options.fetch ?? globalThis.fetch.bind(globalThis);
    this.logging = options.logging !== undefined && options.logging !== false
      ? resolveLogOptions({
          ...(typeof options.logging === "object" ? options.logging : {}),
          enabled:
            typeof options.logging === "object"
              ? (options.logging.enabled ?? true)
              : true,
          label:
            typeof options.logging === "object"
              ? (options.logging.label ?? "AUTH")
              : "AUTH",
        })
      : null;
    this.session = new AuthSessionManager({
      execute: (input, init) => this.fetch(requestUrl(input), init ?? {}),
      refresh: () =>
        this.fetch(this.routes.refresh, {
          method: "POST",
          credentials: "include",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        }),
    });
    this.api = new ApiClient({
      execute: async (input, init) => {
        const url = requestUrl(input);
        const result = await this.session.request(input, init, {
          allowRefresh: this.canRefreshFor(url),
        });
        return result.response;
      },
    });
  }

  methods(origin?: string): Promise<AuthMethods> {
    const query = origin ? `?origin=${encodeURIComponent(origin)}` : "";
    return this.request(`${this.routes.methods}${query}`, { method: "GET" });
  }

  me(): Promise<TUser> {
    return this.request(this.routes.me, { method: "GET" });
  }

  login(username: string, password: string): Promise<{ user: TUser }> {
    return this.request(this.routes.login, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  }

  register(payload: Record<string, unknown>): Promise<{ user: TUser }> {
    return this.request(this.routes.register, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  refresh(): Promise<{ user?: TUser }> {
    return this.request(this.routes.refresh, { method: "POST" });
  }

  logout(): Promise<void> {
    return this.request(this.routes.logout, { method: "POST" });
  }

  requestPasswordReset(email: string): Promise<void> {
    return this.request(this.routes.passwordResetRequest, {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  confirmPasswordReset(payload: {
    email: string;
    code: string;
    password: string;
  }): Promise<void> {
    return this.request(this.routes.passwordResetConfirm, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  sendVerificationCode(): Promise<{ sent: boolean }> {
    return this.request(this.routes.emailVerificationCode, { method: "POST" });
  }

  confirmEmail(code: string): Promise<TUser> {
    return this.request(this.routes.emailConfirm, {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  }

  oauthCallback(
    provider: OAuthProvider,
    payload: Record<string, unknown>,
  ): Promise<{ user: TUser }> {
    return this.request(this.routes.oauthCallback(provider), {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  private async request<T>(
    url: string,
    init: RequestInit,
  ): Promise<T> {
    const headers = new Headers(init.headers);
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    headers.set("X-Requested-With", "XMLHttpRequest");
    return this.api.request<T>(url, {
      ...init,
      signal: init.signal ?? undefined,
      credentials: "include",
      headers,
    });
  }

  private canRefreshFor(url: string): boolean {
    return ![
      this.routes.login,
      this.routes.register,
      this.routes.refresh,
      this.routes.passwordResetRequest,
      this.routes.passwordResetConfirm,
    ].some((route) => url.startsWith(route));
  }

  private async fetch(url: string, init: RequestInit): Promise<Response> {
    const method = (init.method ?? "GET").toUpperCase();
    const startedAt = nowMs();
    this.logSafely(() => this.logRequest(method, url, init.body));

    try {
      const response = await this.fetcher(url, init);
      if (this.logging?.enabled) {
        try {
          const body = await readResponseBody(response.clone());
          this.logResponse(
            method,
            url,
            response.status,
            body,
            nowMs() - startedAt,
          );
        } catch {
          // Logging must never affect authentication requests.
        }
      }
      return response;
    } catch (error) {
      this.logSafely(() =>
        this.logNetworkError(method, url, error, nowMs() - startedAt),
      );
      throw error;
    }
  }

  private logSafely(callback: () => void): void {
    try {
      callback();
    } catch {
      // Logging must never affect authentication requests.
    }
  }

  private logRequest(
    method: string,
    url: string,
    body: BodyInit | null | undefined,
  ): void {
    const logging = this.logging;
    if (!logging?.enabled) return;
    const time = logging.logRequestsTime
      ? formatTime(logging.timeLocale, logging.timestampFormatter)
      : null;
    const message = [
      `%c${logging.label} →`,
      `%c${method}`,
      `%c${formatUrl(url, undefined, logging)}`,
    ];
    const args = [
      style(logging.colors.request),
      style(logging.colors.method),
      style(logging.colors.url),
    ];
    if (time) {
      message.push(`%c[${time}]`);
      args.push(style(logging.colors.data));
    }
    logging.console.groupCollapsed(message.join(" "), ...args);
    const payload = normalizeRequestBody(body);
    if (payload !== undefined) {
      logging.console.log(
        "%cRequest data:",
        style(logging.colors.data),
        formatPayload(payload, logging),
      );
    }
    logging.console.groupEnd();
  }

  private logResponse(
    method: string,
    url: string,
    status: number,
    body: unknown,
    durationMs: number,
  ): void {
    const logging = this.logging;
    if (!logging?.enabled) return;
    const failed = status < 200 || status >= 300;
    const time = logging.logRequestsTime
      ? formatTime(logging.timeLocale, logging.timestampFormatter)
      : null;
    const message = [
      `%c${logging.label} ${failed ? "✕" : "←"}`,
      `%c${method}`,
      `%c${formatUrl(url, undefined, logging)}`,
      `%c[${status}]`,
    ];
    const args = [
      style(failed ? logging.colors.error : logging.colors.response),
      style(logging.colors.method),
      style(logging.colors.url),
      style(failed ? logging.colors.error : logging.colors.response),
    ];
    if (logging.logRequestsDelay) {
      message.push(`%c[${Math.max(0, Math.round(durationMs))}ms]`);
      args.push(style(logging.colors.data));
    }
    if (time) {
      message.push(`%c[${time}]`);
      args.push(style(logging.colors.data));
    }
    logging.console.groupCollapsed(message.join(" "), ...args);
    if (body !== undefined) {
      logging.console.log(
        failed ? "%cError response data:" : "%cResponse data:",
        style(logging.colors.data),
        formatPayload(body, logging),
      );
    }
    logging.console.groupEnd();
  }

  private logNetworkError(
    method: string,
    url: string,
    error: unknown,
    durationMs: number,
  ): void {
    const logging = this.logging;
    if (!logging?.enabled) return;
    const message = [
      `%c${logging.label} ✕`,
      `%c${method}`,
      `%c${formatUrl(url, undefined, logging)}`,
      "%c[NETWORK ERROR]",
    ];
    const args = [
      style(logging.colors.error),
      style(logging.colors.method),
      style(logging.colors.url),
      style(logging.colors.error),
    ];
    if (logging.logRequestsDelay) {
      message.push(`%c[${Math.max(0, Math.round(durationMs))}ms]`);
      args.push(style(logging.colors.data));
    }
    logging.console.groupCollapsed(message.join(" "), ...args);
    logging.console.log(
      "%cError:",
      style(logging.colors.data),
      formatPayload(error, logging),
    );
    logging.console.groupEnd();
  }
}

async function readResponseBody(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined;
  const text = await response.text().catch(() => "");
  if (!text) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function normalizeRequestBody(body: BodyInit | null | undefined): unknown {
  if (!body) return undefined;
  if (typeof body !== "string") return "[body]";
  try {
    return JSON.parse(body) as unknown;
  } catch {
    return body;
  }
}

function nowMs(): number {
  return typeof performance !== "undefined" && typeof performance.now === "function"
    ? performance.now()
    : Date.now();
}

function style(color: string): string {
  return `color: ${color}; font-weight: bold;`;
}

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.toString();
  return input.url;
}
