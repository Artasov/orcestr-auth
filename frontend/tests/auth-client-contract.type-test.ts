import type {
  AuthClient,
  AuthClientContract,
  AuthClientRoutes,
  AuthUser,
} from "../packages/core/dist/index.js";
import {
  AuthProvider,
  useAuthClient,
} from "../packages/react/dist/index.js";
import {
  LoginForm,
  type OAuthAuthorizeHandler,
  type OAuthButtonsOptions,
} from "../packages/forms/dist/index.js";

type NativeUser = AuthUser & {
  id: number;
  username: string;
};

const routes: AuthClientRoutes = {
  login: "native:login",
  register: "native:register",
  methods: "native:methods",
  me: "native:me",
  refresh: "native:refresh",
  logout: "native:logout",
  passwordResetRequest: "native:password-reset-request",
  passwordResetConfirm: "native:password-reset-confirm",
  emailVerificationCode: "native:email-verification-code",
  emailConfirm: "native:email-confirm",
  oauthCallback: (provider) => `native:oauth:${provider}:callback`,
};

const user: NativeUser = { id: 1, username: "native-user" };

const nativeClient: AuthClientContract<NativeUser> = {
  routes,
  async methods() {
    return {
      email_password_allowed: true,
      allowed_oauth_providers: ["github", "google", "yandex"],
      oauth_client_ids: { github: "github-client" },
      allowed_email_domains: [],
    };
  },
  async me() {
    return user;
  },
  async login() {
    return { user };
  },
  async register() {
    return { user };
  },
  async refresh() {
    return { user };
  },
  async logout() {},
  async requestPasswordReset() {},
  async confirmPasswordReset() {},
  async sendVerificationCode() {
    return { sent: true };
  },
  async confirmEmail() {
    return user;
  },
  async oauthCallback() {
    return { user };
  },
};

const providerProps: Parameters<typeof AuthProvider<NativeUser>>[0] = {
  client: nativeClient,
  children: null,
};

void providerProps;

const legacyHookResult: AuthClient<NativeUser> = null as unknown as ReturnType<
  typeof useAuthClient<NativeUser>
>;

void legacyHookResult;

const authorizeHandler: OAuthAuthorizeHandler = async (
  provider,
  clientId,
  next,
  callbackPayload,
) => {
  void [provider, clientId, next, callbackPayload];
};

const oauthButtons: OAuthButtonsOptions = {
  authorizeHandler,
  autoAuthorizeProvider: "google",
};

const loginFormProps: Parameters<typeof LoginForm<NativeUser>>[0] = {
  methods: await nativeClient.methods(),
  oauthButtons,
  oauthLegalConsent: false,
};

void loginFormProps;
