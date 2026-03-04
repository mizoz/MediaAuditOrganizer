
import { AlertTriangle, Check, X, Edit, Shield } from 'lucide-react';
import { cn, formatBytes } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import { Button } from './ui/button';
import type { ConfirmationGate, ConfirmationItem } from '@/types';

interface ConfirmationGateProps {
  gate: ConfirmationGate;
  onApprove: () => void;
  onReject: () => void;
  onModify: () => void;
  onClose: () => void;
}

function RiskBadge({ level }: { level: 'low' | 'medium' | 'high' }) {
  const colors = {
    low: 'bg-green-500/20 text-green-400 border-green-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    high: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border',
      colors[level]
    )}>
      <Shield className="h-3 w-3" />
      {level.toUpperCase()} RISK
    </span>
  );
}

function ConfirmationItemCard({ item }: { item: ConfirmationItem }) {
  return (
    <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="text-sm font-medium text-slate-200">{item.title}</h4>
          <p className="text-xs text-slate-400 mt-1">{item.description}</p>
        </div>
        <RiskBadge level={item.riskLevel} />
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div>
          <p className="text-xs text-slate-500">File Count</p>
          <p className="text-sm font-medium text-slate-200">{item.fileCount.toLocaleString()} files</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Total Size</p>
          <p className="text-sm font-medium text-slate-200">{formatBytes(item.totalSize)}</p>
        </div>
      </div>
      
      {item.details.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-700">
          <p className="text-xs text-slate-500 mb-2">Details:</p>
          <ul className="space-y-1">
            {item.details.slice(0, 3).map((detail, index) => (
              <li key={index} className="text-xs text-slate-400 font-mono">
                <span className="text-slate-600 mr-2">›</span>{detail}
              </li>
            ))}
            {item.details.length > 3 && (
              <li className="text-xs text-slate-500 italic">
                +{item.details.length - 3} more...
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

export function ConfirmationGate({
  gate,
  onApprove,
  onReject,
  onModify,
  onClose,
}: ConfirmationGateProps) {
  const totalFiles = gate.items.reduce((sum, item) => sum + item.fileCount, 0);
  const totalSize = gate.items.reduce((sum, item) => sum + item.totalSize, 0);
  const maxRisk = gate.items.some(i => i.riskLevel === 'high') ? 'high'
    : gate.items.some(i => i.riskLevel === 'medium') ? 'medium'
    : 'low';

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-700">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className={cn(
              'p-2 rounded-lg',
              maxRisk === 'high' ? 'bg-red-500/20' :
              maxRisk === 'medium' ? 'bg-yellow-500/20' :
              'bg-green-500/20'
            )}>
              <AlertTriangle className={cn(
                'h-6 w-6',
                maxRisk === 'high' ? 'text-red-500' :
                maxRisk === 'medium' ? 'text-yellow-500' :
                'text-green-500'
              )} />
            </div>
            <div>
              <DialogTitle className="text-slate-100">
                Confirmation Required
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                Phase {gate.phase} requires your approval before proceeding
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="my-4">
          {/* Summary */}
          <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-xs text-slate-500">Total Files</p>
                  <p className="text-lg font-semibold text-slate-200">
                    {totalFiles.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Total Size</p>
                  <p className="text-lg font-semibold text-slate-200">
                    {formatBytes(totalSize)}
                  </p>
                </div>
              </div>
              <RiskBadge level={maxRisk} />
            </div>
          </div>

          {/* Items */}
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {gate.items.map(item => (
              <ConfirmationItemCard key={item.id} item={item} />
            ))}
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
          >
            Cancel
          </Button>
          <Button
            variant="outline"
            onClick={onModify}
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
          >
            <Edit className="h-4 w-4 mr-2" />
            Modify
          </Button>
          <Button
            variant="destructive"
            onClick={onReject}
            className="bg-red-600 hover:bg-red-700"
          >
            <X className="h-4 w-4 mr-2" />
            Reject
          </Button>
          <Button
            onClick={onApprove}
            className="bg-green-600 hover:bg-green-700"
          >
            <Check className="h-4 w-4 mr-2" />
            Approve
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Example usage with mock data
export function ConfirmationGateDemo() {
  const mockGate: ConfirmationGate = {
    id: 'gate-1',
    phase: 6,
    items: [
      {
        id: 'item-1',
        title: 'Duplicate Files Found',
        description: 'Identified duplicate files that can be safely removed',
        fileCount: 847,
        totalSize: 42949672960, // 40GB
        riskLevel: 'low',
        details: [
          'All duplicates verified by hash comparison',
          'Original files preserved in target location',
          'No unique metadata in duplicate copies',
        ],
      },
      {
        id: 'item-2',
        title: 'Files to Rename',
        description: 'Files that will be renamed according to naming convention',
        fileCount: 1523,
        totalSize: 107374182400, // 100GB
        riskLevel: 'medium',
        details: [
          'Naming pattern: YYYY-MM-DD_Camera_Sequence',
          'Original filenames logged for recovery',
          '3 conflicts detected (manual review needed)',
        ],
      },
    ],
    requiresApproval: true,
  };

  return (
    <ConfirmationGate
      gate={mockGate}
      onApprove={() => console.log('Approved')}
      onReject={() => console.log('Rejected')}
      onModify={() => console.log('Modify')}
      onClose={() => console.log('Close')}
    />
  );
}
