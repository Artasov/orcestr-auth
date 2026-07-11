"use client";

import type { AuthMethods, AuthUser } from "@orcestr/auth-core";
import { useLogin } from "@orcestr/auth-react";
import { Button, Flex, Text } from "@orcestr/ui";
import { useState } from "react";

import { AuthField, AuthFormError, AuthTextField } from "./fields.js";
import { useAuthMessages } from "./i18n.js";
import { OAuthButtons } from "./OAuthButtons.js";

export function LoginForm<TUser extends AuthUser = AuthUser>({
  methods,
  next = "/overview",
  forgotPasswordHref,
  registerHref,
  onSuccess,
}: {
  methods?: AuthMethods;
  next?: string;
  forgotPasswordHref?: string;
  registerHref?: string;
  onSuccess?: (user: TUser) => void;
}) {
  const copy = useAuthMessages();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const mutation = useLogin<TUser>();
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate(
          { username, password },
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
        <AuthField label={copy.login.username}>
          <AuthTextField
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
        </AuthField>
        <AuthField label={copy.common.password}>
          <AuthTextField
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete="current-password"
          />
        </AuthField>
        <Button
          type="submit"
          size={3}
          disabled={
            mutation.isPending || methods?.email_password_allowed === false
          }
        >
          {mutation.isPending ? copy.login.submitting : copy.login.submit}
        </Button>
        {forgotPasswordHref ? (
          <Text fs={14}>
            <a href={forgotPasswordHref}>{copy.login.forgot}</a>
          </Text>
        ) : null}
        {registerHref ? (
          <Text fs={14}>
            <a href={registerHref}>{copy.login.register}</a>
          </Text>
        ) : null}
      </Flex>
    </form>
  );
}
