// Agent status types
export type AgentStatus = 'idle' | 'processing' | 'success' | 'error';

export interface SubAgent {
  id: string;
  name: string;
  status: AgentStatus;
  progress?: number;
  logs?: string[];
  eta?: string;
  lastUpdated: Date;
}

// Workflow phase types
export type PhaseStatus = 'pending' | 'active' | 'completed' | 'blocked';

export interface WorkflowPhase {
  id: number;
  name: string;
  description: string;
  status: PhaseStatus;
  progress: number;
  dependencies?: number[];
  startedAt?: Date;
  completedAt?: Date;
}

// Drive types
export interface DriveInfo {
  id: string;
  name: string;
  mountPoint: string;
  totalSpace: number; // in bytes
  usedSpace: number;
  availableSpace: number;
  isTarget?: boolean;
  isSource?: boolean;
}

// Asset types
export type AssetType = 'photo' | 'video' | 'audio' | 'document' | 'other';

export interface Asset {
  id: string;
  filename: string;
  path: string;
  type: AssetType;
  size: number; // in bytes
  createdAt: Date;
  modifiedAt: Date;
  cameraModel?: string;
  resolution?: string;
  duration?: number; // for videos in seconds
  hash?: string;
  isDuplicate?: boolean;
}

// Confirmation gate types
export interface ConfirmationItem {
  id: string;
  title: string;
  description: string;
  fileCount: number;
  totalSize: number; // in bytes
  riskLevel: 'low' | 'medium' | 'high';
  details: string[];
}

export interface ConfirmationGate {
  id: string;
  phase: number;
  items: ConfirmationItem[];
  requiresApproval: boolean;
  approved?: boolean;
  rejected?: boolean;
  modified?: boolean;
}

// Database query types
export interface DatabaseFilter {
  cameraModel?: string;
  dateFrom?: Date;
  dateTo?: Date;
  sizeMin?: number;
  sizeMax?: number;
  assetType?: AssetType;
  searchQuery?: string;
}

export interface DatabaseSort {
  field: keyof Asset;
  direction: 'asc' | 'desc';
}

export interface DatabaseQuery {
  filters: DatabaseFilter;
  sort: DatabaseSort;
  page: number;
  pageSize: number;
}

export interface DatabaseResult {
  assets: Asset[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Tauri command types
export interface TauriCommand {
  command: string;
  args?: string[];
}

export interface TauriResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
