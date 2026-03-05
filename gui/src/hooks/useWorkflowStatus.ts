import { useQuery } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/core';
import type { WorkflowPhase } from '../types';

// Convert Rust WorkflowPhase to frontend type (handles snake_case to camelCase)
function convertWorkflowPhase(phase: any): WorkflowPhase {
  return {
    id: phase.id,
    name: phase.name,
    description: phase.description,
    status: phase.status as WorkflowPhase['status'],
    progress: phase.progress,
    dependencies: phase.dependencies ?? undefined,
    startedAt: phase.started_at ? new Date(phase.started_at) : undefined,
    completedAt: phase.completed_at ? new Date(phase.completed_at) : undefined,
  };
}

async function fetchWorkflowStatus(): Promise<WorkflowPhase[]> {
  try {
    const phases = await invoke<any[]>('get_workflow_phases');
    return phases.map(convertWorkflowPhase);
  } catch (error) {
    console.error('Failed to fetch workflow status:', error);
    throw error;
  }
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
