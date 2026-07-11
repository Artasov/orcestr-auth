"use client";

import { Button, Flex, Text } from "@orcestr/ui";
import { useState } from "react";

import { AuthField, AuthTextField } from "./fields.js";
import { useAuthMessages } from "./i18n.js";

export function ChangePasswordForm({
  submit,
  pending = false,
}: {
  submit: (payload: { currentPassword: string; newPassword: string }) => void;
  pending?: boolean;
}) {
  const copy = useAuthMessages().change;
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [repeatPassword, setRepeatPassword] = useState("");
  const mismatch = Boolean(repeatPassword && newPassword !== repeatPassword);
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (!mismatch) submit({ currentPassword, newPassword });
      }}
    >
      <Flex col g="3">
        <AuthField label={copy.currentPassword}>
          <AuthTextField
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            type="password"
            autoComplete="current-password"
          />
        </AuthField>
        <AuthField label={copy.newPassword}>
          <AuthTextField
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            type="password"
            autoComplete="new-password"
          />
        </AuthField>
        <AuthField label={copy.repeatPassword}>
          <AuthTextField
            value={repeatPassword}
            onChange={(e) => setRepeatPassword(e.target.value)}
            type="password"
            autoComplete="new-password"
          />
        </AuthField>
        {mismatch ? (
          <Text tone="danger" fs={13}>
            {copy.mismatch}
          </Text>
        ) : null}
        <Button
          type="submit"
          size={3}
          disabled={pending || mismatch || newPassword.length < 8}
        >
          {pending ? copy.submitting : copy.submit}
        </Button>
      </Flex>
    </form>
  );
}
