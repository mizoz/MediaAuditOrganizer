import { SubAgent, WorkflowPhase, DriveInfo, Asset } from '../types';

// Mock data for 12 sub-agents
export const mockAgents: SubAgent[] = [
  {
    id: 'SA-01',
    name: 'env-validator',
    status: 'success',
    progress: 100,
    logs: ['Environment validated', 'Python 3.12 detected', 'All dependencies installed'],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-02',
    name: 'config-auditor',
    status: 'success',
    progress: 100,
    logs: ['Configuration audited', 'No critical issues found'],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-03',
    name: 'db-init',
    status: 'success',
    progress: 100,
    logs: ['Database initialized', 'SQLite schema created', 'Indexes built'],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-04',
    name: 'drive-scanner',
    status: 'success',
    progress: 100,
    logs: ['Scanning drives...', 'Found 3 drives', 'Total capacity: 12TB'],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-05',
    name: 'audit-executor',
    status: 'processing',
    progress: 67,
    logs: ['Scanning source drives...', 'Analyzing file metadata...', 'Computing hashes...'],
    eta: '15 minutes',
    lastUpdated: new Date(),
  },
  {
    id: 'SA-06',
    name: 'dedupe-analyzer',
    status: 'idle',
    progress: 0,
    logs: [],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-07',
    name: 'rename-planner',
    status: 'idle',
    progress: 0,
    logs: [],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-08',
    name: 'transfer-executor',
    status: 'idle',
    progress: 0,
    logs: [],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-09',
    name: 'backup-verifier',
    status: 'idle',
    progress: 0,
    logs: [],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-10',
    name: 'report-generator',
    status: 'idle',
    progress: 0,
    logs: [],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-11',
    name: 'lightroom-reconciler',
    status: 'idle',
    progress: 0,
    logs: [],
    lastUpdated: new Date(),
  },
  {
    id: 'SA-12',
    name: 'cleanup-archiver',
    status: 'idle',
    progress: 0,
    logs: [],
    lastUpdated: new Date(),
  },
];

// Mock data for 11 workflow phases
export const mockWorkflowPhases: WorkflowPhase[] = [
  {
    id: 1,
    name: 'Environment Validation',
    description: 'Validate Python environment and dependencies',
    status: 'completed',
    progress: 100,
    startedAt: new Date(Date.now() - 3600000),
    completedAt: new Date(Date.now() - 3500000),
  },
  {
    id: 2,
    name: 'Configuration Audit',
    description: 'Audit configuration files and settings',
    status: 'completed',
    progress: 100,
    startedAt: new Date(Date.now() - 3500000),
    completedAt: new Date(Date.now() - 3400000),
  },
  {
    id: 3,
    name: 'Database Initialization',
    description: 'Initialize SQLite database and schema',
    status: 'completed',
    progress: 100,
    startedAt: new Date(Date.now() - 3400000),
    completedAt: new Date(Date.now() - 3300000),
  },
  {
    id: 4,
    name: 'Drive Scanning',
    description: 'Scan and enumerate all connected drives',
    status: 'completed',
    progress: 100,
    startedAt: new Date(Date.now() - 3300000),
    completedAt: new Date(Date.now() - 3200000),
  },
  {
    id: 5,
    name: 'Audit Execution',
    description: 'Execute comprehensive media audit',
    status: 'active',
    progress: 67,
    startedAt: new Date(Date.now() - 3200000),
  },
  {
    id: 6,
    name: 'Duplicate Analysis',
    description: 'Analyze and identify duplicate files',
    status: 'pending',
    progress: 0,
    dependencies: [5],
  },
  {
    id: 7,
    name: 'Rename Planning',
    description: 'Plan file renaming operations',
    status: 'pending',
    progress: 0,
    dependencies: [6],
  },
  {
    id: 8,
    name: 'Transfer Execution',
    description: 'Execute file transfer operations',
    status: 'pending',
    progress: 0,
    dependencies: [7],
  },
  {
    id: 9,
    name: 'Backup Verification',
    description: 'Verify backup integrity',
    status: 'pending',
    progress: 0,
    dependencies: [8],
  },
  {
    id: 10,
    name: 'Report Generation',
    description: 'Generate audit and transfer reports',
    status: 'pending',
    progress: 0,
    dependencies: [9],
  },
  {
    id: 11,
    name: 'Cleanup & Archive',
    description: 'Clean up temporary files and archive logs',
    status: 'pending',
    progress: 0,
    dependencies: [10],
  },
];

// Mock drive data
export const mockDrives: DriveInfo[] = [
  {
    id: 'drive-1',
    name: 'Samsung T7 Shield 2TB',
    mountPoint: '/media/az/SAMSUNG_T7_1',
    totalSpace: 2000000000000,
    usedSpace: 1450000000000,
    availableSpace: 550000000000,
    isSource: true,
  },
  {
    id: 'drive-2',
    name: 'WD Black 4TB',
    mountPoint: '/media/az/WD_BLACK_4TB',
    totalSpace: 4000000000000,
    usedSpace: 2100000000000,
    availableSpace: 1900000000000,
    isSource: true,
  },
  {
    id: 'drive-3',
    name: 'Seagate IronWolf 12TB',
    mountPoint: '/media/az/IRONWOLF_12TB',
    totalSpace: 12000000000000,
    usedSpace: 3200000000000,
    availableSpace: 8800000000000,
    isTarget: true,
  },
];

// Mock asset data
export const mockAssets: Asset[] = Array.from({ length: 100 }, (_, i) => ({
  id: `asset-${i + 1}`,
  filename: `IMG_${String(i + 1).padStart(4, '0')}.CR3`,
  path: `/media/az/SAMSUNG_T7_1/2024/01/15/IMG_${String(i + 1).padStart(4, '0')}.CR3`,
  type: i % 5 === 0 ? 'video' : 'photo',
  size: Math.floor(Math.random() * 50000000) + 10000000,
  createdAt: new Date(Date.now() - Math.random() * 86400000 * 365),
  modifiedAt: new Date(Date.now() - Math.random() * 86400000 * 365),
  cameraModel: ['Canon EOS R5', 'Sony A7R IV', 'Nikon Z9'][Math.floor(Math.random() * 3)],
  resolution: ['8192x5464', '7952x5304', '8256x5504'][Math.floor(Math.random() * 3)],
  duration: i % 5 === 0 ? Math.floor(Math.random() * 300) : undefined,
  hash: `sha256:${Math.random().toString(36).substring(2, 15)}`,
  isDuplicate: Math.random() < 0.1,
}));

// Helper functions
export function formatBytes(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let unitIndex = 0;
  let size = bytes;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(date: Date): string {
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
