"use client";

import { useEmailVerification } from "@orcestr/auth-react";
import { Button, Flex } from "@orcestr/ui";
import { useState } from "react";

import { AuthField, AuthFormError, AuthTextField } from "./fields.js";
import { useAuthMessages } from "./i18n.js";

export function VerifyEmailForm({ onSuccess }: { onSuccess?: () => void }) {
  const copy = useAuthMessages();
  const [code, setCode] = useState("");
  const { send, confirm } = useEmailVerification();
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        confirm.mutate(code, { onSuccess });
      }}
    >
      <Flex col g="3">
        <AuthFormError
          error={confirm.error ?? send.error}
          fallback={copy.common.error}
        />
        <AuthField label={copy.verify.code}>
          <AuthTextField
            value={code}
            onChange={(e) =>
              setCode(e.target.value.replace(/\D/gu, "").slice(0, 16))
            }
            autoComplete="one-time-code"
          />
        </AuthField>
        <Button
          type="submit"
          size={3}
          disabled={confirm.isPending || code.length < 4}
        >
          {confirm.isPending ? copy.verify.submitting : copy.verify.submit}
        </Button>
        <Button
          type="button"
          size={2}
          v="soft"
          disabled={send.isPending}
          onClick={() => send.mutate()}
        >
          {send.isPending ? copy.verify.resending : copy.verify.resend}
        </Button>
      </Flex>
    </form>
  );
}
