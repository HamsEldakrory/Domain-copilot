import { useMutation } from "@tanstack/react-query";
import { createAdjuster } from "../api/users";

export const useCreateAdjuster = () => {
  return useMutation({
    mutationFn: createAdjuster,
  });
};
