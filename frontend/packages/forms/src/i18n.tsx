"use client";

import { AuthApiError } from "@orcestr/auth-core";
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
  errors: Record<string, string>;
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
    errors: {
      invalid_credentials: "Invalid email, username or password.",
      "Invalid username or password.": "Invalid email, username or password.",
      user_inactive: "This account is inactive.",
      auth_rate_limited: "Too many attempts. Try again later.",
      password_reset_code_invalid: "The reset code is invalid or expired.",
      password_reset_attempts_exceeded: "Too many invalid code attempts.",
      verification_code_invalid: "The confirmation code is invalid or expired.",
      verification_attempts_exceeded: "Too many invalid code attempts.",
      oauth_provider_not_enabled: "This sign-in provider is not enabled.",
      oauth_account_link_required:
        "An account with this email already exists. Use its existing sign-in method; automatic linking is disabled.",
      oauth_code_exchange_failed: "The OAuth code could not be accepted.",
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
    errors: {
      invalid_credentials: "Неверный email, логин или пароль.",
      "Invalid username or password.": "Неверный email, логин или пароль.",
      user_inactive: "Этот аккаунт отключён.",
      auth_rate_limited: "Слишком много попыток. Повторите позже.",
      password_reset_code_invalid: "Код восстановления неверен или истёк.",
      password_reset_attempts_exceeded: "Слишком много неверных попыток.",
      verification_code_invalid: "Код подтверждения неверен или истёк.",
      verification_attempts_exceeded: "Слишком много неверных попыток.",
      oauth_provider_not_enabled: "Этот способ входа не включён.",
      oauth_account_link_required:
        "Аккаунт с таким email уже существует. Используйте прежний способ входа; автоматическая привязка отключена.",
      oauth_code_exchange_failed: "Не удалось принять OAuth-код.",
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
  if (error instanceof AuthApiError) {
    return messages.errors[error.code] ?? fallback;
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
