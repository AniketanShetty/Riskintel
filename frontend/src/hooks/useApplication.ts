import { useQuery } from "@tanstack/react-query";
import { getApplication } from "@/api/applications";

export const useApplication = (id: string) => {
  return useQuery({
    queryKey: ["applications", id],
    queryFn: () => getApplication(id),
    staleTime: 0, // Fresh fetch required for deterministic FSM visualization
    retry: 1,
  });
};
