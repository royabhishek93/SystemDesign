# Requirements and Clarity Questions

Use these to align scope with interviewers.

## User Requirements
- Playback: Start quickly, seek smoothly, remember position.
- Search: Filter by title, genre, tags.
- Recommendations: Per-profile, based on behavior.
- Personalization: Profiles, age-groups, languages.

## Content Provider Requirements
- Upload: Large files, resilient transfers.
- Distribution: Availability across regions/devices.
- Analytics: Views, completion rates, engagement.

## Scale Estimates (Back-of-the-Envelope)
- Titles: ~100,000
- Avg title size: ~500 GB
- Total storage: ~50 PB (raw; processed outputs add more)
- Metadata per title: ~5 KB → ~500 MB overall

## Clarity Checklist
- Current scope vs future scope: batch ingest? live events?
- Expected size/format: codecs, resolutions, DRM?
- Performance: time-to-first-frame, peak qps?
- Failure handling: resumable uploads, retries, idempotency?
- Compliance: geo-restrictions, content rules?
- Rollout: regions, CDN strategy, cache TTLs?

## Non-Functional Goals
- Reliability: resumable ingest + retries
- Scalability: queue-based async processing
- Cost: CDN offload, storage lifecycle policies
- Observability: metrics, tracing, error tracking