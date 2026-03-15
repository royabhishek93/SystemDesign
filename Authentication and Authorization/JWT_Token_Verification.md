# JWT Token Verification — Easy Explanation

## 1. The Basic Idea

When a user logs into an application, the frontend (browser or mobile app) sends the username and password to the server.

If the credentials are correct:

- The server generates a token (JWT – JSON Web Token)
- The server sends this token back to the frontend.

After that, the frontend stores the token (usually in local storage or cookies).

Now for every request:

```
Frontend → Server
Request + Access Token
```

Example:

```
GET /orders
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The server then checks the token before allowing the request.

### Visual: Complete JWT Authentication Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                    COMPLETE JWT FLOW                                 │
└──────────────────────────────────────────────────────────────────────┘

STEP 1: LOGIN
─────────────

┌─────────────┐
│   CLIENT    │
│  (Browser)  │
│             │
│  Username:  │
│  Password:  │
└──────┬──────┘
       │
       │ POST /login
       │ { username, password }
       ↓
┌─────────────────────────────────┐
│         SERVER                  │
│                                 │
│  1. Validate credentials        │
│  2. Generate JWT Token          │
│     - Create Header             │
│     - Create Payload (user info)│
│     - Sign with Secret Key      │
│                                 │
│  JWT = Header.Payload.Signature │
└──────┬──────────────────────────┘
       │
       │ Response: { token: "eyJhbGc..." }
       ↓
┌─────────────┐
│   CLIENT    │
│             │
│  Store JWT  │
│  (LocalStorage/Cookie)
└─────────────┘


STEP 2: SUBSEQUENT REQUESTS
────────────────────────────

┌─────────────┐
│   CLIENT    │
│             │
│  GET /orders│
│  Authorization: Bearer <JWT>
└──────┬──────┘
       │
       │ Request + JWT Token
       ↓
┌──────────────────────────────────────┐
│            SERVER                    │
│                                      │
│  1. Extract JWT from header          │
│  2. Split into 3 parts               │
│  3. Decode Header & Payload          │
│  4. Regenerate Signature             │
│  5. Compare Signatures               │
│     ├─ Match? ✅ → Allow             │
│     └─ Not Match? ❌ → Reject        │
└──────┬───────────────────────────────┘
       │
       │ Response: { orders: [...] }
       ↓
┌─────────────┐
│   CLIENT    │
│             │
│  Display    │
│  Orders     │
└─────────────┘
```

## 2. Important Question

In interviews, a common question is:

**How does the server verify the token?**
**Does the server store the token in the database and compare it?**

The answer is:

**No.**

JWT authentication is **stateless**, which means the server does not store the token.

Instead, the token itself contains enough information to verify its authenticity.

## 3. Structure of a JWT Token

A JWT token has three parts.

```
Header.Payload.Signature
```

Example:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
.
eyJ1c2VySWQiOjEyMywiZW1haWwiOiJhYmNAZ21haWwuY29tIn0
.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

Each part has a specific purpose.

### Visual: JWT Token Structure

```
┌────────────────────────────────────────────────────────────────────────┐
│                      JWT TOKEN STRUCTURE                               │
└────────────────────────────────────────────────────────────────────────┘

Complete JWT Token:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEyMywiZW1haWwiOiJhYmNAZ21haWwuY29tIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
└────────────┬────────────────────┘ └──────────────┬────────────────────────┘ └────────────┬────────────────┘
          PART 1                              PART 2                              PART 3
          HEADER                             PAYLOAD                           SIGNATURE


PART 1: HEADER (Algorithm & Token Type)
────────────────────────────────────────
Encoded: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
         │
         │ Base64 Decode
         ↓
Decoded: {
           "alg": "HS256",      ← Hashing algorithm
           "typ": "JWT"         ← Token type
         }


PART 2: PAYLOAD (User Data / Claims)
─────────────────────────────────────
Encoded: eyJ1c2VySWQiOjEyMywiZW1haWwiOiJhYmNAZ21haWwuY29tIn0
         │
         │ Base64 Decode
         ↓
Decoded: {
           "userId": 123,
           "email": "abc@gmail.com",
           "role": "ADMIN",
           "exp": 1680000000    ← Expiration time
         }

⚠️  WARNING: Anyone can decode this! Don't store sensitive data!


PART 3: SIGNATURE (Security / Tamper Protection)
─────────────────────────────────────────────────
Encoded: SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

How it's created:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  HMACSHA256(                                                │
│    base64UrlEncode(header) + "." +                          │
│    base64UrlEncode(payload),                                │
│    SECRET_KEY  ← Only server knows this!                    │
│  )                                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

This signature ensures:
✅ Token hasn't been modified
✅ Token was created by the server
✅ Token is authentic


VISUAL BREAKDOWN:
─────────────────

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   HEADER     │  .  │   PAYLOAD    │  .  │  SIGNATURE   │
│              │     │              │     │              │
│ Algorithm    │     │  User Info   │     │ Tamper-Proof │
│ Token Type   │     │  Claims      │     │ Verification │
│              │     │  Expiration  │     │              │
│ (Public)     │     │  (Public)    │     │  (Secret)    │
└──────────────┘     └──────────────┘     └──────────────┘
       ↓                    ↓                     ↓
  Base64 Encode       Base64 Encode      HMAC + Secret Key
       ↓                    ↓                     ↓
  Anyone can           Anyone can           Cannot forge
  decode               decode               without key!
```

## 4. First Part — Header

The header contains information about the token.

Usually it contains:

- Algorithm used for signing the token
- Type of token

Example:

```json
{
 "alg": "HS256",
 "typ": "JWT"
}
```

Explanation:

- **HS256** → Hashing algorithm used to create the signature
- **JWT** → Token type

This header is then Base64 encoded.

## 5. Second Part — Payload

The payload contains the **claims**.

Claims are simply information about the user.

Example:

```json
{
 "userId": 123,
 "email": "user@gmail.com",
 "role": "ADMIN"
}
```

Common payload data:

- user id
- email
- role
- token expiration time
- issued time

**Important point:**

Payload is **encoded** but **not encrypted**.

That means:

- Anyone can decode the payload
- They cannot change it without breaking the signature

Because of this, sensitive information should never be stored in the payload.

For example:

- ❌ password
- ❌ credit card details

## 6. Third Part — Signature

The signature is the most important part.

It ensures that the token has not been changed (tampered).

The signature is created using:

- Encoded header
- Encoded payload
- A secret key stored in the server

Signature formula:

```
Signature =
HMACSHA256(
  Base64UrlEncode(Header) + "." +
  Base64UrlEncode(Payload),
  SecretKey
)
```

**Only the server knows the secret key.**

This is what makes the token secure.

## 7. How the Server Verifies the Token

When the server receives a request with a token, it performs several steps.

### Visual: Complete Token Verification Process

```
┌────────────────────────────────────────────────────────────────────────┐
│              SERVER TOKEN VERIFICATION PROCESS                         │
└────────────────────────────────────────────────────────────────────────┘

INCOMING REQUEST
────────────────
GET /api/orders
Authorization: Bearer eyJhbGc...eyJ1c2V...SflKxw
                       │
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  STEP 1: SPLIT TOKEN                        │
└─────────────────────────────────────────────────────────────┘

Split by "." delimiter:
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Header     │   │   Payload    │   │  Signature   │
│  eyJhbGc...  │   │  eyJ1c2V...  │   │  SflKxw...   │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                   │                   │
       │                   │                   │
       ↓                   ↓                   ↓


┌─────────────────────────────────────────────────────────────┐
│              STEP 2: DECODE HEADER & PAYLOAD                │
└─────────────────────────────────────────────────────────────┘

Decode Header:                 Decode Payload:
eyJhbGc...                     eyJ1c2V...
    │                              │
    │ Base64 Decode                │ Base64 Decode
    ↓                              ↓
{                              {
  "alg": "HS256",                "userId": 123,
  "typ": "JWT"                   "email": "user@gmail.com",
}                                "role": "ADMIN",
                                 "exp": 1680000000
                               }

Server reads:                  Server reads:
✅ Algorithm to use            ✅ User ID: 123
                               ✅ User Email
                               ✅ User Role
                               ✅ Expiration time


┌─────────────────────────────────────────────────────────────┐
│           STEP 3: REGENERATE SIGNATURE                      │
└─────────────────────────────────────────────────────────────┘

Server recreates signature using:

┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Input 1: Encoded Header (from token)                   │
│           eyJhbGc...                                     │
│                                                          │
│  Input 2: Encoded Payload (from token)                  │
│           eyJ1c2V...                                     │
│                                                          │
│  Input 3: Server's Secret Key                           │
│           "MySecretKey123"  ← Only server knows this!    │
│                                                          │
│           ↓                                              │
│                                                          │
│  HMACSHA256(                                             │
│    encodedHeader + "." + encodedPayload,                 │
│    secretKey                                             │
│  )                                                       │
│           ↓                                              │
│                                                          │
│  Generated Signature: SflKxw...                          │
│                                                          │
└──────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│            STEP 4: COMPARE SIGNATURES                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐   ┌─────────────────────────┐
│  Received Signature         │   │  Generated Signature    │
│  (from token)               │   │  (just created)         │
│                             │   │                         │
│  SflKxwRJSMeKKF2QT4f...     │   │  SflKxwRJSMeKKF2QT4f... │
└─────────────┬───────────────┘   └───────────┬─────────────┘
              │                               │
              │                               │
              └───────────────┬───────────────┘
                              │
                       Compare (===)
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ↓                         ↓
        ┌────────────────┐        ┌───────────────┐
        │  MATCH ✅       │        │  NO MATCH ❌   │
        └────────┬───────┘        └───────┬───────┘
                 │                        │
                 ↓                        ↓
    ┌────────────────────────┐  ┌─────────────────────────┐
    │  TOKEN IS VALID        │  │  TOKEN IS INVALID       │
    │                        │  │                         │
    │  ✅ Not modified       │  │  ❌ Token was tampered  │
    │  ✅ Authentic          │  │  ❌ Signature mismatch  │
    │  ✅ From our server    │  │  ❌ Reject request      │
    │  ✅ Allow request      │  │                         │
    └────────────────────────┘  └─────────────────────────┘
                 │                        │
                 ↓                        ↓
    ┌────────────────────────┐  ┌─────────────────────────┐
    │  Check Expiration      │  │  Return 401             │
    │                        │  │  Unauthorized           │
    │  exp: 1680000000       │  └─────────────────────────┘
    │  current: 1679999000   │
    │                        │
    │  Not expired? ✅       │
    └────────┬───────────────┘
             │
             ↓
    ┌────────────────────────┐
    │  Execute Request       │
    │  Return Data           │
    │                        │
    │  200 OK                │
    │  { orders: [...] }     │
    └────────────────────────┘
```

### Step 1 — Split the Token

The server first splits the token into three parts.

- Header
- Payload
- Signature

### Step 2 — Decode Header and Payload

The server decodes:

- header
- payload

using Base64 decoding.

Now the server can read:

- user id
- email
- role
- expiration time

### Step 3 — Generate a New Signature

The server then creates a new signature using:

- encoded header
- encoded payload
- the same secret key

Example:

```
newSignature =
HMACSHA256(
  encodedHeader + "." + encodedPayload,
  secretKey
)
```

### Step 4 — Compare Signatures

Now the server compares:

```
Received Signature
VS
Generated Signature
```

Two possible results:

**Case 1 — Signatures Match**

If both signatures match:

- ✔ token is valid
- ✔ token has not been modified
- ✔ request is allowed

**Case 2 — Signatures Do Not Match**

If the signatures do not match:

- ❌ token was modified
- ❌ token is invalid
- ❌ request is rejected

## 8. Example of Token Tampering

Suppose an attacker changes the payload.

Original payload:

```
userId = 123
role = USER
```

Attacker changes it to:

```
userId = 999
role = ADMIN
```

But the attacker does not know the server's secret key, so they cannot generate the correct signature.

So the token becomes:

```
Modified Payload + Old Signature
```

When the server verifies it:

```
Generated Signature ≠ Received Signature
```

So the server immediately rejects the request.

### Visual: Token Tampering Attack

```
┌────────────────────────────────────────────────────────────────────────┐
│                    TOKEN TAMPERING ATTACK                              │
└────────────────────────────────────────────────────────────────────────┘

ORIGINAL VALID TOKEN
────────────────────

┌──────────────────────────────────────────────────────────────┐
│  Header.Payload.Signature                                    │
│                                                              │
│  eyJhbGc...                                                  │
│  {                                                           │
│    "alg": "HS256"                                            │
│  }                                                           │
│         .                                                    │
│  eyJ1c2V...                                                  │
│  {                                                           │
│    "userId": 123,      ← Original value                      │
│    "role": "USER"      ← Original value                      │
│  }                                                           │
│         .                                                    │
│  SflKxw...                                                   │
│  (Valid signature created with server's secret key)          │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ ✅ Valid token
                              ↓


ATTACKER'S ATTEMPT
──────────────────

Step 1: Attacker decodes payload
        (Anyone can decode Base64!)

Original Payload:                 Attacker Modifies:
{                                 {
  "userId": 123,       →            "userId": 999,     ← Changed!
  "role": "USER"       →            "role": "ADMIN"    ← Changed!
}                                 }


Step 2: Attacker encodes modified payload

Modified Payload (Base64):  XyZ9a2...  ← New encoded value


Step 3: Attacker creates tampered token

┌──────────────────────────────────────────────────────────────┐
│  TAMPERED TOKEN                                              │
│                                                              │
│  eyJhbGc...                 ← Original header (unchanged)    │
│         .                                                    │
│  XyZ9a2...                  ← Modified payload               │
│         .                                                    │
│  SflKxw...                  ← Old signature (unchanged)      │
│                                                              │
│  Problem: Old signature doesn't match new payload!           │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ Attacker sends tampered token
                              ↓


SERVER VERIFICATION
───────────────────

┌──────────────────────────────────────────────────────────────┐
│                   SERVER RECEIVES TOKEN                      │
└──────────────────────────────────────────────────────────────┘

Step 1: Split token
        Header: eyJhbGc...
        Payload: XyZ9a2...  ← Modified
        Signature: SflKxw... ← Old

Step 2: Decode payload
        {
          "userId": 999,
          "role": "ADMIN"
        }

Step 3: Regenerate signature with server's secret key

        HMACSHA256(
          eyJhbGc... + "." + XyZ9a2...,  ← New payload
          secretKey
        )
        = ABC123...  ← New signature (different!)


Step 4: Compare signatures

        ┌─────────────────────┐   ┌─────────────────────┐
        │ Received Signature  │   │ Generated Signature │
        │                     │   │                     │
        │    SflKxw...        │ ≠ │    ABC123...        │
        │    (old)            │   │    (new)            │
        └─────────────────────┘   └─────────────────────┘
                    │                      │
                    └──────────┬───────────┘
                               │
                          NOT EQUAL!
                               │
                               ↓
                    ┌──────────────────────┐
                    │   SIGNATURES MISMATCH│
                    │                      │
                    │   ❌ TOKEN INVALID   │
                    │   ❌ REQUEST REJECTED│
                    │                      │
                    │   Response: 401      │
                    │   Unauthorized       │
                    └──────────────────────┘


WHY ATTACK FAILED
─────────────────

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Attacker modified the payload                              │
│       ↓                                                     │
│  But doesn't know the server's SECRET KEY                   │
│       ↓                                                     │
│  Cannot generate valid signature for modified payload       │
│       ↓                                                     │
│  Server detects signature mismatch                          │
│       ↓                                                     │
│  Request rejected! ✅ Security maintained!                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘


KEY TAKEAWAY
────────────

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  🔐 The signature is the SECURITY MECHANISM                  │
│                                                              │
│  • Anyone can decode and modify the payload                  │
│  • But they CANNOT create a valid signature                  │
│  • Only the server with the secret key can do that           │
│  • This makes JWT tamper-proof!                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 9. Stateless Authentication

JWT authentication is called **stateless authentication**.

Because:

- The server does not store sessions
- The server does not store tokens
- Each request contains the complete authentication information

Benefits:

- ✔ better scalability
- ✔ good for microservices
- ✔ works well with distributed systems

### Visual: Stateful vs Stateless Authentication

```
┌────────────────────────────────────────────────────────────────────────┐
│              STATEFUL vs STATELESS AUTHENTICATION                      │
└────────────────────────────────────────────────────────────────────────┘

STATEFUL AUTHENTICATION (Session-Based)
────────────────────────────────────────

Login:
┌─────────┐                           ┌─────────┐
│ Client  │ ─── username/password ──→ │ Server  │
└─────────┘                           └────┬────┘
     ↑                                     │
     │                                     │ Create session
     │                                     │ Store in database
     │                                     ↓
     │                              ┌─────────────────┐
     │                              │   DATABASE      │
     │                              ├─────────────────┤
     │                              │ Session ID      │
     │   ← sessionID: abc123        │ abc123 → user123│
     │                              └─────────────────┘
┌─────────┐
│ Client  │
│ Stores: │
│ abc123  │
└─────────┘


Subsequent Request:
┌─────────┐                           ┌─────────┐
│ Client  │ ─── sessionID: abc123 ──→ │ Server  │
└─────────┘                           └────┬────┘
                                           │
                                           │ Query database
                                           ↓
                                    ┌─────────────────┐
                                    │   DATABASE      │
                                    │                 │
                                    │ Find session    │
                                    │ abc123 → user123│
                                    └────┬────────────┘
                                         │
                                         │ User found
                                         ↓
                                    ┌─────────┐
                                    │ Server  │
                                    │ Allow   │
                                    │ Request │
                                    └─────────┘

Problems:
❌ Database query on every request (slow)
❌ Session data must be shared across servers
❌ Hard to scale horizontally
❌ Database becomes bottleneck


STATELESS AUTHENTICATION (JWT-Based)
─────────────────────────────────────

Login:
┌─────────┐                           ┌─────────┐
│ Client  │ ─── username/password ──→ │ Server  │
└─────────┘                           └────┬────┘
     ↑                                     │
     │                                     │ Generate JWT
     │                                     │ Sign with secret key
     │                                     │ (NO database storage!)
     │                                     ↓
     │                              JWT Token Created:
     │   ← JWT Token                Header.Payload.Signature
     │   eyJhbGc...
     │
┌─────────┐
│ Client  │
│ Stores: │
│ JWT     │
└─────────┘


Subsequent Request:
┌─────────┐                           ┌─────────┐
│ Client  │ ─── JWT: eyJhbGc... ────→ │ Server  │
└─────────┘                           └────┬────┘
                                           │
                                           │ Verify signature
                                           │ (NO database query!)
                                           │ Decode payload
                                           ↓
                                      Token Valid?
                                           │
                                           │ ✅ Signature matches
                                           │ ✅ Not expired
                                           ↓
                                    ┌─────────┐
                                    │ Server  │
                                    │ Allow   │
                                    │ Request │
                                    └─────────┘

Benefits:
✅ No database query (fast!)
✅ No server-side session storage
✅ Easy to scale horizontally
✅ Perfect for microservices
✅ Works across multiple servers


COMPARISON IN MICROSERVICES
────────────────────────────

Stateful (Session):

Client → Server A → Database (check session)
       → Server B → Database (check session)
       → Server C → Database (check session)

All servers need access to shared session store!


Stateless (JWT):

Client → Server A → Verify JWT (no DB needed) ✅
       → Server B → Verify JWT (no DB needed) ✅
       → Server C → Verify JWT (no DB needed) ✅

Each server independently verifies the token!


SCALING COMPARISON
──────────────────

Stateful (Sessions):
┌─────────┐
│ Client  │
└────┬────┘
     │
     ↓
┌──────────────────────────────────┐
│      Load Balancer               │
└────┬─────────┬─────────┬─────────┘
     │         │         │
     ↓         ↓         ↓
┌────────┐ ┌────────┐ ┌────────┐
│Server A│ │Server B│ │Server C│
└────┬───┘ └────┬───┘ └────┬───┘
     │          │          │
     └──────────┼──────────┘
                ↓
        ┌──────────────┐
        │   SHARED     │
        │   SESSION    │
        │   DATABASE   │  ← Bottleneck!
        └──────────────┘


Stateless (JWT):
┌─────────┐
│ Client  │
└────┬────┘
     │
     ↓
┌──────────────────────────────────┐
│      Load Balancer               │
└────┬─────────┬─────────┬─────────┘
     │         │         │
     ↓         ↓         ↓
┌────────┐ ┌────────┐ ┌────────┐
│Server A│ │Server B│ │Server C│
│Verify  │ │Verify  │ │Verify  │
│JWT     │ │JWT     │ │JWT     │
└────────┘ └────────┘ └────────┘

No shared database needed! ✅
Each server is independent!
```

## 10. Short Interview Answer (Best Way to Say)

You can say this in an interview:

> JWT token has three parts: header, payload, and signature.
> The header contains the algorithm, the payload contains user information, and the signature is generated using the server's secret key.
> When the server receives the token, it recreates the signature using the same secret key and compares it with the received signature.
> If both signatures match, the token is valid and the request is allowed.
> If they do not match, the token is rejected.
> Since the server does not store the token, this mechanism is called stateless authentication.