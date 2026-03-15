# Replay Attack Prevention - Security Interview Guide

## Table of Contents
1. [What is a Replay Attack](#what-is-a-replay-attack)
2. [How Attackers Exploit Replay Attacks](#how-attackers-exploit-replay-attacks)
3. [Prevention Techniques](#prevention-techniques)
4. [Real Code Examples](#real-code-examples)
5. [Production Implementation](#production-implementation)
6. [Interview Questions & Answers](#interview-questions--answers)

---

## What is a Replay Attack

A replay attack is when an attacker intercepts a valid network transmission and fraudulently repeats or delays it to gain unauthorized access or trigger unauthorized actions.

### Visual Representation

```
Normal Flow:
┌──────────┐                          ┌──────────┐
│  Client  │ ──── Request ────────>   │  Server  │
│          │ <─── Response ──────     │          │
└──────────┘                          └──────────┘

Replay Attack Flow:
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Client  │ ──1──>  │ Attacker │         │  Server  │
│          │         │(Intercept)│         │          │
└──────────┘         └─────┬────┘         └──────────┘
                           │                    ▲
                           │                    │
                           └────2. Replay ──────┘
                           (Same request sent again)
```

### Real-World Example

```
Payment Transaction:
┌─────────────────────────────────────────────────────┐
│ Legitimate Request (1:00 PM):                       │
│ POST /api/payment                                   │
│ {                                                   │
│   "from": "account_123",                           │
│   "to": "merchant_456",                            │
│   "amount": 100,                                   │
│   "timestamp": "2026-03-15T13:00:00Z"             │
│ }                                                   │
└─────────────────────────────────────────────────────┘
                    │
                    ▼ (Attacker captures)
┌─────────────────────────────────────────────────────┐
│ Replayed Request (1:05 PM):                         │
│ POST /api/payment                                   │
│ {                                                   │
│   "from": "account_123",    ◄── Same exact data    │
│   "to": "merchant_456",                            │
│   "amount": 100,                                   │
│   "timestamp": "2026-03-15T13:00:00Z"             │
│ }                                                   │
│ Result: Payment processed TWICE!                    │
└─────────────────────────────────────────────────────┘
```

---

## How Attackers Exploit Replay Attacks

### Attack Vector Analysis

```
┌────────────────────────────────────────────────────────┐
│           Common Replay Attack Scenarios               │
├────────────────────────────────────────────────────────┤
│                                                        │
│  1. Financial Fraud                                    │
│     ┌──────────────────────────────────┐              │
│     │ Capture: Transfer $1000          │              │
│     │ Replay:  Transfer $1000 (x100)   │              │
│     │ Result:  $100,000 stolen         │              │
│     └──────────────────────────────────┘              │
│                                                        │
│  2. Authentication Bypass                              │
│     ┌──────────────────────────────────┐              │
│     │ Capture: Valid login token       │              │
│     │ Replay:  Use expired token       │              │
│     │ Result:  Unauthorized access     │              │
│     └──────────────────────────────────┘              │
│                                                        │
│  3. API Abuse                                          │
│     ┌──────────────────────────────────┐              │
│     │ Capture: Premium feature request │              │
│     │ Replay:  Same request (x1000)    │              │
│     │ Result:  Free premium access     │              │
│     └──────────────────────────────────┘              │
│                                                        │
│  4. Session Hijacking                                  │
│     ┌──────────────────────────────────┐              │
│     │ Capture: Session cookie          │              │
│     │ Replay:  Cookie from attacker IP │              │
│     │ Result:  Account takeover        │              │
│     └──────────────────────────────────┘              │
└────────────────────────────────────────────────────────┘
```

### Attack Timeline

```
Time: 00:00                 01:00                 02:00
      │                     │                     │
      │                     │                     │
┌─────▼─────┐         ┌─────▼─────┐        ┌─────▼─────┐
│  Victim   │         │ Attacker  │        │  Victim   │
│ sends     │         │ captures  │        │ suffers   │
│ request   │         │ & replays │        │ loss      │
└───────────┘         └───────────┘        └───────────┘
      │                     │                     │
      │ Valid Request       │ Replayed Request    │
      ├────────────────────>├────────────────────>│
      │                     │                     │
      │                     │ (Captured via:)     │
      │                     │ - Network sniffing  │
      │                     │ - Man-in-the-middle │
      │                     │ - Compromised proxy │
      │                     │ - Browser dev tools │
```

---

## Prevention Techniques

### 1. Nonce (Number Used Once)

A unique, random value that can only be used once.

```
┌───────────────────────────────────────────────────────┐
│              Nonce-Based Protection                    │
└───────────────────────────────────────────────────────┘

Step 1: Client generates unique nonce
┌──────────┐
│  Client  │  Nonce = UUID.randomUUID()
│          │  = "7f3e4d2a-9c8b-4a6f-b1e5-3d7c9a2e1f4b"
└────┬─────┘
     │
     │ Request with nonce
     ▼
┌──────────┐
│  Server  │  1. Check if nonce exists in cache
│          │  2. If exists → REJECT (replay detected!)
│  ┌────┐  │  3. If new → Process & store nonce
│  │Cache│  │  4. Store with TTL (e.g., 5 minutes)
│  └────┘  │
└──────────┘

Nonce Cache (Redis):
┌─────────────────────────────────────────────┐
│ Key: "nonce:7f3e4d2a"  Value: "used"        │
│ TTL: 300 seconds                            │
├─────────────────────────────────────────────┤
│ Key: "nonce:8a4f5e3b"  Value: "used"        │
│ TTL: 285 seconds                            │
└─────────────────────────────────────────────┘

Replay Attempt:
┌──────────┐
│ Attacker │  Sends same nonce: "7f3e4d2a..."
└────┬─────┘
     │
     ▼
┌──────────┐
│  Server  │  1. Check cache
│          │  2. Nonce exists! → REJECT
│          │  3. Return 409 Conflict
└──────────┘
```

### 2. Timestamp-Based Validation

Accept requests only within a time window.

```
┌───────────────────────────────────────────────────────┐
│           Timestamp Validation Flow                    │
└───────────────────────────────────────────────────────┘

Current Time: 13:00:00
Allowed Window: ± 2 minutes

Timeline:
12:57  12:58  12:59  13:00  13:01  13:02  13:03
  │      │      │      │      │      │      │
  │      └──────┴──────┴──────┴──────┘      │
  │          VALID WINDOW (4 min)           │
  │                                         │
REJECT                                   REJECT
(too old)                              (clock skew)

Request Processing:
┌──────────┐
│  Client  │  timestamp = System.currentTimeMillis()
│          │  = 1710507600000 (13:00:00)
└────┬─────┘
     │
     │ POST /api/payment
     │ X-Timestamp: 1710507600000
     ▼
┌──────────┐
│  Server  │
│          │  1. serverTime = System.currentTimeMillis()
│          │  2. requestTime = header("X-Timestamp")
│          │  3. diff = Math.abs(serverTime - requestTime)
│          │
│          │  if (diff > 120000) { // 2 minutes
│          │      return "419 Request Timeout"
│          │  }
└──────────┘

Replay Attack Prevention:
Attacker captures request at 13:00:00
Attacker replays at 13:05:00 (5 minutes later)

┌──────────┐
│  Server  │  Server time: 13:05:00 (1710507900000)
│          │  Request time: 13:00:00 (1710507600000)
│          │  Diff: 300000 ms (5 minutes)
│          │
│          │  300000 > 120000 → REJECT!
└──────────┘
```

### 3. HMAC (Hash-Based Message Authentication Code)

Sign requests with a secret key.

```
┌───────────────────────────────────────────────────────┐
│               HMAC Signature Flow                      │
└───────────────────────────────────────────────────────┘

Client Side:
┌──────────────────────────────────────────────────────┐
│ 1. Prepare request data                              │
│    payload = {                                       │
│      "amount": 100,                                  │
│      "to": "merchant_456",                          │
│      "nonce": "abc123",                             │
│      "timestamp": "1710507600000"                   │
│    }                                                 │
│                                                      │
│ 2. Create signature string                          │
│    signatureBase = "amount=100&to=merchant_456"     │
│                    + "&nonce=abc123"                │
│                    + "&timestamp=1710507600000"     │
│                                                      │
│ 3. Generate HMAC                                     │
│    secret = "shared_secret_key_xyz"                 │
│    signature = HMAC-SHA256(signatureBase, secret)   │
│              = "a3f5e8d9c2b1..."                    │
│                                                      │
│ 4. Send request with signature                      │
│    POST /api/payment                                │
│    X-Signature: a3f5e8d9c2b1...                    │
│    Body: {payload}                                  │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│ Server Side Verification:                            │
│                                                      │
│ 1. Receive request                                   │
│    receivedSignature = header("X-Signature")        │
│    payload = request.getBody()                      │
│                                                      │
│ 2. Reconstruct signature                            │
│    signatureBase = buildFromPayload(payload)        │
│    expectedSignature = HMAC-SHA256(                 │
│                          signatureBase,             │
│                          secret                     │
│                        )                            │
│                                                      │
│ 3. Compare signatures                               │
│    if (receivedSignature == expectedSignature) {    │
│        → VALID REQUEST                              │
│    } else {                                         │
│        → REJECT (tampered or invalid)               │
│    }                                                 │
└──────────────────────────────────────────────────────┘

Why HMAC Prevents Replay:
┌─────────────────────────────────────────────┐
│ Even if attacker captures the request:     │
│                                             │
│ ✗ Cannot modify amount (breaks signature)  │
│ ✗ Cannot change recipient (breaks sig)     │
│ ✗ Cannot reuse old signature (nonce used)  │
│                                             │
│ Attacker needs SECRET KEY to create valid  │
│ signature for any request!                  │
└─────────────────────────────────────────────┘
```

### 4. JWT with JTI (JWT ID)

Use unique JWT identifiers.

```
┌───────────────────────────────────────────────────────┐
│              JWT with JTI Flow                         │
└───────────────────────────────────────────────────────┘

JWT Structure:
┌─────────────────────────────────────────────────────┐
│ Header:                                             │
│ {                                                   │
│   "alg": "HS256",                                  │
│   "typ": "JWT"                                     │
│ }                                                   │
├─────────────────────────────────────────────────────┤
│ Payload:                                            │
│ {                                                   │
│   "sub": "user_123",                               │
│   "jti": "550e8400-e29b-41d4-a716-446655440000", ◄─┐│
│   "iat": 1710507600,                               ││
│   "exp": 1710511200,                               ││
│   "nonce": "abc123xyz"                             ││
│ }                                                   ││
├─────────────────────────────────────────────────────┤│
│ Signature: HMACSHA256(header + payload, secret)    ││
└─────────────────────────────────────────────────────┘│
                                                        │
                    Unique ID (stored in blocklist)────┘

Token Validation Process:
┌──────────┐
│  Client  │  Bearer token in Authorization header
└────┬─────┘
     │
     │ GET /api/protected
     │ Authorization: Bearer eyJhbGc...
     ▼
┌──────────────────────────────────────┐
│  Server                              │
│                                      │
│  1. Decode JWT                       │
│     jti = jwt.getClaim("jti")       │
│     = "550e8400-e29b-41d4..."       │
│                                      │
│  2. Check JTI in Redis              │
│     exists = redis.exists("jti:550e8400")
│                                      │
│  3. Validate                         │
│     if (exists) {                   │
│         → REJECT (already used)     │
│     }                                │
│                                      │
│  4. Mark as used                    │
│     redis.setex(                    │
│         "jti:550e8400",            │
│         3600, // TTL = exp - iat   │
│         "used"                      │
│     )                                │
│                                      │
│  5. Process request                 │
└──────────────────────────────────────┘

JTI Blocklist (Redis):
┌──────────────────────────────────────────────┐
│ Key: "jti:550e8400"  Value: "used"           │
│ Expires: 3600 seconds                        │
├──────────────────────────────────────────────┤
│ Key: "jti:661f9511"  Value: "used"           │
│ Expires: 3245 seconds                        │
└──────────────────────────────────────────────┘

Replay Attack Prevention:
┌──────────┐
│ Attacker │  Reuses same JWT token
└────┬─────┘
     │
     ▼
┌──────────┐
│  Server  │  1. Extract jti: "550e8400"
│          │  2. Check Redis: EXISTS!
│          │  3. REJECT: "Token already used"
└──────────┘
```

### 5. Sequence Numbers

For stateful connections (websockets, gRPC).

```
┌───────────────────────────────────────────────────────┐
│           Sequence Number Tracking                     │
└───────────────────────────────────────────────────────┘

Connection Establishment:
┌──────────┐                          ┌──────────┐
│  Client  │ ─── CONNECT ───────────> │  Server  │
│          │ <── SEQ_START = 0 ─────  │          │
└──────────┘                          └──────────┘

Message Exchange:
┌──────────┐                          ┌──────────┐
│  Client  │                          │  Server  │
│          │                          │          │
│ seq = 1  │ ── MSG (seq=1) ───────>  │ expect=1 ✓│
│          │                          │          │
│ seq = 2  │ ── MSG (seq=2) ───────>  │ expect=2 ✓│
│          │                          │          │
│ seq = 3  │ ── MSG (seq=3) ───────>  │ expect=3 ✓│
└──────────┘                          └──────────┘

Replay Attack Attempt:
┌──────────┐                          ┌──────────┐
│ Attacker │                          │  Server  │
│          │                          │          │
│          │ ── MSG (seq=2) ───────>  │ expect=4 ✗│
│          │ <── REJECT ────────────  │ (too old)│
│          │                          │          │
│          │ ── MSG (seq=10) ──────>  │ expect=4 ✗│
│          │ <── REJECT ────────────  │ (too new)│
└──────────┘                          └──────────┘

Server State:
┌─────────────────────────────────────┐
│ Session ID: "session_abc123"        │
│ Expected Sequence: 4                │
│ Last Processed: 3                   │
│ Window: [4, 5, 6, 7, 8]            │
│                                     │
│ Accept: seq ∈ [expectedSeq, +5]    │
│ Reject: seq < expectedSeq          │
│ Reject: seq > expectedSeq + 5      │
└─────────────────────────────────────┘
```

---

## Real Code Examples

### Example 1: Nonce-Based Prevention (Spring Boot)

```java
@RestController
@RequestMapping("/api/secure")
public class SecurePaymentController {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    private static final long NONCE_TTL_SECONDS = 300; // 5 minutes

    /**
     * Process payment with nonce validation
     *
     * ASCII Flow:
     * Client → [Nonce Check] → [Process] → Response
     *              ↓ exists?
     *              ↓ yes → REJECT
     *              ↓ no  → Continue
     */
    @PostMapping("/payment")
    public ResponseEntity<?> processPayment(
            @RequestBody PaymentRequest request,
            @RequestHeader("X-Nonce") String nonce) {

        // Step 1: Validate nonce exists
        if (nonce == null || nonce.trim().isEmpty()) {
            return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(new ErrorResponse("Nonce is required"));
        }

        // Step 2: Check if nonce was already used
        String nonceKey = "nonce:" + nonce;
        Boolean nonceExists = redisTemplate.hasKey(nonceKey);

        if (Boolean.TRUE.equals(nonceExists)) {
            // REPLAY ATTACK DETECTED!
            log.warn("Replay attack detected! Nonce already used: {}", nonce);
            return ResponseEntity
                .status(HttpStatus.CONFLICT)
                .body(new ErrorResponse("Request already processed"));
        }

        // Step 3: Store nonce (mark as used)
        redisTemplate.opsForValue().set(
            nonceKey,
            "used",
            NONCE_TTL_SECONDS,
            TimeUnit.SECONDS
        );

        // Step 4: Process payment
        PaymentResponse response = processPaymentInternal(request);

        return ResponseEntity.ok(response);
    }

    private PaymentResponse processPaymentInternal(PaymentRequest request) {
        // Actual payment processing logic
        return new PaymentResponse(
            "txn_" + UUID.randomUUID().toString(),
            request.getAmount(),
            "SUCCESS"
        );
    }
}

/**
 * Payment Request DTO
 */
@Data
public class PaymentRequest {
    private String fromAccount;
    private String toAccount;
    private BigDecimal amount;
    private String currency;
}

/**
 * Payment Response DTO
 */
@Data
@AllArgsConstructor
public class PaymentResponse {
    private String transactionId;
    private BigDecimal amount;
    private String status;
}

/**
 * Error Response DTO
 */
@Data
@AllArgsConstructor
public class ErrorResponse {
    private String message;
}
```

### Example 2: Timestamp Validation

```java
@Component
public class TimestampValidator {

    private static final long MAX_REQUEST_AGE_MS = 120000; // 2 minutes

    /**
     * Validate request timestamp
     *
     * Timeline:
     * |-------|-------|-------|-------|
     *    -2m    -1m    NOW    +1m    +2m
     *         [  VALID WINDOW  ]
     */
    public void validateTimestamp(Long requestTimestamp) {
        if (requestTimestamp == null) {
            throw new SecurityException("Timestamp is required");
        }

        long currentTime = System.currentTimeMillis();
        long timeDiff = Math.abs(currentTime - requestTimestamp);

        if (timeDiff > MAX_REQUEST_AGE_MS) {
            throw new SecurityException(
                String.format(
                    "Request too old. Age: %d ms, Max allowed: %d ms",
                    timeDiff, MAX_REQUEST_AGE_MS
                )
            );
        }
    }
}

@RestController
@RequestMapping("/api/secure")
public class TimestampProtectedController {

    @Autowired
    private TimestampValidator timestampValidator;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * Endpoint with timestamp AND nonce validation
     *
     * Protection Layers:
     * ┌─────────────────────┐
     * │ 1. Timestamp Check  │ ← Prevents old replays
     * ├─────────────────────┤
     * │ 2. Nonce Check      │ ← Prevents immediate replays
     * ├─────────────────────┤
     * │ 3. HMAC Signature   │ ← Prevents tampering
     * └─────────────────────┘
     */
    @PostMapping("/transfer")
    public ResponseEntity<?> transfer(
            @RequestBody TransferRequest request,
            @RequestHeader("X-Timestamp") Long timestamp,
            @RequestHeader("X-Nonce") String nonce,
            @RequestHeader("X-Signature") String signature) {

        try {
            // Layer 1: Timestamp validation
            timestampValidator.validateTimestamp(timestamp);

            // Layer 2: Nonce validation
            validateNonce(nonce);

            // Layer 3: Signature validation
            validateSignature(request, timestamp, nonce, signature);

            // Process the transfer
            TransferResponse response = processTransfer(request);

            return ResponseEntity.ok(response);

        } catch (SecurityException e) {
            log.error("Security validation failed: {}", e.getMessage());
            return ResponseEntity
                .status(HttpStatus.FORBIDDEN)
                .body(new ErrorResponse(e.getMessage()));
        }
    }

    private void validateNonce(String nonce) {
        String nonceKey = "nonce:" + nonce;
        if (Boolean.TRUE.equals(redisTemplate.hasKey(nonceKey))) {
            throw new SecurityException("Nonce already used");
        }
        redisTemplate.opsForValue().set(nonceKey, "used", 5, TimeUnit.MINUTES);
    }

    private void validateSignature(
            TransferRequest request,
            Long timestamp,
            String nonce,
            String receivedSignature) {

        String signatureBase = String.format(
            "amount=%s&from=%s&to=%s&nonce=%s&timestamp=%d",
            request.getAmount(),
            request.getFromAccount(),
            request.getToAccount(),
            nonce,
            timestamp
        );

        String expectedSignature = HmacUtils.hmacSha256Hex(
            "shared_secret_key",
            signatureBase
        );

        if (!MessageDigest.isEqual(
                expectedSignature.getBytes(),
                receivedSignature.getBytes())) {
            throw new SecurityException("Invalid signature");
        }
    }

    private TransferResponse processTransfer(TransferRequest request) {
        // Actual transfer logic
        return new TransferResponse(
            "txn_" + UUID.randomUUID(),
            request.getAmount(),
            "COMPLETED"
        );
    }
}

@Data
public class TransferRequest {
    private String fromAccount;
    private String toAccount;
    private BigDecimal amount;
}

@Data
@AllArgsConstructor
public class TransferResponse {
    private String transactionId;
    private BigDecimal amount;
    private String status;
}
```

### Example 3: JWT with JTI

```java
@Service
public class JwtService {

    @Value("${jwt.secret}")
    private String jwtSecret;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * Generate JWT with JTI
     *
     * Token Structure:
     * ┌──────────────────────┐
     * │ Header: alg, typ     │
     * ├──────────────────────┤
     * │ Payload:             │
     * │   - sub (user)       │
     * │   - jti (unique ID)  │ ← Prevents replay
     * │   - iat (issued at)  │
     * │   - exp (expires)    │
     * │   - nonce            │ ← Additional protection
     * ├──────────────────────┤
     * │ Signature            │
     * └──────────────────────┘
     */
    public String generateToken(String userId) {
        long now = System.currentTimeMillis();
        long expirationTime = now + 3600000; // 1 hour

        String jti = UUID.randomUUID().toString();
        String nonce = UUID.randomUUID().toString();

        return Jwts.builder()
            .setSubject(userId)
            .setId(jti)  // JWT ID for replay prevention
            .claim("nonce", nonce)
            .setIssuedAt(new Date(now))
            .setExpiration(new Date(expirationTime))
            .signWith(SignatureAlgorithm.HS256, jwtSecret)
            .compact();
    }

    /**
     * Validate JWT and check for replay
     *
     * Validation Flow:
     * Token → [Decode] → [Verify Signature] → [Check JTI] → Valid/Invalid
     *                          ↓                    ↓
     *                        Invalid            JTI used?
     *                                          yes → Replay!
     *                                          no  → Mark used
     */
    public Claims validateToken(String token) {
        try {
            // Step 1: Parse and verify signature
            Claims claims = Jwts.parser()
                .setSigningKey(jwtSecret)
                .parseClaimsJws(token)
                .getBody();

            // Step 2: Extract JTI
            String jti = claims.getId();
            if (jti == null) {
                throw new SecurityException("JWT missing JTI");
            }

            // Step 3: Check if JTI was already used
            String jtiKey = "jti:" + jti;
            Boolean jtiUsed = redisTemplate.hasKey(jtiKey);

            if (Boolean.TRUE.equals(jtiUsed)) {
                throw new SecurityException(
                    "JWT replay detected! Token already used: " + jti
                );
            }

            // Step 4: Mark JTI as used
            long exp = claims.getExpiration().getTime();
            long now = System.currentTimeMillis();
            long ttl = (exp - now) / 1000; // Convert to seconds

            if (ttl > 0) {
                redisTemplate.opsForValue().set(
                    jtiKey,
                    "used",
                    ttl,
                    TimeUnit.SECONDS
                );
            }

            // Step 5: Return claims for further processing
            return claims;

        } catch (ExpiredJwtException e) {
            throw new SecurityException("Token expired");
        } catch (MalformedJwtException e) {
            throw new SecurityException("Invalid token format");
        } catch (SignatureException e) {            throw new SecurityException("Invalid token signature");
        }
    }
}

/**
 * JWT Authentication Filter
 */
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtService jwtService;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        try {
            // Extract JWT from Authorization header
            String authHeader = request.getHeader("Authorization");

            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String token = authHeader.substring(7);

                // Validate token (includes replay check)
                Claims claims = jwtService.validateToken(token);

                // Set authentication in security context
                String userId = claims.getSubject();
                UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(
                        userId, null, new ArrayList<>()
                    );

                SecurityContextHolder.getContext()
                    .setAuthentication(authentication);
            }

            filterChain.doFilter(request, response);

        } catch (SecurityException e) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.getWriter().write(
                "{\"error\": \"" + e.getMessage() + "\"}"
            );
        }
    }
}
```

### Example 4: HMAC Signature Generator

```java
@Component
public class HmacSignatureService {

    @Value("${hmac.secret}")
    private String secretKey;

    /**
     * Generate HMAC signature for request
     *
     * Signature Process:
     * ┌─────────────────────────────────────────┐
     * │ 1. Extract request data                 │
     * │    ↓                                    │
     * │ 2. Build canonical string               │
     * │    ↓                                    │
     * │ 3. Add timestamp & nonce                │
     * │    ↓                                    │
     * │ 4. Apply HMAC-SHA256 with secret        │
     * │    ↓                                    │
     * │ 5. Return Base64 encoded signature      │
     * └─────────────────────────────────────────┘
     */
    public String generateSignature(
            Map<String, Object> requestData,
            String nonce,
            Long timestamp) {

        // Build canonical string (sorted by key)
        String canonicalString = buildCanonicalString(requestData);

        // Add metadata
        String signatureBase = String.format(
            "%s&nonce=%s&timestamp=%d",
            canonicalString,
            nonce,
            timestamp
        );

        // Generate HMAC
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec =
                new SecretKeySpec(secretKey.getBytes(), "HmacSHA256");
            mac.init(secretKeySpec);

            byte[] hmacBytes = mac.doFinal(signatureBase.getBytes());

            return Base64.getEncoder().encodeToString(hmacBytes);

        } catch (Exception e) {
            throw new RuntimeException("Failed to generate signature", e);
        }
    }

    /**
     * Verify HMAC signature
     *
     * Verification Flow:
     * Received Request → Extract signature → Rebuild signature → Compare
     *                                              ↓
     *                                         If match → Valid
     *                                         If differ → Invalid (tampered/replayed)
     */
    public boolean verifySignature(
            Map<String, Object> requestData,
            String nonce,
            Long timestamp,
            String receivedSignature) {

        // Generate expected signature
        String expectedSignature = generateSignature(
            requestData,
            nonce,
            timestamp
        );

        // Constant-time comparison (prevents timing attacks)
        return MessageDigest.isEqual(
            expectedSignature.getBytes(),
            receivedSignature.getBytes()
        );
    }

    /**
     * Build canonical string from request data
     *
     * Example:
     * Input:  {amount: 100, to: "acc_123", from: "acc_456"}
     * Output: "amount=100&from=acc_456&to=acc_123"
     *         (sorted alphabetically by key)
     */
    private String buildCanonicalString(Map<String, Object> data) {
        return data.entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .map(e -> e.getKey() + "=" + e.getValue())
            .collect(Collectors.joining("&"));
    }
}

/**
 * Client-side signature generation example
 */
@Component
public class SecureApiClient {

    @Autowired
    private HmacSignatureService signatureService;

    @Autowired
    private RestTemplate restTemplate;

    /**
     * Make secure API call with HMAC signature
     *
     * Request Structure:
     * POST /api/secure/payment
     * Headers:
     *   X-Nonce: abc123xyz
     *   X-Timestamp: 1710507600000
     *   X-Signature: k7L9mN2pQ5rT8vW1x...
     * Body: {payment data}
     */
    public PaymentResponse makeSecurePayment(PaymentRequest request) {
        // Generate nonce and timestamp
        String nonce = UUID.randomUUID().toString();
        Long timestamp = System.currentTimeMillis();

        // Convert request to map
        Map<String, Object> requestData = new HashMap<>();
        requestData.put("fromAccount", request.getFromAccount());
        requestData.put("toAccount", request.getToAccount());
        requestData.put("amount", request.getAmount().toString());
        requestData.put("currency", request.getCurrency());

        // Generate signature
        String signature = signatureService.generateSignature(
            requestData,
            nonce,
            timestamp
        );

        // Build HTTP request
        HttpHeaders headers = new HttpHeaders();
        headers.set("X-Nonce", nonce);
        headers.set("X-Timestamp", timestamp.toString());
        headers.set("X-Signature", signature);
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<PaymentRequest> entity =
            new HttpEntity<>(request, headers);

        // Make API call
        ResponseEntity<PaymentResponse> response = restTemplate.exchange(
            "https://api.example.com/secure/payment",
            HttpMethod.POST,
            entity,
            PaymentResponse.class
        );

        return response.getBody();
    }
}
```

---

## Production Implementation

### Complete Security Filter Chain

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Autowired
    private JwtAuthenticationFilter jwtAuthenticationFilter;

    @Autowired
    private ReplayAttackFilter replayAttackFilter;

    /**
     * Security Filter Chain
     *
     * Request Flow:
     * ┌─────────────────────────────────────────────────────────┐
     * │ HTTP Request                                            │
     * └──────────────────┬──────────────────────────────────────┘
     *                    ↓
     * ┌─────────────────────────────────────────────────────────┐
     * │ 1. Replay Attack Filter                                 │
     * │    - Timestamp validation                               │
     * │    - Nonce checking                                     │
     * │    - Signature verification                             │
     * └──────────────────┬──────────────────────────────────────┘
     *                    ↓
     * ┌─────────────────────────────────────────────────────────┐
     * │ 2. JWT Authentication Filter                            │
     * │    - Token validation                                   │
     * │    - JTI replay check                                   │
     * │    - User authentication                                │
     * └──────────────────┬──────────────────────────────────────┘
     *                    ↓
     * ┌─────────────────────────────────────────────────────────┐
     * │ 3. Authorization Filter                                 │
     * │    - Role checking                                      │
     * │    - Permission validation                              │
     * └──────────────────┬──────────────────────────────────────┘
     *                    ↓
     * ┌─────────────────────────────────────────────────────────┐
     * │ Controller                                              │
     * └─────────────────────────────────────────────────────────┘
     */
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .authorizeRequests()
                .antMatchers("/api/public/**").permitAll()
                .antMatchers("/api/secure/**").authenticated()
                .anyRequest().authenticated()
            .and()
            .addFilterBefore(
                replayAttackFilter,
                UsernamePasswordAuthenticationFilter.class
            )
            .addFilterBefore(
                jwtAuthenticationFilter,
                UsernamePasswordAuthenticationFilter.class
            );
    }
}

/**
 * Comprehensive Replay Attack Filter
 */
@Component
public class ReplayAttackFilter extends OncePerRequestFilter {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private HmacSignatureService signatureService;

    @Autowired
    private ObjectMapper objectMapper;

    private static final long MAX_REQUEST_AGE_MS = 120000; // 2 minutes
    private static final String[] PROTECTED_PATHS = {"/api/secure/**"};

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        // Check if path requires replay protection
        if (!requiresProtection(request.getRequestURI())) {
            filterChain.doFilter(request, response);
            return;
        }

        try {
            // Extract security headers
            String nonce = request.getHeader("X-Nonce");
            String timestampStr = request.getHeader("X-Timestamp");
            String signature = request.getHeader("X-Signature");

            // Validate headers exist
            validateHeaders(nonce, timestampStr, signature);

            Long timestamp = Long.parseLong(timestampStr);

            // Step 1: Validate timestamp
            validateTimestamp(timestamp);

            // Step 2: Validate nonce
            validateAndStoreNonce(nonce);

            // Step 3: Validate signature
            validateSignature(request, nonce, timestamp, signature);

            // All checks passed
            filterChain.doFilter(request, response);

        } catch (SecurityException e) {
            sendErrorResponse(response, HttpStatus.FORBIDDEN, e.getMessage());
        } catch (NumberFormatException e) {
            sendErrorResponse(
                response,
                HttpStatus.BAD_REQUEST,
                "Invalid timestamp format"
            );
        }
    }

    private boolean requiresProtection(String uri) {
        return Arrays.stream(PROTECTED_PATHS)
            .anyMatch(pattern ->
                new AntPathMatcher().match(pattern, uri)
            );
    }

    private void validateHeaders(String nonce, String timestamp, String signature) {
        if (nonce == null || nonce.trim().isEmpty()) {
            throw new SecurityException("X-Nonce header is required");
        }
        if (timestamp == null || timestamp.trim().isEmpty()) {
            throw new SecurityException("X-Timestamp header is required");
        }
        if (signature == null || signature.trim().isEmpty()) {
            throw new SecurityException("X-Signature header is required");
        }
    }

    private void validateTimestamp(Long requestTimestamp) {
        long currentTime = System.currentTimeMillis();
        long timeDiff = Math.abs(currentTime - requestTimestamp);

        if (timeDiff > MAX_REQUEST_AGE_MS) {
            throw new SecurityException(
                String.format(
                    "Request expired. Age: %d ms, Max: %d ms",
                    timeDiff, MAX_REQUEST_AGE_MS
                )
            );
        }
    }

    private void validateAndStoreNonce(String nonce) {
        String nonceKey = "nonce:" + nonce;

        // Check if nonce already exists
        Boolean exists = redisTemplate.hasKey(nonceKey);
        if (Boolean.TRUE.equals(exists)) {
            throw new SecurityException(
                "Replay attack detected: Nonce already used"
            );
        }

        // Store nonce with TTL
        redisTemplate.opsForValue().set(
            nonceKey,
            "used",
            MAX_REQUEST_AGE_MS / 1000,
            TimeUnit.SECONDS
        );
    }

    private void validateSignature(
            HttpServletRequest request,
            String nonce,
            Long timestamp,
            String receivedSignature) throws IOException {

        // Read request body
        CachedBodyHttpServletRequest cachedRequest =
            new CachedBodyHttpServletRequest(request);

        String body = StreamUtils.copyToString(
            cachedRequest.getInputStream(),
            StandardCharsets.UTF_8
        );

        // Parse body to map
        Map<String, Object> requestData =
            objectMapper.readValue(body, new TypeReference<>() {});

        // Verify signature
        boolean valid = signatureService.verifySignature(
            requestData,
            nonce,
            timestamp,
            receivedSignature
        );

        if (!valid) {
            throw new SecurityException("Invalid signature");
        }
    }

    private void sendErrorResponse(
            HttpServletResponse response,
            HttpStatus status,
            String message) throws IOException {

        response.setStatus(status.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);

        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("error", message);
        errorResponse.put("timestamp", System.currentTimeMillis());

        response.getWriter().write(
            objectMapper.writeValueAsString(errorResponse)
        );
    }
}

/**
 * Cached request body wrapper
 * (Required because request body can only be read once)
 */
public class CachedBodyHttpServletRequest extends HttpServletRequestWrapper {

    private byte[] cachedBody;

    public CachedBodyHttpServletRequest(HttpServletRequest request)
            throws IOException {
        super(request);
        InputStream requestInputStream = request.getInputStream();
        this.cachedBody = StreamUtils.copyToByteArray(requestInputStream);
    }

    @Override
    public ServletInputStream getInputStream() {
        return new CachedBodyServletInputStream(this.cachedBody);
    }

    @Override
    public BufferedReader getReader() {
        ByteArrayInputStream byteArrayInputStream =
            new ByteArrayInputStream(this.cachedBody);
        return new BufferedReader(
            new InputStreamReader(byteArrayInputStream)
        );
    }
}

/**
 * Cached body input stream
 */
public class CachedBodyServletInputStream extends ServletInputStream {

    private ByteArrayInputStream inputStream;

    public CachedBodyServletInputStream(byte[] cachedBody) {
        this.inputStream = new ByteArrayInputStream(cachedBody);
    }

    @Override
    public boolean isFinished() {
        return inputStream.available() == 0;
    }

    @Override
    public boolean isReady() {
        return true;
    }

    @Override
    public void setReadListener(ReadListener readListener) {
        throw new UnsupportedOperationException();
    }

    @Override
    public int read() {
        return inputStream.read();
    }
}
```

### Redis Configuration for Replay Protection

```java
@Configuration
public class RedisConfig {

    /**
     * Redis Structure for Replay Protection:
     *
     * ┌─────────────────────────────────────────────┐
     * │ Key Pattern: "nonce:{uuid}"                 │
     * │ Value: "used"                               │
     * │ TTL: 120 seconds (request window)           │
     * ├─────────────────────────────────────────────┤
     * │ Key Pattern: "jti:{jwt-id}"                 │
     * │ Value: "used"                               │
     * │ TTL: token expiry time                      │
     * ├─────────────────────────────────────────────┤
     * │ Key Pattern: "seq:{session-id}"             │
     * │ Value: last sequence number                 │
     * │ TTL: session timeout                        │
     * └─────────────────────────────────────────────┘
     */

    @Bean
    public RedisTemplate<String, String> redisTemplate(
            RedisConnectionFactory connectionFactory) {

        RedisTemplate<String, String> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);

        // Use String serialization for keys and values
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new StringRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(new StringRedisSerializer());

        return template;
    }

    @Bean
    public CacheManager cacheManager(RedisConnectionFactory connectionFactory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(2))
            .serializeKeysWith(
                RedisSerializationContext.SerializationPair.fromSerializer(
                    new StringRedisSerializer()
                )
            )
            .serializeValuesWith(
                RedisSerializationContext.SerializationPair.fromSerializer(
                    new GenericJackson2JsonRedisSerializer()
                )
            );

        return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(config)
            .build();
    }
}
```

---

## Interview Questions & Answers

### Q1: What is a replay attack and why is it dangerous?

**Answer:**

A replay attack is when an attacker intercepts a valid network request and retransmits it to fraudulently repeat an action. It's dangerous because:

1. **Financial Loss**: Payment transactions can be duplicated
2. **Unauthorized Access**: Authentication tokens can be reused
3. **Data Integrity**: Same action executed multiple times
4. **Resource Abuse**: API calls replayed to abuse services

**Example:**
```
Legitimate: User transfers $100 to merchant
Attacker:   Captures the request
            Replays it 10 times
Result:     $1000 transferred instead of $100
```

### Q2: How does nonce-based prevention work?

**Answer:**

A nonce (number used once) is a unique identifier added to each request. The server tracks used nonces and rejects duplicates.

**Implementation:**
```
1. Client generates UUID: "a1b2c3d4-..."
2. Client sends request with nonce header
3. Server checks Redis: "nonce:a1b2c3d4-..."
4. If exists → REJECT (replay detected)
5. If new → Process & store with TTL
```

**Pros:**
- Simple to implement
- Effective against immediate replays
- Works with stateless APIs

**Cons:**
- Requires storage (Redis/cache)
- Needs cleanup (TTL management)
- Clock synchronization not required

### Q3: What's the difference between nonce and timestamp validation?

**Answer:**

| Aspect | Nonce | Timestamp |
|--------|-------|-----------|
| **Purpose** | Uniqueness | Freshness |
| **Storage** | Required (Redis) | Not required |
| **Protection** | Prevents exact replays | Prevents old replays |
| **Limitation** | Storage overhead | Clock synchronization needed |
| **Best Use** | Stateless APIs | Real-time systems |

**Combined Approach (Best Practice):**
```java
// Timestamp: Reject old requests
if (requestAge > 2 minutes) {
    reject("Request too old");
}

// Nonce: Reject duplicate requests within window
if (nonceExists(nonce)) {
    reject("Request already processed");
}
```

### Q4: How does HMAC prevent replay attacks?

**Answer:**

HMAC (Hash-based Message Authentication Code) signs requests with a secret key, ensuring integrity and authenticity.

**Process:**
```
Client:
1. Build signature string: "amount=100&to=merchant&nonce=abc&timestamp=123"
2. Sign with secret: HMAC-SHA256(data, secret)
3. Send: Request + Signature

Server:
1. Rebuild signature string from request
2. Sign with same secret
3. Compare signatures
4. If match → Valid
   If differ → Rejected (tampered or invalid)
```

**Why it prevents replay:**
- Attacker cannot modify request (breaks signature)
- Attacker cannot create new signature (lacks secret)
- Combined with nonce: prevents reuse of valid signatures

### Q5: Explain JWT with JTI for replay prevention

**Answer:**

JTI (JWT ID) is a unique identifier in JWT tokens that prevents token reuse.

**Structure:**
```json
{
  "sub": "user_123",
  "jti": "550e8400-e29b-41d4-a716-446655440000",
  "iat": 1710507600,
  "exp": 1710511200
}
```

**Validation:**
```java
1. Decode JWT and extract jti
2. Check Redis: "jti:550e8400-..."
3. If exists → REJECT (token already used)
4. If new → Mark as used with TTL = (exp - now)
5. Process request
```

**Benefits:**
- Prevents token replay
- Automatic cleanup (TTL matches expiry)
- Works with distributed systems (Redis)

### Q6: How would you implement replay protection for WebSocket connections?

**Answer:**

Use sequence numbers for ordered message validation.

**Implementation:**
```java
// Connection establishment
Client connects → Server assigns sequence = 0

// Message exchange
Client sends: { seq: 1, data: "message1" }
Server expects: 1 ✓ → Process & expect next = 2

Client sends: { seq: 2, data: "message2" }
Server expects: 2 ✓ → Process & expect next = 3

// Replay attempt
Attacker sends: { seq: 1, data: "message1" }
Server expects: 3, received: 1 → REJECT (too old)
```

**State Management:**
```java
class WebSocketSession {
    private Long expectedSequence = 0L;
    private static final int SEQUENCE_WINDOW = 5;

    boolean validateSequence(Long receivedSeq) {
        if (receivedSeq < expectedSequence) {
            return false; // Too old
        }
        if (receivedSeq > expectedSequence + SEQUENCE_WINDOW) {
            return false; // Too far ahead
        }
        expectedSequence = receivedSeq + 1;
        return true;
    }
}
```

### Q7: What are the trade-offs between different replay prevention techniques?

**Answer:**

**1. Nonce:**
- **Pros**: Simple, no clock sync needed
- **Cons**: Requires storage, cleanup needed
- **Use case**: REST APIs, payment systems

**2. Timestamp:**
- **Pros**: No storage, self-expiring
- **Cons**: Clock synchronization required
- **Use case**: Real-time systems, IoT

**3. HMAC:**
- **Pros**: Prevents tampering + replay
- **Cons**: Secret key management, computational overhead
- **Use case**: Financial APIs, secure transactions

**4. JWT with JTI:**
- **Pros**: Stateless, distributed-friendly
- **Cons**: Token size, requires storage for JTI
- **Use case**: Microservices, OAuth flows

**5. Sequence Numbers:**
- **Pros**: Efficient, ordered messages
- **Cons**: Stateful, connection-specific
- **Use case**: WebSockets, gRPC streams

**Best Practice**: Combine multiple techniques
```
Timestamp (reject old)
  + Nonce (reject duplicates)
  + HMAC (prevent tampering)
= Comprehensive protection
```

### Q8: How would you handle replay protection in a distributed system?

**Answer:**

**Challenge**: Multiple servers must share replay detection state.

**Solution**: Use distributed cache (Redis)

```
Architecture:
┌──────────┐
│  Client  │
└────┬─────┘
     │ Request (nonce: abc123)
     ▼
┌─────────────────────────────────────┐
│      Load Balancer                  │
└─────────────────────────────────────┘
     │                    │
     ▼                    ▼
┌──────────┐        ┌──────────┐
│ Server 1 │        │ Server 2 │
└────┬─────┘        └────┬─────┘
     │                   │
     └──────┬───────┬────┘
            ▼       ▼
     ┌────────────────────┐
     │  Redis Cluster     │
     │  Shared Nonce DB   │
     └────────────────────┘
```

**Implementation:**
```java
@Service
public class DistributedReplayProtection {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    public boolean validateNonce(String nonce) {
        String key = "nonce:" + nonce;

        // Atomic check-and-set operation
        Boolean isNew = redisTemplate.opsForValue()
            .setIfAbsent(
                key,
                "used",
                120,
                TimeUnit.SECONDS
            );

        return Boolean.TRUE.equals(isNew);
    }
}
```

**Key Points:**
1. Use Redis for shared state
2. Atomic operations (SETNX) prevent race conditions
3. TTL for automatic cleanup
4. Redis cluster for high availability

### Q9: How do you prevent replay attacks in mobile apps?

**Answer:**

Mobile apps face unique challenges: offline mode, device compromise, root/jailbreak.

**Strategy:**
```
┌──────────────────────────────────────────────────────┐
│         Mobile App Security Layers                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│ 1. Device Fingerprinting                            │
│    → deviceId = hash(UUID + vendor + model)         │
│                                                      │
│ 2. Certificate Pinning                              │
│    → Prevent MITM attacks                           │
│                                                      │
│ 3. Request Signing (HMAC)                           │
│    → Sign with app-specific secret                  │
│                                                      │
│ 4. Nonce + Timestamp                                │
│    → Standard replay protection                     │
│                                                      │
│ 5. Token Rotation                                   │
│    → Short-lived access tokens (15 min)            │
│    → Refresh tokens (30 days, one-time use)        │
└──────────────────────────────────────────────────────┘
```

**Code Example:**
```java
// Mobile client
class SecureApiClient {

    String makeSecureRequest(String endpoint, Map<String, Object> data) {
        // Layer 1: Device fingerprint
        String deviceId = getDeviceFingerprint();

        // Layer 2: Nonce & timestamp
        String nonce = UUID.randomUUID().toString();
        long timestamp = System.currentTimeMillis();

        // Layer 3: Build signature
        data.put("deviceId", deviceId);
        data.put("nonce", nonce);
        data.put("timestamp", timestamp);

        String signature = HmacUtils.hmacSha256Hex(
            APP_SECRET,
            buildCanonicalString(data)
        );

        // Layer 4: Make request
        return httpClient.post(endpoint)
            .header("X-Device-Id", deviceId)
            .header("X-Nonce", nonce)
            .header("X-Timestamp", String.valueOf(timestamp))
            .header("X-Signature", signature)
            .body(data)
            .execute();
    }
}
```

### Q10: What monitoring and alerts would you set up for replay attack detection?

**Answer:**

**Monitoring Strategy:**

```
┌──────────────────────────────────────────────────────┐
│            Replay Attack Monitoring                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│ 1. Metrics to Track:                                │
│    ├─ Replay attempts per minute                    │
│    ├─ Failed signature validations                  │
│    ├─ Expired timestamp count                       │
│    ├─ Duplicate nonce count                         │
│    └─ JTI reuse attempts                            │
│                                                      │
│ 2. Alerts:                                          │
│    ├─ CRITICAL: >100 replay attempts/min           │
│    ├─ WARNING:  >10 from same IP                   │
│    └─ INFO:     Pattern anomalies                   │
│                                                      │
│ 3. Logging:                                         │
│    ├─ Log all rejected requests                     │
│    ├─ Include: IP, user, nonce, timestamp          │
│    └─ Store for forensic analysis                   │
└──────────────────────────────────────────────────────┘
```

**Implementation:**
```java
@Component
public class ReplayAttackMonitor {

    @Autowired
    private MeterRegistry meterRegistry;

    @Autowired
    private AlertService alertService;

    public void recordReplayAttempt(String reason, String ip, String user) {
        // Increment metric
        meterRegistry.counter(
            "security.replay.attempts",
            "reason", reason,
            "ip", ip
        ).increment();

        // Log for forensics
        log.warn(
            "Replay attack detected: reason={}, ip={}, user={}",
            reason, ip, user
        );

        // Check threshold for alerts
        long recentAttempts = getRecentAttempts(ip);
        if (recentAttempts > 10) {
            alertService.sendAlert(
                AlertLevel.CRITICAL,
                String.format(
                    "Multiple replay attempts from IP: %s (%d attempts)",
                    ip, recentAttempts
                )
            );
        }
    }

    @Scheduled(fixedRate = 60000) // Every minute
    public void checkReplayPatterns() {
        long totalAttempts = getTotalAttemptsLastMinute();

        if (totalAttempts > 100) {
            alertService.sendAlert(
                AlertLevel.CRITICAL,
                "High volume of replay attacks: " + totalAttempts
            );
        }
    }
}
```

**Dashboard Metrics:**
```
┌────────────────────────────────────────┐
│     Replay Attack Dashboard            │
├────────────────────────────────────────┤
│ Last Hour:                             │
│ ✗ 156 replay attempts blocked          │
│ ✓ 45,823 valid requests processed      │
│                                        │
│ Top Attack Sources:                    │
│ 1. 192.168.1.100 → 45 attempts        │
│ 2. 10.0.0.50     → 23 attempts        │
│ 3. 172.16.0.10   → 18 attempts        │
│                                        │
│ Attack Types:                          │
│ - Duplicate nonce:     78 (50%)       │
│ - Expired timestamp:   52 (33%)       │
│ - Invalid signature:   26 (17%)       │
└────────────────────────────────────────┘
```

---

## Summary

**Replay Attack Prevention Checklist:**

```
✓ Use Nonce for uniqueness
✓ Use Timestamp for freshness
✓ Use HMAC for integrity
✓ Use JWT with JTI for tokens
✓ Use Sequence numbers for streams
✓ Store state in Redis (distributed)
✓ Set appropriate TTLs
✓ Implement monitoring & alerts
✓ Log all security events
✓ Test with attack scenarios
```

**Best Practice Pattern:**
```java
// Multi-layer protection
if (!validateTimestamp(request)) reject();     // Layer 1: Freshness
if (!validateNonce(request)) reject();         // Layer 2: Uniqueness
if (!validateSignature(request)) reject();     // Layer 3: Integrity
processRequest(request);                       // Layer 4: Business logic
```

This comprehensive guide covers all aspects of replay attack prevention for experienced developers preparing for interviews.
