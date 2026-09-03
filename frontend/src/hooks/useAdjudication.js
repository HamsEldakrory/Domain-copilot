import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  askQuestion,
  adjudicateClaim,
  submitApprovalDecision,
  getTrace,
  getJobStatus,
  cancelJob,
} from "../api/adjudication";

export const useAsk = () => {
  return useMutation({
    mutationFn: askQuestion,
  });
};

export const useAdjudicate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adjudicateClaim,
    onSuccess: (_data, variables) => {
      // Refresh the claim to get updated job list
      queryClient.invalidateQueries({ queryKey: ["claim", variables.claimId] });
    },
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

    onSuccess: (_data, _vars, _ctx) => {
      queryClient.invalidateQueries({ queryKey: ["trace", jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobStatus", jobId] });
      queryClient.invalidateQueries({ queryKey: ["claims"] });
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

export const useJobStatus = (jobId, enabled = true) => {
  return useQuery({
    queryKey: ["jobStatus", jobId],
    queryFn: () => getJobStatus(jobId),
    enabled: Boolean(jobId) && enabled,
    refetchInterval: (query) => {
      const { status } = query.state.data ?? {};
      const TERMINAL = ["COMPLETED", "FAILED", "CANCELLED", "WAITING_APPROVAL"];
      if (status && TERMINAL.includes(status)) return false;
      return 3000;
    },
  });
};

export const useCancelJob = (jobId) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => cancelJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobStatus", jobId] });
    },
  });
};
