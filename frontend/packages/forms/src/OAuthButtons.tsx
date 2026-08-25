"use client";

import { buildOAuthAuthorizeUrl, type OAuthProvider } from "@orcestr/auth-core";
import { Button, Flex, type FlexProps } from "@orcestr/ui";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  type ComponentType,
} from "react";

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

export type OAuthAuthorizeHandler = (
  provider: OAuthProvider,
  clientId: string,
  next: string,
  callbackPayload?: Record<string, unknown>,
) => void | Promise<void>;

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
  authorizeHandler?: OAuthAuthorizeHandler;
  autoAuthorizeProvider?: OAuthProvider;
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
  authorizeHandler,
  autoAuthorizeProvider,
  onAuthorize,
  disabled = false,
}: OAuthButtonsProps) {
  const copy = useAuthMessages().oauth;
  const autoAuthorizationStarted = useRef(false);
  const visible = useMemo(
    () =>
      providers.filter((provider) => Boolean(clientIds[provider]?.trim())),
    [clientIds, providers],
  );

  const authorizeProvider = useCallback(
    async (
      provider: OAuthProvider,
      callbackPayload?: Record<string, unknown>,
    ) => {
      const clientId = clientIds[provider] ?? "";
      if (authorizeHandler) {
        await authorizeHandler(provider, clientId, next, callbackPayload);
        return;
      }
      window.location.href = await buildOAuthAuthorizeUrl({
        provider,
        clientId,
        next,
        callbackPayload,
      });
    },
    [authorizeHandler, clientIds, next],
  );

  const requestAuthorization = useCallback(
    async (provider: OAuthProvider) => {
      const authorize = (callbackPayload?: Record<string, unknown>) =>
        authorizeProvider(provider, callbackPayload);
      if (onAuthorize) {
        await onAuthorize({ provider, authorize });
        return;
      }
      await authorize();
    },
    [authorizeProvider, onAuthorize],
  );

  useEffect(() => {
    if (
      autoAuthorizationStarted.current ||
      disabled ||
      !autoAuthorizeProvider ||
      !visible.includes(autoAuthorizeProvider)
    ) {
      return;
    }
    autoAuthorizationStarted.current = true;
    void requestAuthorization(autoAuthorizeProvider);
  }, [
    autoAuthorizeProvider,
    disabled,
    requestAuthorization,
    visible,
  ]);

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
          if (disabled) return;
          void requestAuthorization(provider);
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
