import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getClaims, getClaim, createClaim, getClients, getPolicyVersions } from "../api/claims.js";

export const useClaims = () => {
  return useQuery({
    queryKey: ["claims"],
    queryFn: getClaims,
  });
};

export const useClaim = (claimId) => {
  return useQuery({
    queryKey: ["claim", claimId],
    queryFn: () => getClaim(claimId),
    enabled: Boolean(claimId),
  });
};

export const useCreateClaim = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createClaim,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["claims"] });
    },
  });
};

export const useClients = () =>
  useQuery({ queryKey: ["clients"], queryFn: getClients });

export const usePolicyVersions = () =>
  useQuery({ queryKey: ["policyVersions"], queryFn: getPolicyVersions });

