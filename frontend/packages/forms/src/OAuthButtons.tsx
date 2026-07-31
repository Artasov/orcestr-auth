"use client";

import { buildOAuthAuthorizeUrl, type OAuthProvider } from "@orcestr/auth-core";
import { Button, Flex, type FlexProps } from "@orcestr/ui";
import type { ComponentType } from "react";

import { useAuthMessages } from "./i18n.js";

export type OAuthProviderButtonProps = {
  provider: OAuthProvider;
  label: string;
  onClick: () => void;
  disabled?: boolean;
};

export type OAuthProviderButtonComponent =
  ComponentType<OAuthProviderButtonProps>;

export type OAuthButtonsPlacement =
  "before-fields" | "after-submit" | "after-links";

export type OAuthButtonsOptions = {
  placement?: OAuthButtonsPlacement;
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

export type OAuthAuthorizeRequest = {
  provider: OAuthProvider;
  authorize: (callbackPayload?: Record<string, unknown>) => Promise<void>;
};

export type OAuthButtonsProps = OAuthButtonsOptions & {
  providers: OAuthProvider[];
  clientIds: Partial<Record<OAuthProvider, string>>;
  next: string;
  disabled?: boolean;
  onAuthorize?: (request: OAuthAuthorizeRequest) => void | Promise<void>;
};

function DefaultOAuthProviderButton({
  label,
  onClick,
  disabled,
}: OAuthProviderButtonProps) {
  return (
    <Button
      type="button"
      v="soft"
      size={3}
      disabled={disabled}
      onClick={onClick}
    >
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
  onAuthorize,
  disabled = false,
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
        const authorize = async (callbackPayload?: Record<string, unknown>) => {
          window.location.href = await buildOAuthAuthorizeUrl({
            provider,
            clientId: clientIds[provider] ?? "",
            next,
            callbackPayload,
          });
        };
        const onClick = () => {
          if (disabled) return;
          void (onAuthorize
            ? onAuthorize({ provider, authorize })
            : authorize());
        };

        return (
          <ProviderButton
            key={provider}
            provider={provider}
            label={label}
            onClick={onClick}
            disabled={disabled}
          />
        );
      })}
    </Flex>
  );
}
