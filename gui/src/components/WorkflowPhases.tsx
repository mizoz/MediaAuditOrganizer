
import { CheckCircle, Clock, AlertCircle, ArrowRight, Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Progress } from './ui/progress';
import { useWorkflowStatus } from '@/hooks/useWorkflowStatus';
import type { WorkflowPhase } from '@/types';

interface WorkflowPhasesProps {
  className?: string;
}

interface PhaseNodeProps {
  phase: WorkflowPhase;
  isLast: boolean;
}

function PhaseNode({ phase, isLast }: PhaseNodeProps) {
  const getStatusIcon = () => {
    switch (phase.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-status-success" />;
      case 'active':
        return <Play className="h-5 w-5 text-status-processing animate-pulse" />;
      case 'blocked':
        return <AlertCircle className="h-5 w-5 text-status-error" />;
      default:
        return <Clock className="h-5 w-5 text-status-idle" />;
    }
  };

  const getStatusText = () => {
    switch (phase.status) {
      case 'completed':
        return 'Completed';
      case 'active':
        return 'In Progress';
      case 'blocked':
        return 'Blocked';
      default:
        return 'Pending';
    }
  };

  return (
    <div className="flex items-start gap-4">
      {/* Phase Node */}
      <div className="flex flex-col items-center">
        <div className={cn(
          'flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all',
          phase.status === 'completed' ? 'border-status-success bg-status-success/20' :
          phase.status === 'active' ? 'border-status-processing bg-status-processing/20 animate-pulse' :
          phase.status === 'blocked' ? 'border-status-error bg-status-error/20' :
          'border-slate-700 bg-slate-800'
        )}>
          {getStatusIcon()}
        </div>
        
        {!isLast && (
          <div className={cn(
            'w-0.5 h-16 mt-2',
            phase.status === 'completed' ? 'bg-status-success' :
            'bg-slate-700'
          )} />
        )}
      </div>

      {/* Phase Info */}
      <div className="flex-1 pb-8">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Phase {phase.id}: {phase.name}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">{phase.description}</p>
          </div>
          <div className="text-right">
            <p className={cn(
              'text-xs font-medium',
              phase.status === 'completed' ? 'text-status-success' :
              phase.status === 'active' ? 'text-status-processing' :
              phase.status === 'blocked' ? 'text-status-error' :
              'text-status-idle'
            )}>
              {getStatusText()}
            </p>
            {phase.progress > 0 && (
              <p className="text-xs text-slate-500 mt-0.5">{phase.progress}%</p>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {phase.progress > 0 && (
          <Progress
            value={phase.progress}
            className={cn(
              'h-2',
              phase.status === 'completed' ? '[&>div]:bg-status-success' :
              phase.status === 'active' ? '[&>div]:bg-status-processing' :
              '[&>div]:bg-slate-600'
            )}
          />
        )}

        {/* Timing Info */}
        {(phase.startedAt || phase.completedAt) && (
          <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
            {phase.startedAt && (
              <span>Started: {phase.startedAt.toLocaleTimeString()}</span>
            )}
            {phase.completedAt && (
              <span>Completed: {phase.completedAt.toLocaleTimeString()}</span>
            )}
          </div>
        )}

        {/* Dependencies */}
        {phase.dependencies && phase.dependencies.length > 0 && (
          <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
            <ArrowRight className="h-3 w-3 rotate-90" />
            <span>Depends on: {phase.dependencies.map(d => `Phase ${d}`).join(', ')}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function WorkflowPhases({ className }: WorkflowPhasesProps) {
  const { data: phases, isLoading, error } = useWorkflowStatus();

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center h-full', className)}>
        <Clock className="h-6 w-6 text-slate-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('flex items-center justify-center h-full', className)}>
        <AlertCircle className="h-6 w-6 text-status-error" />
        <span className="ml-2 text-sm text-status-error">Failed to load workflow</span>
      </div>
    );
  }

  const currentPhase = phases?.find(p => p.status === 'active');
  const completedCount = phases?.filter(p => p.status === 'completed').length || 0;
  const totalCount = phases?.length || 0;
  const overallProgress = (completedCount / totalCount) * 100;

  return (
    <div className={cn('p-6 bg-slate-900', className)}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-slate-100">Workflow Progress</h2>
          <span className="text-sm text-slate-400">
            {completedCount} of {totalCount} phases completed
          </span>
        </div>
        <Progress value={overallProgress} className="h-2" />
      </div>

      {/* Current Phase Highlight */}
      {currentPhase && (
        <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Play className="h-4 w-4 text-blue-500 animate-pulse" />
            <span className="text-sm font-medium text-blue-400">Currently Running</span>
          </div>
          <p className="text-lg font-semibold text-slate-200">
            Phase {currentPhase.id}: {currentPhase.name}
          </p>
          <p className="text-sm text-slate-400 mt-1">{currentPhase.description}</p>
        </div>
      )}

      {/* Phase Timeline */}
      <div className="space-y-0">
        {phases?.map((phase, index) => (
          <PhaseNode
            key={phase.id}
            phase={phase}
            isLast={index === (phases?.length || 0) - 1}
          />
        ))}
      </div>
    </div>
  );
}
