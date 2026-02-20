# Scaling and CDN Strategy (Deep Dive)

Goal: Deliver video to millions of concurrent users with predictable latency, high availability, and controlled cost.

## Objectives & SLOs
Plain-English targets (with examples):

- Percentiles (p95/p99): These describe what most users see. p95 means 95% of sessions are faster than this number (only 5% are slower). Example: if startup p95 is 2s, 95% of sessions start in 2 seconds or less.
- Startup latency (time-to-first-frame): Time from pressing play to the first video frame. Targets: p95 ≤ 2s; p99 ≤ 4s. Translation: almost everyone should start quickly; only a very small tail is slower.
- Rebuffering (stall time): Share of watch time users spend waiting (spinner). Target: < 0.5% at p95. The phrase “segment download p95 < segment duration” means CDN delivers each chunk faster than it takes to play, so the buffer grows (e.g., 6s segments; p95 download 4s = good; if 7s, users will stall).
- Edge hit ratio (CDN cache): Percent of requests served from nearby CDN cache instead of your origin. Higher is faster and cheaper. Aim > 90% for popular titles, > 70% overall during big spikes.
- Availability: Playback uptime across the month. 99.95% means ~0.05% allowed downtime. Example: in 30 days (43,200 minutes), 0.0005 × 43,200 ≈ 21.6 minutes total downtime.

## Traffic Patterns & Capacity Planning
- Concurrency: estimate peak concurrent streams (e.g., 1M) from user base and premieres.
- Bitrate ladder: 240p–4K with target bitrates (e.g., 0.4–20 Mbps). Average delivered ~3–5 Mbps/user.
- Throughput planning: 1M × 3 Mbps ≈ 3 Tbps; multi-CDN needed.
- Segment length: 6–10s (HLS/DASH); LL-HLS/low-latency DASH use 1–2s parts with CMAF.
- GOP alignment: ensure keyframes align with segment boundaries to enable fast switching.

## CDN Architecture
### CDN Basics (Plain English)
- What it is: A CDN is a global network of cache servers (edge POPs) that keep temporary copies of files close to users. It is not a database; it doesn’t support queries/transactions—it simply caches and serves files over HTTP.
- What it holds: Cached objects like manifests (m3u8/mpd) and video segments stored in RAM/SSD/HDD on edge servers. Content remains until it expires (TTL), is evicted, or you purge it.
- How it serves: On a request, the CDN checks its cache key (path + query and sometimes device/DRM info). If it’s a hit, the edge serves immediately. If it’s a miss, the CDN fetches from origin, stores a copy, then serves the user.
- Control knobs: Set short TTLs for manifests and longer TTLs for segments; design cache keys to avoid user-specific headers; invalidate/purge paths or use versioned URLs to refresh content safely.
- Source of truth: Your origin (object storage/app servers). The CDN cache is a temporary layer that speeds up delivery and reduces origin load.

## Routing & Multi-CDN
- Geo/DNS routing: GeoDNS or Anycast/BGP to nearest edge POP.
- Multi-CDN controller: real-user measurements (RUM) + health to choose best CDN per region/ISP.
- Failover policy: automatic shift on latency/availability breaches; circuit breakers to stop sending traffic to bad POPs.

## Security & Access Control
- Signed URLs/Tokens: embed expiry + path claims; validate at CDN edge (token-based auth) to reduce origin load.
- DRM compatibility: Widevine/FairPlay/PlayReady key delivery separate from CDN; bind license to device.
- Hotlink protection: referer/origin checks and token binding; IP/ASN-based policies for scraping.
- WAF + DDoS: rate limiting for manifest abuse; protect key endpoints (license server, origin gateway).

## Origin Hardening
- Multi-region: active-active or active-passive origins with object replication and health-checked failover.
- Slow-client protection: write/read timeouts, max header/body size, request queuing caps.
- Range requests: optimized for partial segment reads (seek) with tuned caching and `Accept-Ranges` support.
- Backpressure: shed traffic when origin saturation occurs; prioritize small manifest responses over large objects.

## Performance Techniques
- Protocols: HTTP/2 multiplexing; HTTP/3/QUIC for better lossy network performance.
- CMAF: common container enables LL-HLS/LL-DASH; chunked transfer for partial segments.
- Connection reuse: persistent connections from edge to origin; tune TCP/QUIC parameters.
- Compression: gzip/brotli for manifests; avoid double-compress of already compressed segments.

## Cache Warmup & Premieres
- Pre-warm: push top manifests/first segments to edge before release windows.
- Staggered release: different regions/time windows to avoid global stampedes.
- Edge worker prefetch: when a user requests segment N, prefetch N+1/N+2.

## Failure Scenarios & Playbooks
- CDN POP outage: auto route to nearest healthy POP or alternative CDN; monitor QoE and revert when stable.
- Regional origin failure: shift to secondary region; invalidate stale manifests if variant availability changed.
- Segment 404s during rollout: serve lower rendition or older version; quickly revalidate manifests.
- License server issues: fallback messaging and retry policies with exponential backoff.

## Cost Optimization
- Tiered caching + high hit ratios; lower origin egress.
- Storage lifecycle: move cold renditions to infrequent access; archive very old content.
- Codec choices: HEVC/AV1 reduce delivered bitrate → lower CDN bills (balance device support).
- Edge compute: perform auth/manifest filtering at edge to reduce origin requests.

## Observability & Metrics
- Edge: hit/miss ratio, latency p50/p95/p99, 5xx rates, cache stampedes.
- Origin: egress, concurrent connections, queue depth, request latency, 4xx/5xx.
- Playback QoE: startup time, rebuffer events, average bitrate, error rate per ISP/region/device.
- Business: cost/GB delivered, cache efficiency per title, premiere impact.

## Testing & Chaos
- Synthetic load: simulate segment fetches with realistic patterns (seek, ABR switches).
- Canary rollouts: versioned manifests (e.g., `/v2/manifest.m3u8`) to test small cohorts.
- Fault injection: degrade CDN POP, increase origin latency, drop packets; verify failovers.

## Rollouts & Versioning
- Versioned paths: `/titles/{id}/renditions/{v}/...` allow quick cache busts.
- Blue/Green: maintain old/new manifests/segments concurrently; switch DNS/controller gradually.
- Stale-while-revalidate: enable smooth updates without mass invalidations.

## Edge Compute Use Cases
- Auth at edge: validate signed tokens; block unauthorized.
- Geo restrictions: filter manifests (drop variants) per country/device class.
- Dynamic ad insertion: stitch ad segments into manifests without origin changes.

## Example Numbers (Back-of-the-Envelope)
- 1,000,000 concurrent streams × 3 Mbps ≈ 3 Tbps aggregate.
- With 85% edge hit, origin sees ~0.45 Tbps; tiered caching reduces further.
- Segment length 6s: player fetches ~10 segments/min; plan CDN request rates accordingly.

## Practical Checklist (Interview-Ready)
- Define SLOs and monitor QoE.
- Use multi-CDN with controller + automated failover.
- Tune cache keys/TTLs; pre-warm for spikes.
- Harden origins; support range requests and backpressure.
- Enforce access via signed tokens + DRM.
- Measure, canary, and chaos-test regularly.