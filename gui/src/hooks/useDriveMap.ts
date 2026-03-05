import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/core';
import type { DriveInfo } from '../types';

// Convert Rust DriveInfo to frontend type (handles snake_case to camelCase)
function convertDriveInfo(drive: any): DriveInfo {
  return {
    id: drive.id,
    name: drive.name,
    mountPoint: drive.mount_point,
    totalSpace: drive.total_space,
    usedSpace: drive.used_space,
    availableSpace: drive.available_space,
    isTarget: drive.is_target ?? false,
    isSource: drive.is_source ?? false,
  };
}

async function fetchDrives(): Promise<DriveInfo[]> {
  try {
    const drives = await invoke<any[]>('scan_drives');
    return drives.map(convertDriveInfo);
  } catch (error) {
    console.error('Failed to fetch drives:', error);
    throw error;
  }
}

export function useDriveMap() {
  return useQuery({
    queryKey: ['drives'],
    queryFn: fetchDrives,
    refetchInterval: 10000, // Poll every 10 seconds
    staleTime: 5000,
  });
}

export function useRunAudit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ source, target, dryRun }: { source: string; target: string; dryRun: boolean }) => {
      const result = await invoke<any>('run_audit', { source, target, dryRun });
      return result;
    },
    onSuccess: () => {
      // Refresh drives and workflow status after audit starts
      queryClient.invalidateQueries({ queryKey: ['drives'] });
      queryClient.invalidateQueries({ queryKey: ['workflowStatus'] });
      queryClient.invalidateQueries({ queryKey: ['agentStatus'] });
    },
  });
}

export function useRunDeduplication() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ source, action }: { source: string; action: string }) => {
      const result = await invoke<any>('run_deduplication', { source, action });
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drives'] });
      queryClient.invalidateQueries({ queryKey: ['workflowStatus'] });
      queryClient.invalidateQueries({ queryKey: ['agentStatus'] });
    },
  });
}
