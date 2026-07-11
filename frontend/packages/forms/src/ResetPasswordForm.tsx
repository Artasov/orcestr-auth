"use client";

import { usePasswordResetConfirm } from "@orcestr/auth-react";
import { Alert, Button, Flex } from "@orcestr/ui";
import { useState } from "react";

import { AuthField, AuthFormError, AuthTextField } from "./fields.js";
import { useAuthMessages } from "./i18n.js";

export function ResetPasswordForm({
  email,
  onSuccess,
}: {
  email: string;
  onSuccess?: () => void;
}) {
  const copy = useAuthMessages();
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const mutation = usePasswordResetConfirm();
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate({ email, code, password }, { onSuccess });
      }}
    >
      <Flex col g="3">
        <AuthFormError error={mutation.error} fallback={copy.common.error} />
        {mutation.isSuccess ? (
          <Alert tone="success">
            <span>{copy.reset.success}</span>
          </Alert>
        ) : null}
        <AuthField label={copy.reset.code}>
          <AuthTextField
            value={code}
            onChange={(e) =>
              setCode(e.target.value.replace(/\D/gu, "").slice(0, 16))
            }
            autoComplete="one-time-code"
          />
        </AuthField>
        <AuthField label={copy.reset.newPassword}>
          <AuthTextField
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete="new-password"
          />
        </AuthField>
        <Button
          type="submit"
          size={3}
          disabled={
            mutation.isPending || code.length < 4 || password.length < 8
          }
        >
          {mutation.isPending ? copy.reset.submitting : copy.reset.submit}
        </Button>
      </Flex>
    </form>
  );
}
