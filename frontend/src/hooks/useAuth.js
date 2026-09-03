import { useMutation, useQuery } from "@tanstack/react-query";
import { useDispatch } from "react-redux";
import { login, getCurrentUser } from "../api/auth";
import { setTokens, setUser } from "../store/authSlice";
export const useLogin = () => {
  const dispatch = useDispatch();

  return useMutation({
    mutationFn: login,

    onSuccess: (data) => {
      dispatch(setTokens(data));
    },
  });
};

export const useCurrentUser = (enabled = true) => {
  const dispatch = useDispatch();

  return useQuery({
    queryKey: ["me"],

    queryFn: getCurrentUser,

    enabled,

    onSuccess: (data) => {
      dispatch(setUser(data));
    },
  });
};
