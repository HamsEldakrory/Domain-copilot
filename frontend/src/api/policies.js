import client from "./client";

export const uploadPolicy = async (formData) => {
  const response = await client.post("/policies/upload/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};
