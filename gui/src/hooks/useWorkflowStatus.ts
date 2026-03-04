import { useQuery } from '@tanstack/react-query';
import { mockWorkflowPhases } from '../mock/data';
import type { WorkflowPhase } from '../types';

// In production, this would call a Tauri command to get real workflow status
async function fetchWorkflowStatus(): Promise<WorkflowPhase[]> {
  // TODO: Replace with actual Tauri command
  // return invoke<WorkflowPhase[]>('get_workflow_status');
  return mockWorkflowPhases;
}

export function useWorkflowStatus() {
  return useQuery({
    queryKey: ['workflowStatus'],
    queryFn: fetchWorkflowStatus,
    refetchInterval: 5000, // Poll every 5 seconds
    staleTime: 2000,
  });
}

export function useWorkflowPhase(phaseId: number) {
  const { data: phases, isLoading, error } = useWorkflowStatus();
  
  const phase = phases?.find(p => p.id === phaseId);
  
  return {
    phase,
    isLoading,
    error,
  };
}

export function useCurrentPhase() {
  const { data: phases, isLoading, error } = useWorkflowStatus();
  
  const currentPhase = phases?.find(p => p.status === 'active') || 
                       phases?.find(p => p.status === 'pending');
  
  return {
    currentPhase,
    isLoading,
    error,
  };
}
