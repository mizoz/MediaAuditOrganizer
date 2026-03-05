import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/core';
import type { DatabaseQuery, DatabaseResult, Asset } from '../types';

// Convert database row to Asset type
function convertAsset(row: any): Asset {
  return {
    id: row.id || row.path,
    filename: row.filename || row.path.split('/').pop() || '',
    path: row.path,
    type: mapFileType(row.file_type || row.asset_type || 'other'),
    size: parseInt(row.size_bytes) || 0,
    createdAt: new Date(row.created || row.created_at || Date.now()),
    modifiedAt: new Date(row.modified || row.modified_at || Date.now()),
    cameraModel: row.camera_model || undefined,
    resolution: row.resolution || undefined,
    duration: row.duration ? parseInt(row.duration) : undefined,
    hash: row.md5 || row.hash || undefined,
    isDuplicate: row.is_duplicate || false,
  };
}

function mapFileType(fileType: string): Asset['type'] {
  const typeMap: Record<string, Asset['type']> = {
    'IMAGE': 'photo',
    'VIDEO': 'video',
    'AUDIO': 'audio',
    'DOCUMENT': 'document',
  };
  return typeMap[fileType?.toUpperCase()] || 'other';
}

async function executeQuery(query: DatabaseQuery): Promise<DatabaseResult> {
  try {
    // Build SQL query from filters
    let sql = 'SELECT * FROM assets WHERE 1=1';
    const params: any[] = [];

    if (query.filters?.cameraModel) {
      sql += ' AND camera_model = ?';
      params.push(query.filters.cameraModel);
    }

    if (query.filters?.dateFrom) {
      sql += ' AND created_at >= ?';
      params.push(query.filters.dateFrom.toISOString());
    }

    if (query.filters?.dateTo) {
      sql += ' AND created_at <= ?';
      params.push(query.filters.dateTo.toISOString());
    }

    if (query.filters?.sizeMin) {
      sql += ' AND size_bytes >= ?';
      params.push(query.filters.sizeMin);
    }

    if (query.filters?.sizeMax) {
      sql += ' AND size_bytes <= ?';
      params.push(query.filters.sizeMax);
    }

    if (query.filters?.searchQuery) {
      sql += ' AND filename LIKE ?';
      params.push(`%${query.filters.searchQuery}%`);
    }

    // Add sorting
    const sortField = query.sort?.field || 'filename';
    const sortDir = query.sort?.direction || 'asc';
    sql += ` ORDER BY ${sortField} ${sortDir.toUpperCase()}`;

    // Add pagination
    const offset = (query.page - 1) * query.pageSize;
    sql += ` LIMIT ${query.pageSize} OFFSET ${offset}`;

    // Execute query
    const resultJson = await invoke<string>('query_database', { sql });
    const rows = JSON.parse(resultJson);

    // Get total count
    const countSql = 'SELECT COUNT(*) as count FROM assets';
    const countJson = await invoke<string>('query_database', { sql: countSql });
    const countResult = JSON.parse(countJson);
    const total = parseInt(countResult[0]?.count || '0');

    return {
      assets: rows.map(convertAsset),
      total,
      page: query.page,
      pageSize: query.pageSize,
      totalPages: Math.ceil(total / query.pageSize),
    };
  } catch (error) {
    console.error('Database query failed:', error);
    throw error;
  }
}

export function useDatabaseQuery(query: DatabaseQuery) {
  return useQuery({
    queryKey: ['database', query],
    queryFn: () => executeQuery(query),
    staleTime: 30000, // 30 seconds
  });
}

export function useExecuteSql() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sql: string) => {
      const result = await invoke<string>('query_database', { sql });
      return JSON.parse(result);
    },
    onSuccess: () => {
      // Invalidate database queries after mutation
      queryClient.invalidateQueries({ queryKey: ['database'] });
    },
  });
}
