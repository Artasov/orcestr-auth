from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from orcestr_core import ApiError


class AuthErrorCode(StrEnum):
    INVALID_CREDENTIALS = "invalid_credentials"
    NOT_AUTHENTICATED = "not_authenticated"
    SESSION_EXPIRED = "session_expired"
    SESSION_INVALID = "session_invalid"
    USER_INACTIVE = "user_inactive"
    AUTH_RATE_LIMITED = "auth_rate_limited"
    CSRF_HEADER_MISSING = "csrf_header_missing"
    EMAIL_TAKEN = "email_taken"
    USERNAME_TAKEN = "username_taken"
    USERNAME_INVALID = "username_invalid"
    EMAIL_MISSING = "email_missing"
    EMAIL_DOMAIN_NOT_ALLOWED = "email_domain_not_allowed"
    COUNTRY_NOT_SUPPORTED = "country_not_supported"
    REFRESH_TOKEN_MISSING = "refresh_token_missing"
    REFRESH_TOKEN_INVALID = "refresh_token_invalid"
    REFRESH_TOKEN_REUSED = "refresh_token_reused"
    REFRESH_TOKEN_EXPIRED = "refresh_token_expired"
    PASSWORD_RESET_RATE_LIMITED = "password_reset_rate_limited"
    PASSWORD_RESET_CODE_INVALID = "password_reset_code_invalid"
    PASSWORD_RESET_ATTEMPTS_EXCEEDED = "password_reset_attempts_exceeded"
    VERIFICATION_RESEND_TOO_SOON = "verification_resend_too_soon"
    VERIFICATION_CODE_INVALID = "verification_code_invalid"
    VERIFICATION_ATTEMPTS_EXCEEDED = "verification_attempts_exceeded"
    CURRENT_PASSWORD_INVALID = "current_password_invalid"
    NEW_PASSWORD_MATCHES_CURRENT = "new_password_matches_current"
    OAUTH_PROVIDER_NOT_SUPPORTED = "oauth_provider_not_supported"
    OAUTH_PROVIDER_NOT_ENABLED = "oauth_provider_not_enabled"
    OAUTH_PROVIDER_NOT_ALLOWED = "oauth_provider_not_allowed"
    OAUTH_ACCOUNT_LINK_REQUIRED = "oauth_account_link_required"
    OAUTH_CODE_EXCHANGE_FAILED = "oauth_code_exchange_failed"
    OAUTH_PROVIDER_UNAVAILABLE = "oauth_provider_unavailable"
    OAUTH_PROVIDER_TIMEOUT = "oauth_provider_timeout"
    OAUTH_USERINFO_FAILED = "oauth_userinfo_failed"
    OAUTH_ACCESS_TOKEN_MISSING = "oauth_access_token_missing"
    OAUTH_ORIGIN_NOT_ALLOWED = "oauth_origin_not_allowed"
    OAUTH_REDIRECT_URI_NOT_ALLOWED = "oauth_redirect_uri_not_allowed"
    OAUTH_EMAIL_MISSING = "oauth_email_missing"


AUTH_ERROR_MESSAGES: Mapping[AuthErrorCode, str] = {
    AuthErrorCode.INVALID_CREDENTIALS: "Invalid username or password.",
    AuthErrorCode.NOT_AUTHENTICATED: "Authentication is required.",
    AuthErrorCode.SESSION_EXPIRED: "The session has expired.",
    AuthErrorCode.SESSION_INVALID: "The session is invalid.",
    AuthErrorCode.USER_INACTIVE: "The user account is inactive.",
    AuthErrorCode.AUTH_RATE_LIMITED: "Too many authentication attempts.",
    AuthErrorCode.CSRF_HEADER_MISSING: "The request security check failed.",
    AuthErrorCode.EMAIL_TAKEN: "An account with this email already exists.",
    AuthErrorCode.USERNAME_TAKEN: "This username is already taken.",
    AuthErrorCode.USERNAME_INVALID: "The username is invalid.",
    AuthErrorCode.EMAIL_MISSING: "An email address is required.",
    AuthErrorCode.EMAIL_DOMAIN_NOT_ALLOWED: "This email domain is not allowed.",
    AuthErrorCode.COUNTRY_NOT_SUPPORTED: "Authentication is not available in this location.",
    AuthErrorCode.REFRESH_TOKEN_MISSING: "The refresh token is missing.",
    AuthErrorCode.REFRESH_TOKEN_INVALID: "The refresh token is invalid.",
    AuthErrorCode.REFRESH_TOKEN_REUSED: "The refresh token has already been used.",
    AuthErrorCode.REFRESH_TOKEN_EXPIRED: "The refresh token has expired.",
    AuthErrorCode.PASSWORD_RESET_RATE_LIMITED: "Too many password reset requests.",
    AuthErrorCode.PASSWORD_RESET_CODE_INVALID: "The password reset code is invalid.",
    AuthErrorCode.PASSWORD_RESET_ATTEMPTS_EXCEEDED: "Too many invalid reset code attempts.",
    AuthErrorCode.VERIFICATION_RESEND_TOO_SOON: "A verification code was requested too recently.",
    AuthErrorCode.VERIFICATION_CODE_INVALID: "The verification code is invalid.",
    AuthErrorCode.VERIFICATION_ATTEMPTS_EXCEEDED: "Too many invalid verification attempts.",
    AuthErrorCode.CURRENT_PASSWORD_INVALID: "The current password is incorrect.",
    AuthErrorCode.NEW_PASSWORD_MATCHES_CURRENT: "The new password must differ from the current password.",
    AuthErrorCode.OAUTH_PROVIDER_NOT_SUPPORTED: "The OAuth provider is not supported.",
    AuthErrorCode.OAUTH_PROVIDER_NOT_ENABLED: "The OAuth provider is not enabled.",
    AuthErrorCode.OAUTH_PROVIDER_NOT_ALLOWED: "The OAuth provider is not allowed.",
    AuthErrorCode.OAUTH_ACCOUNT_LINK_REQUIRED: "The account must be linked explicitly.",
    AuthErrorCode.OAUTH_CODE_EXCHANGE_FAILED: "The OAuth code exchange failed.",
    AuthErrorCode.OAUTH_PROVIDER_UNAVAILABLE: "The OAuth provider is unavailable.",
    AuthErrorCode.OAUTH_PROVIDER_TIMEOUT: "The OAuth provider timed out.",
    AuthErrorCode.OAUTH_USERINFO_FAILED: "The OAuth profile request failed.",
    AuthErrorCode.OAUTH_ACCESS_TOKEN_MISSING: "The OAuth access token is missing.",
    AuthErrorCode.OAUTH_ORIGIN_NOT_ALLOWED: "The OAuth request origin is not allowed.",
    AuthErrorCode.OAUTH_REDIRECT_URI_NOT_ALLOWED: "The OAuth callback URI is not allowed.",
    AuthErrorCode.OAUTH_EMAIL_MISSING: "The OAuth provider did not return an email address.",
}


def auth_api_error(
    *,
    status_code: int,
    code: AuthErrorCode,
    headers: Mapping[str, str] | None = None,
) -> ApiError:
    return ApiError(
        status_code=status_code,
        code=code.value,
        message=AUTH_ERROR_MESSAGES[code],
        headers=headers,
    )
