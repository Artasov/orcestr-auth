"use client";

import { isAuthErrorCode, type AuthErrorCode } from "@orcestr/auth-core";
import { isApiError } from "@orcestr/core";
import { createContext, useContext, useMemo, type ReactNode } from "react";

export type AuthLocale = "en" | "ru";

export type AuthMessages = {
  common: {
    email: string;
    password: string;
    error: string;
    backToLogin: string;
  };
  login: {
    username: string;
    submit: string;
    submitting: string;
    forgot: string;
    register: string;
  };
  register: {
    username: string;
    firstName: string;
    lastName: string;
    submit: string;
    submitting: string;
    login: string;
  };
  forgot: { submit: string; submitting: string; sent: string };
  reset: {
    code: string;
    newPassword: string;
    submit: string;
    submitting: string;
    success: string;
  };
  verify: {
    code: string;
    submit: string;
    submitting: string;
    resend: string;
    resending: string;
  };
  change: {
    currentPassword: string;
    newPassword: string;
    repeatPassword: string;
    submit: string;
    submitting: string;
    mismatch: string;
  };
  oauth: {
    signInWith: string;
    providers: Record<"github" | "google" | "yandex", string>;
  };
  legal: {
    title: string;
    description: string;
    acceptPrefix: string;
    version: string;
    optional: string;
    confirm: string;
    cancel: string;
  };
  errors: Record<AuthErrorCode, string>;
};

export type AuthMessageOverrides = {
  [K in keyof AuthMessages]?: Partial<AuthMessages[K]>;
};

export const authMessages: Record<AuthLocale, AuthMessages> = {
  en: {
    common: {
      email: "Email",
      password: "Password",
      error: "Unable to complete the request.",
      backToLogin: "Back to sign in",
    },
    login: {
      username: "Email or username",
      submit: "Sign in",
      submitting: "Signing in...",
      forgot: "Forgot password?",
      register: "Create account",
    },
    register: {
      username: "Username",
      firstName: "First name",
      lastName: "Last name",
      submit: "Create account",
      submitting: "Creating...",
      login: "Sign in",
    },
    forgot: {
      submit: "Send reset code",
      submitting: "Sending...",
      sent: "If the account exists, a reset code has been sent.",
    },
    reset: {
      code: "Reset code",
      newPassword: "New password",
      submit: "Change password",
      submitting: "Changing...",
      success: "Password changed.",
    },
    verify: {
      code: "Confirmation code",
      submit: "Confirm email",
      submitting: "Confirming...",
      resend: "Send code again",
      resending: "Sending...",
    },
    change: {
      currentPassword: "Current password",
      newPassword: "New password",
      repeatPassword: "Repeat new password",
      submit: "Change password",
      submitting: "Changing...",
      mismatch: "Passwords do not match.",
    },
    oauth: {
      signInWith: "Sign in with {provider}",
      providers: { github: "GitHub", google: "Google", yandex: "Yandex" },
    },
    legal: {
      title: "Review and accept the legal documents",
      description:
        "Please review the current versions before continuing. Your acceptance will be recorded for these versions.",
      acceptPrefix: "I accept",
      version: "Version",
      optional: "optional",
      confirm: "Accept and continue",
      cancel: "Cancel",
    },
    errors: {
      invalid_credentials: "Invalid email, username or password.",
      not_authenticated: "Sign in to continue.",
      session_expired: "Your session has expired. Sign in again.",
      session_invalid: "Your session is invalid. Sign in again.",
      user_inactive: "This account is inactive.",
      auth_rate_limited: "Too many attempts. Try again later.",
      email_taken: "An account with this email already exists.",
      username_taken: "This username is already taken.",
      username_invalid: "Enter a valid username.",
      email_missing: "Add an email address to continue.",
      email_domain_not_allowed: "This email domain is not allowed.",
      country_not_supported: "Sign-in is not available in your location.",
      refresh_token_missing: "Your session has ended. Sign in again.",
      refresh_token_invalid: "Your session is invalid. Sign in again.",
      refresh_token_reused: "Your session was revoked. Sign in again.",
      refresh_token_expired: "Your session has expired. Sign in again.",
      password_reset_rate_limited:
        "Too many password reset requests. Try again later.",
      password_reset_code_invalid: "The reset code is invalid or expired.",
      password_reset_attempts_exceeded: "Too many invalid code attempts.",
      verification_resend_too_soon:
        "Wait before requesting another confirmation code.",
      verification_code_invalid: "The confirmation code is invalid or expired.",
      verification_attempts_exceeded: "Too many invalid code attempts.",
      current_password_invalid: "The current password is incorrect.",
      new_password_matches_current:
        "The new password must be different from the current password.",
      oauth_provider_not_supported: "This sign-in provider is not supported.",
      oauth_provider_not_enabled: "This sign-in provider is not enabled.",
      oauth_provider_not_allowed:
        "This sign-in provider is not available in your location.",
      oauth_account_link_required:
        "An account with this email already exists. Use its existing sign-in method; automatic linking is disabled.",
      oauth_code_exchange_failed: "The OAuth code could not be accepted.",
      oauth_provider_unavailable:
        "The sign-in provider is temporarily unavailable. Try again in a few minutes.",
      oauth_provider_timeout:
        "The sign-in provider did not respond in time. Try again.",
      oauth_userinfo_failed:
        "The sign-in provider did not return the account profile. Try again.",
      oauth_access_token_missing:
        "The sign-in provider did not return an access token. Start sign-in again.",
      oauth_origin_not_allowed: "The sign-in origin is not allowed.",
      oauth_redirect_uri_not_allowed:
        "The sign-in callback address is not allowed.",
      oauth_email_missing:
        "The sign-in provider did not return a usable email address.",
      csrf_header_missing: "The request security check failed.",
    },
  },
  ru: {
    common: {
      email: "Email",
      password: "Пароль",
      error: "Не удалось выполнить запрос.",
      backToLogin: "Вернуться ко входу",
    },
    login: {
      username: "Email или логин",
      submit: "Войти",
      submitting: "Входим...",
      forgot: "Забыли пароль?",
      register: "Создать аккаунт",
    },
    register: {
      username: "Логин",
      firstName: "Имя",
      lastName: "Фамилия",
      submit: "Создать аккаунт",
      submitting: "Создаём...",
      login: "Войти",
    },
    forgot: {
      submit: "Отправить код",
      submitting: "Отправляем...",
      sent: "Если аккаунт существует, код восстановления отправлен.",
    },
    reset: {
      code: "Код восстановления",
      newPassword: "Новый пароль",
      submit: "Сменить пароль",
      submitting: "Сохраняем...",
      success: "Пароль изменён.",
    },
    verify: {
      code: "Код подтверждения",
      submit: "Подтвердить email",
      submitting: "Проверяем...",
      resend: "Отправить код ещё раз",
      resending: "Отправляем...",
    },
    change: {
      currentPassword: "Текущий пароль",
      newPassword: "Новый пароль",
      repeatPassword: "Повторите новый пароль",
      submit: "Сменить пароль",
      submitting: "Сохраняем...",
      mismatch: "Пароли не совпадают.",
    },
    oauth: {
      signInWith: "Войти через {provider}",
      providers: { github: "GitHub", google: "Google", yandex: "Яндекс" },
    },
    legal: {
      title: "Ознакомьтесь и примите документы",
      description:
        "Перед продолжением ознакомьтесь с актуальными версиями. Принятие будет сохранено именно для этих версий.",
      acceptPrefix: "Я принимаю",
      version: "Версия",
      optional: "необязательно",
      confirm: "Принять и продолжить",
      cancel: "Отмена",
    },
    errors: {
      invalid_credentials: "Неверный email, логин или пароль.",
      not_authenticated: "Войдите, чтобы продолжить.",
      session_expired: "Сессия истекла. Войдите снова.",
      session_invalid: "Сессия недействительна. Войдите снова.",
      user_inactive: "Этот аккаунт отключён.",
      auth_rate_limited: "Слишком много попыток. Повторите позже.",
      email_taken: "Аккаунт с таким email уже существует.",
      username_taken: "Этот логин уже занят.",
      username_invalid: "Введите корректный логин.",
      email_missing: "Добавьте email, чтобы продолжить.",
      email_domain_not_allowed: "Этот домен email не разрешён.",
      country_not_supported: "Вход недоступен в вашем регионе.",
      refresh_token_missing: "Сессия завершена. Войдите снова.",
      refresh_token_invalid: "Сессия недействительна. Войдите снова.",
      refresh_token_reused: "Сессия отозвана. Войдите снова.",
      refresh_token_expired: "Сессия истекла. Войдите снова.",
      password_reset_rate_limited:
        "Слишком много запросов восстановления. Повторите позже.",
      password_reset_code_invalid: "Код восстановления неверен или истёк.",
      password_reset_attempts_exceeded: "Слишком много неверных попыток.",
      verification_resend_too_soon: "Подождите перед повторной отправкой кода.",
      verification_code_invalid: "Код подтверждения неверен или истёк.",
      verification_attempts_exceeded: "Слишком много неверных попыток.",
      current_password_invalid: "Текущий пароль введён неверно.",
      new_password_matches_current:
        "Новый пароль должен отличаться от текущего.",
      oauth_provider_not_supported: "Этот способ входа не поддерживается.",
      oauth_provider_not_enabled: "Этот способ входа не включён.",
      oauth_provider_not_allowed:
        "Этот способ входа недоступен в вашем регионе.",
      oauth_account_link_required:
        "Аккаунт с таким email уже существует. Используйте прежний способ входа; автоматическая привязка отключена.",
      oauth_code_exchange_failed: "Не удалось принять OAuth-код.",
      oauth_provider_unavailable:
        "Сервис входа временно недоступен. Повторите попытку через несколько минут.",
      oauth_provider_timeout:
        "Сервис входа не ответил вовремя. Повторите попытку.",
      oauth_userinfo_failed:
        "Сервис входа не вернул данные аккаунта. Повторите попытку.",
      oauth_access_token_missing:
        "Сервис входа не вернул токен доступа. Начните вход заново.",
      oauth_origin_not_allowed: "Источник запроса на вход не разрешён.",
      oauth_redirect_uri_not_allowed: "Адрес возврата после входа не разрешён.",
      oauth_email_missing: "Сервис входа не вернул подходящий email.",
      csrf_header_missing: "Не пройдена проверка безопасности запроса.",
    },
  },
};

const AuthI18nContext = createContext<AuthMessages>(authMessages.en);

export function AuthI18nProvider({
  locale,
  overrides,
  children,
}: {
  locale: AuthLocale;
  overrides?: AuthMessageOverrides;
  children: ReactNode;
}) {
  const value = useMemo(
    () => mergeMessages(authMessages[locale], overrides),
    [locale, overrides],
  );
  return (
    <AuthI18nContext.Provider value={value}>
      {children}
    </AuthI18nContext.Provider>
  );
}

export function useAuthMessages(): AuthMessages {
  return useContext(AuthI18nContext);
}

export function resolveAuthErrorMessage(
  error: unknown,
  messages: AuthMessages,
  fallback = messages.common.error,
): string {
  if (isApiError(error)) {
    return isAuthErrorCode(error.code) ? messages.errors[error.code] : fallback;
  }
  return error instanceof Error ? error.message : fallback;
}

function mergeMessages(
  base: AuthMessages,
  overrides?: AuthMessageOverrides,
): AuthMessages {
  if (!overrides) return base;
  return Object.fromEntries(
    Object.entries(base).map(([key, value]) => [
      key,
      { ...value, ...(overrides[key as keyof AuthMessages] ?? {}) },
    ]),
  ) as AuthMessages;
}
