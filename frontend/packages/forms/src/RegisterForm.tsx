"use client";

import type { AuthMethods, AuthUser } from "@orcestr/auth-core";
import { useRegister } from "@orcestr/auth-react";
import { Button, Flex, Text } from "@orcestr/ui";
import { useState, type ReactNode } from "react";

import { AuthField, AuthFormError, AuthTextField } from "./fields.js";
import { useAuthMessages } from "./i18n.js";
import { OAuthButtons } from "./OAuthButtons.js";

export function RegisterForm<TUser extends AuthUser = AuthUser>({
  loginHref,
  extraPayload,
  legalContent,
  onSuccess,
  methods,
  next = "/overview",
  disabled = false,
}: {
  loginHref?: string;
  extraPayload?: Record<string, unknown> | (() => Record<string, unknown>);
  legalContent?: ReactNode;
  onSuccess?: (user: TUser) => void;
  methods?: AuthMethods;
  next?: string;
  disabled?: boolean;
}) {
  const copy = useAuthMessages();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const mutation = useRegister<TUser>();
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        const extension =
          typeof extraPayload === "function" ? extraPayload() : extraPayload;
        mutation.mutate(
          {
            username: username || undefined,
            email,
            password,
            first_name: firstName || undefined,
            last_name: lastName || undefined,
            ...extension,
          },
          { onSuccess: ({ user }) => onSuccess?.(user) },
        );
      }}
    >
      <Flex col g="3">
        <OAuthButtons
          providers={methods?.allowed_oauth_providers ?? []}
          clientIds={methods?.oauth_client_ids ?? {}}
          next={next}
        />
        <AuthFormError error={mutation.error} fallback={copy.common.error} />
        <AuthField label={copy.register.username}>
          <AuthTextField
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
        </AuthField>
        <AuthField label={copy.common.email}>
          <AuthTextField
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            autoComplete="email"
          />
        </AuthField>
        <AuthField label={copy.register.firstName}>
          <AuthTextField
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            autoComplete="given-name"
          />
        </AuthField>
        <AuthField label={copy.register.lastName}>
          <AuthTextField
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            autoComplete="family-name"
          />
        </AuthField>
        <AuthField label={copy.common.password}>
          <AuthTextField
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete="new-password"
          />
        </AuthField>
        {legalContent}
        <Button
          type="submit"
          size={3}
          disabled={
            disabled ||
            mutation.isPending ||
            methods?.email_password_allowed === false ||
            !email ||
            password.length < 8
          }
        >
          {mutation.isPending ? copy.register.submitting : copy.register.submit}
        </Button>
        {loginHref ? (
          <Text fs={14}>
            <a href={loginHref}>{copy.register.login}</a>
          </Text>
        ) : null}
      </Flex>
    </form>
  );
}
