import type { ApiExecutor } from "@orcestr/core";

export type AuthSessionRequestResult = {
  response: Response;
  refreshFailed: boolean;
};

export class AuthSessionManager {
  private readonly execute: ApiExecutor;
  private readonly refresh: () => Promise<Response>;
  private refreshPromise: Promise<boolean> | null = null;

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
    let response = await this.execute(input, init);
    if (response.status !== 401 || options.allowRefresh === false) {
      return { response, refreshFailed: false };
    }
    if (!(await this.refreshOnce())) {
      return { response, refreshFailed: true };
    }
    response = await this.execute(input, init);
    return { response, refreshFailed: false };
  }

  private refreshOnce(): Promise<boolean> {
    if (this.refreshPromise) return this.refreshPromise;
    this.refreshPromise = (async () => {
      try {
        return (await this.refresh()).ok;
      } catch {
        return false;
      } finally {
        this.refreshPromise = null;
      }
    })();
    return this.refreshPromise;
  }
}

