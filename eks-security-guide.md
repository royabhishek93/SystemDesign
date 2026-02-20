# EKS Security Guide for React + Java Microservices (Beginner Q/A Style)

> Interview Level: 5+ Years | AWS EKS + Spring Boot + React
> Last Updated: February 15, 2026

---

## Q1) What are we trying to secure?

**Answer (Simple)**: A React web app and Java microservices running on AWS EKS.

**Why this is hard**:
- Many moving parts (browser, API, cluster, database).
- Attackers can try many entry points.

**Workflow (Simple)**:
```
User -> React (Browser) -> ALB + WAF -> Java API (EKS) -> Database
```

**Block Diagram (Simple)**:
```
+------+     +-------+     +---------+     +-----------+     +----------+
| User | --> | React | --> | ALB+WAF | --> | Java API  | --> | Database |
+------+     +-------+     +---------+     +-----------+     +----------+
```

---

## Q2) What stack is assumed?

**Answer (Simple)**:
- Cognito (OIDC) for login
- CloudFront + S3 for React
- ALB Ingress + WAF for edge
- mTLS inside cluster (service mesh)
- Secrets Manager + CSI
- IRSA for AWS permissions

**Why this helps**:
- Managed services reduce security mistakes.

**Block Diagram (Simple)**:
```
React -> CloudFront/S3 -> ALB/WAF -> EKS -> DB
			Cognito (login)
			Secrets Manager
			IRSA
```

---

## Q3) What are the main security goals?

**Answer (Simple)**:
- Authn: know who is calling
- Authz: allow only permitted actions
- Encrypt data in transit and at rest
- Limit blast radius (least privilege)
- Detect and respond quickly

**Workflow (Simple)**:
```
Identity -> Access Rules -> Encryption -> Isolation -> Monitoring
```

**Block Diagram (Simple)**:
```
Authn -> Authz -> TLS/KMS -> Least Privilege -> Logs/Alerts
```

---

## Security Patterns (Beginner, Across the Guide)

**Answer (Simple)**: These are repeatable safety habits used everywhere in this guide.

**Patterns (Simple)**:
- **Defense in depth**: Multiple layers (WAF + JWT + NetworkPolicy).
- **Least privilege**: Give only needed access (IRSA, tight roles).
- **Zero trust**: Always verify (mTLS, JWT checks every call).
- **Secure by default**: Deny by default, allow specific rules.
- **Rate limiting**: Slow down abuse (WAF, login limits).
- **Input validation**: Reject bad inputs early (WAF + app checks).
- **Secrets isolation**: Keep secrets out of code (Secrets Manager).
- **Encryption everywhere**: TLS in transit, KMS at rest.
- **Separation of duties**: Dev vs ops permissions split.
- **Monitoring + response**: Logs, alerts, and runbooks.

**Block Diagram (Simple)**:
```
Layers -> Least Privilege -> Verify Always -> Deny by Default -> Monitor
```

---

## Q4) How does login work (React + Cognito)?

**Challenge**: Stolen tokens or insecure login flow.

**Answer (Simple)**: Use OIDC + PKCE so tokens are secure. The login page can be a Cognito Hosted UI, or your React app can show a login button that redirects to Cognito.

**Workflow (Simple)**:
```
Browser -> Cognito Login -> Auth Code -> Token (PKCE) -> API call
```

**Block Diagram (Simple)**:
```
+---------+   Redirect   +-----------------+   Tokens   +-----------+
| React   | -----------> | Cognito Login   | ---------> | API Call  |
+---------+              +-----------------+           +-----------+
```

**Key controls**:
- Use PKCE
- Avoid localStorage for tokens
- Short-lived access tokens

**PKCE Step-by-Step (Simple)**:

**Step 1: App creates a secret**
- App generates a random string called the `code_verifier`.

**Step 2: App creates a challenge**
- App hashes the verifier to make a `code_challenge`.

**Note (Easy English)**:
- `code_verifier` = your secret (keep it in the app).
- `code_challenge` = the scrambled hash of that secret (safe to send).

**Step 3: Send challenge to Cognito**
- App redirects to Cognito with the `code_challenge`.

**Step 4: Cognito returns auth code**
- After login, Cognito sends an `auth_code` back to the app.

**Step 5: App exchanges code**
- App sends `auth_code + code_verifier` to Cognito.

**Step 6: Cognito verifies**
- Cognito checks if `code_verifier` matches the original `code_challenge`.

**Step 7: Tokens**
- If match: tokens are issued.
- If not: request is denied.

**PKCE Flow Diagram (Simple)**:
```
App creates code_verifier
App hashes -> code_challenge

React App ----------------------> Cognito
	(send code_challenge)

User logs in at Cognito

Cognito ------------------------> React App
	(returns auth_code)

React App ----------------------> Cognito
	(send auth_code + code_verifier)

Cognito checks match
If ok -> tokens
If not -> deny
```

---

## Q5) How does the API verify the user?

**Challenge**: Fake tokens or tampered roles.

**Answer (Simple)**: Validate JWT signature and roles with JWKS.

**Workflow (Simple)**:
```
API receives token -> verify signature -> check roles -> allow/deny
```

**Block Diagram (Simple)**:
```
Token -> Verify JWKS -> Check Role -> Allow/Deny
```

**Note (Easy English)**:
- Cognito “seals” the token with a private key.
- The API uses Cognito’s public key to check the seal.
- If the seal matches, the token is real; otherwise it is rejected.

---

## Q6) How do we protect the edge (public entry)?

**Challenge**: Bots, brute force, and web attacks.

**Answer (Simple)**: ALB terminates TLS, WAF blocks bad traffic.

**How it works inside (Simple)**:
- **ALB (TLS)**: ALB ends HTTPS, checks the certificate, decrypts traffic, then forwards clean HTTP to the service. This stops snooping and tampering while data travels.
- **WAF rules**: WAF runs a rule engine before traffic hits the API. It checks IP reputation, rate limits, and known attack patterns, then blocks or allows.

**Easy English (More Detail)**:
- **ALB (TLS)**: Think of a security gate that opens only for locked (HTTPS) trucks. ALB checks the lock (certificate), opens the truck (decrypts), then sends goods inside. If the lock is wrong, it refuses entry.
- **WAF rules**: Think of a guard list. WAF checks each request against the list: too many requests, bad IPs, or attack patterns. If it looks bad, it stops it.
- **Bots**: Bots are robots spamming requests. WAF can slow them down (rate limit), block their IPs, or challenge them.
- **Brute force**: Repeated password guessing. WAF limits how many tries per minute and blocks after failures.
- **Web attacks**: Bad requests like SQL injection or XSS. WAF has known patterns and blocks them.

**How it stops the attacks (Simple)**:
- **Bots**: WAF rate limits, blocks bad IPs, and can use bot control to challenge or block.
- **Brute force**: WAF rate limits login attempts per IP/user and blocks repeated failures.
- **Web attacks**: WAF signatures block SQL injection, XSS, and path traversal.

**How attackers try, and how it stops them (Simple)**:
- **Bots**: Attacker runs scripts that hit the API thousands of times per minute. WAF sees the burst and blocks or slows those IPs.
- **Brute force**: Attacker tries many passwords on the login endpoint. WAF rate limits and blocks after repeated failures.
- **SQL injection**: Attacker sends input like `' OR 1=1 --` in a form. WAF detects the pattern and blocks the request.
- **XSS**: Attacker sends `<script>` in inputs. WAF blocks known XSS patterns before it reaches the app.
- **Path traversal**: Attacker tries `../../etc/passwd`. WAF blocks traversal patterns.

**Workflow (Simple)**:
```
Internet -> ALB (TLS) -> WAF rules -> API
```

**Block Diagram (Simple)**:
```
Internet -> ALB (TLS) -> WAF -> API
```

**Block Diagram (Detailed)**:
```
			  +------------------+
Internet ->| ALB (TLS check)  |-> decrypted HTTP
			  +------------------+
							|
							v
			  +------------------+
			  | WAF Rule Engine  |
			  | - Rate limits    |
			  | - IP reputation  |
			  | - Attack patterns|
			  +------------------+
							|
							v
						+------+
						| API  |
						+------+
```

---

## Q7) How do services talk safely inside EKS?

**Challenge**: Rogue pods or spoofed traffic.

**Answer (Simple)**: Use mTLS plus NetworkPolicies.

**Workflow (Simple)**:
```
Service A <mTLS> Service B
NetworkPolicy allows only specific calls
```

**Block Diagram (Simple)**:
```
Service A <mTLS> Service B
	|                |
	+-- NetworkPolicy allows --+
```

---

## Q8) How do we manage AWS permissions safely?

**Challenge**: One service gets too much AWS access.

**Answer (Simple)**: Use IRSA so each pod has least privilege.

**Workflow (Simple)**:
```
Pod -> Service Account -> IAM Role -> AWS Resource
```

**Block Diagram (Simple)**:
```
Pod -> SA -> IRSA Role -> AWS
```

---

## Q9) How do we store secrets safely?

**Challenge**: Secrets in YAML or Git leak.

**Answer (Simple)**: Secrets Manager + CSI mounts at runtime.

**Workflow (Simple)**:
```
Secrets Manager -> CSI -> Pod env/volume
```

**Block Diagram (Simple)**:
```
Secrets Manager -> CSI Driver -> Pod
```

---

## Q10) How is data encrypted?

**Challenge**: Stolen disks or traffic snooping.

**Answer (Simple)**: TLS in transit, KMS at rest.

**Workflow (Simple)**:
```
Client -> TLS -> ALB -> TLS -> Service -> TLS -> DB
DB data encrypted with KMS
```

**Block Diagram (Simple)**:
```
Client -> TLS -> ALB -> TLS -> Service -> TLS -> DB -> KMS
```

---

## Q11) How do we keep images safe (supply chain)?

**Challenge**: Vulnerable or malicious images.

**Answer (Simple)**: Scan, sign, and keep an SBOM.

**Workflow (Simple)**:
```
Build -> Scan -> Sign -> Deploy (only signed)
```

**Block Diagram (Simple)**:
```
Build -> Scan -> Sign -> Deploy
```

---

## Q12) How do we detect and respond to attacks?

**Challenge**: Attacks go unnoticed.

**Answer (Simple)**: Central logs + alerts + runbooks.

**Workflow (Simple)**:
```
Alert -> On-call -> Investigate -> Block -> Postmortem
```

**Block Diagram (Simple)**:
```
Alert -> On-call -> Investigate -> Block -> Postmortem
```

---

# Scenarios (Q/A + Workflow)

## Scenario 1) User Login + API Access

**Challenge**: Secure login and API calls.

**Answer (Simple)**: OIDC + PKCE, JWT validation, WAF.

**Workflow (Simple)**:
```
Browser -> Cognito -> Token -> ALB + WAF -> Java API -> DB
```

**Block Diagram (Simple)**:
```
Browser -> Cognito -> Token -> ALB/WAF -> API -> DB
```

## Scenario 2) Service-to-Service Calls

**Challenge**: Stop fake internal calls.

**Answer (Simple)**: mTLS + NetworkPolicy.

**Workflow (Simple)**:
```
Service A <mTLS> Service B (allowed only by policy)
```

**Block Diagram (Simple)**:
```
Service A <mTLS> Service B
```

## Scenario 3) Admin-Only Endpoints

**Challenge**: Normal users hitting admin APIs.

**Answer (Simple)**: Role checks in JWT.

**Workflow (Simple)**:
```
Admin -> JWT (ROLE_ADMIN) -> API -> allow
User -> JWT (ROLE_USER) -> API -> deny
```

**Block Diagram (Simple)**:
```
ROLE_ADMIN -> Allow
ROLE_USER  -> Deny
```

## Scenario 4) Multi-Tenant Isolation

**Challenge**: One tenant seeing another tenant data.

**Answer (Simple)**: Use tenantId from JWT, filter in DB.

**Workflow (Simple)**:
```
JWT tenantId -> API -> DB filter by tenantId
```

**Block Diagram (Simple)**:
```
JWT tenantId -> API -> DB (tenant filter)
```

## Scenario 5) Data at Rest and In Transit

**Challenge**: Data leaks in transit or from storage.

**Answer (Simple)**: TLS + KMS.

**Workflow (Simple)**:
```
TLS everywhere + DB encrypted with KMS
```

**Block Diagram (Simple)**:
```
TLS -> TLS -> TLS -> DB (KMS)
```

## Scenario 6) Incident Response

**Challenge**: Fast recovery after attack.

**Answer (Simple)**: Alerts, block traffic, rotate secrets.

**Workflow (Simple)**:
```
Alert -> Investigate -> Block -> Rotate -> Review
```

**Block Diagram (Simple)**:
```
Alert -> Investigate -> Block -> Rotate -> Review
```

---

# Quick Checklist (Beginner)

- Use Cognito OIDC + PKCE
- Validate JWT in API
- ALB + WAF at the edge
- IRSA for least privilege
- NetworkPolicies + mTLS
- Secrets Manager + CSI
- TLS + KMS encryption
- Scan + sign images
- Central logs + alerts
