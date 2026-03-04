import { useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { useTaskWatcher, useTaskCancellation } from '@/services/TaskWatcher';
import { Clock, CheckCircle, XCircle, AlertCircle, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ClaimTicketProps {
  taskId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onMonitor?: () => void;
  autoDismiss?: boolean;
}

export function ClaimTicket({ taskId, isOpen, onClose, onMonitor, autoDismiss = true }: ClaimTicketProps) {
  const { task, isLoading, isCompleted, isFailed, heartbeatHealth } = useTaskWatcher(taskId);
  const { cancel, isCancelling } = useTaskCancellation();

  // Auto-dismiss on completion
  useEffect(() => {
    if (autoDismiss && isCompleted && isOpen) {
      const timer = setTimeout(() => {
        onClose();
      }, 3000); // Wait 3 seconds after completion before auto-dismiss
      return () => clearTimeout(timer);
    }
  }, [isCompleted, isOpen, autoDismiss, onClose]);

  if (!taskId || !isOpen) return null;

  const getStatusIcon = () => {
    if (isLoading) return <Activity className="h-5 w-5 text-blue-400 animate-spin" />;
    if (isCompleted) return <CheckCircle className="h-5 w-5 text-status-success" />;
    if (isFailed) return <XCircle className="h-5 w-5 text-status-error" />;
    if (heartbeatHealth === 'critical') return <AlertCircle className="h-5 w-5 text-status-error" />;
    if (heartbeatHealth === 'warning') return <AlertCircle className="h-5 w-5 text-status-warning" />;
    return <Activity className="h-5 w-5 text-blue-400" />;
  };

  const getStatusText = () => {
    if (isLoading) return 'Loading...';
    if (isCompleted) return 'Completed';
    if (isFailed) return task?.status === 'cancelled' ? 'Cancelled' : 'Failed';
    if (heartbeatHealth === 'critical') return 'No Heartbeat';
    if (heartbeatHealth === 'warning') return 'Slow Response';
    return 'Running';
  };

  const getStatusColor = () => {
    if (isLoading) return 'text-blue-400';
    if (isCompleted) return 'text-status-success';
    if (isFailed) return 'text-status-error';
    if (heartbeatHealth === 'critical') return 'text-status-error';
    if (heartbeatHealth === 'warning') return 'text-status-warning';
    return 'text-blue-400';
  };

  const getHeartbeatColor = () => {
    if (heartbeatHealth === 'healthy') return 'bg-status-success';
    if (heartbeatHealth === 'warning') return 'bg-status-warning';
    if (heartbeatHealth === 'critical') return 'bg-status-error';
    return 'bg-slate-500';
  };

  const formatTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatDuration = (start?: string, end?: string) => {
    if (!start) return 'N/A';
    const startDate = new Date(start);
    const endDate = end ? new Date(end) : new Date();
    const diffMs = endDate.getTime() - startDate.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    
    if (diffSecs < 60) return `${diffSecs}s`;
    if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ${diffSecs % 60}s`;
    return `${Math.floor(diffSecs / 3600)}h ${Math.floor((diffSecs % 3600) / 60)}m`;
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
        <DialogHeader>
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <DialogTitle className="text-lg font-semibold">
              {isCompleted ? 'Task Completed' : isFailed ? 'Task Failed' : 'Background Job Running'}
            </DialogTitle>
          </div>
          <DialogDescription className="text-slate-400">
            Task ID: <code className="bg-slate-800 px-2 py-0.5 rounded text-xs">{taskId}</code>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Task Type */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Task Type</span>
            <span className="text-slate-200 font-medium">{task?.task_type || 'Unknown'}</span>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Progress</span>
              <span className={cn('font-medium', getStatusColor())}>
                {task?.progress_pct ?? 0}%
              </span>
            </div>
            <Progress value={task?.progress_pct ?? 0} className="h-2" />
          </div>

          {/* Heartbeat Indicator */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Heartbeat</span>
            <div className="flex items-center gap-2">
              <div className={cn('h-2 w-2 rounded-full', getHeartbeatColor())} />
              <span className="text-slate-200">{getStatusText()}</span>
            </div>
          </div>

          {/* Timing Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-slate-400">Started</span>
              <p className="text-slate-200 font-medium">{formatTime(task?.started_at)}</p>
            </div>
            <div>
              <span className="text-slate-400">Duration</span>
              <p className="text-slate-200 font-medium">
                {formatDuration(task?.started_at, task?.completed_at)}
              </p>
            </div>
          </div>

          {/* Files Processed */}
          {(task?.files_processed !== undefined || task?.files_total !== undefined) && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Files Processed</span>
              <span className="text-slate-200 font-medium">
                {task?.files_processed ?? 0} / {task?.files_total ?? '?'}
              </span>
            </div>
          )}

          {/* Errors */}
          {task?.errors !== undefined && task.errors > 0 && (
            <div className="flex items-center gap-2 text-sm text-status-warning">
              <AlertCircle className="h-4 w-4" />
              <span>{task.errors} error(s) encountered</span>
            </div>
          )}

          {/* Estimated Completion */}
          {task?.estimated_completion && !isCompleted && !isFailed && (
            <div className="flex items-center gap-2 text-sm text-blue-400">
              <Clock className="h-4 w-4" />
              <span>ETA: {task.estimated_completion}</span>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          {!isCompleted && !isFailed && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => cancel(taskId, () => {})}
              disabled={isCancelling === taskId}
              className="bg-red-600 hover:bg-red-500"
            >
              {isCancelling === taskId ? 'Cancelling...' : 'Cancel'}
            </Button>
          )}
          
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              onMonitor?.();
              onClose();
            }}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200"
          >
            Monitor
          </Button>
          
          {(isCompleted || isFailed) && (
            <Button
              variant="default"
              size="sm"
              onClick={onClose}
              className="bg-blue-600 hover:bg-blue-500"
            >
              {isCompleted ? 'Close' : 'Dismiss'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
