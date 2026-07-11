import { Alert, Flex, Text, TextField } from "@orcestr/ui";
import type { ChangeEventHandler, ReactNode } from "react";

import { resolveAuthErrorMessage, useAuthMessages } from "./i18n.js";

export function AuthField({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <Flex col g="1">
      <Text as="label" fs={14} fw="medium">
        {label}
      </Text>
      {children}
    </Flex>
  );
}

export function AuthTextField(props: {
  value: string;
  onChange: ChangeEventHandler<HTMLInputElement>;
  type?: string;
  autoComplete?: string;
  placeholder?: string;
}) {
  return <TextField size="3" {...props} />;
}

export function AuthFormError({
  error,
  fallback,
}: {
  error: unknown;
  fallback: string;
}) {
  const messages = useAuthMessages();
  if (!error) return null;
  const message = resolveAuthErrorMessage(error, messages, fallback);
  return (
    <Alert tone="danger">
      <span>{message}</span>
    </Alert>
  );
}
