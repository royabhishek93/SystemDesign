                    ┌───────────────┐
                    │    Web / App  │
                    └───────┬───────┘
                            │
            ┌───────────────┴────────────────┐
            │          CONTROL PLANE          │
            │   (Low QPS, metadata only)      │
            └────────────────────────────────┘
                            │
                 (1) Upload Init Request
                            │
                    ┌───────▼───────┐
                    │ API Gateway   │
                    │ Auth + Rate   │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ Upload Service│
                    │ (Stateless)   │
                    │---------------│
                    │ uploadId      │
                    │ presigned URLs│
                    │ multipart info│
                    └───────┬───────┘
                            │
                 (2) Upload Session Response
                            │
                    ┌───────▼───────┐
                    │    Web / App  │
                    └───────┬───────┘
                            │
            ┌───────────────┴────────────────┐
            │            DATA PLANE           │
            │     (High throughput bytes)     │
            └────────────────────────────────┘
                            │
                 (3) Direct Chunk Upload
                            │
              ┌─────────────▼─────────────┐
              │     Object Storage         │
              │      (Raw Videos)          │
              │----------------------------│
              │ multipart + resume         │
              └─────────────┬─────────────┘
                            │
                 (4) Upload Complete Event
                            │
                    ┌───────▼───────┐
                    │ Event Queue   │
                    │ (Kafka / SQS) │
                    └───────┬───────┘
                            │
                 (5) Async Processing
                            │
        ┌───────────────────▼───────────────────┐
        │     Video Processing Pipeline          │
        │----------------------------------------│
        │ Transcoding (144p–1080p)               │
        │ Thumbnail generation                   │
        │ Codec validation                       │
        │ Malware scan                           │
        │ Copyright / Content ID                 │
        └───────────────────┬───────────────────┘
                            │
                 (6) Processed Output
                            │
              ┌─────────────▼─────────────┐
              │     Object Storage         │
              │   (Processed Videos)       │
              └─────────────┬─────────────┘
                            │
                 (7) CDN Origin Fetch
                            │
                    ┌───────▼───────┐
                    │      CDN      │
                    └───────────────┘

        ┌──────────────── METADATA & STATE ────────────────┐
        │                                                    │
        │  (5) ──► Metadata Service ──► Metadata DB (SQL)   │
        │           status: UPLOADING / READY / FAILED      │
        └───────────────────────────────────────────────────┘

        ┌──────────────── FAILURE HANDLING ─────────────────┐
        │                                                    │
        │  Retries → Dead Letter Queue → Alert + Manual Ops  │
        │                                                    │
        └───────────────────────────────────────────────────┘
