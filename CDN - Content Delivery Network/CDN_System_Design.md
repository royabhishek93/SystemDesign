# CDN (Content Delivery Network) - Delivering Content at Lightning Speed

## 1. What is a CDN?

**CDN (Content Delivery Network)** is a geographically distributed network of servers that delivers content to users from the nearest server location.

### Why CDN is Needed:

- ✅ Faster content delivery (reduced latency)
- ✅ Reduced server load
- ✅ Better user experience globally
- ✅ Handle traffic spikes
- ✅ DDoS protection
- ✅ Lower bandwidth costs
- ✅ Improved SEO rankings

### Visual: Without vs With CDN

```
┌────────────────────────────────────────────────────────────────────────┐
│                  WITHOUT CDN (SLOW & CENTRALIZED)                      │
└────────────────────────────────────────────────────────────────────────┘

ALL users hit single origin server:

User in USA (New York)
     │
     │ 10ms latency
     ↓
User in Europe (London)
     │
     │ 100ms latency
     ↓
User in Asia (Tokyo)
     │
     │ 200ms latency
     ↓
User in Australia (Sydney)
     │
     │ 250ms latency
     ↓
┌────────────────────────────────────┐
│  ORIGIN SERVER                     │
│  Location: USA (Virginia)          │
│                                    │
│  Problems:                         │
│  ❌ High latency for distant users │
│  ❌ Single point of failure        │
│  ❌ High bandwidth costs           │
│  ❌ Server overload                │
│  ❌ Slow for global users          │
└────────────────────────────────────┘

User Experience:
• USA: 10ms (Good)
• Europe: 100ms (Okay)
• Asia: 200ms (Slow) ❌
• Australia: 250ms (Very Slow) ❌


WITH CDN (FAST & DISTRIBUTED)
──────────────────────────────

Users hit nearest CDN edge server:

┌─────────────┐         ┌─────────────┐
│ User in USA │         │ CDN Edge    │
│ (New York)  │────10ms→│ New York    │
└─────────────┘         └─────────────┘
                               │
                               ↓ Cache hit (instant)
                        ┌─────────────┐
                        │ Content     │
                        └─────────────┘

┌─────────────┐         ┌─────────────┐
│ User in     │         │ CDN Edge    │
│ Europe      │────15ms→│ London      │
│ (London)    │         └─────────────┘
└─────────────┘                │
                               ↓ Cache hit
                        ┌─────────────┐
                        │ Content     │
                        └─────────────┘

┌─────────────┐         ┌─────────────┐
│ User in     │         │ CDN Edge    │
│ Asia        │────20ms→│ Tokyo       │
│ (Tokyo)     │         └─────────────┘
└─────────────┘                │
                               ↓ Cache hit
                        ┌─────────────┐
                        │ Content     │
                        └─────────────┘

┌─────────────┐         ┌─────────────┐
│ User in     │         │ CDN Edge    │
│ Australia   │────25ms→│ Sydney      │
│ (Sydney)    │         └─────────────┘
└─────────────┘                │
                               ↓ Cache hit
                        ┌─────────────┐
                        │ Content     │
                        └─────────────┘

User Experience:
• USA: 10ms (Excellent) ✅
• Europe: 15ms (Excellent) ✅
• Asia: 20ms (Excellent) ✅
• Australia: 25ms (Excellent) ✅

All users get fast experience!
10-25x improvement for distant users!
```

## 2. CDN Architecture

### Visual: Complete CDN System

```
┌────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE CDN ARCHITECTURE                           │
└────────────────────────────────────────────────────────────────────────┘

                        GLOBAL USERS
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  👤 USA    👤 Europe    👤 Asia    👤 Australia    👤 Africa │
└─┬────────┬──────────┬──────────┬──────────────┬──────────┬───┘
  │        │          │          │              │          │
  │        │          │          │              │          │
  ↓        ↓          ↓          ↓              ↓          ↓

LAYER 1: DNS ROUTING (GeoDNS)
┌────────────────────────────────────────────────────────────────┐
│                  CDN DNS SERVER                                │
│                                                                │
│  User queries: cdn.example.com                                 │
│  Returns: IP of nearest edge server                            │
│                                                                │
│  Example responses:                                            │
│  • USA user → 192.0.2.1 (New York edge)                        │
│  • EU user → 198.51.100.1 (London edge)                        │
│  • Asia user → 203.0.113.1 (Tokyo edge)                        │
└────────────────────────────────────────────────────────────────┘
  │        │          │          │              │          │
  ↓        ↓          ↓          ↓              ↓          ↓

LAYER 2: EDGE SERVERS (POP - Point of Presence)
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ New York │ │ London   │ │ Tokyo    │ │ Sydney   │ │ Lagos    │
│ Edge     │ │ Edge     │ │ Edge     │ │ Edge     │ │ Edge     │
│          │ │          │ │          │ │          │ │          │
│ Cache:   │ │ Cache:   │ │ Cache:   │ │ Cache:   │ │ Cache:   │
│ • Images │ │ • Images │ │ • Images │ │ • Images │ │ • Images │
│ • Videos │ │ • Videos │ │ • Videos │ │ • Videos │ │ • Videos │
│ • HTML   │ │ • HTML   │ │ • HTML   │ │ • HTML   │ │ • HTML   │
│ • CSS/JS │ │ • CSS/JS │ │ • CSS/JS │ │ • CSS/JS │ │ • CSS/JS │
│          │ │          │ │          │ │          │ │          │
│ Hit: 90% │ │ Hit: 88% │ │ Hit: 92% │ │ Hit: 85% │ │ Hit: 87% │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │            │
     │ If cache miss (10%)     │            │            │
     └────────────┼────────────┼────────────┼────────────┘
                  │            │            │
                  ↓            ↓            ↓

LAYER 3: REGIONAL CACHES (Mid-Tier)
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ North America    │  │ Europe           │  │ Asia Pacific     │
│ Regional Cache   │  │ Regional Cache   │  │ Regional Cache   │
│                  │  │                  │  │                  │
│ Aggregates from: │  │ Aggregates from: │  │ Aggregates from: │
│ • NY Edge        │  │ • London Edge    │  │ • Tokyo Edge     │
│ • LA Edge        │  │ • Paris Edge     │  │ • Singapore Edge │
│ • Chicago Edge   │  │ • Frankfurt Edge │  │ • Mumbai Edge    │
│                  │  │                  │  │                  │
│ Hit: 70%         │  │ Hit: 72%         │  │ Hit: 68%         │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         │ If still miss (30%) │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ↓

LAYER 4: ORIGIN SHIELD (Optional)
┌──────────────────────────────────────────────────────────────┐
│                    ORIGIN SHIELD                             │
│                                                              │
│  • Protects origin from cache misses                         │
│  • Single point of contact for origin                        │
│  • Collapses duplicate requests                              │
│  • Further caching layer                                     │
│                                                              │
│  Example: 1000 edge misses → 1 origin request ✅            │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ Final miss (5-10%)
                           ↓

LAYER 5: ORIGIN SERVER
┌──────────────────────────────────────────────────────────────┐
│                    ORIGIN SERVER                             │
│                    (Your Application)                        │
│                                                              │
│  Location: US-East (Virginia)                                │
│                                                              │
│  Only serves:                                                │
│  • Cache misses (5-10% of traffic)                           │
│  • Dynamic content                                           │
│  • API requests                                              │
│                                                              │
│  Benefits:                                                   │
│  ✅ 90-95% less traffic                                      │
│  ✅ Lower bandwidth costs                                    │
│  ✅ Better performance                                       │
└──────────────────────────────────────────────────────────────┘


REQUEST FLOW EXAMPLE
────────────────────

User in Tokyo requests: cdn.example.com/image.jpg

Step 1: DNS Query
  User → DNS → "Tokyo edge server: 203.0.113.1"

Step 2: Request to Edge
  User → Tokyo Edge → Check cache

Step 3a: Cache HIT (90% of time)
  Tokyo Edge → Return image (20ms) ✅

Step 3b: Cache MISS (10% of time)
  Tokyo Edge → Regional Cache
    → Check cache
      → HIT? Return (50ms)
      → MISS? → Origin Shield → Origin
         → Return (200ms)
         → Cache at all levels
```

## 3. How CDN Caching Works

### Visual: Cache Lifecycle

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CDN CACHE LIFECYCLE                             │
└────────────────────────────────────────────────────────────────────────┘

FIRST REQUEST (CACHE MISS)
──────────────────────────

User 1 requests: /images/logo.png
     │
     ↓
┌─────────────────────────────────────┐
│  CDN Edge Server (London)           │
│                                     │
│  1. Check cache: logo.png           │
│     Result: NOT FOUND ❌            │
│                                     │
│  2. Request from origin             │
└────────┬────────────────────────────┘
         │
         │ GET /images/logo.png
         ↓
┌─────────────────────────────────────┐
│  Origin Server                      │
│                                     │
│  3. Serve file                      │
│     Size: 50KB                      │
│     Response Headers:               │
│     Cache-Control: max-age=86400    │
│     (cache for 24 hours)            │
└────────┬────────────────────────────┘
         │
         │ Return file + headers
         ↓
┌─────────────────────────────────────┐
│  CDN Edge Server                    │
│                                     │
│  4. Store in cache                  │
│     Key: /images/logo.png           │
│     Value: [file data]              │
│     TTL: 86400 seconds              │
│                                     │
│  5. Return to user                  │
│     Time: 200ms (slow) ❌           │
└─────────────────────────────────────┘


SUBSEQUENT REQUESTS (CACHE HIT)
────────────────────────────────

User 2,3,4... request: /images/logo.png
     │
     ↓
┌─────────────────────────────────────┐
│  CDN Edge Server (London)           │
│                                     │
│  1. Check cache: logo.png           │
│     Result: FOUND ✅                │
│                                     │
│  2. Return from cache               │
│     (No origin request!)            │
│     Time: 20ms (fast) ✅            │
└─────────────────────────────────────┘


CACHE EXPIRATION
────────────────

After 24 hours:

┌─────────────────────────────────────┐
│  CDN Edge Server                    │
│                                     │
│  Cache entry expired:               │
│  • Created: T0                      │
│  • TTL: 86400s (24 hours)           │
│  • Current: T0 + 86401s             │
│  • Status: EXPIRED ❌               │
│                                     │
│  Next request:                      │
│  → Cache miss                       │
│  → Fetch from origin again          │
│  → Re-cache                         │
└─────────────────────────────────────┘


CACHE HEADERS CONTROL
──────────────────────

Origin server response headers:

Example 1: Long cache (static assets)
Cache-Control: public, max-age=31536000, immutable
(Cache for 1 year, never revalidate)

Example 2: Short cache (dynamic content)
Cache-Control: public, max-age=300
(Cache for 5 minutes)

Example 3: No cache
Cache-Control: no-cache, no-store, must-revalidate
(Don't cache at all)

Example 4: Conditional cache
Cache-Control: max-age=3600
ETag: "abc123xyz"
(Cache for 1 hour, then revalidate with ETag)


CACHE INVALIDATION (PURGE)
───────────────────────────

When content changes, need to purge cache:

┌─────────────────────────────────────┐
│  Developer updates logo.png         │
└────────┬────────────────────────────┘
         │
         │ API call to CDN
         ↓
┌─────────────────────────────────────┐
│  CDN API                            │
│                                     │
│  POST /purge                        │
│  {                                  │
│    "files": ["/images/logo.png"]    │
│  }                                  │
└────────┬────────────────────────────┘
         │
         │ Broadcast purge
         ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│ NY Edge  │  │ London   │  │ Tokyo    │
│          │  │ Edge     │  │ Edge     │
│ DELETE   │  │ DELETE   │  │ DELETE   │
│ logo.png │  │ logo.png │  │ logo.png │
└──────────┘  └──────────┘  └──────────┘

All edges purged! ✅
Next request fetches fresh version.


CACHE HIT RATIO
───────────────

Ideal distribution:

┌────────────────────────────────────────┐
│  Total Requests: 1,000,000             │
│                                        │
│  Cache Hits: 900,000 (90%) ✅          │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                  │
│                                        │
│  Cache Misses: 100,000 (10%)           │
│  ▓▓                                    │
│                                        │
│  Origin Requests: 100,000 (10%)        │
│  ▓▓                                    │
└────────────────────────────────────────┘

Benefits:
• 90% requests served instantly from cache
• 90% reduction in origin traffic
• 90% reduction in bandwidth costs
• Much better performance
```

## 4. CDN Use Cases

### Visual: What to Cache vs Not Cache

```
┌────────────────────────────────────────────────────────────────────────┐
│                    WHAT TO CACHE IN CDN                                │
└────────────────────────────────────────────────────────────────────────┘

✅ PERFECT FOR CDN
──────────────────

1. STATIC ASSETS
┌─────────────────────────────────────┐
│  • Images (PNG, JPG, GIF, WebP)     │
│  • Videos (MP4, WebM)               │
│  • CSS files                        │
│  • JavaScript files                 │
│  • Fonts (WOFF, WOFF2, TTF)         │
│  • PDFs, documents                  │
│                                     │
│  Cache duration: 1 year             │
│  Immutable: Yes                     │
│  Compression: Yes                   │
└─────────────────────────────────────┘

Example:
https://cdn.example.com/static/logo-v2.png
└─ Version in filename = can cache forever


2. HTML PAGES (Static/Semi-Static)
┌─────────────────────────────────────┐
│  • Landing pages                    │
│  • Blog posts                       │
│  • Documentation                    │
│  • Marketing pages                  │
│                                     │
│  Cache duration: 5-60 minutes       │
│  Stale-while-revalidate: Yes        │
└─────────────────────────────────────┘


3. API RESPONSES (Read-Only)
┌─────────────────────────────────────┐
│  • Public data                      │
│  • Product catalogs                 │
│  • News feeds                       │
│  • Weather data                     │
│                                     │
│  Cache duration: 1-30 minutes       │
│  Conditional: Yes (ETag)            │
└─────────────────────────────────────┘


❌ NOT SUITABLE FOR CDN
───────────────────────

1. USER-SPECIFIC DATA
┌─────────────────────────────────────┐
│  • User profiles                    │
│  • Shopping carts                   │
│  • Private messages                 │
│  • Account settings                 │
│                                     │
│  Reason: Different per user         │
│  Solution: Don't cache OR           │
│           use signed URLs           │
└─────────────────────────────────────┘


2. DYNAMIC/FREQUENTLY CHANGING
┌─────────────────────────────────────┐
│  • Live sports scores               │
│  • Stock prices                     │
│  • Real-time chat                   │
│  • Live auction bids                │
│                                     │
│  Reason: Changes every second       │
│  Solution: WebSockets, SSE          │
└─────────────────────────────────────┘


3. SENSITIVE DATA
┌─────────────────────────────────────┐
│  • Payment information              │
│  • Passwords                        │
│  • Personal health records          │
│  • Banking transactions             │
│                                     │
│  Reason: Security risk              │
│  Solution: Never cache              │
└─────────────────────────────────────┘


SMART CACHING EXAMPLE
─────────────────────

Product Page Architecture:

┌────────────────────────────────────────────────────┐
│  Product Page: /products/laptop-xyz                │
├────────────────────────────────────────────────────┤
│                                                    │
│  ✅ Cached by CDN (Static):                        │
│  • HTML skeleton                                   │
│  • Product images                                  │
│  • CSS/JS files                                    │
│  • Product description (rarely changes)            │
│                                                    │
│  ❌ Not cached (Dynamic):                          │
│  • Current price (may change)                      │
│  • Inventory count (real-time)                     │
│  • User reviews (new reviews added)                │
│  • "Add to cart" status (user-specific)            │
│                                                    │
│  Strategy:                                         │
│  • CDN serves HTML skeleton (fast)                 │
│  • JavaScript fetches dynamic data (API)           │
│  • Best of both worlds!                            │
└────────────────────────────────────────────────────┘

Page Load:
1. CDN serves HTML (20ms) ✅
2. Browser renders skeleton
3. JavaScript fetches price/inventory (100ms)
4. Updates page dynamically

Result: Fast initial load + Fresh data!
```

## 5. CDN Pull vs Push

### Visual: Two Deployment Models

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PULL CDN (LAZY LOADING)                             │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT: CDN fetches content from origin on-demand (first request)

FLOW:
─────

Request 1 (Cache Miss):
User → CDN Edge → (Not in cache) → Origin → File → CDN → User
       Store in cache for next time

Request 2+ (Cache Hit):
User → CDN Edge → (Found in cache!) → User
       No origin request needed ✅


DETAILED FLOW:
──────────────

T0: User 1 requests /video.mp4
┌──────────┐       ┌──────────┐       ┌──────────┐
│  User 1  │ ────→ │ CDN Edge │ ────→ │  Origin  │
└──────────┘       │          │       │  Server  │
     ↑             │  MISS ❌ │       └────┬─────┘
     │             └────┬─────┘            │
     │                  │                  │
     │                  │ ←────────────────┘
     │                  │   video.mp4
     │                  │
     │                  │ Store in cache
     │                  │
     │ ←────────────────┘
     │   video.mp4 (slow: 2 seconds)


T1: User 2 requests same /video.mp4
┌──────────┐       ┌──────────┐
│  User 2  │ ────→ │ CDN Edge │
└──────────┘       │          │
     ↑             │  HIT ✅  │
     │             └────┬─────┘
     │                  │
     │ ←────────────────┘
     │   video.mp4 (fast: 50ms)


PROS & CONS:
────────────

✅ PROS:
• Easy setup (just point DNS to CDN)
• No manual file upload
• Automatic caching
• Only popular content cached
• Saves storage space

❌ CONS:
• First request slow (cache miss)
• Origin must be publicly accessible
• Bandwidth cost on first request


┌────────────────────────────────────────────────────────────────────────┐
│                    PUSH CDN (PRE-POPULATION)                           │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT: You upload files to CDN manually in advance

FLOW:
─────

Step 1: Deploy (One-time)
Developer → CDN API → Upload files → CDN stores globally

Step 2: User requests
User → CDN Edge → (Already in cache!) → User
       Fast from first request ✅


DETAILED FLOW:
──────────────

T0: Developer uploads files (before users access)
┌──────────┐       ┌──────────┐
│Developer │ ────→ │ CDN API  │
└──────────┘       └────┬─────┘
                        │
        Upload via API  │
        or Web UI       │
                        ↓
        ┌───────────────────────────────┐
        │  CDN distributes to all edges │
        └───┬─────────┬─────────┬───────┘
            ↓         ↓         ↓
        ┌───────┐ ┌───────┐ ┌───────┐
        │ NY    │ │ London│ │ Tokyo │
        │ Edge  │ │ Edge  │ │ Edge  │
        └───────┘ └───────┘ └───────┘

        All edges have content! ✅


T1: User 1 requests /video.mp4 (FIRST REQUEST)
┌──────────┐       ┌──────────┐
│  User 1  │ ────→ │ CDN Edge │
└──────────┘       │          │
     ↑             │  HIT ✅  │  ← Already cached!
     │             └────┬─────┘
     │                  │
     │ ←────────────────┘
     │   video.mp4 (fast: 50ms)

Even first request is fast! ✅


PROS & CONS:
────────────

✅ PROS:
• Fast from first request
• No cache miss
• Predictable performance
• Origin can be private
• Better for large files

❌ CONS:
• Manual upload required
• More setup complexity
• All files cached (uses more storage)
• Need deployment process
• Must track file versions


COMPARISON TABLE:
─────────────────

┌──────────────────┬─────────────┬──────────────┐
│   Feature        │    Pull     │    Push      │
├──────────────────┼─────────────┼──────────────┤
│ Setup            │ Easy        │ Complex      │
│ First request    │ Slow        │ Fast         │
│ Subsequent       │ Fast        │ Fast         │
│ Storage          │ Efficient   │ All files    │
│ Deployment       │ Automatic   │ Manual       │
│ Use case         │ Websites    │ Large files  │
│                  │ APIs        │ Videos       │
│                  │             │ Releases     │
└──────────────────┴─────────────┴──────────────┘


HYBRID APPROACH:
────────────────

Best of both worlds:

┌────────────────────────────────────────────────┐
│  • Push: Critical files (HTML, CSS, JS)        │
│    → Fast first load                           │
│                                                │
│  • Pull: Images, videos, user-generated        │
│    → Automatic caching                         │
└────────────────────────────────────────────────┘
```

## 6. Advanced CDN Features

### Visual: Modern CDN Capabilities

```
┌────────────────────────────────────────────────────────────────────────┐
│                    ADVANCED CDN FEATURES                               │
└────────────────────────────────────────────────────────────────────────┘

FEATURE 1: IMAGE OPTIMIZATION
──────────────────────────────

Original request:
GET /image.jpg

CDN automatically:
┌─────────────────────────────────────┐
│  1. Detects user's device           │
│     • Browser: Chrome                │
│     • Screen: Retina                 │
│     • Network: 4G                    │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  2. Optimizes image                 │
│     • Convert to WebP (smaller)      │
│     • Resize to screen size          │
│     • Compress quality: 85%          │
│     • Lazy load support              │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  3. Serve optimized version         │
│     Original: 2MB                   │
│     Optimized: 200KB ✅             │
│     10x smaller!                    │
└─────────────────────────────────────┘


FEATURE 2: EDGE COMPUTING (Serverless)
───────────────────────────────────────

Run code at the edge (near users):

┌─────────────────────────────────────┐
│  User request                       │
│  GET /api/user?id=123               │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  CDN Edge (London)                  │
│                                     │
│  Run edge function:                 │
│  • Authentication check             │
│  • Rate limiting                    │
│  • A/B testing                      │
│  • Personalization                  │
│  • Response modification            │
│                                     │
│  No origin trip needed! ✅          │
└─────────────────────────────────────┘

Benefits:
• Ultra-low latency (5-10ms)
• Reduced origin load
• Better user experience

Use cases:
• Auth at edge
• URL rewrites
• Geolocation-based content
• Bot detection


FEATURE 3: HTTP/2 & HTTP/3
───────────────────────────

Old HTTP/1.1:
┌────────────────────────────┐
│  Request 1: HTML           │ ──→ Wait
│  Request 2: CSS            │ ──→ Wait
│  Request 3: JS             │ ──→ Wait
│  Request 4: Image          │ ──→ Wait
│                            │
│  Serial (one at a time) ❌ │
└────────────────────────────┘

Modern HTTP/2:
┌────────────────────────────┐
│  Request 1: HTML     ─┐    │
│  Request 2: CSS      ─┤    │
│  Request 3: JS       ─┼──→ All parallel
│  Request 4: Image    ─┘    │
│                            │
│  Multiplexing ✅           │
│  Much faster!              │
└────────────────────────────┘


FEATURE 4: DDoS PROTECTION
──────────────────────────

Attack scenario:
┌────────────────────────────┐
│  1 million bots             │
│  All attack website         │
└────┬───────────────────────┘
     │
     │ 1M requests/sec
     ↓
┌────────────────────────────┐
│  CDN Edge                  │
│                            │
│  Detects attack:           │
│  • Unusual traffic pattern │
│  • Same IP ranges          │
│  • Bot signatures          │
│                            │
│  Actions:                  │
│  • Rate limit              │
│  • Challenge (CAPTCHA)     │
│  • Block malicious IPs     │
│  • Serve from cache        │
│                            │
│  Origin protected! ✅      │
└────────────────────────────┘

Origin server:
• Normal traffic only
• No attack traffic
• Still accessible


FEATURE 5: SSL/TLS TERMINATION
───────────────────────────────

Without CDN:
User ──HTTPS──→ Origin (CPU intensive)

With CDN:
User ──HTTPS──→ CDN Edge (handles SSL)
CDN Edge ──HTTP──→ Origin (or HTTPS)

Benefits:
• Faster (edge closer to user)
• Offload SSL processing
• Managed certificates
• Automatic renewal


FEATURE 6: ANALYTICS
────────────────────

CDN provides detailed metrics:

┌────────────────────────────────────────┐
│  CDN Dashboard                         │
├────────────────────────────────────────┤
│                                        │
│  Traffic by Location:                  │
│  • USA: 45%  ████████████████████      │
│  • Europe: 30%  ████████████           │
│  • Asia: 20%  ████████                 │
│  • Other: 5%  ██                       │
│                                        │
│  Cache Performance:                    │
│  • Hit ratio: 92% ✅                   │
│  • Bandwidth saved: 2.5 TB             │
│  • Origin requests: 8%                 │
│                                        │
│  Top Files:                            │
│  • /image.jpg: 50K requests            │
│  • /video.mp4: 30K requests            │
│  • /style.css: 25K requests            │
│                                        │
│  Performance:                          │
│  • Avg latency: 45ms                   │
│  • P95 latency: 120ms                  │
│  • P99 latency: 250ms                  │
└────────────────────────────────────────┘
```

## 7. Popular CDN Providers

### Visual: CDN Provider Comparison

```
┌────────────────────────────────────────────────────────────────────────┐
│                    CDN PROVIDER COMPARISON                             │
└────────────────────────────────────────────────────────────────────────┘

CLOUDFLARE
──────────
┌─────────────────────────────────────┐
│  • POPs: 300+ cities                │
│  • Free tier: Yes ✅                │
│  • Edge computing: Yes              │
│  • DDoS protection: Excellent       │
│  • Features: Rich                   │
│  • Pricing: Affordable              │
│                                     │
│  Best for:                          │
│  • Small to large websites          │
│  • DDoS protection                  │
│  • Edge functions                   │
└─────────────────────────────────────┘

AWS CLOUDFRONT
──────────────
┌─────────────────────────────────────┐
│  • POPs: 400+ locations             │
│  • Free tier: 1TB/month             │
│  • Integration: AWS ecosystem       │
│  • Edge computing: Lambda@Edge      │
│  • Features: Comprehensive          │
│  • Pricing: Pay-as-you-go           │
│                                     │
│  Best for:                          │
│  • AWS customers                    │
│  • Enterprise applications          │
│  • Video streaming                  │
└─────────────────────────────────────┘

FASTLY
──────
┌─────────────────────────────────────┐
│  • POPs: 70+ locations              │
│  • Real-time purging: < 150ms       │
│  • Edge computing: Compute@Edge     │
│  • Configuration: VCL (programmable)│
│  • Features: Developer-friendly     │
│  • Pricing: Premium                 │
│                                     │
│  Best for:                          │
│  • High-traffic websites            │
│  • Media companies                  │
│  • Real-time applications           │
└─────────────────────────────────────┘

AKAMAI
──────
┌─────────────────────────────────────┐
│  • POPs: 4,100+ locations           │
│  • Market leader (oldest)           │
│  • Features: Enterprise-grade       │
│  • Scale: Massive                   │
│  • Pricing: Enterprise              │
│                                     │
│  Best for:                          │
│  • Large enterprises                │
│  • Mission-critical apps            │
│  • High security needs              │
└─────────────────────────────────────┘

GOOGLE CLOUD CDN
────────────────
┌─────────────────────────────────────┐
│  • POPs: 100+ locations             │
│  • Integration: Google Cloud        │
│  • Network: Google's backbone       │
│  • Features: Good                   │
│  • Pricing: Competitive             │
│                                     │
│  Best for:                          │
│  • Google Cloud users               │
│  • YouTube-like applications        │
│  • Global reach                     │
└─────────────────────────────────────┘


COST COMPARISON (Example)
──────────────────────────

Traffic: 10TB/month, Global

┌──────────────┬───────────────┐
│  Provider    │  Cost/month   │
├──────────────┼───────────────┤
│  Cloudflare  │  $200-500     │
│  AWS          │  $850         │
│  Fastly      │  $1,200       │
│  Akamai      │  $2,000+      │
│  Google      │  $800         │
└──────────────┴───────────────┘

Note: Prices vary by region and features
```

## 8. System Design Interview Answer

### Short Answer (3-4 minutes):

> **CDN (Content Delivery Network)** is a geographically distributed network of servers that caches and delivers content from locations nearest to users, reducing latency from 200ms to 20ms (10x improvement).
>
> **Architecture** consists of multiple layers:
> 1. **DNS routing (GeoDNS)**: Directs users to nearest edge server
> 2. **Edge servers (PoPs)**: Cache content at 200-400+ global locations
> 3. **Regional caches**: Mid-tier aggregation layer
> 4. **Origin shield**: Optional layer to protect origin from cache misses
> 5. **Origin server**: Your application (serves 5-10% of traffic)
>
> **CDN caching** works through:
> - **Pull model**: CDN fetches from origin on first request (cache miss), subsequent requests served from cache (90%+ hit rate)
> - **Push model**: Files pre-uploaded to CDN, all requests fast from start
> - **Cache headers**: `Cache-Control: max-age=3600` tells CDN how long to cache
> - **TTL**: Auto-expiration after specified time
> - **Purge/Invalidation**: API to clear cache when content changes
>
> **What to cache**:
> - ✅ Static assets (images, CSS, JS, videos) - cache for 1 year
> - ✅ HTML pages - cache for 5-60 minutes with revalidation
> - ✅ Public API responses - cache for 1-30 minutes
> - ❌ User-specific data, frequently changing data, sensitive data
>
> **Advanced features**:
> - Image optimization (auto-resize, format conversion, compression)
> - Edge computing (serverless functions at edge)
> - HTTP/2 & HTTP/3 support
> - DDoS protection
> - SSL/TLS termination
> - Real-time analytics
>
> **Benefits**: 90% reduction in origin traffic, 10x faster delivery, lower bandwidth costs, better SEO, DDoS protection, and ability to handle traffic spikes.
>
> **Popular providers**: Cloudflare (affordable, DDoS protection), AWS CloudFront (AWS integration), Fastly (real-time purging), Akamai (enterprise), Google Cloud CDN.

---

## Key Technologies:
- **Cloudflare**: Most popular, generous free tier
- **AWS CloudFront**: Best AWS integration
- **Fastly**: Real-time purging, programmable
- **Akamai**: Enterprise leader
- **HTTP/2 & HTTP/3**: Modern protocols for faster delivery
- **WebP**: Modern image format (smaller, faster)
