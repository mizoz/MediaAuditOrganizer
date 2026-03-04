import { useEffect, useRef, useState } from 'react';
import { useTaskWatcher, useTaskCancellation, getTaskLogs } from '@/services/TaskWatcher';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  ArrowLeft, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Activity, 
  Clock, 
  FileText,
  HardDrive,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface TaskDetailProps {
  taskId: string;
  onBack: () => void;
}

export function TaskDetail({ taskId, onBack }: TaskDetailProps) {
  const { task, isLoading, isCompleted, isFailed, heartbeatHealth, progressHistory, refresh } = useTaskWatcher(taskId);
  const { cancel, isCancelling } = useTaskCancellation();
  const [logs, setLogs] = useState<string>('');
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Fetch logs
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const taskLogs = await getTaskLogs(taskId, 100);
        setLogs(taskLogs);
      } catch (err) {
        setLogs('Failed to load logs');
      }
    };

    fetchLogs();
    
    // Poll logs every 3 seconds
    const intervalId = setInterval(fetchLogs, 3000);
    return () => clearInterval(intervalId);
  }, [taskId]);

  // Auto-scroll logs
  useEffect(() => {
    if (isAutoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isAutoScroll]);

  const getStatusIcon = () => {
    if (isLoading) return <Activity className="h-6 w-6 text-blue-400 animate-spin" />;
    if (isCompleted) return <CheckCircle className="h-6 w-6 text-status-success" />;
    if (isFailed) return <XCircle className="h-6 w-6 text-status-error" />;
    if (heartbeatHealth === 'critical') return <AlertCircle className="h-6 w-6 text-status-error" />;
    if (heartbeatHealth === 'warning') return <AlertCircle className="h-6 w-6 text-status-warning" />;
    return <Activity className="h-6 w-6 text-blue-400" />;
  };

  const getStatusText = () => {
    if (isLoading) return 'Loading...';
    if (isCompleted) return 'Completed';
    if (isFailed) return task?.status === 'cancelled' ? 'Cancelled' : 'Failed';
    if (heartbeatHealth === 'critical') return 'No Heartbeat (>60s)';
    if (heartbeatHealth === 'warning') return 'Slow Response (30-60s)';
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
    if (heartbeatHealth === 'healthy') return 'bg-status-success shadow-[0_0_10px_rgba(34,197,94,0.5)]';
    if (heartbeatHealth === 'warning') return 'bg-status-warning shadow-[0_0_10px_rgba(234,179,8,0.5)]';
    if (heartbeatHealth === 'critical') return 'bg-status-error shadow-[0_0_10px_rgba(239,68,68,0.5)]';
    return 'bg-slate-500';
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
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

  // Simple progress chart (SVG)
  const renderProgressChart = () => {
    if (progressHistory.length < 2) return null;

    const width = 400;
    const height = 100;
    const padding = 10;
    
    const maxPoints = 50;
    const recentHistory = progressHistory.slice(-maxPoints);
    
    const points = recentHistory.map((point, index) => {
      const x = padding + (index / (maxPoints - 1)) * (width - 2 * padding);
      const y = height - padding - (point.progress / 100) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(' ');

    return (
      <div className="w-full overflow-hidden">
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="bg-slate-950 rounded">
          {/* Grid lines */}
          <line x1={padding} y1={height/2} x2={width-padding} y2={height/2} stroke="#334155" strokeWidth="1" strokeDasharray="4" />
          
          {/* Progress line */}
          <polyline
            points={points}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* End point */}
          {recentHistory.length > 0 && (
            <circle
              cx={padding + ((recentHistory.length - 1) / (maxPoints - 1)) * (width - 2 * padding)}
              cy={height - padding - (recentHistory[recentHistory.length - 1].progress / 100) * (height - 2 * padding)}
              r="4"
              fill="#3b82f6"
            />
          )}
        </svg>
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>{recentHistory.length > 0 ? new Date(recentHistory[0].timestamp).toLocaleTimeString() : ''}</span>
          <span>{recentHistory.length > 0 ? new Date(recentHistory[recentHistory.length - 1].timestamp).toLocaleTimeString() : ''}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="h-screen bg-obsidian-900 text-slate-100 flex flex-col">
      {/* Header */}
      <div className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-900/50">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <h1 className="text-lg font-semibold">Task Details</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refresh}
            className="border-slate-700 text-slate-400 hover:bg-slate-800"
          >
            Refresh
          </Button>
          {!isCompleted && !isFailed && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => cancel(taskId, () => {})}
              disabled={isCancelling === taskId}
              className="bg-red-600 hover:bg-red-500"
            >
              {isCancelling === taskId ? 'Cancelling...' : 'Cancel Task'}
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Task Info Card */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-100 mb-1">
                  {task?.task_type || 'Unknown Task'}
                </h2>
                <p className="text-sm text-slate-400 font-mono">{taskId}</p>
              </div>
              <div className={cn('px-3 py-1 rounded-full text-sm font-medium', getStatusColor(), 'bg-slate-800')}>
                {getStatusText()}
              </div>
            </div>

            {/* Progress */}
            <div className="space-y-2 mb-6">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Overall Progress</span>
                <span className={cn('text-sm font-bold', getStatusColor())}>
                  {task?.progress_pct ?? 0}%
                </span>
              </div>
              <Progress value={task?.progress_pct ?? 0} className="h-3" />
            </div>

            {/* Progress Chart */}
            {renderProgressChart()}

            {/* Metadata Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800">
              <div>
                <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                  <Clock className="h-4 w-4" />
                  <span>Started</span>
                </div>
                <p className="text-slate-200 font-medium">{formatDateTime(task?.started_at)}</p>
              </div>
              <div>
                <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                  <Clock className="h-4 w-4" />
                  <span>Completed</span>
                </div>
                <p className="text-slate-200 font-medium">{formatDateTime(task?.completed_at)}</p>
              </div>
              <div>
                <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                  <Activity className="h-4 w-4" />
                  <span>Duration</span>
                </div>
                <p className="text-slate-200 font-medium">
                  {formatDuration(task?.started_at, task?.completed_at)}
                </p>
              </div>
              <div>
                <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                  <div className={cn('h-2 w-2 rounded-full', getHeartbeatColor())} />
                  <span>Heartbeat</span>
                </div>
                <p className="text-slate-200 font-medium">{getStatusText()}</p>
              </div>
            </div>

            {/* Additional Stats */}
            <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-800">
              {(task?.files_processed !== undefined || task?.files_total !== undefined) && (
                <div className="flex items-center gap-2">
                  <HardDrive className="h-4 w-4 text-slate-400" />
                  <div>
                    <p className="text-xs text-slate-400">Files Processed</p>
                    <p className="text-sm font-medium text-slate-200">
                      {task?.files_processed ?? 0} / {task?.files_total ?? '?'}
                    </p>
                  </div>
                </div>
              )}
              {task?.errors !== undefined && (
                <div className="flex items-center gap-2">
                  <AlertTriangle className={cn('h-4 w-4', task.errors > 0 ? 'text-status-warning' : 'text-slate-400')} />
                  <div>
                    <p className="text-xs text-slate-400">Errors</p>
                    <p className={cn('text-sm font-medium', task.errors > 0 ? 'text-status-warning' : 'text-slate-200')}>
                      {task.errors}
                    </p>
                  </div>
                </div>
              )}
              {task?.estimated_completion && !isCompleted && (
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-400" />
                  <div>
                    <p className="text-xs text-slate-400">Estimated Completion</p>
                    <p className="text-sm font-medium text-blue-400">{task.estimated_completion}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Logs Panel */}
          <div className="bg-slate-900 rounded-lg border border-slate-800 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-200">Task Logs</h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsAutoScroll(!isAutoScroll)}
                className={cn(
                  'text-xs',
                  isAutoScroll ? 'text-blue-400 bg-blue-900/20' : 'text-slate-400'
                )}
              >
                Auto-scroll: {isAutoScroll ? 'ON' : 'OFF'}
              </Button>
            </div>
            <ScrollArea className="h-64 w-full">
              <div className="p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap">
                {logs || 'No logs available'}
                <div ref={logsEndRef} />
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    </div>
  );
}
