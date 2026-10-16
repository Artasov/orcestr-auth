import type { ApiExecutor } from "@orcestr/core";

export type AuthSessionRequestResult = {
  response: Response;
  refreshFailed: boolean;
};

export class AuthSessionManager {
  private readonly execute: ApiExecutor;
  private readonly refresh: () => Promise<Response>;
  private refreshPromise: Promise<Response> | null = null;
  private generation = 0;

  constructor(options: {
    execute: ApiExecutor;
    refresh: () => Promise<Response>;
  }) {
    this.execute = options.execute;
    this.refresh = options.refresh;
  }

  async request(
    input: RequestInfo | URL,
    init?: RequestInit,
    options: { allowRefresh?: boolean } = {},
  ): Promise<AuthSessionRequestResult> {
    const generation = this.generation;
    let response = await this.execute(input, init);
    if (response.status !== 401 || options.allowRefresh === false) {
      return { response, refreshFailed: false };
    }
    // A slow 401 can arrive after another request has already renewed cookies.
    if (generation === this.generation) {
      const refreshed = await this.refreshOnce();
      if (!refreshed.ok) {
        const expired = refreshed.status === 401 || refreshed.status === 403;
        return {
          response: expired ? response : refreshed.clone(),
          refreshFailed: expired,
        };
      }
    }
    response = await this.execute(input, init);
    return { response, refreshFailed: response.status === 401 };
  }

  private refreshOnce(): Promise<Response> {
    if (this.refreshPromise) return this.refreshPromise;
    this.refreshPromise = (async () => {
      try {
        const response = await this.refresh();
        if (response.ok) this.generation += 1;
        return response;
      } finally {
        this.refreshPromise = null;
      }
    })();
    return this.refreshPromise;
  }
}

