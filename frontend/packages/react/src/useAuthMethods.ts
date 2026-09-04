"use client";

import { useSyncExternalStore } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthClient } from "./provider.js";

const subscribe = () => () => {};
const browserOrigin = () => window.location.origin;
const serverOrigin = () => undefined;

/** Fetch public sign-in policy for the actual origin after hydration. */
export function useAuthMethods(origin?: string) {
  const client = useAuthClient();
  const currentOrigin = useSyncExternalStore(subscribe, browserOrigin, serverOrigin);
  const requestOrigin = origin ?? currentOrigin;
  return useQuery({
    queryKey: ["orcestr-auth", "methods", client.routes.methods, requestOrigin],
    queryFn: () => client.methods(requestOrigin),
    enabled: requestOrigin !== undefined,
    retry: false,
    staleTime: 30_000,
  });
}
