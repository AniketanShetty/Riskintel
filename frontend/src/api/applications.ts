import { apiClient } from "./client";
import type { ApplicationDetailResponse, PaginatedApplicationList, PaginatedDeadLetterList } from "./contracts";

export const getApplications = async (skip = 0, limit = 50): Promise<PaginatedApplicationList> => {
  const { data } = await apiClient.get<PaginatedApplicationList>("/applications", {
    params: { skip, limit },
  });
  return data;
};

export const getApplication = async (id: string): Promise<ApplicationDetailResponse> => {
  const { data } = await apiClient.get<ApplicationDetailResponse>(`/applications/${id}`);
  return data;
};

export const getDeadLetters = async (skip = 0, limit = 50): Promise<PaginatedDeadLetterList> => {
  const { data } = await apiClient.get<PaginatedDeadLetterList>("/dlq", {
    params: { skip, limit },
  });
  return data;
};

export const createApplication = async (payload: any): Promise<{session_id: string, current_state: string}> => {
  const { data } = await apiClient.post("/apply", payload, {
    headers: {
      "X-Idempotency-Key": crypto.randomUUID()
    }
  });
  return data;
};
