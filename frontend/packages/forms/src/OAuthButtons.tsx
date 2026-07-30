"use client";

import { buildOAuthAuthorizeUrl, type OAuthProvider } from "@orcestr/auth-core";
import { Button, Flex, type FlexProps } from "@orcestr/ui";
import type { ComponentType } from "react";

import { useAuthMessages } from "./i18n.js";

export type OAuthProviderButtonProps = {
  provider: OAuthProvider;
  label: string;
  onClick: () => void;
};

export type OAuthProviderButtonComponent =
  ComponentType<OAuthProviderButtonProps>;

export type OAuthButtonsOptions = {
  direction?: "row" | "column";
  align?: FlexProps["a"];
  justify?: FlexProps["j"];
  gap?: FlexProps["g"];
  className?: string;
  buttonComponent?: OAuthProviderButtonComponent;
  buttonComponents?: Partial<
    Record<OAuthProvider, OAuthProviderButtonComponent>
  >;
};

export type OAuthButtonsProps = OAuthButtonsOptions & {
  providers: OAuthProvider[];
  clientIds: Partial<Record<OAuthProvider, string>>;
  next: string;
};

function DefaultOAuthProviderButton({
  label,
  onClick,
}: OAuthProviderButtonProps) {
  return (
    <Button type="button" v="soft" size={3} onClick={onClick}>
      {label}
    </Button>
  );
}

export function OAuthButtons({
  providers,
  clientIds,
  next,
  direction = "column",
  align,
  justify,
  gap = "2",
  className,
  buttonComponent,
  buttonComponents,
}: OAuthButtonsProps) {
  const copy = useAuthMessages().oauth;
  const visible = providers.filter((provider) =>
    Boolean(clientIds[provider]?.trim()),
  );
  if (!visible.length) return null;

  return (
    <Flex
      direction={direction}
      wrap={direction === "row"}
      a={align}
      j={justify}
      g={gap}
      className={className}
    >
      {visible.map((provider) => {
        const ProviderButton =
          buttonComponents?.[provider] ??
          buttonComponent ??
          DefaultOAuthProviderButton;
        const label = copy.signInWith.replace(
          "{provider}",
          copy.providers[provider],
        );
        const onClick = () => {
          void (async () => {
            window.location.href = await buildOAuthAuthorizeUrl({
              provider,
              clientId: clientIds[provider] ?? "",
              next,
            });
          })();
        };

        return (
          <ProviderButton
            key={provider}
            provider={provider}
            label={label}
            onClick={onClick}
          />
        );
      })}
    </Flex>
  );
}
