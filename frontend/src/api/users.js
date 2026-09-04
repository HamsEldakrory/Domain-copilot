import client from "./client";

export const createAdjuster = async (data) => {
  const response = await client.post("/users/adjusters/", data);
  return response.data;
};
