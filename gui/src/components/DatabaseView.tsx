import { useState, useMemo } from 'react';
import { Search, Filter, ChevronDown, ChevronUp, ChevronLeft, ChevronRight } from 'lucide-react';
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
import { mockAssets } from '@/mock/data';
import type { Asset, AssetType, DatabaseFilter, DatabaseSort } from '@/types';

interface DatabaseViewProps {
  className?: string;
}

const ASSET_TYPES: AssetType[] = ['photo', 'video', 'audio', 'document', 'other'];

export function DatabaseView({ className }: DatabaseViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<DatabaseFilter>({});
  const [sort, setSort] = useState<DatabaseSort>({ field: 'createdAt', direction: 'desc' });
  const [page, setPage] = useState(1);
  const pageSize = 100;

  // Filter and sort assets
  const filteredAssets = useMemo(() => {
    let result = [...mockAssets];

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        asset =>
          asset.filename.toLowerCase().includes(query) ||
          asset.path.toLowerCase().includes(query) ||
          asset.cameraModel?.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (filter.assetType) {
      result = result.filter(asset => asset.type === filter.assetType);
    }
    if (filter.cameraModel) {
      result = result.filter(
        asset => asset.cameraModel === filter.cameraModel
      );
    }
    if (filter.dateFrom) {
      result = result.filter(asset => asset.createdAt >= filter.dateFrom!);
    }
    if (filter.dateTo) {
      result = result.filter(asset => asset.createdAt <= filter.dateTo!);
    }
    if (filter.sizeMin) {
      result = result.filter(asset => asset.size >= filter.sizeMin!);
    }
    if (filter.sizeMax) {
      result = result.filter(asset => asset.size <= filter.sizeMax!);
    }

    // Apply sorting
    result.sort((a, b) => {
      const aVal = a[sort.field];
      const bVal = b[sort.field];
      
      if (aVal === undefined || bVal === undefined) return 0;
      
      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sort.direction === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [searchQuery, filter, sort]);

  // Pagination
  const totalPages = Math.ceil(filteredAssets.length / pageSize);
  const paginatedAssets = filteredAssets.slice(
    (page - 1) * pageSize,
    page * pageSize
  );

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

  return (
    <div className={cn('flex flex-col h-full bg-slate-900', className)}>
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">Asset Database</h2>
            <p className="text-sm text-slate-400">
              {filteredAssets.length.toLocaleString()} assets found
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
            <option value="Canon EOS R5">Canon EOS R5</option>
            <option value="Sony A7R IV">Sony A7R IV</option>
            <option value="Nikon Z9">Nikon Z9</option>
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
            {paginatedAssets.map((asset, index) => (
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
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="p-4 border-t border-slate-800 flex items-center justify-between">
        <p className="text-sm text-slate-400">
          Page {page} of {totalPages}
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
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="border-slate-700 text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
