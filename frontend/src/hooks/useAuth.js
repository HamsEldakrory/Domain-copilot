import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { login, getCurrentUser } from "../api/auth";
import { setTokens, setUser, logout as logoutAction } from "../store/authSlice";

export const useLogin = () => {
  const dispatch = useDispatch();

  return useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      dispatch(setTokens(data));
    },
  });
};

/**
 * Fetches the current authenticated user and stores them in Redux.
 * React Query v5 removed onSuccess; we use useEffect on the data instead.
 */
export const useCurrentUser = (enabled = true) => {
  const dispatch = useDispatch();

  const query = useQuery({
    queryKey: ["me"],
    queryFn: getCurrentUser,
    enabled,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  useEffect(() => {
    if (query.data) {
      dispatch(setUser(query.data));
    }
  }, [query.data, dispatch]);

  return query;
};

/**
 * Logout hook: clears tokens, React Query cache, and redirects to /login.
 */
export const useLogout = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return () => {
    dispatch(logoutAction());
    queryClient.clear();
    navigate("/login", { replace: true });
  };
};
