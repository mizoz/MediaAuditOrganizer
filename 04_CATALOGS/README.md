# 04_CATALOGS

Lightroom catalogs, Capture One sessions, and metadata databases.

## Purpose

This directory stores catalog files from photo management software. These catalogs reference media files but do not contain the actual images/videos.

## Structure

```
04_CATALOGS/
├── Lightroom/
│   └── [CatalogName].lrcat
├── CaptureOne/
│   └── [SessionName].captureone
└── MetadataDB/
    └── [DatabaseName].db
```

## Usage

- Store catalog files here, not the actual media
- Backup catalogs regularly (they contain edit history and metadata)
- Link catalogs to media in 01_PHOTOS/ and 02_VIDEOS/

## Created

2026-03-04 as part of MediaAuditOrganizer Phase 2 (Option B — Full Industrial Structure)
