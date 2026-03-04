import React, { useState, useEffect } from 'react';
import { LayoutDashboard, HardDrive, Database, Activity, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AgentMonitor } from './AgentMonitor';
import { DriveMap } from './DriveMap';
import { DatabaseView } from './DatabaseView';
import { WorkflowPhases } from './WorkflowPhases';
import { ConfirmationGateDemo } from './ConfirmationGate';
import { ActiveTasksBadge } from './ActiveTasksBadge';
import { ClaimTicket } from './ClaimTicket';
import { TaskDetail } from './TaskDetail';
import { useActiveTasks } from '@/services/TaskWatcher';

type Tab = 'dashboard' | 'drives' | 'database' | 'workflow' | 'settings';

interface DashboardProps {
  className?: string;
}

export function Dashboard({ className }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [showConfirmationGate, setShowConfirmationGate] = useState(false);
  const [showClaimTicket, setShowClaimTicket] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [showTaskDetail, setShowTaskDetail] = useState(false);
  const [detailTaskId, setDetailTaskId] = useState<string | null>(null);
  const { tasks: activeTasks } = useActiveTasks();

  // Auto-show claim ticket when new task starts
  useEffect(() => {
    if (activeTasks.length > 0 && !showClaimTicket && !currentTaskId) {
      const latestTask = activeTasks[0];
      setCurrentTaskId(latestTask.task_id);
      setShowClaimTicket(true);
    }
  }, [activeTasks.length, showClaimTicket, currentTaskId, activeTasks]);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="h-4 w-4" /> },
    { id: 'drives', label: 'Drive Map', icon: <HardDrive className="h-4 w-4" /> },
    { id: 'database', label: 'Database', icon: <Database className="h-4 w-4" /> },
    { id: 'workflow', label: 'Workflow', icon: <Activity className="h-4 w-4" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="h-4 w-4" /> },
  ];

  return (
    <div className={cn('flex h-screen bg-obsidian-900 text-slate-100', className)}>
      {/* Sidebar */}
      <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-slate-800">
          <h1 className="text-lg font-bold text-slate-100">MediaAudit</h1>
          <p className="text-xs text-slate-500">Organizer v1.0.0</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-3 w-full px-3 py-2.5 rounded-md text-sm transition-colors',
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Active Tasks Badge */}
        <div className="px-2 pb-2">
          <ActiveTasksBadge onTaskClick={(taskId) => {
            setDetailTaskId(taskId);
            setShowTaskDetail(true);
          }} />
        </div>

        {/* Agent Monitor in Sidebar */}
        <div className="h-1/2 border-t border-slate-800">
          <AgentMonitor />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Top Bar */}
        <div className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-900/50">
          <h2 className="text-lg font-semibold text-slate-200">
            {tabs.find(t => t.id === activeTab)?.label}
          </h2>
          <div className="flex items-center gap-4">
            {/* Demo button for confirmation gate */}
            <button
              onClick={() => setShowConfirmationGate(true)}
              className="px-3 py-1.5 text-xs bg-yellow-600 hover:bg-yellow-500 rounded transition-colors"
            >
              Demo: Confirmation Gate
            </button>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-status-success" />
              <span className="text-xs text-slate-400">System Online</span>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="h-[calc(100vh-3.5rem)] overflow-auto">
          {activeTab === 'dashboard' && (
            <div className="grid grid-cols-2 gap-6 p-6">
              <div className="col-span-2">
                <WorkflowPhases />
              </div>
              <div>
                <DriveMap />
              </div>
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                <h3 className="text-lg font-semibold text-slate-100 mb-4">Quick Stats</h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-slate-400">Total Assets</p>
                    <p className="text-2xl font-bold text-slate-200">15,847</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Duplicates Found</p>
                    <p className="text-2xl font-bold text-yellow-400">847</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Storage Used</p>
                    <p className="text-2xl font-bold text-blue-400">6.8 TB</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Last Audit</p>
                    <p className="text-sm font-medium text-slate-300">2 hours ago</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'drives' && <DriveMap className="h-full" />}
          
          {activeTab === 'database' && <DatabaseView className="h-full" />}
          
          {activeTab === 'workflow' && <WorkflowPhases className="h-full" />}
          
          {activeTab === 'settings' && (
            <div className="p-6">
              <h2 className="text-lg font-semibold text-slate-100 mb-4">Settings</h2>
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                <p className="text-slate-400">Settings panel coming soon...</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Gate Demo Modal */}
      {showConfirmationGate && (
        <ConfirmationGateDemo />
      )}

      {/* Claim Ticket Modal */}
      <ClaimTicket
        taskId={currentTaskId}
        isOpen={showClaimTicket}
        onClose={() => {
          setShowClaimTicket(false);
          setCurrentTaskId(null);
        }}
        onMonitor={() => {
          if (currentTaskId) {
            setDetailTaskId(currentTaskId);
            setShowTaskDetail(true);
          }
        }}
      />

      {/* Task Detail View */}
      {showTaskDetail && detailTaskId && (
        <TaskDetail
          taskId={detailTaskId}
          onBack={() => {
            setShowTaskDetail(false);
            setDetailTaskId(null);
          }}
        />
      )}
    </div>
  );
}
