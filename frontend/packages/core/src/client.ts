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
};

export class AuthApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message = code,
  ) {
    super(message);
    this.name = "AuthApiError";
  }
}

export class AuthClient<TUser extends AuthUser = AuthUser> {
  readonly routes: AuthClientRoutes;
  private readonly fetcher: typeof globalThis.fetch;

  constructor(options: AuthClientOptions) {
    this.routes = options.routes;
    this.fetcher = options.fetch ?? globalThis.fetch.bind(globalThis);
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
    allowRefresh = true,
  ): Promise<T> {
    let response = await this.fetcher(url, {
      ...init,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        ...init.headers,
      },
    });
    if (response.status === 401 && allowRefresh && this.canRefreshFor(url)) {
      const refreshed = await this.fetcher(this.routes.refresh, {
        method: "POST",
        credentials: "include",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (refreshed.ok) {
        return this.request<T>(url, init, false);
      }
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const code = String(
        body.error ?? body.detail ?? `auth_http_${response.status}`,
      );
      throw new AuthApiError(response.status, code);
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
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
}
