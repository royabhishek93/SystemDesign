# OAuth 2.0 — Easy Explanation

## 1. What is OAuth 2.0?

OAuth 2.0 is an **authorization framework** (not authentication).

It allows a third-party application to access your resources on another service **without sharing your password**.

**Real-world example:**

When you click "Login with Google" on a website:

- The website doesn't get your Google password
- Google asks: "Do you want to allow this app to access your profile?"
- You approve
- The website gets permission to access your Google profile

This is OAuth 2.0 in action.

## 2. Key Terminology

Before understanding the flow, you need to know these terms:

### Resource Owner
- The **user** who owns the data
- Example: You (the person with a Google account)

### Resource Server
- The server that **hosts the protected resources**
- Example: Google's servers (storing your profile, emails, etc.)

### Client
- The **application** that wants to access the user's data
- Example: A third-party app like Trello or Notion

### Authorization Server
- The server that **authenticates the user** and issues access tokens
- Example: Google's OAuth server

### Access Token
- A **token** that allows the client to access protected resources
- Like a temporary key card

### Refresh Token
- A **long-lived token** used to get a new access token when it expires
- Like a master key that can generate temporary key cards

## 3. Why OAuth 2.0?

### Problem Without OAuth:

Suppose you want to use a third-party app (like Canva) to access your Google Drive files.

**Old approach (BAD):**

1. Canva asks for your Google username and password
2. You give them your credentials
3. Canva logs into Google on your behalf

**Issues:**

- ❌ You shared your password with Canva
- ❌ Canva has full access to your account
- ❌ You can't revoke access without changing your password
- ❌ If Canva is hacked, your Google account is compromised

### Solution With OAuth:

1. Canva redirects you to Google
2. Google asks: "Allow Canva to access your Drive files?"
3. You approve
4. Google gives Canva an **access token** (not your password)
5. Canva uses the token to access only your Drive files

**Benefits:**

- ✔ Password never shared
- ✔ Limited access (only what you approved)
- ✔ You can revoke access anytime
- ✔ More secure

### Visual: Problem Without OAuth vs With OAuth

```
┌────────────────────────────────────────────────────────────────────────┐
│              WITHOUT OAuth 2.0 (Old Way - INSECURE)                    │
└────────────────────────────────────────────────────────────────────────┘

┌──────────┐
│  User    │
└────┬─────┘
     │
     │ 1. User wants to use Canva to edit Google Drive files
     ↓
┌──────────────────┐
│     CANVA        │
│                  │
│ "Enter your      │
│  Google username │
│  and password"   │
└────┬─────────────┘
     │
     │ 2. User gives Canva their Google credentials
     │    Username: user@gmail.com
     │    Password: myPassword123  ← 🚨 SECURITY RISK!
     ↓
┌──────────────────┐
│     CANVA        │
│                  │
│ Stores:          │
│ user@gmail.com   │
│ myPassword123    │ ← 🚨 Canva has your real password!
└────┬─────────────┘
     │
     │ 3. Canva logs into Google using your credentials
     ↓
┌──────────────────┐
│  GOOGLE          │
│                  │
│ ✅ Login success │
│                  │
│ Canva has FULL   │
│ access to        │
│ everything!      │
└──────────────────┘

Problems:
❌ Password shared with third party
❌ Canva has unrestricted access
❌ Can't revoke access (must change password)
❌ If Canva is hacked, Google account compromised
❌ No audit trail
❌ Canva can do anything in your account


┌────────────────────────────────────────────────────────────────────────┐
│              WITH OAuth 2.0 (Modern Way - SECURE)                      │
└────────────────────────────────────────────────────────────────────────┘

┌──────────┐
│  User    │
└────┬─────┘
     │
     │ 1. User wants to use Canva to edit Google Drive files
     ↓
┌──────────────────┐
│     CANVA        │
│                  │
│ "Login with      │
│  Google"         │
└────┬─────────────┘
     │
     │ 2. Canva redirects user to Google
     ↓
┌──────────────────────────────────────┐
│        GOOGLE LOGIN PAGE             │
│                                      │
│  Enter your Google credentials:      │
│  (Directly on Google's site, not    │
│   shared with Canva!)               │
│                                      │
│  Username: user@gmail.com            │
│  Password: ************              │
│                                      │
│  ✅ Login                            │
└────┬─────────────────────────────────┘
     │
     │ 3. Google shows permission screen
     ↓
┌──────────────────────────────────────┐
│        GOOGLE PERMISSION PAGE        │
│                                      │
│  Canva wants to access:              │
│  ☑ View and download your Drive files│
│  ☑ Upload files to your Drive        │
│                                      │
│  Limited access, not full account!   │
│                                      │
│  [Deny]  [Allow]                     │
└────┬─────────────────────────────────┘
     │
     │ 4. User approves
     ↓
┌──────────────────────────────────────┐
│        GOOGLE                        │
│                                      │
│  Generates Access Token:             │
│  ya29.a0AfH6SMBx...                  │
│                                      │
│  Token allows:                       │
│  ✅ Drive file access only           │
│  ❌ No email access                  │
│  ❌ No password                      │
└────┬─────────────────────────────────┘
     │
     │ 5. Google gives token to Canva
     ↓
┌──────────────────┐
│     CANVA        │
│                  │
│ Receives:        │
│ Access Token     │
│ (NOT password!)  │
│                  │
│ Can only access  │
│ Drive files      │
└────┬─────────────┘
     │
     │ 6. Canva uses token to access Drive
     ↓
┌──────────────────┐
│  GOOGLE DRIVE    │
│                  │
│ ✅ Token valid   │
│ ✅ Access granted│
│                  │
│ Limited to Drive │
│ files only       │
└──────────────────┘

Benefits:
✅ Password NEVER shared with Canva
✅ Limited access (only Drive files)
✅ Can revoke access anytime (from Google settings)
✅ If Canva is hacked, only token is leaked (can revoke)
✅ Complete audit trail
✅ Canva can only do what user approved
```

## 4. OAuth 2.0 Flow — Authorization Code Grant (Most Common)

This is the most secure and commonly used OAuth flow.

### Step-by-Step Flow:

```
User (Resource Owner)
    ↓
Client Application (e.g., Trello)
    ↓
Authorization Server (e.g., Google)
    ↓
Resource Server (e.g., Google Drive)
```

### Complete Visual Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│         OAuth 2.0 AUTHORIZATION CODE FLOW (Complete)                   │
└────────────────────────────────────────────────────────────────────────┘

ACTORS:
───────
┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  ┌──────────────┐
│    USER     │  │   TRELLO    │  │     GOOGLE       │  │    GOOGLE    │
│  (Resource  │  │   (Client)  │  │ (Authorization   │  │   (Resource  │
│   Owner)    │  │             │  │     Server)      │  │    Server)   │
└─────────────┘  └─────────────┘  └──────────────────┘  └──────────────┘


STEP 1: User Initiates Login
──────────────────────────────

User                Trello
  │                   │
  │ Click "Login      │
  │  with Google"     │
  │──────────────────→│
  │                   │
  │                   │ Redirect to Google with:
  │                   │ • client_id
  │                   │ • redirect_uri
  │                   │ • scope (permissions)
  │                   │ • state (security)
  │                   │
  │←──────────────────│
  │                   │
  │  302 Redirect to:
  │  https://accounts.google.com/o/oauth2/auth?
  │    client_id=123456
  │    &redirect_uri=https://trello.com/callback
  │    &response_type=code
  │    &scope=profile email
  │    &state=xyz123
  │
  ↓


STEP 2: User Authenticates at Google
──────────────────────────────────────

User                              Google Auth Server
  │                                      │
  │  GET /o/oauth2/auth?...              │
  │─────────────────────────────────────→│
  │                                      │
  │                                      │ 1. Verify client_id
  │                                      │ 2. Show login page
  │                                      │
  │  ←────────────────────────────────────
  │  Login Page:                         │
  │  ┌───────────────────────────┐       │
  │  │  Google Login             │       │
  │  │                           │       │
  │  │  Email: _______________   │       │
  │  │  Password: ____________   │       │
  │  │                           │       │
  │  │  [Sign In]                │       │
  │  └───────────────────────────┘       │
  │                                      │
  │  User enters credentials             │
  │─────────────────────────────────────→│
  │                                      │
  │                                      │ Validate credentials
  │                                      │ ✅ Success
  │                                      │
  ↓                                      ↓


STEP 3: User Grants Permission
────────────────────────────────

User                              Google Auth Server
  │                                      │
  │  ←────────────────────────────────────
  │  Permission Screen:                  │
  │  ┌───────────────────────────┐       │
  │  │  Trello wants to:         │       │
  │  │                           │       │
  │  │  ☑ View your profile      │       │
  │  │  ☑ View your email        │       │
  │  │                           │       │
  │  │  [Deny]  [Allow]          │       │
  │  └───────────────────────────┘       │
  │                                      │
  │  User clicks "Allow"                 │
  │─────────────────────────────────────→│
  │                                      │
  │                                      │ Generate authorization code
  │                                      │ code = "AUTH_CODE_123"
  │                                      │ (Short-lived: 10 mins)
  │                                      │
  ↓                                      ↓


STEP 4: Redirect with Authorization Code
──────────────────────────────────────────

User                Trello              Google Auth Server
  │                   │                      │
  │  ←────────────────────────────────────────
  │  302 Redirect to:                        │
  │  https://trello.com/callback?            │
  │    code=AUTH_CODE_123                    │
  │    &state=xyz123                         │
  │                   │                      │
  │──────────────────→│                      │
  │                   │                      │
  │                   │ Verify state         │
  │                   │ ✅ State matches!    │
  │                   │                      │
  ↓                   ↓                      ↓


STEP 5: Exchange Code for Access Token
────────────────────────────────────────
(Server-to-Server, User not involved)

                 Trello Backend          Google Auth Server
                      │                          │
                      │ POST /token              │
                      │ Body:                    │
                      │ • grant_type=            │
                      │   authorization_code     │
                      │ • code=AUTH_CODE_123     │
                      │ • client_id=123456       │
                      │ • client_secret=SECRET   │
                      │ • redirect_uri=...       │
                      │─────────────────────────→│
                      │                          │
                      │                          │ Verify:
                      │                          │ ✅ Code valid
                      │                          │ ✅ Client authenticated
                      │                          │ ✅ Redirect URI matches
                      │                          │
                      │                          │ Generate tokens:
                      │                          │ • access_token
                      │                          │ • refresh_token
                      │                          │ • expires_in
                      │                          │
                      │  ←───────────────────────│
                      │  Response:               │
                      │  {                       │
                      │    "access_token":       │
                      │      "ya29.a0AfH6...",   │
                      │    "refresh_token":      │
                      │      "1//0gQ7r...",      │
                      │    "expires_in": 3600,   │
                      │    "token_type": "Bearer"│
                      │  }                       │
                      │                          │
                      ↓                          ↓


STEP 6: Access Protected Resources
────────────────────────────────────

User              Trello Backend          Google Resource Server
  │                   │                          │
  │  Request data     │                          │
  │──────────────────→│                          │
  │                   │                          │
  │                   │ GET /oauth2/v1/userinfo  │
  │                   │ Authorization: Bearer    │
  │                   │   ya29.a0AfH6...         │
  │                   │─────────────────────────→│
  │                   │                          │
  │                   │                          │ Validate token
  │                   │                          │ ✅ Token valid
  │                   │                          │ ✅ Has required scope
  │                   │                          │
  │                   │  ←───────────────────────│
  │                   │  {                       │
  │                   │    "id": "123456789",    │
  │                   │    "email": "user@...",  │
  │                   │    "name": "John Doe"    │
  │                   │  }                       │
  │                   │                          │
  │  ←────────────────│                          │
  │  Show user data   │                          │
  │                   │                          │
  ↓                   ↓                          ↓


STEP 7: Token Expiration & Refresh
────────────────────────────────────
(Happens after access token expires, e.g., 1 hour)

                 Trello Backend          Google Auth Server
                      │                          │
                      │ Access token expired!    │
                      │                          │
                      │ POST /token              │
                      │ Body:                    │
                      │ • grant_type=            │
                      │   refresh_token          │
                      │ • refresh_token=         │
                      │   1//0gQ7r...            │
                      │ • client_id=123456       │
                      │ • client_secret=SECRET   │
                      │─────────────────────────→│
                      │                          │
                      │                          │ Verify refresh token
                      │                          │ ✅ Valid
                      │                          │
                      │                          │ Generate new
                      │                          │ access token
                      │                          │
                      │  ←───────────────────────│
                      │  {                       │
                      │    "access_token":       │
                      │      "ya29.NEW_TOKEN",   │
                      │    "expires_in": 3600    │
                      │  }                       │
                      │                          │
                      │ Continue using new token │
                      │                          │
                      ↓                          ↓


SUMMARY OF TOKEN FLOW
──────────────────────

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Authorization Code (Short-lived: 10 mins)                  │
│  └─→ Used once to get access token                          │
│                                                             │
│  Access Token (Short-lived: 1 hour)                         │
│  └─→ Used to access protected resources                     │
│      When expired, use refresh token                        │
│                                                             │
│  Refresh Token (Long-lived: days/weeks)                     │
│  └─→ Used to get new access tokens                          │
│      Stored securely, never exposed to user                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Steps:

#### Step 1: User Clicks "Login with Google"

The client application (Trello) redirects the user to Google's authorization server.

**Request:**

```
GET https://accounts.google.com/o/oauth2/auth
  ?client_id=123456
  &redirect_uri=https://trello.com/callback
  &response_type=code
  &scope=profile email
  &state=random_string
```

**Parameters:**

- `client_id` → Identifies the client (Trello)
- `redirect_uri` → Where to send the user after authorization
- `response_type=code` → Requesting an authorization code
- `scope` → What permissions the client wants (profile, email, etc.)
- `state` → Random value for security (prevents CSRF attacks)

#### Step 2: User Logs In and Approves

- Google shows a login page
- User enters credentials
- Google shows: "Trello wants to access your profile and email. Allow?"
- User clicks "Allow"

#### Step 3: Authorization Server Sends Authorization Code

Google redirects the user back to Trello with an **authorization code**.

**Redirect:**

```
https://trello.com/callback
  ?code=AUTH_CODE_123
  &state=random_string
```

**Important:**

- The authorization code is **short-lived** (usually expires in 10 minutes)
- It's not the access token yet

#### Step 4: Client Exchanges Code for Access Token

Trello's backend makes a **server-to-server** request to Google.

**Request:**

```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=AUTH_CODE_123
&client_id=123456
&client_secret=SECRET_KEY
&redirect_uri=https://trello.com/callback
```

**Parameters:**

- `grant_type=authorization_code` → Type of grant
- `code` → The authorization code received
- `client_secret` → Secret key (proves Trello is legitimate)

**Response:**

```json
{
  "access_token": "ya29.a0AfH6SMBx...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "1//0gQ7r...",
  "scope": "profile email"
}
```

#### Step 5: Client Accesses Protected Resources

Now Trello can access the user's Google profile using the access token.

**Request:**

```
GET https://www.googleapis.com/oauth2/v1/userinfo
Authorization: Bearer ya29.a0AfH6SMBx...
```

**Response:**

```json
{
  "id": "123456789",
  "email": "user@gmail.com",
  "name": "John Doe",
  "picture": "https://..."
}
```

#### Step 6: Access Token Expires — Use Refresh Token

Access tokens are **short-lived** (e.g., 1 hour).

When the access token expires, the client uses the **refresh token** to get a new one.

**Request:**

```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token=1//0gQ7r...
&client_id=123456
&client_secret=SECRET_KEY
```

**Response:**

```json
{
  "access_token": "ya29.NEW_TOKEN...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## 5. OAuth 2.0 Grant Types

OAuth 2.0 has several **grant types** (flows) for different scenarios.

### Visual: All Grant Types Comparison

```
┌────────────────────────────────────────────────────────────────────────┐
│                OAuth 2.0 GRANT TYPES OVERVIEW                          │
└────────────────────────────────────────────────────────────────────────┘

1. AUTHORIZATION CODE GRANT (Most Secure)
──────────────────────────────────────────

Use Case: Web apps with backend server
Security: ✅ Client secret on server (secure)

User → Client → Auth Server → Auth Code → Client
                                            ↓
                            Exchange code + secret for token
                                            ↓
                                       Access Token

Flow:
┌──────┐    ┌────────┐    ┌──────────┐    ┌──────────┐
│ User │ ─→ │ Client │ ─→ │   Auth   │ ─→ │ Resource │
└──────┘    │ (Web)  │    │  Server  │    │  Server  │
            └────────┘    └──────────┘    └──────────┘
                 ↓              ↓
           Auth Code    Access Token


2. AUTHORIZATION CODE + PKCE (For Mobile/SPA)
──────────────────────────────────────────────

Use Case: Mobile apps, Single Page Apps (React, Angular)
Security: ✅ PKCE prevents interception (no client secret needed)

User → Client → Auth Server → Auth Code → Client
         ↓                                   ↓
    Generate code_verifier        Verify code_challenge
    & code_challenge                       ↓
                                    Access Token

Flow:
┌──────┐    ┌────────┐    ┌──────────┐    ┌──────────┐
│ User │ ─→ │Mobile/ │ ─→ │   Auth   │ ─→ │ Resource │
└──────┘    │  SPA   │    │  Server  │    │  Server  │
            └────────┘    └──────────┘    └──────────┘
                 ↓              ↓
           Auth Code +   Access Token
           Code Verifier


3. IMPLICIT GRANT (Deprecated - Don't Use!)
────────────────────────────────────────────

Use Case: Old SPAs (no longer recommended)
Security: ❌ Token in URL (insecure)

User → Client → Auth Server → Access Token (directly in URL)
                                     ↓
                              ❌ Exposed in browser

Flow:
┌──────┐    ┌────────┐    ┌──────────┐
│ User │ ─→ │  SPA   │ ─→ │   Auth   │
└──────┘    │        │    │  Server  │
            └────────┘    └──────────┘
                 ↑              ↓
           Access Token (in redirect URL)
           ❌ Security risk!


4. CLIENT CREDENTIALS GRANT (Machine-to-Machine)
─────────────────────────────────────────────────

Use Case: Server-to-server communication (no user)
Security: ✅ Client secret used

Service A → Auth Server → Access Token → Service B

Flow:
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Service  │ ─→ │   Auth   │ ─→ │ Service  │
│    A     │    │  Server  │    │    B     │
└──────────┘    └──────────┘    └──────────┘
      ↓              ↓
 client_id +   Access Token
 client_secret

Example: Cron job accessing API


5. RESOURCE OWNER PASSWORD CREDENTIALS (Legacy)
────────────────────────────────────────────────

Use Case: Highly trusted apps only (not recommended)
Security: ❌ User gives password to client

User → Client (with password) → Auth Server → Access Token

Flow:
┌──────┐    ┌────────┐    ┌──────────┐
│ User │ ─→ │ Client │ ─→ │   Auth   │
└──────┘    │        │    │  Server  │
   ↓        └────────┘    └──────────┘
Password         ↓              ↓
shared!    username +    Access Token
          password


COMPARISON TABLE
────────────────

┌──────────────────┬─────────────┬──────────┬───────────────┐
│   Grant Type     │  Use Case   │ Security │   User Login  │
├──────────────────┼─────────────┼──────────┼───────────────┤
│ Authorization    │ Web apps    │   ✅✅   │ Redirect to   │
│ Code             │ with server │          │ auth provider │
├──────────────────┼─────────────┼──────────┼───────────────┤
│ Auth Code +PKCE  │ Mobile/SPA  │   ✅✅   │ Redirect to   │
│                  │             │          │ auth provider │
├──────────────────┼─────────────┼──────────┼───────────────┤
│ Implicit         │ (Deprecated)│   ❌     │ Redirect to   │
│                  │             │          │ auth provider │
├──────────────────┼─────────────┼──────────┼───────────────┤
│ Client           │ Server to   │   ✅     │ No user       │
│ Credentials      │ server      │          │ involved      │
├──────────────────┼─────────────┼──────────┼───────────────┤
│ Password         │ Trusted     │   ❌     │ Direct to     │
│ Credentials      │ apps only   │          │ client        │
└──────────────────┴─────────────┴──────────┴───────────────┘
```

### 1. Authorization Code Grant (Most Secure)

- **Use case:** Web applications with a backend
- **Flow:** User → Client → Auth Server → Access Token
- **Security:** Client secret is stored on the server

### 2. Authorization Code with PKCE (for Mobile/SPA)

- **Use case:** Mobile apps, Single Page Applications (React, Angular)
- **Flow:** Similar to Authorization Code, but uses PKCE for extra security
- **Security:** No client secret needed (prevents interception)

### 3. Implicit Grant (Deprecated)

- **Use case:** Old SPAs (no longer recommended)
- **Flow:** Access token returned directly (no authorization code)
- **Security:** Less secure (token exposed in URL)

### 4. Client Credentials Grant

- **Use case:** Machine-to-machine communication (no user involved)
- **Flow:** Client → Auth Server → Access Token
- **Example:** A backend service accessing an API

### 5. Resource Owner Password Credentials Grant (Legacy)

- **Use case:** Trusted applications only
- **Flow:** User gives username/password to the client
- **Security:** Not recommended (defeats the purpose of OAuth)

## 6. OAuth 2.0 vs JWT

| Feature | OAuth 2.0 | JWT |
|---------|-----------|-----|
| **Purpose** | Authorization framework | Token format |
| **What it does** | Defines how to get access tokens | Defines token structure |
| **Use case** | Third-party access | Stateless authentication |
| **Token type** | Can use JWT or opaque tokens | Always JWT format |

**Important:**

OAuth 2.0 can use JWT as the token format, but they are not the same thing.

### Visual: OAuth 2.0 vs JWT

```
┌────────────────────────────────────────────────────────────────────────┐
│                    OAuth 2.0 vs JWT                                    │
└────────────────────────────────────────────────────────────────────────┘

OAuth 2.0
─────────
WHAT IT IS:
• Authorization Framework (not a protocol)
• Defines HOW to get access tokens
• Defines authorization flows

WHAT IT DOES:
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Defines the process:                                    │
│                                                          │
│  User → Client → Authorization Server                    │
│                        ↓                                 │
│                  Authorization Code                      │
│                        ↓                                 │
│                  Access Token                            │
│                        ↓                                 │
│                  Resource Server                         │
│                                                          │
└──────────────────────────────────────────────────────────┘

TOKEN FORMAT:
Can use ANY token format:
• JWT (structured, self-contained)
• Opaque token (random string, database lookup)

EXAMPLE:
Access Token = "ya29.a0AfH6SMBx..." (could be anything)


JWT (JSON Web Token)
────────────────────
WHAT IT IS:
• Token Format/Structure
• Defines HOW tokens are structured
• Self-contained (has all info inside)

WHAT IT DOES:
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Defines the structure:                                  │
│                                                          │
│  Header.Payload.Signature                                │
│                                                          │
│  {alg,typ}.{userId,email,role}.{signature}               │
│                                                          │
│  Self-contained: all info in the token itself            │
│  No database lookup needed                               │
│                                                          │
└──────────────────────────────────────────────────────────┘

TOKEN FORMAT:
Always follows JWT structure:
• Header (algorithm, type)
• Payload (claims, user info)
• Signature (tamper protection)

EXAMPLE:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEyM30.SflKxw...


HOW THEY RELATE
───────────────

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  OAuth 2.0 (Framework)                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │  "How do I get a token?"                              │  │
│  │                                                       │  │
│  │  Can use either:                                      │  │
│  │                                                       │  │
│  │  Option 1: JWT Token                                  │  │
│  │  ┌─────────────────────────────────────┐             │  │
│  │  │ eyJhbGc...                          │             │  │
│  │  │ Header.Payload.Signature            │  ← JWT     │  │
│  │  │ Self-contained, no DB lookup        │             │  │
│  │  └─────────────────────────────────────┘             │  │
│  │                                                       │  │
│  │  Option 2: Opaque Token                               │  │
│  │  ┌─────────────────────────────────────┐             │  │
│  │  │ 9f8d7e6c5b4a3...                    │             │  │
│  │  │ Random string                       │             │  │
│  │  │ Requires DB lookup                  │             │  │
│  │  └─────────────────────────────────────┘             │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘


REAL-WORLD EXAMPLE
──────────────────

Scenario: Login with Google

OAuth 2.0:
  ↓
Defines the flow:
1. User clicks "Login with Google"
2. Redirect to Google
3. User approves
4. Get authorization code
5. Exchange for access token
6. Use token to access resources

JWT:
  ↓
Defines the token format (if Google uses JWT):
Access Token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
               └─ Header: {alg, typ}
               └─ Payload: {sub, email, iat, exp}
               └─ Signature: (verification)


COMPARISON TABLE
────────────────

┌───────────────────┬─────────────────┬─────────────────────┐
│      Feature      │   OAuth 2.0     │        JWT          │
├───────────────────┼─────────────────┼─────────────────────┤
│ Type              │ Framework       │ Token Format        │
├───────────────────┼─────────────────┼─────────────────────┤
│ Purpose           │ Authorization   │ Data Structure      │
├───────────────────┼─────────────────┼─────────────────────┤
│ Defines           │ How to get      │ How token is        │
│                   │ tokens          │ structured          │
├───────────────────┼─────────────────┼─────────────────────┤
│ Use Case          │ Third-party     │ Stateless auth,     │
│                   │ access          │ API authentication  │
├───────────────────┼─────────────────┼─────────────────────┤
│ Contains          │ Multiple flows  │ Header, Payload,    │
│                   │ (auth code,     │ Signature           │
│                   │ client cred,    │                     │
│                   │ etc.)           │                     │
├───────────────────┼─────────────────┼─────────────────────┤
│ Token Type        │ Can be JWT or   │ Always JWT          │
│                   │ opaque          │                     │
├───────────────────┼─────────────────┼─────────────────────┤
│ Example           │ Authorization   │ eyJhbGciOiJIUzI1... │
│                   │ Code Grant flow │                     │
└───────────────────┴─────────────────┴─────────────────────┘


KEY TAKEAWAY
────────────

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  OAuth 2.0 = The process of getting authorized             │
│  JWT = The format/structure of the token                    │
│                                                             │
│  They can work together:                                    │
│  • Use OAuth 2.0 to GET the token                           │
│  • Use JWT as the FORMAT of that token                      │
│                                                             │
│  But they are NOT the same thing!                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 7. OAuth 2.0 Scopes

Scopes define **what permissions** the client is requesting.

**Examples:**

- `profile` → Access basic profile info
- `email` → Access email address
- `openid` → OpenID Connect (authentication layer on top of OAuth)
- `drive.readonly` → Read-only access to Google Drive
- `drive.file` → Access files created by the app

**In the authorization request:**

```
scope=profile email drive.readonly
```

## 8. Security Best Practices

### 1. Use HTTPS
- Always use HTTPS for OAuth requests
- Prevents token interception

### 2. Use State Parameter
- Prevents CSRF attacks
- Validate that the returned state matches the sent state

### 3. Use PKCE for Mobile/SPA
- Adds extra security layer
- Prevents authorization code interception

### 4. Store Tokens Securely
- Never store tokens in localStorage (XSS vulnerable)
- Use httpOnly cookies or secure storage

### 5. Validate Redirect URIs
- Authorization server should validate redirect URIs
- Prevents token theft

### 6. Use Short-Lived Access Tokens
- Access tokens should expire quickly (e.g., 1 hour)
- Use refresh tokens to get new access tokens

## 9. Common Interview Questions

### Q1: What is the difference between OAuth 2.0 and OAuth 1.0?

- OAuth 1.0 required cryptographic signing of every request
- OAuth 2.0 relies on HTTPS and is simpler
- OAuth 2.0 supports multiple grant types
- OAuth 2.0 has better mobile support

### Q2: What is the difference between authentication and authorization?

- **Authentication:** Verifying who you are (login)
- **Authorization:** Verifying what you can access (permissions)
- OAuth 2.0 is for **authorization**, not authentication
- OpenID Connect (built on OAuth 2.0) adds authentication

### Q3: Why use authorization code instead of directly returning access token?

- **Security:** Access token never exposed in the browser URL
- **Client authentication:** Backend can prove its identity with client secret
- **Token security:** Tokens are exchanged server-to-server

### Q4: What is PKCE and why is it needed?

- **PKCE:** Proof Key for Code Exchange
- **Purpose:** Prevents authorization code interception attacks
- **Use case:** Mobile apps and SPAs (can't store client secret securely)
- **How it works:** Generates a code verifier and challenge, validates on token exchange

## 10. Quick Interview Answer

You can say this in an interview:

> OAuth 2.0 is an authorization framework that allows third-party applications to access user resources without sharing passwords.
>
> In the authorization code flow, the user is redirected to the authorization server, approves the request, and an authorization code is returned to the client.
> The client then exchanges this code for an access token using its client secret in a server-to-server call.
> The access token is used to access protected resources on the resource server.
>
> OAuth 2.0 supports multiple grant types for different scenarios, such as authorization code for web apps, PKCE for mobile apps, and client credentials for machine-to-machine communication.
>
> It's important to note that OAuth 2.0 is for authorization, not authentication. For authentication, we use OpenID Connect, which is built on top of OAuth 2.0.