# Interview Cheat Sheet (15+ Years)

Use this as a concise recap during interviews.

## End-to-End Flow
1. Client → API: request upload
2. API → DB: store metadata, return presigned multipart url
3. Client → Storage: multipart upload parts
4. Client → API: finalize
5. API → Queue: enqueue processing job
6. Workers → Storage: transcode/encrypt/package outputs
7. API/Workers → DB: update availability per rendition
8. User → Player: request playback
9. Player → CDN: fetch manifests + segments (HLS/DASH)

## Trade-Offs to Mention
- Presigned vs proxy upload: cost, latency, scalability
- Chunk size: startup latency vs seek accuracy vs overhead
- Codecs: CPU cost vs bandwidth savings
- DRM: security vs device compatibility
- CDN TTLs: freshness vs cache efficiency

## Numbers (Sample)
- Titles: 100k
- Raw size: 50 PB
- Metadata: 5 KB/title → 500 MB overall
- Segment length: 6–10s

## Reliability Patterns
- Resumable multipart upload, per-part retry
- Idempotent finalize and processing stages
- DLQ for failed jobs, alerts for stalls

## Observability
- Metrics for upload/processing/playback
- Trace IDs through ingest → jobs → playback

## Common Interview Questions
- How do you handle failed uploads at 500 GB scale?
- Why use async processing and queues?
- How do you design adaptive bitrate ladders?
- What’s your CDN cache strategy for premieres?
- How do you enforce geo-restrictions and DRM?

## Bonus Talking Points
- Multi-region strategy: active-passive for origin, edge-only global
- Cost optimization: cold storage tiers, codec choices, cache hit rates