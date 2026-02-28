# Auth System (OAuth / SSO) - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is an Auth System?
An auth system verifies identity (authentication) and checks permissions (authorization). It issues tokens so services can trust the user without repeated logins.

## 2) Clarifying Questions (Interview Warm-up)
- Is it consumer login, enterprise SSO, or both?
- What are the supported IdPs (Google, Azure AD, Okta)?
- Do we need MFA, device trust, or step-up auth?
- Token lifetime and refresh strategy?
- Is it multi-tenant with tenant-specific policies?

## 3) Approaches to Implement Auth

### Approach A: Session-Based Auth
What it is:
- Server stores session; client has a session cookie.

Pros:
- Simple and secure for web apps

Cons:
- Harder to scale across regions
- Needs session store

### Approach B: JWT-Based Auth (Stateless)
What it is:
- Token contains claims; services validate signature.

Pros:
- Scales well
- Works across microservices

Cons:
- Token revocation is hard
- Requires key rotation

### Approach C: OAuth 2.0 + OpenID Connect
What it is:
- Standard for delegated access and SSO.

Pros:
- Widely supported
- Works with external IdPs

Cons:
- More moving parts
- Needs correct flow choice

### Approach D: SAML SSO
What it is:
- Common in enterprise legacy systems.

Pros:
- Enterprise compatibility

Cons:
- XML complexity
- Harder to integrate with modern mobile apps

### Approach E: API Key + HMAC
What it is:
- Keys for machine-to-machine auth.

Pros:
- Simple and fast

Cons:
- Poor user-level security
- Key rotation required

### Approach F: mTLS (Mutual TLS)
What it is:
- Both client and server present certificates.

Pros:
- Very strong security

Cons:
- Certificate management burden

### Approach G: Central Auth Service (Token Issuer)
What it is:
- Dedicated service issues and verifies tokens.

Pros:
- Centralized policy control
- Easier auditing

Cons:
- Single point of failure if not HA

### Approach H: Zero Trust + Policy Engine
What it is:
- Every call is evaluated by policy rules (OPA / Cedar).

Pros:
- Fine-grained authorization

Cons:
- Higher latency and complexity

## 4) Common Technologies
- OAuth/OpenID: Keycloak, Okta, Auth0, Azure AD
- JWT libraries: Nimbus, Jose4j
- Policy engines: OPA, AWS Cedar
- Session stores: Redis, DynamoDB

## 5) Key Concepts (Interview Must-Know)
- Access tokens vs refresh tokens
- Token expiration and rotation
- RBAC vs ABAC
- MFA and step-up auth
- Secure cookie flags (HttpOnly, SameSite)

## 6) Production Checklist
- Key rotation and JWKS endpoint
- Global logout / token revocation strategy
- Secure storage for refresh tokens
- Audit logs for auth events

## 7) Quick Interview Answer (30 seconds)
"Auth systems verify identity and permissions. Common approaches are session-based auth for web apps, JWT for stateless scaling, and OAuth/OIDC for SSO. For enterprise, SAML may be needed, while mTLS and policy engines add stronger security. Choice depends on scale, client types, and compliance needs."
