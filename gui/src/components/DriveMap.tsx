import { useState } from 'react';
import { HardDrive, Upload, Download, Target } from 'lucide-react';
import { cn, formatBytes } from '@/lib/utils';
import { mockDrives } from '@/mock/data';
import type { DriveInfo } from '@/types';

interface DriveMapProps {
  className?: string;
  onTargetChange?: (driveId: string) => void;
}

interface DriveCardProps {
  drive: DriveInfo;
  isTarget: boolean;
  onSelectTarget: (driveId: string) => void;
}

function DriveCard({ drive, isTarget, onSelectTarget }: DriveCardProps) {
  const usagePercent = (drive.usedSpace / drive.totalSpace) * 100;
  
  return (
    <div
      className={cn(
        'relative p-4 rounded-lg border transition-all cursor-pointer',
        isTarget
          ? 'border-blue-500 bg-blue-500/10'
          : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
      )}
      onClick={() => onSelectTarget(drive.id)}
    >
      {isTarget && (
        <div className="absolute top-2 right-2">
          <Target className="h-4 w-4 text-blue-500" />
        </div>
      )}
      
      <div className="flex items-start gap-3">
        <div className={cn(
          'p-2 rounded-lg',
          isTarget ? 'bg-blue-500/20' : 'bg-slate-700'
        )}>
          <HardDrive className={cn(
            'h-6 w-6',
            isTarget ? 'text-blue-500' : 'text-slate-400'
          )} />
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-slate-200 truncate">
            {drive.name}
          </h3>
          <p className="text-xs text-slate-500 font-mono mt-1 truncate">
            {drive.mountPoint}
          </p>
          
          {/* Usage bar */}
          <div className="mt-3">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>{formatBytes(drive.usedSpace)} used</span>
              <span>{formatBytes(drive.availableSpace)} free</span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={cn(
                  'h-full transition-all',
                  isTarget ? 'bg-blue-500' : 'bg-slate-500'
                )}
                style={{ width: `${usagePercent}%` }}
              />
            </div>
            <div className="mt-1 text-xs text-slate-500">
              {formatBytes(drive.totalSpace)} total • {usagePercent.toFixed(0)}% used
            </div>
          </div>
        </div>
      </div>
      
      {/* Action buttons */}
      <div className="mt-4 flex gap-2">
        {drive.isSource && (
          <button className="flex items-center gap-1 px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 rounded transition-colors">
            <Upload className="h-3 w-3" />
            Source
          </button>
        )}
        {drive.isTarget && (
          <button className="flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 rounded transition-colors">
            <Download className="h-3 w-3" />
            Target
          </button>
        )}
      </div>
    </div>
  );
}

export function DriveMap({ className, onTargetChange }: DriveMapProps) {
  const [drives, setDrives] = useState<DriveInfo[]>(mockDrives);
  const [targetDriveId, setTargetDriveId] = useState<string>(
    mockDrives.find(d => d.isTarget)?.id || mockDrives[0]?.id
  );

  const handleSelectTarget = (driveId: string) => {
    setTargetDriveId(driveId);
    onTargetChange?.(driveId);
    
    // Update drive flags
    setDrives(prev => prev.map(d => ({
      ...d,
      isTarget: d.id === driveId,
    })));
  };

  return (
    <div className={cn('p-6 bg-slate-900', className)}>
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-100">Drive Map</h2>
        <p className="text-sm text-slate-400 mt-1">
          Select target drive and drag source drives here
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {drives.map(drive => (
          <DriveCard
            key={drive.id}
            drive={drive}
            isTarget={drive.id === targetDriveId}
            onSelectTarget={handleSelectTarget}
          />
        ))}
        
        {/* Drop zone placeholder */}
        <div className="p-4 rounded-lg border-2 border-dashed border-slate-700 bg-slate-800/30 flex items-center justify-center min-h-[200px]">
          <div className="text-center text-slate-500">
            <HardDrive className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Drag drives here</p>
            <p className="text-xs mt-1">or click to browse</p>
          </div>
        </div>
      </div>
      
      {/* Summary */}
      <div className="mt-6 p-4 bg-slate-800/50 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-400">Total Capacity</p>
            <p className="text-lg font-semibold text-slate-200">
              {formatBytes(drives.reduce((sum, d) => sum + d.totalSpace, 0))}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-400">Total Used</p>
            <p className="text-lg font-semibold text-slate-200">
              {formatBytes(drives.reduce((sum, d) => sum + d.usedSpace, 0))}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-400">Total Available</p>
            <p className="text-lg font-semibold text-slate-200">
              {formatBytes(drives.reduce((sum, d) => sum + d.availableSpace, 0))}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
