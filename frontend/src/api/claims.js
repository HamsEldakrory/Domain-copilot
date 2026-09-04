import client from "./client";

export const getClaims = async () => {
  const response = await client.get("/claims/");
  return response.data;
};

export const getClaim = async (claimId) => {
  const response = await client.get(`/claims/${claimId}/`);
  return response.data;
};

export const createClaim = async (data) => {
  const response = await client.post("/claims/create/", data);
  return response.data;
};

export const getClients = async () => {
  const response = await client.get("/clients/");
  return response.data;
};

export const getPolicyVersions = async () => {
  const response = await client.get("/policy-versions/");
  return response.data;
};
