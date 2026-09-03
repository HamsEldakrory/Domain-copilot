import client from "./client";
export const askQuestion = async (query) => {
  const response = await client.post("/ask/", {
    query,
  });
  return response.data;
};

export const adjudicateClaim = async ({
  claimId,
  claimedAmount,
  deductibleOverride,
}) => {
  const payload = {
    claim_id: claimId,
    claimed_amount: Number(claimedAmount),
  };
  if (
    deductibleOverride !== undefined &&
    deductibleOverride !== null &&
    deductibleOverride !== ""
  ) {
    payload.deductible_override = Number(deductibleOverride);
  }
  const response = await client.post("/adjudicate/", payload);
  return response.data;
};

export const submitApprovalDecision = async ({
  jobId,
  decision,
  outcome,
  rationale,
}) => {
  const response = await client.post(`/jobs/${jobId}/approval/`, {
    decision,
    ...(outcome && { outcome }),
    rationale,
  });
  return response.data;
};

export const getTrace = async (jobId) => {
  const response = await client.get(`/jobs/${jobId}/trace/`);
  return response.data;
};
