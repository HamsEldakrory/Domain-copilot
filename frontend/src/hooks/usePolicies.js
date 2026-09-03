import { useMutation } from "@tanstack/react-query";
import { uploadPolicy } from "../api/policies";
export const useUploadPolicy = () => {
  return useMutation({
    mutationFn: uploadPolicy,
  });
};
