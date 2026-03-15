# Advanced Rate Limiting - Multi-IP Attack Protection

## Table of Contents
1. [Understanding Rate Limiting Attacks](#understanding-rate-limiting-attacks)
2. [How Attackers Bypass Basic Rate Limiting](#how-attackers-bypass-basic-rate-limiting)
3. [Detection Strategies](#detection-strategies)
4. [Prevention Techniques](#prevention-techniques)
5. [Distributed Rate Limiting with Redis](#distributed-rate-limiting-with-redis)
6. [Production Code Examples](#production-code-examples)
7. [Interview Questions & Answers](#interview-questions--answers)

---

## Understanding Rate Limiting Attacks

Rate limiting controls how many requests a client can make in a time window. Attackers try to bypass these limits to abuse services.

### Basic Rate Limiting (Easily Bypassed)

```
Simple IP-Based Rate Limiting:
┌────────────────────────────────────────────────────────┐
│ Rule: Maximum 100 requests per minute per IP          │
└────────────────────────────────────────────────────────┘

Normal User:
┌──────────────┐
│ User (1 IP)  │  → 50 requests/min → ✓ Allowed
└──────────────┘

Attacker (Single IP):
┌──────────────┐
│ Attacker     │  → 150 requests/min → ✗ Blocked at 100
└──────────────┘
     ▼
  BLOCKED
```

### Multi-IP Attack (Bypasses Basic Limit)

```
Distributed Attack:
┌────────────────────────────────────────────────────────┐
│ Attacker uses multiple IPs to bypass rate limit       │
└────────────────────────────────────────────────────────┘

┌───────────────┐
│   Attacker    │
│  Bot Network  │
└───────┬───────┘
        │
        ├──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ IP: .1  │   │ IP: .2  │   │ IP: .3  │   │ IP: .4  │
   │ 99 req  │   │ 99 req  │   │ 99 req  │   │ 99 req  │
   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Server    │
                    │ Sees 396    │
                    │ requests    │
                    │ from "4 IPs"│
                    │ Each under  │
                    │ limit ✓     │
                    └─────────────┘

Result: Attack succeeds because each IP stays under limit!
```

### Attack Sources

```
┌─────────────────────────────────────────────────────────┐
│         Common Multi-IP Attack Sources                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. Botnets                                             │
│    ┌─────────────────────────────────────┐            │
│    │ Infected devices worldwide          │            │
│    │ • Compromised PCs                   │            │
│    │ • Hacked IoT devices                │            │
│    │ • Malware-infected phones           │            │
│    └─────────────────────────────────────┘            │
│                                                         │
│ 2. Cloud Instances                                     │
│    ┌─────────────────────────────────────┐            │
│    │ Rented/stolen cloud resources       │            │
│    │ • AWS EC2 instances                 │            │
│    │ • Azure VMs                         │            │
│    │ • GCP Compute Engine                │            │
│    └─────────────────────────────────────┘            │
│                                                         │
│ 3. Proxy Networks                                      │
│    ┌─────────────────────────────────────┐            │
│    │ Rotating proxy services             │            │
│    │ • Residential proxies               │            │
│    │ • Data center proxies               │            │
│    │ • Mobile proxies (4G/5G)            │            │
│    └─────────────────────────────────────┘            │
│                                                         │
│ 4. VPN Services                                        │
│    ┌─────────────────────────────────────┐            │
│    │ IP address rotation                 │            │
│    │ • Commercial VPN providers          │            │
│    │ • Anonymous VPNs                    │            │
│    │ • Tor exit nodes                    │            │
│    └─────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

---

## How Attackers Bypass Basic Rate Limiting

### Attack Pattern Analysis

```
Timeline of Multi-IP Attack:
════════════════════════════════════════════════════════════

Time: 0s        10s       20s       30s       40s       50s
      │         │         │         │         │         │

IP 1: ████████████████████████████████████████████████████
      (100 requests spread over 60 seconds)

IP 2:     ████████████████████████████████████████████████
          (100 requests, slightly offset)

IP 3:         ████████████████████████████████████████████
              (100 requests, slightly offset)

IP 4:             ████████████████████████████████████████
                  (100 requests, slightly offset)

═══════════════════════════════════════════════════════════

Server's View:
┌──────────────────────────────────────────────────────┐
│ IP 1: 100 req/min → ✓ Under limit                   │
│ IP 2: 100 req/min → ✓ Under limit                   │
│ IP 3: 100 req/min → ✓ Under limit                   │
│ IP 4: 100 req/min → ✓ Under limit                   │
│                                                      │
│ TOTAL: 400 requests/min → Attack succeeds!          │
└──────────────────────────────────────────────────────┘
```

### Attack Techniques

```
┌─────────────────────────────────────────────────────────┐
│         Sophisticated Bypass Techniques                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. IP Rotation (Most Common)                           │
│    ┌──────────────────────────────────┐               │
│    │ Request 1:   IP 192.168.1.1      │               │
│    │ Request 2:   IP 192.168.1.2      │               │
│    │ Request 3:   IP 192.168.1.3      │               │
│    │ ...cycle through 1000 IPs        │               │
│    └──────────────────────────────────┘               │
│                                                         │
│ 2. Distributed Timing                                  │
│    ┌──────────────────────────────────┐               │
│    │ Spread requests across time      │               │
│    │ Each IP: 1 req/second            │               │
│    │ 100 IPs: 100 req/second total    │               │
│    │ No single IP exceeds limit       │               │
│    └──────────────────────────────────┘               │
│                                                         │
│ 3. Session Manipulation                                │
│    ┌──────────────────────────────────┐               │
│    │ New session per IP               │               │
│    │ Clear cookies between requests   │               │
│    │ Randomize User-Agent             │               │
│    │ Change browser fingerprint       │               │
│    └──────────────────────────────────┘               │
│                                                         │
│ 4. API Key Farming                                     │
│    ┌──────────────────────────────────┐               │
│    │ Create multiple accounts         │               │
│    │ Each account: unique API key     │               │
│    │ Rotate keys across requests      │               │
│    │ Each key under its limit         │               │
│    └──────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

### Attack Visualization

```
Basic Rate Limiter (FAILS against multi-IP):
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌─────────┐                                       │
│  │  Check  │  if (requestCount[ip] > limit)        │
│  │  IP     │      reject()                         │
│  │  Only   │                                       │
│  └─────────┘                                       │
│                                                     │
│  Problem: Doesn't detect coordinated attack        │
│  from multiple IPs targeting same resource         │
└─────────────────────────────────────────────────────┘

Advanced Rate Limiter (DETECTS multi-IP):
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌─────────┐   ┌────────────┐   ┌──────────────┐  │
│  │  Check  │   │  Analyze   │   │  Detect      │  │
│  │  IP     │ + │  Behavior  │ + │  Patterns    │  │
│  │  Limit  │   │  Profile   │   │  Anomalies   │  │
│  └─────────┘   └────────────┘   └──────────────┘  │
│       │              │                  │          │
│       └──────────────┴──────────────────┘          │
│                      │                             │
│              ┌───────▼────────┐                    │
│              │  Fingerprint   │                    │
│              │  Real Identity │                    │
│              └────────────────┘                    │
└─────────────────────────────────────────────────────┘
```

---

## Detection Strategies

### 1. Device Fingerprinting

Identify unique devices beyond IP addresses.

```
┌─────────────────────────────────────────────────────────┐
│           Device Fingerprint Components                 │
└─────────────────────────────────────────────────────────┘

Browser Fingerprint:
┌──────────────────────────────────────────┐
│ User-Agent:    Chrome/122.0.6261.112     │
│ Screen:        1920x1080                 │
│ Timezone:      -08:00 (PST)              │
│ Language:      en-US                     │
│ Platform:      MacIntel                  │
│ Plugins:       [PDF, Chrome PDF]         │
│ Canvas Hash:   a8f3d92b...               │
│ WebGL Hash:    7c2e4f1a...               │
│ Fonts:         [Arial, Times, ...]       │
│ Audio Context: 124.0434...               │
└──────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│ Generate Fingerprint Hash                │
│ fingerprint = SHA256(                    │
│   userAgent +                            │
│   screen +                               │
│   timezone +                             │
│   canvas +                               │
│   webgl +                                │
│   fonts                                  │
│ )                                        │
│                                          │
│ = "f8e2d9a1c4b7e3f5..."                 │
└──────────────────────────────────────────┘

Detection:
┌────────────────────────────────────────────────┐
│ Same fingerprint from multiple IPs?           │
│                                                │
│ IP 1 (192.168.1.1) → fingerprint: f8e2d9a1   │
│ IP 2 (192.168.1.2) → fingerprint: f8e2d9a1   │
│ IP 3 (192.168.1.3) → fingerprint: f8e2d9a1   │
│                                                │
│ → ATTACK DETECTED! Same device using         │
│   different IPs (proxy/VPN rotation)          │
└────────────────────────────────────────────────┘
```

### 2. Behavioral Analysis

Detect abnormal request patterns.

```
┌─────────────────────────────────────────────────────────┐
│             Behavioral Pattern Analysis                 │
└─────────────────────────────────────────────────────────┘

Normal User Behavior:
Time:  0s    10s   20s   30s   40s   50s   60s
       │     │     │     │     │     │     │
Req:   ●           ●       ●           ●
       │<--pause-->│<-pause->│<--pause-->│

Characteristics:
- Variable intervals
- Human-like pauses
- Mixed endpoints
- Session continuity

Bot/Attack Behavior:
Time:  0s    10s   20s   30s   40s   50s   60s
       │     │     │     │     │     │     │
Req:   ●●●●● ●●●●● ●●●●● ●●●●● ●●●●● ●●●●● ●●●●●
       │(constant high rate)                    │

Characteristics:
- Perfect timing (e.g., exactly 1 req/sec)
- No pauses
- Same endpoint repeatedly
- No session context

┌──────────────────────────────────────────────────────┐
│            Behavioral Signals (Red Flags)            │
├──────────────────────────────────────────────────────┤
│                                                      │
│ ✗ Request rate too consistent (bot-like)            │
│ ✗ No JavaScript execution (headless browser)        │
│ ✗ Missing referrer headers                          │
│ ✗ Suspicious User-Agent (automated tools)           │
│ ✗ No mouse movements (not human)                    │
│ ✗ Keyboard patterns too fast                        │
│ ✗ Linear navigation (no browsing)                   │
│ ✗ API calls only (no page loads)                    │
└──────────────────────────────────────────────────────┘
```

### 3. Clustering Analysis

Group related requests to detect coordinated attacks.

```
┌─────────────────────────────────────────────────────────┐
│          Request Clustering Detection                   │
└─────────────────────────────────────────────────────────┘

Scenario: 100 different IPs attacking same endpoint

Step 1: Track requests by endpoint
┌─────────────────────────────────────────┐
│ Endpoint: /api/expensive-operation      │
│                                         │
│ Last minute:                            │
│ - IP 1.1.1.1    → 5 requests           │
│ - IP 2.2.2.2    → 4 requests           │
│ - IP 3.3.3.3    → 6 requests           │
│ - IP 4.4.4.4    → 5 requests           │
│ ... (96 more IPs)                       │
│                                         │
│ Total: 500 requests from 100 IPs       │
└─────────────────────────────────────────┘

Step 2: Calculate cluster score
┌─────────────────────────────────────────┐
│ Cluster Detection:                      │
│                                         │
│ uniqueIPs = 100                        │
│ totalRequests = 500                    │
│ avgPerIP = 5                           │
│                                         │
│ Normal: 1-2 IPs with high volume      │
│ Attack: 100 IPs with similar volume   │
│                                         │
│ Score = uniqueIPs * avgPerIP           │
│       = 100 * 5 = 500                  │
│                                         │
│ Threshold: 100                         │
│ Result: 500 > 100 → ATTACK!           │
└─────────────────────────────────────────┘

Visual Representation:
Normal Traffic:
●●●●●●●●●● (10 IPs, varied rates)
    │
    Most from 1-2 IPs

Attack Traffic:
● ● ● ● ● ● ● ● ● ● ... (100 IPs)
│ │ │ │ │ │ │ │ │ │
└─┴─┴─┴─┴─┴─┴─┴─┴─┴─── All similar rates
                       (coordinated!)
```

### 4. IP Reputation Scoring

Use historical data to identify malicious IPs.

```
┌─────────────────────────────────────────────────────────┐
│              IP Reputation System                       │
└─────────────────────────────────────────────────────────┘

Reputation Score (0-100):
┌─────────────────────────────────────────┐
│ 90-100: Trusted (known good IPs)        │
│ 70-89:  Normal (regular traffic)        │
│ 40-69:  Suspicious (watch closely)      │
│ 0-39:   Malicious (block/challenge)     │
└─────────────────────────────────────────┘

Scoring Factors:
┌─────────────────────────────────────────────────────┐
│ Factor                    | Impact on Score          │
├─────────────────────────────────────────────────────┤
│ Known datacenter IP       | -20 points              │
│ Known proxy service       | -15 points              │
│ High request rate         | -10 points              │
│ Failed auth attempts      | -5 points per fail      │
│ CAPTCHA failures          | -3 points per fail      │
│ Rate limit violations     | -10 points              │
│ Successful transactions   | +2 points               │
│ Long session duration     | +5 points               │
│ Geographic consistency    | +3 points               │
│ Consistent fingerprint    | +5 points               │
└─────────────────────────────────────────────────────┘

Example Calculation:
┌──────────────────────────────────────────┐
│ IP: 192.168.1.100                        │
│                                          │
│ Starting score:         70               │
│ + Successful txn (×3):  +6               │
│ + Long session:         +5               │
│ - Rate limit hit:       -10              │
│ - Known proxy:          -15              │
│                         ───              │
│ Final score:            56 (Suspicious)  │
│                                          │
│ Action: Require CAPTCHA                  │
└──────────────────────────────────────────┘

Reputation Database:
┌────────────────────────────────────────────────┐
│ IP              | Score | Last Seen | Status   │
├────────────────────────────────────────────────┤
│ 1.2.3.4        | 92    | 1m ago    | Trusted  │
│ 5.6.7.8        | 75    | 5m ago    | Normal   │
│ 192.168.1.100  | 56    | now       | Watch    │
│ 10.0.0.50      | 15    | now       | Block    │
└────────────────────────────────────────────────┘
```

---

## Prevention Techniques

### 1. Multi-Dimensional Rate Limiting

Rate limit on multiple dimensions simultaneously.

```
┌─────────────────────────────────────────────────────────┐
│        Multi-Dimensional Rate Limiting                  │
└─────────────────────────────────────────────────────────┘

Traditional (Single Dimension):
┌──────────────────┐
│ Limit by IP only │ ← Easily bypassed with multiple IPs
└──────────────────┘

Advanced (Multi-Dimensional):
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Dimension 1: IP Address                           │
│  └─ Max 100 req/min per IP                         │
│                                                     │
│  Dimension 2: User ID (authenticated)              │
│  └─ Max 200 req/min per user                       │
│                                                     │
│  Dimension 3: Device Fingerprint                   │
│  └─ Max 150 req/min per device                     │
│                                                     │
│  Dimension 4: API Endpoint                         │
│  └─ Max 1000 req/min total per endpoint            │
│                                                     │
│  Dimension 5: Geographic Region                    │
│  └─ Max 5000 req/min per country                   │
│                                                     │
│  Dimension 6: Session ID                           │
│  └─ Max 50 req/min per session                     │
│                                                     │
└─────────────────────────────────────────────────────┘

Request Processing:
┌──────────────────────────────────────────────────────┐
│ Incoming Request                                     │
│ IP: 1.2.3.4                                         │
│ User: user_123                                      │
│ Fingerprint: abc123                                 │
│ Endpoint: /api/search                               │
│ Country: US                                         │
│ Session: sess_xyz                                   │
└───────────────────────┬──────────────────────────────┘
                        ▼
        ┌───────────────────────────────┐
        │   Check ALL Dimensions:       │
        ├───────────────────────────────┤
        │ ✓ IP limit:          45/100   │
        │ ✓ User limit:        120/200  │
        │ ✓ Fingerprint:       80/150   │
        │ ✗ Endpoint limit:    1001/1000│ ← REJECT!
        │ ✓ Country limit:     3200/5000│
        │ ✓ Session limit:     25/50    │
        └───────────────────────────────┘
                        │
                        ▼
            [Request Rejected: Endpoint limit exceeded]

Attack Prevention:
Attacker uses 100 different IPs → ✓ Each IP under limit
BUT endpoint dimension catches total volume → ✗ BLOCKED!
```

### 2. Token Bucket Algorithm

Smooth rate limiting with burst allowance.

```
┌─────────────────────────────────────────────────────────┐
│            Token Bucket Algorithm                       │
└─────────────────────────────────────────────────────────┘

Concept:
┌─────────────────────────────────┐
│         Token Bucket            │
│                                 │
│   Capacity: 100 tokens          │
│   Refill:   10 tokens/second    │
│                                 │
│   ┌─────────────────────┐       │
│   │ ●●●●●●●●●●●●●●●●●●  │       │
│   │ ●●●●●●●●●●  (30)    │       │
│   └─────────────────────┘       │
│                                 │
│   Each request = 1 token        │
└─────────────────────────────────┘

Timeline:
Time:    0s      1s      2s      3s      4s      5s
         │       │       │       │       │       │
Tokens:  100     90      100     85      95      100
         │       │       │       │       │       │
Events:  │       │       │       │       │       │
         │       ├─10 req├─refill├─15 req├─refill│
         │       │       │+10    │       │       │
         │       │       │       │       │       │
         │       90 left 100     85 left 95      100

Burst Handling:
┌────────────────────────────────────────────────┐
│ Scenario: User inactive for 10 seconds        │
│                                                │
│ Bucket refills to max: 100 tokens             │
│ User sends 50 requests at once                 │
│ Result: ✓ Allowed (burst within capacity)     │
│ Remaining: 50 tokens                           │
│                                                │
│ User sends another 60 requests immediately     │
│ Result: 50 allowed, 10 rejected               │
└────────────────────────────────────────────────┘

State in Redis:
┌────────────────────────────────────────────┐
│ Key: "bucket:192.168.1.1"                  │
│ Value: {                                   │
│   "tokens": 65,                           │
│   "lastRefill": 1710507600000,            │
│   "capacity": 100,                        │
│   "refillRate": 10                        │
│ }                                          │
└────────────────────────────────────────────┘
```

### 3. Sliding Window Log

Precise request tracking with rolling time window.

```
┌─────────────────────────────────────────────────────────┐
│           Sliding Window Log Algorithm                  │
└─────────────────────────────────────────────────────────┘

Fixed Window (Problem):
│<────── 1 minute ──────>│<────── 1 minute ──────>│
│                        │                        │
├────────────────────────┼────────────────────────┤
│    Window 1            │     Window 2           │
│                        │                        │
│                   100 req│100 req                │
│                        ●│●                       │
        12:00:59 ────────^│^──── 12:01:01
                          │
    200 requests in 2 seconds!
    But each window sees only 100 → Both allowed ✗

Sliding Window (Solution):
┌────────────────────────────────────────────────────┐
│      Request Log (Timestamps)                      │
├────────────────────────────────────────────────────┤
│ [12:00:05.123, 12:00:12.456, 12:00:18.789, ...]  │
└────────────────────────────────────────────────────┘

Current time: 12:00:45.000
Look back: 60 seconds
Window: 11:59:45.000 to 12:00:45.000

┌────────────────────────────────────────────────────┐
│        Sliding Window (Always 60 seconds)          │
└────────────────────────────────────────────────────┘

Time: 11:59:00    11:59:30    12:00:00    12:00:30    12:01:00
      │           │           │           │           │
      │           │           │           │           │
      │<──────────── 60 sec window ────────────>│
      │           │           │           │     ▲     │
      │           │           │           │     │     │
                                        Current time

At 12:00:30:
- Count requests from 11:59:30 to 12:00:30
- Remove older timestamps
- Check against limit

Redis Structure:
┌────────────────────────────────────────────────┐
│ Key: "requests:192.168.1.1"                    │
│ Type: Sorted Set                               │
│ Score: Timestamp                               │
│ Value: Request ID                              │
├────────────────────────────────────────────────┤
│ 1710507600123: "req_1"                         │
│ 1710507605456: "req_2"                         │
│ 1710507612789: "req_3"                         │
│ ...                                            │
└────────────────────────────────────────────────┘

Algorithm:
1. Add current request: ZADD key timestamp requestId
2. Remove old entries: ZREMRANGEBYSCORE key 0 (now - 60sec)
3. Count in window: ZCARD key
4. If count > limit → REJECT
```

### 4. CAPTCHA Challenge

Challenge suspicious traffic.

```
┌─────────────────────────────────────────────────────────┐
│          Progressive CAPTCHA Challenge                  │
└─────────────────────────────────────────────────────────┘

Decision Tree:
┌──────────────────────────────────────────────────────┐
│                  Incoming Request                    │
└────────────────────┬─────────────────────────────────┘
                     │
         ┌───────────▼──────────┐
         │ Check Reputation     │
         └───────────┬──────────┘
                     │
         ┌───────────┴──────────┐
         │                      │
    Score > 70              Score ≤ 70
    (Trusted)               (Suspicious)
         │                      │
         ▼                      ▼
   ┌──────────┐          ┌─────────────┐
   │  Allow   │          │ Check Rate  │
   │ Directly │          └──────┬──────┘
   └──────────┘                 │
                     ┌──────────┴─────────┐
                     │                    │
                Under limit           Over limit
                     │                    │
                     ▼                    ▼
              ┌──────────┐         ┌──────────────┐
              │  Allow   │         │ CAPTCHA      │
              │          │         │ Challenge    │
              └──────────┘         └──────┬───────┘
                                          │
                                ┌─────────┴────────┐
                                │                  │
                          Pass CAPTCHA        Fail CAPTCHA
                                │                  │
                                ▼                  ▼
                          ┌──────────┐       ┌─────────┐
                          │  Allow   │       │  Block  │
                          │ +10 rep  │       │ -20 rep │
                          └──────────┘       └─────────┘

CAPTCHA Levels:
┌─────────────────────────────────────────────────┐
│ Level 1: Checkbox ("I'm not a robot")          │
│          Simple, user-friendly                  │
│          Score 40-60                           │
│                                                 │
│ Level 2: Image selection                       │
│          Medium difficulty                      │
│          Score 20-40                           │
│                                                 │
│ Level 3: Complex puzzle                        │
│          High difficulty                        │
│          Score 0-20                            │
└─────────────────────────────────────────────────┘
```

### 5. WAF (Web Application Firewall)

Deploy intelligent traffic filtering.

```
┌─────────────────────────────────────────────────────────┐
│      WAF Architecture for Rate Limit Protection         │
└─────────────────────────────────────────────────────────┘

Traffic Flow:
┌──────────┐
│ Internet │
└─────┬────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│                     WAF Layer                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐               │
│  │ IP Reputation│  │ Geo-blocking │               │
│  │   Check      │  │   Check      │               │
│  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                        │
│         └────────┬────────┘                        │
│                  ▼                                  │
│         ┌─────────────────┐                        │
│         │  Pattern Match  │                        │
│         │  - Bot signatures│                       │
│         │  - Known attacks │                       │
│         └────────┬─────────┘                       │
│                  │                                  │
│                  ▼                                  │
│         ┌─────────────────┐                        │
│         │ Rate Limiting   │                        │
│         │ - Per IP        │                        │
│         │ - Per endpoint  │                        │
│         │ - Global        │                        │
│         └────────┬─────────┘                       │
│                  │                                  │
└──────────────────┼─────────────────────────────────┘
                   │
            ┌──────┴──────┐
            │    Allow    │
            │   or Block  │
            └──────┬──────┘
                   │
                   ▼
         ┌──────────────────┐
         │  Backend Servers │
         └──────────────────┘

WAF Rules Example:
┌────────────────────────────────────────────────────┐
│ Rule 1: Block known bot User-Agents               │
│   if userAgent matches /bot|crawler|scraper/i     │
│   then BLOCK                                       │
│                                                    │
│ Rule 2: Challenge datacenter IPs                  │
│   if IP in datacenterRanges                       │
│   then CAPTCHA                                     │
│                                                    │
│ Rule 3: Limit login attempts                      │
│   if endpoint == "/api/login"                     │
│   and requestsPerIP > 5/minute                    │
│   then BLOCK for 15 minutes                       │
│                                                    │
│ Rule 4: Detect distributed attacks                │
│   if uniqueIPs > 50                               │
│   and targetEndpoint == same                      │
│   and timeWindow < 1 minute                       │
│   then ALERT + CHALLENGE_ALL                      │
└────────────────────────────────────────────────────┘
```

---

## Distributed Rate Limiting with Redis

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│      Distributed Rate Limiting Architecture             │
└─────────────────────────────────────────────────────────┘

┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Client 1 │   │ Client 2 │   │ Client 3 │   │ Client 4 │
└─────┬────┘   └─────┬────┘   └─────┬────┘   └─────┬────┘
      │              │              │              │
      └──────────────┴──────────────┴──────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    Load Balancer       │
              └────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Server 1   │   │   Server 2   │   │   Server 3   │
│              │   │              │   │              │
│ Rate Limiter │   │ Rate Limiter │   │ Rate Limiter │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   Redis Cluster        │
              │  (Shared Rate Limit    │
              │   State)               │
              ├────────────────────────┤
              │ Key: "limit:IP"        │
              │ Value: request_count   │
              │ TTL: window_duration   │
              └────────────────────────┘

Why Redis?
┌────────────────────────────────────────────────┐
│ ✓ Atomic operations (INCR, ZADD)              │
│ ✓ Automatic expiry (TTL)                      │
│ ✓ High performance (in-memory)                │
│ ✓ Shared state across all servers             │
│ ✓ Built-in data structures (Sorted Sets)      │
│ ✓ Lua scripts for complex operations          │
└────────────────────────────────────────────────┘
```

### Redis Data Structures

```
┌─────────────────────────────────────────────────────────┐
│         Redis Data Structures for Rate Limiting         │
└─────────────────────────────────────────────────────────┘

1. Simple Counter (Fixed Window):
┌────────────────────────────────────────────┐
│ Key: "rate:192.168.1.1:2026-03-15-14:30"   │
│ Type: String                               │
│ Value: "45"  (request count)               │
│ TTL: 60 seconds                            │
│                                            │
│ Commands:                                  │
│ INCR rate:192.168.1.1:2026-03-15-14:30    │
│ EXPIRE rate:192.168.1.1:2026-03-15-14:30  │
└────────────────────────────────────────────┘

2. Sorted Set (Sliding Window):
┌────────────────────────────────────────────┐
│ Key: "requests:192.168.1.1"                │
│ Type: Sorted Set (ZSET)                    │
│                                            │
│ Score (timestamp) : Member (request ID)    │
│ ─────────────────────────────────────────  │
│ 1710507600123     : "req_001"              │
│ 1710507605456     : "req_002"              │
│ 1710507612789     : "req_003"              │
│ 1710507618234     : "req_004"              │
│                                            │
│ Commands:                                  │
│ ZADD requests:IP timestamp requestId       │
│ ZREMRANGEBYSCORE requests:IP 0 oldTime     │
│ ZCARD requests:IP                          │
└────────────────────────────────────────────┘

3. Hash (Token Bucket):
┌────────────────────────────────────────────┐
│ Key: "bucket:192.168.1.1"                  │
│ Type: Hash                                 │
│                                            │
│ Field         : Value                      │
│ ─────────────────────────────────────────  │
│ tokens        : "75"                       │
│ lastRefill    : "1710507600000"            │
│ capacity      : "100"                      │
│ refillRate    : "10"                       │
│                                            │
│ Commands:                                  │
│ HGET bucket:IP tokens                      │
│ HSET bucket:IP tokens newValue             │
│ HMGET bucket:IP tokens lastRefill          │
└────────────────────────────────────────────┘

4. Multi-Dimensional (Multiple Keys):
┌────────────────────────────────────────────┐
│ Dimension 1 (IP):                          │
│ rate:ip:192.168.1.1 → 45                   │
│                                            │
│ Dimension 2 (User):                        │
│ rate:user:user_123 → 120                   │
│                                            │
│ Dimension 3 (Endpoint):                    │
│ rate:endpoint:/api/search → 850            │
│                                            │
│ Dimension 4 (Fingerprint):                 │
│ rate:fp:abc123xyz → 67                     │
│                                            │
│ Dimension 5 (IP Reputation):               │
│ reputation:192.168.1.1 → 56                │
└────────────────────────────────────────────┘
```

---

## Production Code Examples

### Example 1: Multi-Dimensional Rate Limiter

```java
@Component
public class AdvancedRateLimiter {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * Multi-dimensional rate limiting
     *
     * Architecture:
     * ┌────────────────────────────────────────────┐
     * │ Check multiple dimensions:                 │
     * │ 1. IP address                              │
     * │ 2. User ID                                 │
     * │ 3. Device fingerprint                      │
     * │ 4. API endpoint                            │
     * │ 5. Geographic region                       │
     * │                                            │
     * │ If ANY dimension exceeds → REJECT          │
     * └────────────────────────────────────────────┘
     */
    public boolean allowRequest(RateLimitContext context) {
        // Check each dimension
        boolean ipAllowed = checkDimension(
            "ip:" + context.getIpAddress(),
            100, // 100 requests per minute
            60   // 60 seconds window
        );

        boolean userAllowed = checkDimension(
            "user:" + context.getUserId(),
            200, // 200 requests per minute
            60
        );

        boolean fingerprintAllowed = checkDimension(
            "fingerprint:" + context.getFingerprint(),
            150, // 150 requests per minute
            60
        );

        boolean endpointAllowed = checkDimension(
            "endpoint:" + context.getEndpoint(),
            1000, // 1000 total requests per minute
            60
        );

        boolean regionAllowed = checkDimension(
            "region:" + context.getCountry(),
            5000, // 5000 requests per minute per country
            60
        );

        // All dimensions must pass
        return ipAllowed && userAllowed && fingerprintAllowed
            && endpointAllowed && regionAllowed;
    }

    /**
     * Check single dimension using sliding window
     */
    private boolean checkDimension(
            String key,
            int maxRequests,
            int windowSeconds) {

        long now = System.currentTimeMillis();
        long windowStart = now - (windowSeconds * 1000);

        String redisKey = "rate:" + key;

        try {
            // Execute as Lua script for atomicity
            String script =
                "redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[1]) " +
                "local count = redis.call('ZCARD', KEYS[1]) " +
                "if count < tonumber(ARGV[3]) then " +
                "  redis.call('ZADD', KEYS[1], ARGV[2], ARGV[4]) " +
                "  redis.call('EXPIRE', KEYS[1], ARGV[5]) " +
                "  return 1 " +
                "else " +
                "  return 0 " +
                "end";

            Long result = redisTemplate.execute(
                new DefaultRedisScript<>(script, Long.class),
                Collections.singletonList(redisKey),
                String.valueOf(windowStart),
                String.valueOf(now),
                String.valueOf(maxRequests),
                UUID.randomUUID().toString(),
                String.valueOf(windowSeconds)
            );

            return result != null && result == 1;

        } catch (Exception e) {
            // Fail open (allow request) if Redis is down
            log.error("Rate limiter error: {}", e.getMessage());
            return true;
        }
    }
}

/**
 * Rate Limit Context
 */
@Data
@Builder
public class RateLimitContext {
    private String ipAddress;
    private String userId;
    private String fingerprint;
    private String endpoint;
    private String country;
    private String userAgent;
    private Long timestamp;
}
```

### Example 2: Device Fingerprinting

```java
@Service
public class DeviceFingerprintService {

    /**
     * Generate device fingerprint from request
     *
     * Fingerprint Components:
     * ┌─────────────────────────────────────┐
     * │ • User-Agent string                 │
     * │ • Accept-Language header            │
     * │ • Screen resolution (from JS)       │
     * │ • Timezone offset                   │
     * │ • Canvas fingerprint (from JS)      │
     * │ • WebGL fingerprint (from JS)       │
     * │ • Installed fonts list              │
     * └─────────────────────────────────────┘
     */
    public String generateFingerprint(HttpServletRequest request) {
        StringBuilder fpData = new StringBuilder();

        // Browser headers
        fpData.append(request.getHeader("User-Agent"));
        fpData.append("|");
        fpData.append(request.getHeader("Accept-Language"));
        fpData.append("|");
        fpData.append(request.getHeader("Accept-Encoding"));
        fpData.append("|");

        // Custom headers from client-side JS
        fpData.append(request.getHeader("X-Screen-Resolution"));
        fpData.append("|");
        fpData.append(request.getHeader("X-Timezone-Offset"));
        fpData.append("|");
        fpData.append(request.getHeader("X-Canvas-Hash"));
        fpData.append("|");
        fpData.append(request.getHeader("X-WebGL-Hash"));

        // Generate hash
        return DigestUtils.sha256Hex(fpData.toString());
    }

    /**
     * Detect if same fingerprint is used from multiple IPs
     * (Indicates proxy rotation attack)
     */
    public boolean isSuspiciousFingerprint(
            String fingerprint,
            String currentIp) {

        String key = "fingerprint:ips:" + fingerprint;

        // Add current IP to set
        redisTemplate.opsForSet().add(key, currentIp);
        redisTemplate.expire(key, 1, TimeUnit.HOURS);

        // Count unique IPs for this fingerprint
        Long uniqueIps = redisTemplate.opsForSet().size(key);

        // If same device fingerprint from >5 different IPs → suspicious
        return uniqueIps != null && uniqueIps > 5;
    }
}

/**
 * Client-side JavaScript for fingerprinting
 */
/*
<script>
// Generate canvas fingerprint
function getCanvasFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('fingerprint', 2, 2);
    return canvas.toDataURL().slice(-50); // Last 50 chars
}

// Generate WebGL fingerprint
function getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    return gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
}

// Send fingerprint with all requests
const fingerprint = {
    screenResolution: `${screen.width}x${screen.height}`,
    timezoneOffset: new Date().getTimezoneOffset(),
    canvasHash: getCanvasFingerprint(),
    webglHash: getWebGLFingerprint()
};

// Add to request headers
headers['X-Screen-Resolution'] = fingerprint.screenResolution;
headers['X-Timezone-Offset'] = fingerprint.timezoneOffset;
headers['X-Canvas-Hash'] = fingerprint.canvasHash;
headers['X-WebGL-Hash'] = fingerprint.webglHash;
</script>
*/
```

### Example 3: Behavioral Analysis Engine

```java
@Service
public class BehavioralAnalysisService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * Analyze request patterns to detect bots
     *
     * Bot Indicators:
     * ┌──────────────────────────────────────────┐
     * │ ✗ Perfectly timed requests (1/sec)       │
     * │ ✗ No mouse movements                     │
     * │ ✗ No JavaScript execution                │
     * │ ✗ Linear navigation (no browsing)        │
     * │ ✗ Suspicious User-Agent                  │
     * │ ✗ Missing common headers                 │
     * └──────────────────────────────────────────┘
     */
    public BehaviorScore analyzeBehavior(
            String identifier,
            HttpServletRequest request) {

        BehaviorScore score = new BehaviorScore();

        // Check 1: Request timing consistency
        score.addScore(
            "timing",
            analyzeRequestTiming(identifier)
        );

        // Check 2: JavaScript execution
        score.addScore(
            "javascript",
            hasJavaScriptMarkers(request) ? 10 : -20
        );

        // Check 3: Mouse activity
        score.addScore(
            "mouse",
            hasMouseActivity(request) ? 10 : -15
        );

        // Check 4: User-Agent analysis
        score.addScore(
            "userAgent",
            analyzeUserAgent(request.getHeader("User-Agent"))
        );

        // Check 5: Navigation pattern
        score.addScore(
            "navigation",
            analyzeNavigationPattern(identifier)
        );

        // Check 6: Header completeness
        score.addScore(
            "headers",
            analyzeHeaders(request)
        );

        return score;
    }

    /**
     * Analyze request timing for bot-like patterns
     *
     * Timeline Analysis:
     * Human:     ●    ●  ●     ●●        ● (variable)
     * Bot:       ●●●●●●●●●●●●●●●●●●●●●●● (consistent)
     */
    private int analyzeRequestTiming(String identifier) {
        String key = "timing:" + identifier;

        // Get last 10 request timestamps
        List<String> timestamps = redisTemplate.opsForList()
            .range(key, 0, 9);

        if (timestamps == null || timestamps.size() < 5) {
            return 0; // Not enough data
        }

        // Calculate intervals
        List<Long> intervals = new ArrayList<>();
        for (int i = 1; i < timestamps.size(); i++) {
            long current = Long.parseLong(timestamps.get(i));
            long previous = Long.parseLong(timestamps.get(i - 1));
            intervals.add(current - previous);
        }

        // Calculate standard deviation
        double mean = intervals.stream()
            .mapToLong(Long::longValue)
            .average()
            .orElse(0);

        double variance = intervals.stream()
            .mapToDouble(interval -> Math.pow(interval - mean, 2))
            .average()
            .orElse(0);

        double stdDev = Math.sqrt(variance);

        // Low standard deviation = bot-like (consistent timing)
        // High standard deviation = human-like (variable timing)
        if (stdDev < 100) {  // < 100ms variation
            return -20;  // Very suspicious (bot)
        } else if (stdDev < 500) {
            return -5;   // Somewhat suspicious
        } else {
            return 10;   // Human-like
        }
    }

    /**
     * Check for JavaScript execution markers
     */
    private boolean hasJavaScriptMarkers(HttpServletRequest request) {
        // Client sends these if JS is enabled
        return request.getHeader("X-Requested-With") != null ||
               request.getHeader("X-Canvas-Hash") != null ||
               request.getHeader("X-Screen-Resolution") != null;
    }

    /**
     * Check for mouse activity
     */
    private boolean hasMouseActivity(HttpServletRequest request) {
        // Client sends mouse event hash if real user
        return request.getHeader("X-Mouse-Hash") != null;
    }

    /**
     * Analyze User-Agent for bot signatures
     */
    private int analyzeUserAgent(String userAgent) {
        if (userAgent == null || userAgent.isEmpty()) {
            return -30; // No User-Agent = bot
        }

        String ua = userAgent.toLowerCase();

        // Known bot signatures
        String[] botKeywords = {
            "bot", "crawler", "spider", "scraper",
            "curl", "wget", "python", "java",
            "http", "library", "automation"
        };

        for (String keyword : botKeywords) {
            if (ua.contains(keyword)) {
                return -25; // Bot detected
            }
        }

        // Check for valid browser
        if (ua.contains("chrome") || ua.contains("firefox") ||
            ua.contains("safari") || ua.contains("edge")) {
            return 10; // Likely legitimate
        }

        return -10; // Unknown/suspicious
    }

    /**
     * Analyze navigation pattern
     */
    private int analyzeNavigationPattern(String identifier) {
        String key = "nav:" + identifier;

        // Get recent pages visited
        List<String> pages = redisTemplate.opsForList()
            .range(key, 0, 19);

        if (pages == null || pages.isEmpty()) {
            return 0;
        }

        // Calculate unique pages ratio
        long uniquePages = pages.stream().distinct().count();
        double ratio = (double) uniquePages / pages.size();

        // Bots often hit same endpoint repeatedly
        // Humans browse different pages
        if (ratio < 0.3) {  // < 30% unique
            return -15;  // Repetitive (bot-like)
        } else if (ratio > 0.7) {  // > 70% unique
            return 15;   // Varied (human-like)
        }

        return 0;
    }

    /**
     * Analyze HTTP headers
     */
    private int analyzeHeaders(HttpServletRequest request) {
        int score = 0;

        // Expected headers from real browsers
        if (request.getHeader("Accept") != null) score += 2;
        if (request.getHeader("Accept-Language") != null) score += 2;
        if (request.getHeader("Accept-Encoding") != null) score += 2;
        if (request.getHeader("Referer") != null) score += 3;
        if (request.getHeader("Cookie") != null) score += 3;

        // Suspicious patterns
        String accept = request.getHeader("Accept");
        if (accept != null && accept.equals("*/*")) {
            score -= 5; // Generic accept header (bot-like)
        }

        return score;
    }
}

/**
 * Behavior Score
 */
@Data
public class BehaviorScore {
    private int totalScore = 50; // Start at neutral
    private Map<String, Integer> componentScores = new HashMap<>();

    public void addScore(String component, int score) {
        componentScores.put(component, score);
        totalScore += score;
    }

    public boolean isBot() {
        return totalScore < 30; // Threshold for bot detection
    }

    public boolean isSuspicious() {
        return totalScore < 50 && totalScore >= 30;
    }

    public boolean isTrusted() {
        return totalScore >= 70;
    }
}
```

### Example 4: IP Reputation System

```java
@Service
public class IpReputationService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    /**
     * IP Reputation Scoring System
     *
     * Score Range: 0-100
     * ┌─────────────────────────────────┐
     * │ 90-100: Trusted                 │
     * │ 70-89:  Normal                  │
     * │ 40-69:  Suspicious              │
     * │ 0-39:   Malicious               │
     * └─────────────────────────────────┘
     */
    public IpReputation getReputation(String ipAddress) {
        String key = "reputation:" + ipAddress;
        String json = redisTemplate.opsForValue().get(key);

        if (json == null) {
            // New IP: Start with neutral score
            return new IpReputation(ipAddress, 70);
        }

        try {
            return objectMapper.readValue(json, IpReputation.class);
        } catch (Exception e) {
            return new IpReputation(ipAddress, 70);
        }
    }

    /**
     * Update reputation based on behavior
     */
    public void recordEvent(String ipAddress, ReputationEvent event) {
        IpReputation reputation = getReputation(ipAddress);

        switch (event.getType()) {
            case SUCCESSFUL_REQUEST:
                reputation.adjustScore(+1);
                break;
            case FAILED_AUTH:
                reputation.adjustScore(-5);
                reputation.incrementFailedAuths();
                break;
            case RATE_LIMIT_EXCEEDED:
                reputation.adjustScore(-10);
                reputation.incrementRateLimitViolations();
                break;
            case CAPTCHA_PASSED:
                reputation.adjustScore(+5);
                break;
            case CAPTCHA_FAILED:
                reputation.adjustScore(-3);
                break;
            case SUCCESSFUL_TRANSACTION:
                reputation.adjustScore(+3);
                break;
            case REPLAY_ATTACK_DETECTED:
                reputation.adjustScore(-20);
                reputation.markAsMalicious();
                break;
            case BOT_DETECTED:
                reputation.adjustScore(-15);
                break;
        }

        // Check against known databases
        if (isKnownProxy(ipAddress)) {
            reputation.adjustScore(-15);
            reputation.setIsProxy(true);
        }

        if (isDatacenterIp(ipAddress)) {
            reputation.adjustScore(-10);
            reputation.setIsDatacenter(true);
        }

        // Save updated reputation
        saveReputation(reputation);
    }

    /**
     * Save reputation to Redis
     */
    private void saveReputation(IpReputation reputation) {
        try {
            String key = "reputation:" + reputation.getIpAddress();
            String json = objectMapper.writeValueAsString(reputation);

            redisTemplate.opsForValue().set(
                key,
                json,
                7, // 7 days TTL
                TimeUnit.DAYS
            );
        } catch (Exception e) {
            log.error("Failed to save reputation: {}", e.getMessage());
        }
    }

    /**
     * Check if IP is known proxy
     */
    private boolean isKnownProxy(String ipAddress) {
        // Check against proxy database (could be external service)
        // For example: https://proxycheck.io API
        String key = "proxy:check:" + ipAddress;
        Boolean cached = redisTemplate.hasKey(key);

        if (Boolean.TRUE.equals(cached)) {
            return true;
        }

        // Could call external API here
        // For demo, check against local set
        Boolean isProxy = redisTemplate.opsForSet()
            .isMember("known:proxies", ipAddress);

        if (Boolean.TRUE.equals(isProxy)) {
            redisTemplate.opsForValue().set(
                key, "true", 24, TimeUnit.HOURS
            );
        }

        return Boolean.TRUE.equals(isProxy);
    }

    /**
     * Check if IP belongs to datacenter
     */
    private boolean isDatacenterIp(String ipAddress) {
        // Check against datacenter CIDR ranges
        // AWS, Google Cloud, Azure, etc.
        // This is simplified - production would use CIDR matching
        String[] datacenterPrefixes = {
            "13.", "18.", "52.", "54.", // AWS
            "35.", "34.",               // GCP
            "40.", "104.", "137."       // Azure
        };

        for (String prefix : datacenterPrefixes) {
            if (ipAddress.startsWith(prefix)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Get recommended action based on reputation
     */
    public ReputationAction getRecommendedAction(String ipAddress) {
        IpReputation reputation = getReputation(ipAddress);
        int score = reputation.getScore();

        if (score >= 90) {
            return ReputationAction.ALLOW;
        } else if (score >= 70) {
            return ReputationAction.ALLOW;
        } else if (score >= 40) {
            return ReputationAction.CHALLENGE; // CAPTCHA
        } else {
            return ReputationAction.BLOCK;
        }
    }
}

/**
 * IP Reputation Model
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class IpReputation {
    private String ipAddress;
    private int score = 70; // Neutral start
    private int failedAuths = 0;
    private int rateLimitViolations = 0;
    private boolean isProxy = false;
    private boolean isDatacenter = false;
    private boolean isMalicious = false;
    private long firstSeen = System.currentTimeMillis();
    private long lastSeen = System.currentTimeMillis();

    public IpReputation(String ipAddress, int initialScore) {
        this.ipAddress = ipAddress;
        this.score = initialScore;
    }

    public void adjustScore(int delta) {
        this.score = Math.max(0, Math.min(100, this.score + delta));
        this.lastSeen = System.currentTimeMillis();
    }

    public void incrementFailedAuths() {
        this.failedAuths++;
    }

    public void incrementRateLimitViolations() {
        this.rateLimitViolations++;
    }

    public void markAsMalicious() {
        this.isMalicious = true;
        this.score = Math.min(this.score, 20);
    }
}

/**
 * Reputation Event
 */
@Data
@AllArgsConstructor
public class ReputationEvent {
    private ReputationEventType type;
    private String details;
    private long timestamp;

    public enum ReputationEventType {
        SUCCESSFUL_REQUEST,
        FAILED_AUTH,
        RATE_LIMIT_EXCEEDED,
        CAPTCHA_PASSED,
        CAPTCHA_FAILED,
        SUCCESSFUL_TRANSACTION,
        REPLAY_ATTACK_DETECTED,
        BOT_DETECTED
    }
}

/**
 * Reputation Action
 */
public enum ReputationAction {
    ALLOW,      // Let through
    CHALLENGE,  // Show CAPTCHA
    BLOCK       // Reject
}
```

### Example 5: Complete Rate Limiting Filter

```java
@Component
@Order(1) // Execute first in filter chain
public class AdvancedRateLimitFilter extends OncePerRequestFilter {

    @Autowired
    private AdvancedRateLimiter rateLimiter;

    @Autowired
    private DeviceFingerprintService fingerprintService;

    @Autowired
    private BehavioralAnalysisService behaviorAnalysis;

    @Autowired
    private IpReputationService reputationService;

    @Autowired
    private ObjectMapper objectMapper;

    /**
     * Complete rate limiting workflow
     *
     * Flow:
     * ┌──────────────────────────────────────────┐
     * │ 1. Extract request metadata              │
     * │ 2. Check IP reputation                   │
     * │ 3. Generate device fingerprint           │
     * │ 4. Analyze behavior                      │
     * │ 5. Multi-dimensional rate limit check    │
     * │ 6. Record metrics                        │
     * │ 7. Allow or reject                       │
     * └──────────────────────────────────────────┘
     */
    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        // Skip rate limiting for health checks
        if (request.getRequestURI().equals("/health")) {
            filterChain.doFilter(request, response);
            return;
        }

        try {
            // Step 1: Extract metadata
            String ipAddress = getClientIp(request);
            String userId = extractUserId(request);
            String fingerprint = fingerprintService.generateFingerprint(request);
            String endpoint = request.getRequestURI();
            String country = request.getHeader("CloudFront-Viewer-Country");

            // Step 2: Check reputation
            IpReputation reputation = reputationService.getReputation(ipAddress);
            ReputationAction action = reputationService.getRecommendedAction(ipAddress);

            if (action == ReputationAction.BLOCK) {
                rejectRequest(response, "IP blocked due to low reputation");
                reputationService.recordEvent(
                    ipAddress,
                    new ReputationEvent(
                        ReputationEventType.RATE_LIMIT_EXCEEDED,
                        "Blocked by reputation",
                        System.currentTimeMillis()
                    )
                );
                return;
            }

            // Step 3: Analyze behavior
            BehaviorScore behaviorScore = behaviorAnalysis.analyzeBehavior(
                ipAddress,
                request
            );

            if (behaviorScore.isBot()) {
                rejectRequest(response, "Bot detected");
                reputationService.recordEvent(
                    ipAddress,
                    new ReputationEvent(
                        ReputationEventType.BOT_DETECTED,
                        "Behavior analysis",
                        System.currentTimeMillis()
                    )
                );
                return;
            }

            // Step 4: Check for suspicious fingerprint usage
            if (fingerprintService.isSuspiciousFingerprint(fingerprint, ipAddress)) {
                rejectRequest(response, "Suspicious device fingerprint");
                return;
            }

            // Step 5: Multi-dimensional rate limiting
            RateLimitContext context = RateLimitContext.builder()
                .ipAddress(ipAddress)
                .userId(userId)
                .fingerprint(fingerprint)
                .endpoint(endpoint)
                .country(country != null ? country : "UNKNOWN")
                .userAgent(request.getHeader("User-Agent"))
                .timestamp(System.currentTimeMillis())
                .build();

            boolean allowed = rateLimiter.allowRequest(context);

            if (!allowed) {
                rejectRequest(response, "Rate limit exceeded");
                reputationService.recordEvent(
                    ipAddress,
                    new ReputationEvent(
                        ReputationEventType.RATE_LIMIT_EXCEEDED,
                        endpoint,
                        System.currentTimeMillis()
                    )
                );
                return;
            }

            // Step 6: Record successful request
            reputationService.recordEvent(
                ipAddress,
                new ReputationEvent(
                    ReputationEventType.SUCCESSFUL_REQUEST,
                    endpoint,
                    System.currentTimeMillis()
                )
            );

            // Step 7: Add rate limit headers
            addRateLimitHeaders(response, context);

            // Allow request to proceed
            filterChain.doFilter(request, response);

        } catch (Exception e) {
            log.error("Rate limit filter error: {}", e.getMessage(), e);
            // Fail open: allow request if filter fails
            filterChain.doFilter(request, response);
        }
    }

    /**
     * Extract client IP (handle proxies)
     */
    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddr();
        }
        // X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2)
        // Take the first one
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip;
    }

    /**
     * Extract user ID from JWT or session
     */
    private String extractUserId(HttpServletRequest request) {
        // Try JWT
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            try {
                String token = authHeader.substring(7);
                Claims claims = Jwts.parser()
                    .setSigningKey("secret")
                    .parseClaimsJws(token)
                    .getBody();
                return claims.getSubject();
            } catch (Exception e) {
                // Invalid token, continue
            }
        }

        // Try session
        HttpSession session = request.getSession(false);
        if (session != null) {
            Object userId = session.getAttribute("userId");
            if (userId != null) {
                return userId.toString();
            }
        }

        return "anonymous";
    }

    /**
     * Add rate limit info to response headers
     */
    private void addRateLimitHeaders(
            HttpServletResponse response,
            RateLimitContext context) {
        response.addHeader("X-RateLimit-Limit", "100");
        response.addHeader("X-RateLimit-Remaining", "45");
        response.addHeader("X-RateLimit-Reset", "1710507660");
    }

    /**
     * Reject request with 429 status
     */
    private void rejectRequest(
            HttpServletResponse response,
            String reason) throws IOException {

        response.setStatus(429); // Too Many Requests
        response.setContentType("application/json");

        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("error", "Rate limit exceeded");
        errorResponse.put("message", reason);
        errorResponse.put("timestamp", System.currentTimeMillis());
        errorResponse.put("retryAfter", 60); // seconds

        response.getWriter().write(
            objectMapper.writeValueAsString(errorResponse)
        );
    }
}
```

---

## Interview Questions & Answers

### Q1: Why is simple IP-based rate limiting not enough?

**Answer:**

Simple IP-based rate limiting can be easily bypassed by attackers using multiple IPs.

**Problems with IP-only limiting:**
```
Attacker Strategy:
┌────────────────────────────────────────┐
│ 1. Use botnet (1000s of IPs)          │
│ 2. Each IP: 99 requests (under limit) │
│ 3. Total: 99,000 requests succeed!    │
└────────────────────────────────────────┘

Server sees:
IP 1: 99 requests → ✓ OK
IP 2: 99 requests → ✓ OK
...
IP 1000: 99 requests → ✓ OK

Total: 99,000 requests (attack succeeds)
```

**Better approach:**
- Multi-dimensional limiting (IP + user + fingerprint + endpoint)
- Behavioral analysis (detect bot patterns)
- IP reputation scoring
- Device fingerprinting
- CAPTCHA challenges

### Q2: Explain the token bucket algorithm and when to use it

**Answer:**

Token bucket allows controlled burst traffic while maintaining average rate.

**How it works:**
```
Bucket: Holds tokens (capacity: 100)
Refill: 10 tokens/second
Cost: 1 token per request

Timeline:
Time 0s: 100 tokens available
User sends 50 requests → 50 tokens consumed → 50 left

Time 5s: Refilled +50 tokens → 100 tokens
User sends 80 requests → 80 consumed → 20 left

Time 6s: Refilled +10 tokens → 30 tokens
User sends 40 requests → 30 allowed, 10 rejected
```

**When to use:**
- APIs that need burst capacity (e.g., batch uploads)
- User-facing applications (better UX)
- Variable workload patterns

**vs Fixed Window:**
Token bucket is better for UX because it allows bursts while fixed window can cause request clustering at window boundaries.

### Q3: How would you detect coordinated attacks from multiple IPs?

**Answer:**

Use clustering analysis and pattern detection.

**Detection signals:**
```
1. Temporal Clustering:
   - 100 IPs all start at same time
   - Similar request patterns
   → Coordinated attack

2. Target Clustering:
   - Multiple IPs hitting same endpoint
   - Unusual concentration
   → Targeted attack

3. Behavioral Similarity:
   - Same User-Agent from many IPs
   - Identical timing patterns
   - Same request sequences
   → Bot network

4. Geographic Anomaly:
   - IPs from unusual locations
   - For example: Small website suddenly
     getting traffic from 50 countries
   → Suspicious
```

**Implementation:**
```java
// Check if too many unique IPs hitting same endpoint
public boolean detectClusteredAttack(String endpoint) {
    String key = "endpoint:ips:" + endpoint;
    Long uniqueIps = redisTemplate.opsForSet().size(key);

    String countKey = "endpoint:count:" + endpoint;
    String count = redisTemplate.opsForValue().get(countKey);

    if (uniqueIps != null && count != null) {
        long totalRequests = Long.parseLong(count);
        // If >50 IPs and high volume
        if (uniqueIps > 50 && totalRequests > 1000) {
            return true; // Attack detected
        }
    }

    return false;
}
```

### Q4: What is device fingerprinting and how does it help?

**Answer:**

Device fingerprinting identifies unique devices beyond IP addresses.

**Components:**
```
┌────────────────────────────────────────┐
│ Browser Fingerprint:                   │
│ • User-Agent                           │
│ • Screen resolution                    │
│ • Timezone                             │
│ • Canvas rendering hash                │
│ • WebGL renderer hash                  │
│ • Installed fonts                      │
│ • Audio context                        │
└────────────────────────────────────────┘
```

**How it helps:**
```
Scenario: Attacker rotating through 100 IPs

Without fingerprinting:
✗ Server sees 100 different "users"
✗ Each under rate limit
✗ Attack succeeds

With fingerprinting:
✓ Server detects same device fingerprint
✓ All 100 IPs traced to single device
✓ Rate limit applied to device
✓ Attack blocked
```

**Limitation:** Advanced attackers can randomize fingerprints, so combine with other techniques.

### Q5: Explain sliding window vs fixed window rate limiting

**Answer:**

**Fixed Window:**
```
Window: 12:00:00 - 12:01:00
Limit: 100 requests

Problem: Burst at boundary
11:59:58 ── 100 requests ──┐
                            │ 200 requests
12:00:02 ── 100 requests ──┘ in 4 seconds!

Each window: ✓ Under limit
Reality: ✗ Traffic spike
```

**Sliding Window:**
```
Always looks back 60 seconds from current time

At 12:00:30:
Count from 11:59:30 to 12:00:30

At 12:00:45:
Count from 11:59:45 to 12:00:45

Benefits:
✓ No boundary issues
✓ More accurate
✓ Prevents burst exploitation
```

**Implementation:**
```java
// Fixed window (simple but flawed)
String key = "rate:" + ip + ":" + getCurrentMinute();
Long count = redis.incr(key);

// Sliding window (better but more complex)
long now = System.currentTimeMillis();
long windowStart = now - 60000;

// Add current request
redis.zadd("requests:" + ip, now, requestId);

// Remove old requests
redis.zremrangeByScore("requests:" + ip, 0, windowStart);

// Count requests in window
Long count = redis.zcard("requests:" + ip);
```

### Q6: How do you handle rate limiting in a distributed system?

**Answer:**

Use Redis as shared state with atomic operations.

**Architecture:**
```
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Server 1 │   │ Server 2 │   │ Server 3 │
└────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │
     └──────────────┼──────────────┘
                    │
                    ▼
            ┌────────────────┐
            │ Redis Cluster  │
            │ (Shared State) │
            └────────────────┘
```

**Challenges:**
```
1. Race Conditions:
   Server 1 reads: count = 99
   Server 2 reads: count = 99
   Both increment → count = 101 (exceeds 100 limit!)

   Solution: Atomic operations (Lua scripts)

2. Clock Synchronization:
   Server 1 time: 12:00:00
   Server 2 time: 12:00:05
   → Different window calculations

   Solution: Use Redis time or central timestamp

3. Network Partitions:
   Redis temporarily unreachable
   → Fail open or closed?

   Solution: Circuit breaker pattern
```

**Atomic Lua Script:**
```lua
-- Atomic increment and check
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if count > tonumber(ARGV[2]) then
    return 0  -- Reject
else
    return 1  -- Allow
end
```

### Q7: What is IP reputation scoring and how do you implement it?

**Answer:**

IP reputation tracks historical behavior to identify malicious IPs.

**Scoring system:**
```
Score Range: 0-100
┌──────────────────────────────────┐
│ 90-100: Trusted (whitelist)      │
│ 70-89:  Normal (allow)           │
│ 40-69:  Suspicious (challenge)   │
│ 0-39:   Malicious (block)        │
└──────────────────────────────────┘

Events that lower score:
- Rate limit violation: -10
- Failed authentication: -5
- CAPTCHA failure: -3
- Replay attack: -20
- Bot detected: -15
- Known proxy: -15
- Datacenter IP: -10

Events that raise score:
- Successful transaction: +3
- Long session: +5
- CAPTCHA passed: +5
- Consistent fingerprint: +5
- Geographic consistency: +3
```

**Implementation:**
```java
public void updateReputation(String ip, Event event) {
    IpReputation rep = getReputation(ip);

    switch (event) {
        case RATE_LIMIT_EXCEEDED:
            rep.adjustScore(-10);
            if (rep.getViolations() > 5) {
                rep.markAsMalicious();
            }
            break;
        case SUCCESSFUL_PAYMENT:
            rep.adjustScore(+3);
            break;
    }

    saveReputation(rep);

    // Take action based on score
    if (rep.getScore() < 40) {
        blockIp(ip);
    } else if (rep.getScore() < 70) {
        challengeWithCaptcha(ip);
    }
}
```

### Q8: How do you balance security and user experience?

**Answer:**

Use progressive security measures based on risk.

**Progressive Security:**
```
┌────────────────────────────────────────────┐
│ Risk Level → Security Measure             │
├────────────────────────────────────────────┤
│                                            │
│ LOW (trusted IP, good reputation)          │
│ → No friction, allow all requests          │
│                                            │
│ MEDIUM (unknown IP, normal behavior)       │
│ → Standard rate limits                     │
│                                            │
│ ELEVATED (suspicious patterns)             │
│ → Stricter limits + monitoring             │
│                                            │
│ HIGH (multiple violations)                 │
│ → CAPTCHA challenge                        │
│                                            │
│ CRITICAL (confirmed attack)                │
│ → Temporary block + alert                  │
└────────────────────────────────────────────┘
```

**Examples:**
```java
public SecurityAction determineAction(String ip) {
    IpReputation rep = getReputation(ip);
    BehaviorScore behavior = analyzeBehavior(ip);

    // Trusted user: minimal friction
    if (rep.getScore() >= 90 && behavior.isTrusted()) {
        return new SecurityAction(
            ActionType.ALLOW,
            "rate_limit_generous"  // 200/min
        );
    }

    // Normal user: standard protection
    if (rep.getScore() >= 70) {
        return new SecurityAction(
            ActionType.ALLOW,
            "rate_limit_standard"  // 100/min
        );
    }

    // Suspicious: challenge but don't block
    if (rep.getScore() >= 40) {
        return new SecurityAction(
            ActionType.CHALLENGE,
            "captcha_medium"  // Show CAPTCHA
        );
    }

    // Malicious: block
    return new SecurityAction(
        ActionType.BLOCK,
        "temporary_block"  // Block for 15 min
    );
}
```

**Key principle:** Good users should never notice security, bad actors should be stopped.

### Q9: How do you monitor and alert on rate limiting attacks?

**Answer:**

Track key metrics and set up alerts for anomalies.

**Metrics to monitor:**
```
┌────────────────────────────────────────────┐
│ 1. Rate Limit Metrics:                     │
│    • Requests blocked per minute           │
│    • Rejection rate (%)                    │
│    • Top blocked IPs                       │
│                                            │
│ 2. Attack Indicators:                      │
│    • Unique IPs per endpoint               │
│    • Request clustering score              │
│    • Bot detection rate                    │
│                                            │
│ 3. Performance Metrics:                    │
│    • Redis latency                         │
│    • Filter execution time                 │
│    • Error rate                            │
└────────────────────────────────────────────┘
```

**Alert rules:**
```java
@Component
public class RateLimitMonitor {

    @Scheduled(fixedRate = 60000) // Every minute
    public void checkForAttacks() {
        // Alert 1: High rejection rate
        double rejectionRate = calculateRejectionRate();
        if (rejectionRate > 0.2) { // >20%
            alerting.sendAlert(
                AlertLevel.WARNING,
                "High rate limit rejection: " + rejectionRate
            );
        }

        // Alert 2: Coordinated attack
        for (String endpoint : getMonitoredEndpoints()) {
            long uniqueIps = getUniqueIpsForEndpoint(endpoint);
            if (uniqueIps > 100) {
                alerting.sendAlert(
                    AlertLevel.CRITICAL,
                    "Possible coordinated attack on " + endpoint
                );
            }
        }

        // Alert 3: Known malicious IPs
        long blockedIps = countBlockedIps();
        if (blockedIps > 50) {
            alerting.sendAlert(
                AlertLevel.INFO,
                blockedIps + " IPs currently blocked"
            );
        }
    }
}
```

**Dashboard:**
```
┌────────────────────────────────────────┐
│ Rate Limiting Dashboard                │
├────────────────────────────────────────┤
│ Last Hour:                             │
│ • Total requests: 1,245,823            │
│ • Blocked: 12,456 (1.0%)              │
│ • CAPTCHAs shown: 3,421               │
│                                        │
│ Top Blocked IPs:                       │
│ 1. 192.168.1.100 → 456 blocks         │
│ 2. 10.0.0.50     → 234 blocks         │
│                                        │
│ Attack Detection:                      │
│ • Coordinated attacks: 2 detected      │
│ • Bot traffic: 5.2%                   │
│ • Proxy rotation: 8 instances          │
└────────────────────────────────────────┘
```

### Q10: What are the trade-offs of different rate limiting algorithms?

**Answer:**

| Algorithm | Pros | Cons | Use Case |
|-----------|------|------|----------|
| **Fixed Window** | Simple, low memory | Boundary burst problem | Low-stakes APIs |
| **Sliding Window** | Accurate, fair | Higher memory, complex | Production APIs |
| **Token Bucket** | Allows bursts, smooth | State management | User-facing apps |
| **Leaky Bucket** | Constant rate, simple | No burst allowance | Queue systems |

**Detailed comparison:**

```
Fixed Window:
┌──────────────────────────────────────┐
│ Pros:                                │
│ • Very simple implementation         │
│ • Low memory (1 counter per window)  │
│ • Fast (single INCR operation)       │
│                                      │
│ Cons:                                │
│ • Boundary burst issue               │
│ • Less accurate                      │
│ • Can be exploited                   │
└──────────────────────────────────────┘

Sliding Window:
┌──────────────────────────────────────┐
│ Pros:                                │
│ • No boundary issues                 │
│ • More accurate                      │
│ • Fair to all users                  │
│                                      │
│ Cons:                                │
│ • Higher memory (timestamp per req)  │
│ • More complex                       │
│ • Cleanup needed                     │
└──────────────────────────────────────┘

Token Bucket:
┌──────────────────────────────────────┐
│ Pros:                                │
│ • Allows traffic bursts              │
│ • Good user experience               │
│ • Flexible (tunable refill rate)     │
│                                      │
│ Cons:                                │
│ • State management                   │
│ • Clock synchronization needed       │
│ • Can allow large bursts             │
└──────────────────────────────────────┘
```

**Recommendation:** Use sliding window for most production systems, with token bucket for user-facing APIs that need burst support.

---

## Summary

**Multi-IP Attack Protection Checklist:**

```
✓ Multi-dimensional rate limiting
  - IP address
  - User ID
  - Device fingerprint
  - API endpoint
  - Geographic region

✓ Detection mechanisms
  - Device fingerprinting
  - Behavioral analysis
  - Clustering detection
  - IP reputation scoring

✓ Prevention techniques
  - Distributed rate limiting (Redis)
  - Progressive CAPTCHA challenges
  - WAF integration
  - Automatic IP blocking

✓ Monitoring & alerting
  - Real-time metrics
  - Attack detection
  - Dashboard visualization
  - Automated responses

✓ User experience
  - Minimal friction for legitimate users
  - Progressive security measures
  - Clear error messages
  - Fast response times
```

This comprehensive guide covers advanced rate limiting for protection against sophisticated multi-IP attacks, preparing you for senior-level system design interviews.
