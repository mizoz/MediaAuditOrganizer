import { useQuery } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/core';
import type { SubAgent } from '../types';

// Convert Rust SubAgent to frontend type (handles snake_case to camelCase)
function convertSubAgent(agent: any): SubAgent {
  return {
    id: agent.id,
    name: agent.name,
    status: agent.status as SubAgent['status'],
    progress: agent.progress ?? undefined,
    logs: agent.logs ?? undefined,
    eta: agent.eta ?? undefined,
    lastUpdated: new Date(agent.last_updated),
  };
}

async function fetchAgentStatus(): Promise<SubAgent[]> {
  try {
    const agents = await invoke<any[]>('get_agent_status');
    return agents.map(convertSubAgent);
  } catch (error) {
    console.error('Failed to fetch agent status:', error);
    throw error;
  }
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
