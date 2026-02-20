# Streaming and Chunking

Goal: Fast playback, smooth seeking, network-friendly delivery.

## Chunking Options
- Fixed size: e.g., 1 MB segments (simple, storage-heavy).
- Time-based: 6–10s segments (common for HLS/DASH).
- Scene-based: content-aware cuts (advanced, costly).

## Protocols
- HLS: HTTP Live Streaming (Apple) — widely supported.
- DASH: MPEG-DASH — standardized, flexible.

## Player Behavior
- Adaptive bitrate: switches renditions based on bandwidth/CPU.
- Seeking: jumps to segment boundaries quickly.
- Resume: uses watch history to start from last position.

## Server Side
- Origin: serves manifests/segments from object storage.
- CDN: caches popular segments near users, reduces origin load.
- Cache control: tuned TTLs, cache keys per rendition.

## Metadata Links
- Title → renditions → manifests (m3u8/mpd) → segments.
- Regions/DRM: control availability by locale and device.