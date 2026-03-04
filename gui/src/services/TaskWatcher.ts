import { invoke } from '@tauri-apps/api/core';
import { useEffect, useState, useCallback } from 'react';

// ===== TYPES =====

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface TaskInfo {
  task_id: string;
  task_type: string;
  status: TaskStatus;
  progress_pct: number;
  started_at: string;
  completed_at?: string;
  last_heartbeat: string;
  estimated_completion?: string;
  files_processed?: number;
  files_total?: number;
  errors?: number;
  log_file?: string;
}

export interface TaskHeartbeat {
  task_id: string;
  timestamp: string;
  progress_pct: number;
  status: TaskStatus;
}

// ===== TAURI COMMANDS =====

/**
 * Get status of a specific task
 */
export async function getTaskStatus(taskId: string): Promise<TaskInfo> {
  return invoke<TaskInfo>('get_task_status', { taskId });
}

/**
 * List all active tasks
 */
export async function listActiveTasks(): Promise<TaskInfo[]> {
  return invoke<TaskInfo[]>('list_active_tasks');
}

/**
 * Cancel a running task
 */
export async function cancelTask(taskId: string): Promise<boolean> {
  return invoke<boolean>('cancel_task', { taskId });
}

/**
 * Get task logs (last N lines)
 */
export async function getTaskLogs(taskId: string, lines: number = 100): Promise<string> {
  return invoke<string>('get_task_logs', { taskId, lines });
}

// ===== REACT HOOKS =====

/**
 * Hook to watch a specific task's progress
 * Polls every 2 seconds and auto-unsubscribes on unmount
 */
export function useTaskWatcher(taskId: string | null) {
  const [task, setTask] = useState<TaskInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<{ timestamp: Date; progress: number }[]>([]);

  const fetchTask = useCallback(async () => {
    if (!taskId) {
      setTask(null);
      setIsLoading(false);
      return;
    }

    try {
      const taskInfo = await getTaskStatus(taskId);
      setTask(taskInfo);
      setError(null);

      // Track progress history for charts
      setHistory(prev => {
        const newEntry = { timestamp: new Date(), progress: taskInfo.progress_pct };
        // Keep last 100 data points
        const updated = [...prev, newEntry].slice(-100);
        return updated;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch task status');
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    if (!taskId) return;

    // Initial fetch
    fetchTask();

    // Poll every 2 seconds
    const intervalId = setInterval(fetchTask, 2000);

    // Cleanup on unmount
    return () => {
      clearInterval(intervalId);
    };
  }, [taskId, fetchTask]);

  // Calculate heartbeat health
  const getHeartbeatHealth = useCallback(() => {
    if (!task?.last_heartbeat) return 'unknown';

    const lastHeartbeat = new Date(task.last_heartbeat).getTime();
    const now = Date.now();
    const diffSeconds = (now - lastHeartbeat) / 1000;

    if (diffSeconds < 30) return 'healthy'; // green
    if (diffSeconds < 60) return 'warning'; // yellow
    return 'critical'; // red
  }, [task?.last_heartbeat]);

  return {
    task,
    isLoading,
    error,
    isRunning: task?.status === 'running' || task?.status === 'pending',
    isCompleted: task?.status === 'completed',
    isFailed: task?.status === 'failed' || task?.status === 'cancelled',
    heartbeatHealth: getHeartbeatHealth(),
    progressHistory: history,
    refresh: fetchTask,
  };
}

/**
 * Hook to subscribe to all active tasks
 */
export function useActiveTasks() {
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const activeTasks = await listActiveTasks();
      setTasks(activeTasks);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch active tasks');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();

    // Poll every 2 seconds
    const intervalId = setInterval(fetchTasks, 2000);

    return () => {
      clearInterval(intervalId);
    };
  }, [fetchTasks]);

  // Aggregate status
  const healthyCount = tasks.filter(t => t.status === 'running' && t.progress_pct >= 0).length;
  const warningCount = tasks.filter(t => {
    if (!t.last_heartbeat) return false;
    const diff = (Date.now() - new Date(t.last_heartbeat).getTime()) / 1000;
    return diff >= 30 && diff < 60;
  }).length;
  const failureCount = tasks.filter(t => t.status === 'failed' || t.status === 'cancelled').length;

  const overallHealth = failureCount > 0 ? 'critical' : warningCount > 0 ? 'warning' : 'healthy';

  return {
    tasks,
    isLoading,
    error,
    activeCount: tasks.length,
    healthyCount,
    warningCount,
    failureCount,
    overallHealth,
    refresh: fetchTasks,
  };
}

/**
 * Hook to handle task cancellation with confirmation
 */
export function useTaskCancellation() {
  const [isCancelling, setIsCancelling] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cancel = useCallback(async (taskId: string, onConfirm: () => void) => {
    // Require explicit confirmation
    if (!window.confirm(`Are you sure you want to cancel task ${taskId}? This action cannot be undone.`)) {
      return false;
    }

    setIsCancelling(taskId);
    setError(null);

    try {
      onConfirm(); // Execute any pre-cancel callbacks
      const result = await cancelTask(taskId);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel task');
      return false;
    } finally {
      setIsCancelling(null);
    }
  }, []);

  return {
    cancel,
    isCancelling,
    error,
  };
}
