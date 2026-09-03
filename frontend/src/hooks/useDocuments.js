import { useQuery } from "@tanstack/react-query";
import { getDocumentStatus, getDocumentsList } from "../api/documents";

export const useDocumentStatus = (documentId, enabled = false) => {
  return useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocumentStatus(documentId),
    enabled: Boolean(documentId) && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "ingested" || status === "failed") {
        return false;
      }
      return 2000;
    },
  });
};

export const useDocuments = () => {
  return useQuery({
    queryKey: ["documents"],
    queryFn: getDocumentsList,
    refetchInterval: 3000,
  });
};
