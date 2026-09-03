import client from "./client";
export const getDocumentStatus = async (documentId) => {
  const response = await client.get(`/documents/${documentId}/`);
  return response.data;
};

export const getDocumentsList = async () => {
  const response = await client.get("/documents/");
  return response.data;
};
