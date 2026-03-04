import { useState } from 'react';
import { ChevronRight, Activity, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { cn, getStatusColor } from '@/lib/utils';
import { ScrollArea } from './ui/scroll-area';
import { useAgentStatus } from '@/hooks/useAgentStatus';
import type { SubAgent } from '@/types';

interface AgentMonitorProps {
  className?: string;
}

interface AgentItemProps {
  agent: SubAgent;
  isExpanded: boolean;
  onToggle: () => void;
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'idle':
      return <Clock className="h-4 w-4" />;
    case 'processing':
      return <Activity className="h-4 w-4 animate-pulse" />;
    case 'success':
      return <CheckCircle className="h-4 w-4" />;
    case 'error':
      return <XCircle className="h-4 w-4" />;
    default:
      return <Clock className="h-4 w-4" />;
  }
}

function AgentItem({ agent, isExpanded, onToggle }: AgentItemProps) {
  return (
    <div className="border-b border-slate-800 last:border-0">
      <button
        onClick={onToggle}
        className={cn(
          'flex w-full items-center justify-between p-3 hover:bg-slate-800/50 transition-colors',
          'text-left'
        )}
      >
        <div className="flex items-center gap-3">
          <ChevronRight
            className={cn(
              'h-4 w-4 text-slate-500 transition-transform',
              isExpanded && 'rotate-90'
            )}
          />
          <div className={cn('h-2 w-2 rounded-full', getStatusColor(agent.status))} />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-500">{agent.id}</span>
              <span className="text-sm font-medium text-slate-200">{agent.name}</span>
            </div>
            {agent.progress !== undefined && agent.progress > 0 && (
              <div className="mt-1 flex items-center gap-2">
                <div className="h-1 w-24 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={cn('h-full transition-all', getStatusColor(agent.status))}
                    style={{ width: `${agent.progress}%` }}
                  />
                </div>
                <span className="text-xs text-slate-500">{agent.progress}%</span>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {agent.status === 'processing' && agent.eta && (
            <span className="text-xs text-slate-500">ETA: {agent.eta}</span>
          )}
          {getStatusIcon(agent.status)}
        </div>
      </button>
      
      {isExpanded && agent.logs && agent.logs.length > 0 && (
        <div className="bg-slate-900/50 p-3 pl-11">
          <div className="space-y-1">
            {agent.logs.map((log, index) => (
              <div key={index} className="text-xs text-slate-400 font-mono">
                <span className="text-slate-600 mr-2">›</span>{log}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function AgentMonitor({ className }: AgentMonitorProps) {
  const { data: agents, isLoading, error } = useAgentStatus();
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  const toggleAgent = (agentId: string) => {
    setExpandedAgents(prev => {
      const next = new Set(prev);
      if (next.has(agentId)) {
        next.delete(agentId);
      } else {
        next.add(agentId);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center h-full', className)}>
        <Activity className="h-6 w-6 text-slate-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('flex items-center justify-center h-full', className)}>
        <AlertCircle className="h-6 w-6 text-status-error" />
        <span className="ml-2 text-sm text-status-error">Failed to load agents</span>
      </div>
    );
  }

  const statusCounts = {
    idle: agents?.filter(a => a.status === 'idle').length || 0,
    processing: agents?.filter(a => a.status === 'processing').length || 0,
    success: agents?.filter(a => a.status === 'success').length || 0,
    error: agents?.filter(a => a.status === 'error').length || 0,
  };

  return (
    <div className={cn('flex flex-col h-full bg-slate-900', className)}>
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <h2 className="text-lg font-semibold text-slate-100">Sub-Agents</h2>
        <div className="mt-3 flex gap-2">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-status-idle" />
            <span className="text-xs text-slate-400">{statusCounts.idle}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-status-processing" />
            <span className="text-xs text-slate-400">{statusCounts.processing}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-status-success" />
            <span className="text-xs text-slate-400">{statusCounts.success}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-status-error" />
            <span className="text-xs text-slate-400">{statusCounts.error}</span>
          </div>
        </div>
      </div>

      {/* Agent List */}
      <ScrollArea className="flex-1">
        <div className="divide-y divide-slate-800">
          {agents?.map(agent => (
            <AgentItem
              key={agent.id}
              agent={agent}
              isExpanded={expandedAgents.has(agent.id)}
              onToggle={() => toggleAgent(agent.id)}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
