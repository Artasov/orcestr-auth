"use client";

import { Button, Flex, Spinner, Text } from "@orcestr/ui";
import { AuthFormError } from "./fields.js";
import { useAuthMessages } from "./i18n.js";

export type AuthMethodsStatusProps = {
  methodsPending?: boolean;
  methodsError?: unknown;
  onRetryMethods?: () => void;
};

export function AuthMethodsStatus({
  methodsPending, methodsError, onRetryMethods,
}: AuthMethodsStatusProps) {
  const copy = useAuthMessages();
  if (methodsPending) return (
    <Flex a="center" g="2" role="status">
      <Spinner /><Text>{copy.common.loadingMethods}</Text>
    </Flex>
  );
  if (!methodsError) return null;
  return (
    <Flex col g="2">
      <AuthFormError error={methodsError} fallback={copy.common.error} />
      {onRetryMethods ? <Button type="button" v="soft" onClick={onRetryMethods}>
        {copy.common.retry}
      </Button> : null}
    </Flex>
  );
}
