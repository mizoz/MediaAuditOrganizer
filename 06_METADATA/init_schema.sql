-- MediaAuditOrganizer Database Schema
-- Generated: 2026-03-03
-- SQLite with WAL mode for performance

-- Enable WAL mode for better concurrent performance
PRAGMA journal_mode = WAL;

-- Set cache size to 64MB for better performance
PRAGMA cache_size = -64000;

-- ============================================
-- TABLE 1: assets — Core file metadata
-- ============================================
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    extension TEXT,
    file_size_bytes INTEGER,
    md5_hash TEXT,
    sha256_hash TEXT,
    mime_type TEXT,
    created_date TEXT,
    modified_date TEXT,
    ingested_date TEXT DEFAULT (datetime('now')),
    asset_type TEXT CHECK(asset_type IN ('photo', 'video', 'audio', 'document', 'other')),
    folder_path TEXT,
    year INTEGER,
    month INTEGER,
    is_duplicate INTEGER DEFAULT 0,
    lightroom_catalog_id INTEGER,
    backup_verified INTEGER DEFAULT 0,
    last_verified_date TEXT,
    UNIQUE(file_path, sha256_hash)
);

-- ============================================
-- TABLE 2: exif_data — Photo EXIF metadata
-- ============================================
CREATE TABLE IF NOT EXISTS exif_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    date_taken TEXT,
    camera_make TEXT,
    camera_model TEXT,
    lens_model TEXT,
    iso INTEGER,
    shutter_speed TEXT,
    aperture TEXT,
    focal_length TEXT,
    gps_latitude REAL,
    gps_longitude REAL,
    gps_altitude REAL,
    orientation INTEGER,
    color_space TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 3: video_metadata — Video metadata
-- ============================================
CREATE TABLE IF NOT EXISTS video_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    duration_seconds REAL,
    codec_name TEXT,
    width INTEGER,
    height INTEGER,
    frame_rate REAL,
    bit_rate INTEGER,
    audio_codec TEXT,
    creation_time TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 4: duplicates — Duplicate detection results
-- ============================================
CREATE TABLE IF NOT EXISTS duplicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id_1 INTEGER NOT NULL,
    asset_id_2 INTEGER NOT NULL,
    duplicate_type TEXT CHECK(duplicate_type IN ('exact', 'similar', 'near_duplicate')),
    similarity_score REAL,
    detected_date TEXT DEFAULT (datetime('now')),
    action_taken TEXT CHECK(action_taken IN ('none', 'archived', 'deleted', 'kept', 'pending')),
    action_date TEXT,
    FOREIGN KEY (asset_id_1) REFERENCES assets(id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id_2) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 5: transfers — Transfer logs
-- ============================================
CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT NOT NULL,
    dest_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    md5_hash TEXT,
    sha256_hash TEXT,
    transfer_date TEXT DEFAULT (datetime('now')),
    transfer_status TEXT CHECK(transfer_status IN ('pending', 'in_progress', 'completed', 'failed', 'retry')),
    verification_status TEXT CHECK(verification_status IN ('not_verified', 'verified', 'mismatch', 'failed')),
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    ingestion_id INTEGER,
    FOREIGN KEY (ingestion_id) REFERENCES ingestion_logs(id) ON DELETE SET NULL
);

-- ============================================
-- TABLE 6: backups — Backup records
-- ============================================
CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    backup_location TEXT NOT NULL,
    backup_path TEXT NOT NULL,
    sha256_hash TEXT,
    backup_date TEXT DEFAULT (datetime('now')),
    verified_date TEXT,
    verification_status TEXT CHECK(verification_status IN ('not_verified', 'verified', 'failed')),
    backup_size_bytes INTEGER,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 7: lightroom_catalog — Lightroom catalog references
-- ============================================
CREATE TABLE IF NOT EXISTS lightroom_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog_path TEXT NOT NULL,
    asset_id INTEGER NOT NULL,
    catalog_file_path TEXT,
    catalog_entry_date TEXT,
    rating INTEGER CHECK(rating >= 0 AND rating <= 5),
    color_label TEXT,
    keywords TEXT,
    is_missing INTEGER DEFAULT 0,
    last_sync_date TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 8: ingestion_logs — Drive ingestion session records
-- ============================================
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drive_path TEXT NOT NULL,
    drive_label TEXT,
    project_name TEXT,
    start_time TEXT DEFAULT (datetime('now')),
    end_time TEXT,
    total_files INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    duplicates_found INTEGER DEFAULT 0,
    files_transferred INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    status TEXT CHECK(status IN ('in_progress', 'completed', 'failed', 'partial')),
    report_path TEXT,
    error_message TEXT
);

-- ============================================
-- TABLE 9: rename_history — File rename audit trail
-- ============================================
CREATE TABLE IF NOT EXISTS rename_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    old_path TEXT NOT NULL,
    new_path TEXT NOT NULL,
    rename_date TEXT DEFAULT (datetime('now')),
    rename_reason TEXT,
    pattern_applied TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 10: integrity_checks — Periodic integrity audit results
-- ============================================
CREATE TABLE IF NOT EXISTS integrity_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date TEXT DEFAULT (datetime('now')),
    check_type TEXT CHECK(check_type IN ('full', 'sample', 'hash_verification', 'backup_verification')),
    sample_size INTEGER,
    files_checked INTEGER DEFAULT 0,
    files_passed INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    mismatches INTEGER DEFAULT 0,
    status TEXT CHECK(status IN ('in_progress', 'completed', 'failed', 'partial')),
    report_path TEXT
);

-- ============================================
-- TABLE 11: config_snapshots — Configuration version history
-- ============================================
CREATE TABLE IF NOT EXISTS config_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    settings_hash TEXT,
    rename_rules_hash TEXT,
    snapshot_date TEXT DEFAULT (datetime('now')),
    settings_json TEXT,
    rename_rules_json TEXT,
    notes TEXT
);

-- ============================================
-- INDEXES for frequently queried columns
-- ============================================
CREATE INDEX IF NOT EXISTS idx_assets_ingested_date ON assets(ingested_date);
CREATE INDEX IF NOT EXISTS idx_assets_asset_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_sha256_hash ON assets(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_exif_data_camera_model ON exif_data(camera_model);
CREATE INDEX IF NOT EXISTS idx_duplicates_detected_date ON duplicates(detected_date);

-- Additional useful indexes
CREATE INDEX IF NOT EXISTS idx_assets_file_path ON assets(file_path);
CREATE INDEX IF NOT EXISTS idx_assets_modified_date ON assets(modified_date);
CREATE INDEX IF NOT EXISTS idx_backups_asset_id ON backups(asset_id);
CREATE INDEX IF NOT EXISTS idx_backups_backup_date ON backups(backup_date);
CREATE INDEX IF NOT EXISTS idx_lightroom_catalog_asset_id ON lightroom_catalog(asset_id);
CREATE INDEX IF NOT EXISTS idx_transfers_transfer_date ON transfers(transfer_date);
CREATE INDEX IF NOT EXISTS idx_rename_history_asset_id ON rename_history(asset_id);
