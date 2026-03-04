import { useState } from 'react';
import { useActiveTasks } from '@/services/TaskWatcher';
import { Activity, CheckCircle, AlertTriangle, XCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ActiveTasksBadgeProps {
  onTaskClick?: (taskId: string) => void;
}

export function ActiveTasksBadge({ onTaskClick }: ActiveTasksBadgeProps) {
  const { tasks, activeCount, healthyCount, warningCount, failureCount, overallHealth, isLoading } = useActiveTasks();
  const [isExpanded, setIsExpanded] = useState(false);

  if (activeCount === 0 && !isLoading) {
    return null;
  }

  const getBadgeColor = () => {
    if (overallHealth === 'critical') return 'bg-status-error text-white';
    if (overallHealth === 'warning') return 'bg-status-warning text-slate-900';
    return 'bg-status-success text-white';
  };

  const getIcon = () => {
    if (isLoading) return <Activity className="h-3 w-3 animate-spin" />;
    if (overallHealth === 'critical') return <XCircle className="h-3 w-3" />;
    if (overallHealth === 'warning') return <AlertTriangle className="h-3 w-3" />;
    return <CheckCircle className="h-3 w-3" />;
  };

  const getStatusColor = (task: typeof tasks[0]) => {
    if (task.status === 'completed') return 'text-status-success';
    if (task.status === 'failed' || task.status === 'cancelled') return 'text-status-error';
    if (!task.last_heartbeat) return 'text-slate-400';
    
    const diff = (Date.now() - new Date(task.last_heartbeat).getTime()) / 1000;
    if (diff > 60) return 'text-status-error';
    if (diff > 30) return 'text-status-warning';
    return 'text-status-success';
  };

  const formatTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatProgress = (progress: number) => {
    if (progress >= 100) return '100%';
    return `${progress}%`;
  };

  return (
    <div className="relative">
      {/* Badge Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
          getBadgeColor(),
          'hover:opacity-90'
        )}
      >
        {getIcon()}
        <span>{activeCount} active</span>
      </button>

      {/* Expanded Panel */}
      {isExpanded && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsExpanded(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute bottom-full left-0 mb-2 w-80 bg-slate-900 border border-slate-800 rounded-lg shadow-xl z-50 overflow-hidden">
            {/* Header */}
            <div className="p-3 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-200">Active Tasks</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(false)}
                className="h-6 w-6 p-0 text-slate-400 hover:text-slate-200"
              >
                ×
              </Button>
            </div>

            {/* Summary */}
            <div className="px-3 py-2 bg-slate-950/50 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1 text-status-success">
                  <CheckCircle className="h-3 w-3" />
                  {healthyCount}
                </span>
                <span className="flex items-center gap-1 text-status-warning">
                  <AlertTriangle className="h-3 w-3" />
                  {warningCount}
                </span>
                <span className="flex items-center gap-1 text-status-error">
                  <XCircle className="h-3 w-3" />
                  {failureCount}
                </span>
              </div>
              <span className="text-slate-500">Total: {activeCount}</span>
            </div>

            {/* Task List */}
            <ScrollArea className="h-64">
              <div className="p-2 space-y-1">
                {tasks.map(task => (
                  <button
                    key={task.task_id}
                    onClick={() => {
                      onTaskClick?.(task.task_id);
                      setIsExpanded(false);
                    }}
                    className="w-full p-2 rounded hover:bg-slate-800 transition-colors text-left"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-slate-200 truncate max-w-[120px]">
                        {task.task_type}
                      </span>
                      <span className={cn('text-xs font-medium', getStatusColor(task))}>
                        {formatProgress(task.progress_pct)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <Clock className="h-3 w-3" />
                      <span className="truncate max-w-[150px]">{task.task_id}</span>
                      <span>•</span>
                      <span>{formatTime(task.started_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            </ScrollArea>

            {/* Footer */}
            <div className="p-2 border-t border-slate-800 text-center">
              <button
                onClick={() => setIsExpanded(false)}
                className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
