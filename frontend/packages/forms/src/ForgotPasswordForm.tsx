"use client";

import { usePasswordResetRequest } from "@orcestr/auth-react";
import { Alert, Button, Flex } from "@orcestr/ui";
import { useState } from "react";

import { AuthField, AuthFormError, AuthTextField } from "./fields.js";
import { useAuthMessages } from "./i18n.js";

export function ForgotPasswordForm({
  onCodeRequested,
}: {
  onCodeRequested?: (email: string) => void;
}) {
  const copy = useAuthMessages();
  const [email, setEmail] = useState("");
  const mutation = usePasswordResetRequest();
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate(email, { onSuccess: () => onCodeRequested?.(email) });
      }}
    >
      <Flex col g="3">
        <AuthFormError error={mutation.error} fallback={copy.common.error} />
        {mutation.isSuccess ? (
          <Alert tone="success">
            <span>{copy.forgot.sent}</span>
          </Alert>
        ) : null}
        <AuthField label={copy.common.email}>
          <AuthTextField
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            autoComplete="email"
          />
        </AuthField>
        <Button
          type="submit"
          size={3}
          disabled={mutation.isPending || !email.trim()}
        >
          {mutation.isPending ? copy.forgot.submitting : copy.forgot.submit}
        </Button>
      </Flex>
    </form>
  );
}
