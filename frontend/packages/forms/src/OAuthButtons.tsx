"use client";

import { buildOAuthAuthorizeUrl, type OAuthProvider } from "@orcestr/auth-core";
import { Button, Flex } from "@orcestr/ui";

import { useAuthMessages } from "./i18n.js";

export function OAuthButtons({
  providers,
  clientIds,
  next,
}: {
  providers: OAuthProvider[];
  clientIds: Partial<Record<OAuthProvider, string>>;
  next: string;
}) {
  const copy = useAuthMessages().oauth;
  const visible = providers.filter((provider) =>
    Boolean(clientIds[provider]?.trim()),
  );
  if (!visible.length) return null;
  return (
    <Flex col g="2">
      {visible.map((provider) => (
        <Button
          key={provider}
          type="button"
          v="soft"
          size={3}
          onClick={async () => {
            window.location.href = await buildOAuthAuthorizeUrl({
              provider,
              clientId: clientIds[provider] ?? "",
              next,
            });
          }}
        >
          {copy.signInWith.replace("{provider}", copy.providers[provider])}
        </Button>
      ))}
    </Flex>
  );
}
