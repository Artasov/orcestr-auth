"use client";

import type { AuthClient, AuthUser } from "@orcestr/auth-core";
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
} from "@tanstack/react-query";
import { createContext, useContext, type ReactNode } from "react";

const AUTH_USER_QUERY_KEY = ["orcestr-auth", "current-user"] as const;

type AuthContextValue<TUser extends AuthUser> = {
  client: AuthClient<TUser>;
};

const AuthContext = createContext<AuthContextValue<AuthUser> | null>(null);

export function AuthProvider<TUser extends AuthUser>({
  client,
  children,
}: {
  client: AuthClient<TUser>;
  children: ReactNode;
}) {
  return (
    <AuthContext.Provider value={{ client } as AuthContextValue<AuthUser>}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthClient<
  TUser extends AuthUser = AuthUser,
>(): AuthClient<TUser> {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider is missing.");
  return value.client as AuthClient<TUser>;
}

export function useCurrentUser<TUser extends AuthUser = AuthUser>() {
  const client = useAuthClient<TUser>();
  return useQuery({
    queryKey: AUTH_USER_QUERY_KEY,
    queryFn: () => client.me(),
    retry: false,
    staleTime: 30_000,
  });
}

export function useLogin<
  TUser extends AuthUser = AuthUser,
>(): UseMutationResult<
  { user: TUser },
  Error,
  { username: string; password: string }
> {
  const client = useAuthClient<TUser>();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ username, password }) => client.login(username, password),
    onSuccess: ({ user }) => {
      queryClient.setQueryData(AUTH_USER_QUERY_KEY, user);
    },
  });
}

export function useRegister<TUser extends AuthUser = AuthUser>() {
  const client = useAuthClient<TUser>();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => client.register(payload),
    onSuccess: ({ user }) =>
      queryClient.setQueryData(AUTH_USER_QUERY_KEY, user),
  });
}

export function useLogout() {
  const client = useAuthClient();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => client.logout(),
    onSuccess: () =>
      queryClient.removeQueries({ queryKey: AUTH_USER_QUERY_KEY }),
  });
}

export function usePasswordResetRequest() {
  const client = useAuthClient();
  return useMutation({
    mutationFn: (email: string) => client.requestPasswordReset(email),
  });
}

export function usePasswordResetConfirm() {
  const client = useAuthClient();
  return useMutation({
    mutationFn: (payload: { email: string; code: string; password: string }) =>
      client.confirmPasswordReset(payload),
  });
}

export function useEmailVerification() {
  const client = useAuthClient();
  const queryClient = useQueryClient();
  const send = useMutation({ mutationFn: () => client.sendVerificationCode() });
  const confirm = useMutation({
    mutationFn: (code: string) => client.confirmEmail(code),
    onSuccess: (user) => queryClient.setQueryData(AUTH_USER_QUERY_KEY, user),
  });
  return { send, confirm };
}
