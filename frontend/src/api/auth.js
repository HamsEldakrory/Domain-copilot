import client from "./client";

export const login = async (credentials) => {
  const response = await client.post("/auth/jwt/create/", credentials);

  return response.data;
};

export const getCurrentUser = async () => {
  const response = await client.get("/auth/me/");

  return response.data;
};
