import { useState, useMemo } from 'react';
import { Search, Filter, ChevronDown, ChevronUp, ChevronLeft, ChevronRight, AlertCircle, Loader2 } from 'lucide-react';
import { cn, formatBytes, formatDate } from '@/lib/utils';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from './ui/table';
import { Button } from './ui/button';
import type { Asset, AssetType, DatabaseFilter, DatabaseSort } from '@/types';
import { useDatabaseQuery } from '@/hooks/useDatabase';

interface DatabaseViewProps {
  className?: string;
}

const ASSET_TYPES: AssetType[] = ['photo', 'video', 'audio', 'document', 'other'];

export function DatabaseView({ className }: DatabaseViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<DatabaseFilter>({});
  const [sort, setSort] = useState<DatabaseSort>({ field: 'filename', direction: 'asc' });
  const [page, setPage] = useState(1);
  const pageSize = 100;

  const query = useMemo(() => ({
    filters: {
      ...filter,
      searchQuery: searchQuery || undefined,
    },
    sort,
    page,
    pageSize,
  }), [filter, sort, page, searchQuery]);

  const { data, isLoading, error } = useDatabaseQuery(query);

  // Camera models extracted from data for filter dropdown
  const cameraModels = useMemo(() => {
    if (!data?.assets) return [];
    const models = new Set(data.assets.map(a => a.cameraModel).filter(Boolean));
    return Array.from(models).sort();
  }, [data?.assets]);

  const handleSort = (field: keyof Asset) => {
    setSort(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc',
    }));
  };

  const SortIcon = ({ field }: { field: keyof Asset }) => {
    if (sort.field !== field) return null;
    return sort.direction === 'asc' ? (
      <ChevronUp className="h-4 w-4 ml-1" />
    ) : (
      <ChevronDown className="h-4 w-4 ml-1" />
    );
  };

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center h-full', className)}>
        <Loader2 className="h-8 w-8 text-slate-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('flex items-center justify-center h-full flex-col gap-4', className)}>
        <AlertCircle className="h-12 w-12 text-status-error" />
        <div className="text-center">
          <p className="text-lg font-semibold text-status-error">Failed to load database</p>
          <p className="text-sm text-slate-400">{String(error)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex flex-col h-full bg-slate-900', className)}>
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">Asset Database</h2>
            <p className="text-sm text-slate-400">
              {data?.total?.toLocaleString() || 0} assets found
            </p>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search assets..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-500" />
            <select
              value={filter.assetType || ''}
              onChange={e => setFilter(prev => ({
                ...prev,
                assetType: e.target.value as AssetType || undefined,
              }))}
              className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-200 focus:outline-none"
            >
              <option value="">All Types</option>
              {ASSET_TYPES.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <select
            value={filter.cameraModel || ''}
            onChange={e => setFilter(prev => ({
              ...prev,
              cameraModel: e.target.value || undefined,
            }))}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-200 focus:outline-none"
          >
            <option value="">All Cameras</option>
            {cameraModels.map(model => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-800">
              <TableHead className="w-[50px]">#</TableHead>
              <TableHead
                className="cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('filename')}
              >
                <div className="flex items-center">
                  Filename
                  <SortIcon field="filename" />
                </div>
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('type')}
              >
                <div className="flex items-center">
                  Type
                  <SortIcon field="type" />
                </div>
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('size')}
              >
                <div className="flex items-center">
                  Size
                  <SortIcon field="size" />
                </div>
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('cameraModel')}
              >
                <div className="flex items-center">
                  Camera
                  <SortIcon field="cameraModel" />
                </div>
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-slate-800"
                onClick={() => handleSort('createdAt')}
              >
                <div className="flex items-center">
                  Created
                  <SortIcon field="createdAt" />
                </div>
              </TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.assets.map((asset, index) => (
              <TableRow key={asset.id} className="border-slate-800">
                <TableCell className="text-slate-500">
                  {(page - 1) * pageSize + index + 1}
                </TableCell>
                <TableCell className="font-mono text-sm text-slate-300">
                  {asset.filename}
                </TableCell>
                <TableCell>
                  <span className={cn(
                    'px-2 py-1 rounded text-xs font-medium',
                    asset.type === 'photo' ? 'bg-blue-500/20 text-blue-400' :
                    asset.type === 'video' ? 'bg-purple-500/20 text-purple-400' :
                    'bg-slate-700 text-slate-400'
                  )}>
                    {asset.type}
                  </span>
                </TableCell>
                <TableCell className="text-slate-400">
                  {formatBytes(asset.size)}
                </TableCell>
                <TableCell className="text-slate-400">
                  {asset.cameraModel || '-'}
                </TableCell>
                <TableCell className="text-slate-400">
                  {formatDate(asset.createdAt)}
                </TableCell>
                <TableCell>
                  {asset.isDuplicate && (
                    <span className="text-xs text-red-400">⚠️</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {(!data?.assets || data.assets.length === 0) && (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-12 text-slate-400">
                  No assets found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="p-4 border-t border-slate-800 flex items-center justify-between">
        <p className="text-sm text-slate-400">
          Page {page} of {data?.totalPages || 1}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="border-slate-700 text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(p => Math.min(data?.totalPages || 1, p + 1))}
            disabled={page === data?.totalPages}
            className="border-slate-700 text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
