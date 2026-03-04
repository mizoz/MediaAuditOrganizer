import { useQuery } from '@tanstack/react-query';
import { mockAgents } from '../mock/data';
import type { SubAgent } from '../types';

// In production, this would call a Tauri command to get real agent status
async function fetchAgentStatus(): Promise<SubAgent[]> {
  // TODO: Replace with actual Tauri command
  // return invoke<SubAgent[]>('get_agent_status');
  return mockAgents;
}

export function useAgentStatus() {
  return useQuery({
    queryKey: ['agentStatus'],
    queryFn: fetchAgentStatus,
    refetchInterval: 5000, // Poll every 5 seconds
    staleTime: 2000,
  });
}

export function useAgent(agentId: string) {
  const { data: agents, isLoading, error } = useAgentStatus();
  
  const agent = agents?.find(a => a.id === agentId);
  
  return {
    agent,
    isLoading,
    error,
  };
}
