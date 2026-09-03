import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  askQuestion,
  adjudicateClaim,
  submitApprovalDecision,
  getTrace,
} from "../api/adjudication";
export const useAsk = () => {
  return useMutation({
    mutationFn: askQuestion,
  });
};
export const useAdjudicate = () => {
  return useMutation({
    mutationFn: adjudicateClaim,
  });
};
export const useApprovalDecision = (jobId) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) =>
      submitApprovalDecision({
        jobId,
        ...payload,
      }),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["trace", jobId],
      });
    },
  });
};

export const useTrace = (jobId, enabled = false) => {
  return useQuery({
    queryKey: ["trace", jobId],
    queryFn: () => getTrace(jobId),
    enabled: Boolean(jobId) && enabled,
  });
};
