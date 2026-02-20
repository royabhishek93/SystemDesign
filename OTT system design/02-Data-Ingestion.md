# Data Ingestion (Presigned + Multipart)

Goal: Ingest multi-GB/TB media reliably and efficiently while keeping application servers out of the data path.

## Recommended Flow
1. Client → API: start upload (title, description, tags, release date, creator).
2. API → DB: upsert metadata, create ingestion record with status `initiated`.
3. API → Storage: create presigned multipart URL (uploadId, part size constraints).
4. API → Client: return presigned URL + uploadId + partSize (e.g., 64–128 MB).
5. Client → Storage: upload parts in parallel; retry failed parts; resume if interrupted.
6. Client → API: finalize; include list of part ETags.
7. API → Storage: verify object completion (checksum/ETag); mark status `ingested` and enqueue processing.

## Why Presigned URLs?
- Removes heavy upload traffic from app servers; avoids double-hop copying.
- Better scalability under spikes; leverages storage front-door capacity and global accelerators.
- Lower latency and cost; fewer compute resources for the app tier.

### Presigned URLs: A Simple Story
- Picture a creator in Delhi uploading a 500 GB movie. If we force the upload through our application server, the data goes creator → app server → storage. That’s a double-hop. The app server becomes a bottleneck, burns CPU, and during spikes it throttles or fails.
- With presigned URLs, the app server only hands out a short‑lived, signed ticket. The creator uploads straight to storage: creator → storage. No double-hop, fewer moving parts.
- Why it scales: the storage front door is built to absorb huge, bursty traffic globally. We lean on their edge endpoints and transfer acceleration instead of trying to scale our own compute fleet.
- Why it’s faster/cheaper: fewer network hops, fewer copies, and our app servers stop pushing gigabytes—they just coordinate (issue URL, track status, finalize). This lowers latency for creators and saves compute $$$ for us.
- When many creators upload at once (a festival week), storage scales horizontally. Our app tier stays responsive because it isn’t busy shuttling bytes; it simply authenticates, issues presigned URLs, and records progress.

### Why not scale our app fleet?
- Meaning: "Scaling our own compute fleet" means adding more app servers/VMs/containers, network capacity, and storage I/O to handle direct upload traffic (creator → app → storage).
- Why that’s expensive and risky:
	- Network and egress: each upload consumes high upstream bandwidth; many simultaneous uploads need very large NIC and egress capacity.
	- CPU, memory, and I/O: proxied uploads and processing (checksums, virus scan, temp buffering) consume CPU, RAM, and disk IOPS.
	- Operational complexity: autoscaling rules, warm pools, health checks, and monitoring increase operational burden and chance of misconfiguration.
	- Cost: running many large instances and paying extra egress/storage copies is costly compared to issuing presigned URLs.
- Concrete example: 1,000 concurrent uploads at 100 Mbps each equals 100 Gbps incoming to your app tier — that requires many high‑bandwidth instances and complex load balancing.
- Interview line: “Scaling our own fleet means provisioning and managing lots of servers, network, and I/O to carry the bytes — presigned URLs avoid that by sending data straight to storage, which is cheaper and simpler to operate.”

## Multipart Upload Details
- Part size: 64–128 MB typical; larger parts reduce request count but make retries heavier.
- Parallelism: tune client concurrency (e.g., 4–16 parts) based on network/CPU.
- Checksums: use MD5/SHA256 per-part where supported; verify ETags.
- Resume: store uploadId client-side; list uploaded parts and continue.
- Transfer acceleration/CDN: optionally enable accelerated endpoints for global creators.

## Failure Handling & Idempotency
- Client retries per-part with exponential backoff; abort or pause on persistent failures.
- Finalize endpoint is idempotent: repeated calls safe; server checks object integrity.
- Renew presigned URLs: refresh on expiry; validate ownership and remaining time.
- Quotas: enforce per-creator size/time limits; prevent abuse.

## Metadata Storage (PostgreSQL)
- Schema: titles table + JSONB metadata for flexible fields.
- Indexes: title, genre, tags, release date; GIN index on JSONB for tags.
- Status: `initiated`, `uploading`, `ingested`, `processing`, `published`.
- Provenance: `creator_id`, `source`, `upload_origin` for audit.

## APIs (Example)
- POST /uploads: returns `{ uploadId, presignedUrl, partSize }`
- POST /uploads/{id}/complete: validates, finalizes, enqueues processing
- GET /titles/{id}: metadata read
- GET /uploads/{id}/status: client can poll ingestion state

## Observability
- Events: `upload_started`, `part_completed`, `upload_completed`, `finalize_failed`.
- Metrics: bytes uploaded, parts retried, average part throughput, total ingest time.
- Tracing: correlate client session → API → storage → processing enqueue.

## Security & Governance
- Auth: signed creator tokens; scope to title/tenant.
- Limits: max file size, allowed codecs/containers; server-side validation.
- Virus/malware scanning hooks for non-video assets.

## Advanced Patterns
- Direct-to-storage with client-side hashing; server validates manifest of parts.
- Ingest proxies for restricted networks (fall back to streaming through app server).
- Multi-region ingest: write to nearest bucket; replicate to primary processing region.