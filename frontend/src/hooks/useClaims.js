import { useQuery } from "@tanstack/react-query";
import { getClaims, getClaim } from "../api/claims";
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
