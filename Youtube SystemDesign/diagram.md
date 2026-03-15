## Interview-Ready System Architecture

### Video Upload & Processing System - Complete Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE (Low QPS - Metadata)                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐  1. Upload Init    ┌─────────────────┐                      │
│  │   Web / App  │ ──────────────────▶ │  API Gateway    │                      │
│  │   (Client)   │                     │  Auth + Rate    │                      │
│  └──────────────┘                     │  Limiting       │                      │
│         │                              └────────┬────────┘                      │
│         │                                       │                               │
│         │  2. Session Response                  ▼                               │
│         │     (uploadId + URLs)        ┌─────────────────┐                      │
│         │ ◀───────────────────────────  │ Upload Service  │                      │
│         │                               │   (Stateless)   │                      │
│         │                               │ Returns:        │                      │
│         │                               │ - uploadId      │                      │
│         │                               │ - presigned URLs│                      │
│         │                               │ - multipart info│                      │
│         │                               └─────────────────┘                      │
│         │                                                                        │
└─────────┼────────────────────────────────────────────────────────────────────────┘
          │
┌─────────┼────────────────────────────────────────────────────────────────────────┐
│         │              DATA PLANE (High Throughput - Bytes)                      │
├─────────┼────────────────────────────────────────────────────────────────────────┤
│         │                                                                        │
│         │ 3. Multipart Upload                                                   │
│         │    (Direct, with Resume)                                              │
│         ▼                                                                        │
│  ┌──────────────────┐                                                           │
│  │ Object Storage   │  4. Upload Complete Event                                 │
│  │  (Raw Videos)    │ ─────────────────────────────────▶ ┌──────────────────┐  │
│  │   S3 / GCS       │                                    │  Event Queue     │  │
│  └──────────────────┘                                    │  Kafka / SQS     │  │
│                                                           └────────┬─────────┘  │
│                                                                    │             │
│                                                                    │ 5. Async    │
│                                                                    │ Processing  │
│                                                                    ▼             │
│                                                    ┌──────────────────────────┐ │
│                                                    │ Video Processing Pipeline│ │
│                                                    │ ──────────────────────── │ │
│                                                    │ • Transcode 144p-1080p   │ │
│                                                    │ • Generate Thumbnails    │ │
│                                                    │ • Codec validation       │ │
│                                                    │ • Malware scan           │ │
│                                                    │ • Content ID check       │ │
│                                                    └───────────┬──────────────┘ │
│                                                                │                 │
│                                                                │ 6. Renditions   │
│                                                                │    & Thumbnails │
│                                                                ▼                 │
│  ┌──────────────────┐                        ┌──────────────────────────┐      │
│  │ Object Storage   │  7. Origin Fetch       │         CDN              │      │
│  │ (Processed)      │ ─────────────────────▶ │  (CloudFront / Akamai)   │      │
│  │  S3 / GCS        │                        │   Global Edge Nodes      │      │
│  └──────────────────┘                        └──────────────────────────┘      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                        METADATA & STATE MANAGEMENT                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│         ┌─────────────┐                      ┌────────────────┐                │
│         │ Event Queue │ ────────────────────▶│ Metadata       │                │
│         │             │   Status Updates     │ Service        │                │
│         └─────────────┘                      └───────┬────────┘                │
│                                                      │                          │
│                                                      ▼                          │
│                                              ┌────────────────┐                 │
│                                              │ Metadata DB    │                 │
│                                              │ (SQL/NoSQL)    │                 │
│                                              │ - Upload status│                 │
│                                              │ - Video info   │                 │
│                                              │ - User data    │                 │
│                                              └────────────────┘                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FAILURE HANDLING                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│         ┌─────────────┐                                                         │
│         │ Event Queue │ ◀───── retries ─────┐                                  │
│         │             │                      │                                  │
│         └──────┬──────┘                      │                                  │
│                │                             │                                  │
│                │ (max retries exceeded)      │                                  │
│                ▼                                                                │
│         ┌──────────────────┐                                                    │
│         │ Dead Letter Queue│                                                    │
│         │      (DLQ)       │                                                    │
│         └────────┬─────────┘                                                    │
│                  │                                                              │
│                  ▼                                                              │
│         ┌──────────────────┐                                                    │
│         │ Alerts + Manual  │                                                    │
│         │   Operations     │                                                    │
│         │  - PagerDuty     │                                                    │
│         │  - Slack alerts  │                                                    │
│         └──────────────────┘                                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Multipart Upload Sequence Flow

```
┌────────┐          ┌────────────┐       ┌─────────────┐       ┌──────────────┐
│ Client │          │    API     │       │   Upload    │       │   Object     │
│        │          │  Gateway   │       │   Service   │       │   Storage    │
└───┬────┘          └─────┬──────┘       └──────┬──────┘       └──────┬───────┘
    │                     │                     │                      │
    │ 1. Init Upload      │                     │                      │
    │    (with auth)      │                     │                      │
    ├────────────────────▶│                     │                      │
    │                     │                     │                      │
    │                     │ 2. Create Session   │                      │
    │                     ├────────────────────▶│                      │
    │                     │                     │                      │
    │                     │                     │ 3. Generate presigned│
    │                     │                     │    URLs + uploadId   │
    │ 4. Session Response │                     │                      │
    │    (uploadId +      │◀────────────────────┤                      │
    │     part URLs)      │                     │                      │
    │◀────────────────────┤                     │                      │
    │                     │                     │                      │
    │ ╔═══════════════════════════════════════════════════════════════╗│
    │ ║              5. Upload Parts (Loop)                          ║│
    │ ║  ┌──────────────────────────────────────────────────────────┐║│
    │ ║  │ For each part:                                           │║│
    │ ║  │ PUT /part1 (presigned URL) ────────────────────────────▶ │║│
    │ ║  │ PUT /part2 (presigned URL) ────────────────────────────▶ │║│
    │ ║  │ PUT /partN (presigned URL) ────────────────────────────▶ │║│
    │ ║  │                                                           │║│
    │ ║  │ Note: Client can resume from any failed part             │║│
    │ ║  └──────────────────────────────────────────────────────────┘║│
    │ ╚═══════════════════════════════════════════════════════════════╝│
    │                     │                     │                      │
    │ 6. Complete         │                     │                      │
    │    Multipart        │                     │                      │
    ├──────────────────────────────────────────────────────────────────▶
    │                     │                     │                      │
    │                     │                     │ 7. Upload Complete   │
    │                     │                     │    Event (uploadId)  │
    │                     │                     │◀─────────────────────┤
    │                     │                     │                      │
    │                     │                     │ 8. Enqueue Processing│
    │                     │                     │    (to Kafka/SQS)    │
    │                     │                     ├────────────────────▶ Queue
    │                     │                     │                      │
    │ 9. Success Response │                     │                      │
    │◀────────────────────┴─────────────────────┤                      │
    │                                           │                      │
```

### Talking Points (use with the diagram)
- Control vs Data Plane separation: metadata low-QPS; bytes direct to storage via presigned URLs.
- Idempotency via `uploadId` and deterministic object keys; safe retries.
- Eventual consistency: reconcile via processing events + status updates in SQL.
- Backpressure: autoscale consumers on queue lag; API rate limits protect control plane.
- Failure handling: bounded retries → DLQ → alerts and manual ops.
- Observability: track `uploadId` across logs/metrics/traces; SLIs include time-to-ready and CDN hit ratio.

### Alternative Online Tools
- diagrams.net (draw.io): manual diagramming with layers, export PNG/SVG.
- Excalidraw: hand-drawn style; great for whiteboard interviews.
- PlantUML Editor: code-first diagrams; good for sequence/state diagrams.
- Miro or Figma: collaborative boards; polished visual styling.

## Demo Architecture - Horizontally Grouped Lanes

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│  CLIENT LAYER                                                                        │
│  ┌──────────────┐                                                                    │
│  │   Web / App  │                                                                    │
│  │   (Browser   │                                                                    │
│  │    Mobile)   │                                                                    │
│  └──────┬───────┘                                                                    │
│         │                                                                            │
└─────────┼────────────────────────────────────────────────────────────────────────────┘
          │
┌─────────┼────────────────────────────────────────────────────────────────────────────┐
│         │    CONTROL PLANE (Low QPS)                                                 │
│         │                                                                            │
│         │  Init Request                                                              │
│         ├──────────────▶ ┌─────────────────┐                                        │
│         │                │   API Gateway   │                                        │
│         │                │  Auth + Rate    │                                        │
│         │                │    Limiting     │                                        │
│         │                └────────┬────────┘                                        │
│         │                         │                                                 │
│         │                         ▼                                                 │
│         │                ┌─────────────────┐         ┌──────────────────┐          │
│         │◀───────────────┤ Upload Service  │────────▶│ Metadata Service │          │
│         │  Session Info  │   (Stateless)   │ Updates │                  │          │
│         │  uploadId+URLs └─────────────────┘         └─────────┬────────┘          │
│         │                                                       │                   │
│         │                                             ┌─────────▼─────────┐         │
│         │                                             │   Metadata DB     │         │
│         │                                             │  (SQL/NoSQL)      │         │
│         │                                             └───────────────────┘         │
│         │                                                                           │
└─────────┼───────────────────────────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────────────────────────┐
│         │    DATA PLANE (High Throughput)                                           │
│         │                                                                            │
│         │  Multipart PUT                                                             │
│         ├─────────────────────────▶ ┌───────────────────┐                           │
│         │                           │  Object Storage   │                           │
│         │                           │   (Raw Videos)    │                           │
│         │                           └─────────┬─────────┘                           │
│         │                                     │                                     │
│         │                                     │ Complete Event                      │
│         │                                     ▼                                     │
│         │                           ┌───────────────────┐                           │
│         │                           │  Object Storage   │                           │
│         │                           │  (Processed)      │                           │
│         │                           └─────────┬─────────┘                           │
│         │                                     │                                     │
│         │                                     │ Origin Fetch                        │
│         │                                     ▼                                     │
│         │                           ┌───────────────────┐                           │
│         │◀──────────────────────────┤       CDN         │                           │
│         │   Video Stream            │ (CloudFront)      │                           │
│         │                           └───────────────────┘                           │
│         │                                                                           │
└─────────┼───────────────────────────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────────────────────────┐
│         │    ASYNC PROCESSING PIPELINE                                              │
│         │                                                                            │
│         │                           ┌───────────────────┐                           │
│         │                           │   Event Queue     │                           │
│         │                           │   Kafka / SQS     │                           │
│         │                           └─────────┬─────────┘                           │
│         │                                     │                                     │
│         │                                     ▼                                     │
│         │                           ┌───────────────────┐                           │
│         │                           │     Workers       │                           │
│         │                           │  ───────────────  │                           │
│         │                           │  • Transcode      │                           │
│         │                           │  • Scan           │                           │
│         │                           │  • Content ID     │                           │
│         │                           └─────────┬─────────┘                           │
│         │                                     │                                     │
│         │                                     │ Success                             │
│         │                                     ├────────────▶ [Processed Storage]    │
│         │                                     │                                     │
│         │                                     │ Failure                             │
│         │                                     ├────────────▶ ┌──────────────────┐  │
│         │                                     │              │ Dead Letter Queue│  │
│         │                                     │              └────────┬─────────┘  │
│         │                                     │                       │            │
│         │                                     │                       ▼            │
│         │                                     │              ┌──────────────────┐  │
│         │                                     │              │ Alerts + Manual  │  │
│         │                                     │              │   Operations     │  │
│         │                                     │              └──────────────────┘  │
│         │                                     │                                     │
└─────────┴─────────────────────────────────────────────────────────────────────────────┘

KEY FEATURES:
• Control vs Data Plane separation: metadata (low-QPS) vs bytes (direct to storage via presigned URLs)
• Idempotency via uploadId and deterministic object keys for safe retries
• Eventual consistency: reconcile via processing events + status updates in SQL
• Backpressure: autoscale consumers on queue lag; API rate limits protect control plane
• Failure handling: bounded retries → DLQ → alerts and manual ops
```

## Complete Processing Sequence with Retries & Failure Handling

```
Client   APIGW    Upload   Storage   Queue    Worker    Meta     CDN
  │       │         │         │        │        │        │        │
  │       │         │         │        │        │        │        │
  │ 1. Init Upload  │         │        │        │        │        │
  │   (auth)        │         │        │        │        │        │
  ├──────────────▶  │         │        │        │        │        │
  │       │         │         │        │        │        │        │
  │       │ 2. Create Session │        │        │        │        │
  │       ├─────────────────▶ │        │        │        │        │
  │       │         │         │        │        │        │        │
  │       │         │ 3. Response      │        │        │        │
  │       │         │   uploadId+URLs  │        │        │        │
  │◀──────┴─────────┴─────────┤        │        │        │        │
  │                           │        │        │        │        │
  │                           │        │        │        │        │
  │ ╔════════════════════════════════════════════════════════════╗│
  │ ║  4. Upload Parts (Loop)                                   ║│
  │ ║  ┌────────────────────────────────────────────────────┐   ║│
  │ ║  │ PUT part1 (presigned) ───────────────────────────▶ │   ║│
  │ ║  │ PUT part2 (presigned) ───────────────────────────▶ │   ║│
  │ ║  │ PUT partN (presigned) ───────────────────────────▶ │   ║│
  │ ║  │                                                     │   ║│
  │ ║  │ Note: Resume supported via part numbers            │   ║│
  │ ║  └────────────────────────────────────────────────────┘   ║│
  │ ╚════════════════════════════════════════════════════════════╝│
  │                           │        │        │        │        │
  │ 5. Complete Multipart     │        │        │        │        │
  ├───────────────────────────▶        │        │        │        │
  │                           │        │        │        │        │
  │                           │ 6. Upload Complete Event  │        │
  │                           │        │  (uploadId)      │        │
  │                           ├────────────────▶│        │        │
  │                           │        │        │        │        │
  │                           │        │ 7. Consume (uploadId)     │
  │                           │        │        │        │        │
  │                           │        │        ├───────▶│        │
  │                           │        │        │        │        │
  │                           │        │        │ ╔══════╧═══════════════════╗
  │                           │        │        │ ║  PARALLEL PROCESSING     ║
  │                           │        │        │ ╠════════════════════════════
  │                           │        │        │ ║                          ║
  │                           │        │        │ ║ 8a. Transcode            ║
  │                           │        │        │ ║     144p, 360p, 720p,    ║
  │                           │ 8a. Write renditions      1080p               ║
  │                           │◀───────────────────────────┤                  ║
  │                           │        │        │ ║                          ║
  │                           │        │        │ ║ 8b. Generate             ║
  │                           │        │        │ ║     Thumbnails           ║
  │                           │◀───────────────────────────┤                  ║
  │                           │        │        │ ║                          ║
  │                           │        │        │ ║ 8c. Update Metadata      ║
  │                           │        │        │ ║     status: PROCESSING   ║
  │                           │        │        │ ║     → READY              ║
  │                           │        │        │        ├─────────────────▶  │
  │                           │        │        │ ║                      (Metadata DB)
  │                           │        │        │ ║                          ║
  │                           │        │        │ ╚══════════════════════════╝
  │                           │        │        │        │        │        │
  │                           │        │        │        │        │        │
  │                           │        │        │    ┌───┴────────┴────┐   │
  │                           │        │        │    │   SUCCESS?      │   │
  │                           │        │        │    └───┬────────┬────┘   │
  │                           │        │        │        │        │        │
  │                           │        │        │     YES│     NO │        │
  │                           │        │        │        │        │        │
  │                           │        │        │        ▼        ▼        │
  │                           │        │        │   ┌─────────┐ ┌─────────┐
  │                           │        │        │   │ 9. Warm │ │  DLQ    │
  │                           │        │        │   │   CDN   │ │ (reason)│
  │                           │        │        │   │  Cache  │ └────┬────┘
  │                           │        │        │   └────┬────┘      │
  │                           │        │        │        │           │
  │                           │        │        │        │           ▼
  │                           │◀────────────────────────┬┘    ┌───────────┐
  │                           │  First fetch / Origin   │     │  Alerts   │
  │                           │        │        │       │     │  + Manual │
  │                           │        │        │       │     │    Ops    │
  │                           │        │        │       │     └───────────┘
  │                           │        │        │       │
  │                           │        │        │   10. Meta: READY
  │                           │        │        │       ├──────────────────▶
  │                           │        │        │       │            (status)
  │                           │        │        │       │
  │                           │        │        │       │
```

### Key Insights:
- uploadId acts as the thread of traceability across all systems
- Parallel processing (transcoding, thumbnails, metadata) improves speed
- Failure path: bounded retries → DLQ → alerts and manual operations
- CDN warming on first fetch ensures optimal delivery performance
- Idempotency checks prevent duplicate processing even on retries
```

### Demo Tips
- Keep text minimal; narrate steps verbally using the numbering.
- Use `uploadId` as the thread of traceability across both diagrams.
- Highlight Control vs Data Plane first, then zoom into the sequence.
