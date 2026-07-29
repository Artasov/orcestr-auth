export const AUTH_ERROR_CODES = {
  invalidCredentials: "invalid_credentials",
  notAuthenticated: "not_authenticated",
  sessionExpired: "session_expired",
  sessionInvalid: "session_invalid",
  userInactive: "user_inactive",
  authRateLimited: "auth_rate_limited",
  csrfHeaderMissing: "csrf_header_missing",
  emailTaken: "email_taken",
  usernameTaken: "username_taken",
  usernameInvalid: "username_invalid",
  emailMissing: "email_missing",
  emailDomainNotAllowed: "email_domain_not_allowed",
  countryNotSupported: "country_not_supported",
  refreshTokenMissing: "refresh_token_missing",
  refreshTokenInvalid: "refresh_token_invalid",
  refreshTokenReused: "refresh_token_reused",
  refreshTokenExpired: "refresh_token_expired",
  passwordResetRateLimited: "password_reset_rate_limited",
  passwordResetCodeInvalid: "password_reset_code_invalid",
  passwordResetAttemptsExceeded: "password_reset_attempts_exceeded",
  verificationResendTooSoon: "verification_resend_too_soon",
  verificationCodeInvalid: "verification_code_invalid",
  verificationAttemptsExceeded: "verification_attempts_exceeded",
  currentPasswordInvalid: "current_password_invalid",
  newPasswordMatchesCurrent: "new_password_matches_current",
  oauthProviderNotSupported: "oauth_provider_not_supported",
  oauthProviderNotEnabled: "oauth_provider_not_enabled",
  oauthProviderNotAllowed: "oauth_provider_not_allowed",
  oauthAccountLinkRequired: "oauth_account_link_required",
  oauthCodeExchangeFailed: "oauth_code_exchange_failed",
  oauthProviderUnavailable: "oauth_provider_unavailable",
  oauthProviderTimeout: "oauth_provider_timeout",
  oauthUserinfoFailed: "oauth_userinfo_failed",
  oauthAccessTokenMissing: "oauth_access_token_missing",
  oauthOriginNotAllowed: "oauth_origin_not_allowed",
  oauthRedirectUriNotAllowed: "oauth_redirect_uri_not_allowed",
  oauthEmailMissing: "oauth_email_missing",
} as const;

export type AuthErrorCode =
  (typeof AUTH_ERROR_CODES)[keyof typeof AUTH_ERROR_CODES];

const AUTH_ERROR_CODE_SET = new Set<string>(Object.values(AUTH_ERROR_CODES));

export function isAuthErrorCode(value: string): value is AuthErrorCode {
  return AUTH_ERROR_CODE_SET.has(value);
}
