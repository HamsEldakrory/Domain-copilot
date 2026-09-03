import client from "./client";

/**
 * Ask a RAG question against a specific claim's policy.
 * Backend endpoint: POST /claims/{claimId}/ask/
 */
export const askQuestion = async ({ claimId, query, policyVersionId }) => {
  const payload = { query };
  if (policyVersionId) payload.policy_version_id = policyVersionId;
  const response = await client.post(`/claims/${claimId}/ask/`, payload);
  return response.data;
};

/**
 * Submit a claim for async adjudication.
 * Backend endpoint: POST /adjudicate/
 */
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

/**
 * Submit a human approval/rejection decision on a job.
 * Backend endpoint: POST /jobs/{jobId}/approve/   ← CORRECT URL
 */
export const submitApprovalDecision = async ({
  jobId,
  decision,
  outcome,
  rationale,
  comment,
  final_payout,
  original_recommendation,
}) => {
  const payload = { decision };
  if (outcome)                 payload.outcome                 = outcome;
  if (rationale)               payload.rationale               = rationale;
  if (comment)                 payload.comment                 = comment;
  if (final_payout !== undefined && final_payout !== null) payload.final_payout = final_payout;
  if (original_recommendation) payload.original_recommendation = original_recommendation;
  const response = await client.post(`/jobs/${jobId}/approve/`, payload);
  return response.data;
};

/**
 * Get job status.
 * Backend endpoint: GET /jobs/{jobId}/
 */
export const getJobStatus = async (jobId) => {
  const response = await client.get(`/jobs/${jobId}/`);
  return response.data;
};

/**
 * Cancel a running job.
 * Backend endpoint: POST /jobs/{jobId}/cancel/
 */
export const cancelJob = async (jobId) => {
  const response = await client.post(`/jobs/${jobId}/cancel/`);
  return response.data;
};

/**
 * Fetch execution trace for a job.
 * Backend endpoint: GET /jobs/{jobId}/trace/
 */
export const getTrace = async (jobId) => {
  const response = await client.get(`/jobs/${jobId}/trace/`);
  return response.data;
};
