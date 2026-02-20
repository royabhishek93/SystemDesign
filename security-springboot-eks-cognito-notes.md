# Interview Notes: Spring Boot Security Starter + Cognito + EKS

## One-liner answer
- We validate JWT at the edge to block unauthenticated traffic, and every microservice still enforces fine-grained authorization (scopes/roles) for defense in depth.

## How the request flows
- React app authenticates with Cognito and gets JWT.
- Requests go through CloudFront/WAF and API Gateway or ALB.
- Edge validates JWT (authorizer) and forwards request to EKS.
- Microservice validates JWT again and enforces method-level scopes/roles.

## Why every microservice still enforces auth
- Cognito only issues tokens (identity provider). It does not authorize your business actions.
- Edge validation blocks invalid tokens, but services must enforce least privilege.
- Zero-trust: never assume upstream checks are enough.

## What code is shared (security starter)
- Stateless Spring Security config (no server sessions).
- OAuth2 Resource Server with JWT validation.
- Common headers (HSTS, frame options).
- Common JWT to roles/scopes mapping (scope claim, Cognito groups).

### Shared starter: core config
```java
@Configuration
@EnableMethodSecurity
@EnableConfigurationProperties(SecurityProps.class)
public class SecurityAutoConfiguration {

	@Bean
	SecurityFilterChain securityFilterChain(HttpSecurity http, SecurityProps props) throws Exception {
		http
			.csrf(csrf -> csrf.disable())
			.sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
			.cors(Customizer.withDefaults())
			.authorizeHttpRequests(auth -> auth
				.requestMatchers(props.getPermitAll().toArray(new String[0])).permitAll()
				.anyRequest().authenticated()
			)
			.oauth2ResourceServer(oauth2 -> oauth2
				.jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthenticationConverter(props)))
			)
			.headers(headers -> headers
				.httpStrictTransportSecurity(hsts -> hsts.includeSubDomains(true).maxAgeInSeconds(31536000))
				.frameOptions(HeadersConfigurer.FrameOptionsConfig::deny)
			);
		return http.build();
	}

	@Bean
	JwtAuthenticationConverter jwtAuthenticationConverter(SecurityProps props) {
		JwtGrantedAuthoritiesConverter scopes = new JwtGrantedAuthoritiesConverter();
		scopes.setAuthorityPrefix(props.getScopePrefix());
		scopes.setAuthoritiesClaimName(props.getScopeClaim());

		JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
		converter.setJwtGrantedAuthoritiesConverter(jwt -> {
			Collection<GrantedAuthority> authorities = new ArrayList<>(scopes.convert(jwt));
			if (props.isMapCognitoGroups()) {
				List<String> groups = jwt.getClaimAsStringList("cognito:groups");
				if (groups != null) {
					groups.forEach(g -> authorities.add(new SimpleGrantedAuthority("ROLE_" + g)));
				}
			}
			return authorities;
		});
		return converter;
	}
}
```

### Shared starter: properties
```java
@ConfigurationProperties(prefix = "security")
public class SecurityProps {
	private List<String> permitAll = List.of("/actuator/health", "/actuator/info");
	private String scopeClaim = "scope";
	private String scopePrefix = "SCOPE_";
	private boolean mapCognitoGroups = true;

	// getters/setters
}
```

## What is service-specific
- Method-level rules using scopes/roles: `@PreAuthorize("hasAuthority('SCOPE_orders.read')")`.
- Endpoint-level access control for each domain.

### Service config (resource server)
```yaml
spring:
	security:
		oauth2:
			resourceserver:
				jwt:
					issuer-uri: https://cognito-idp.<region>.amazonaws.com/<user-pool-id>

security:
	permit-all:
		- /actuator/health
		- /actuator/info
```

### Service-level authorization
```java
@RestController
@RequestMapping("/api/orders")
public class OrdersController {

		@GetMapping
		@PreAuthorize("hasAuthority('SCOPE_orders.read')")
		public List<String> listOrders() {
				return List.of("o-1", "o-2");
		}

		@PostMapping
		@PreAuthorize("hasAuthority('SCOPE_orders.write')")
		public String createOrder() {
				return "created";
		}
}
```

## Example interview sound bite
- "Cognito authenticates users and issues JWT. Edge validates the token, but each service authorizes actions based on scopes/roles. We standardize security with a shared starter to keep it consistent." 

## Easy-English explanation of the code (talk track)
- "This config makes the service stateless, so we do not store sessions on the server."
- "Every request must carry a JWT token, usually in the Authorization header."
- "Spring validates that token using Cognito's issuer/JWKs."
- "Then we map token scopes and groups into Spring authorities."
- "Finally, each endpoint checks a specific permission like orders.read or orders.write."

## What to mention in the discussion
- "Cognito is the identity provider. It issues tokens, but it does not decide business permissions."
- "API Gateway or ALB blocks invalid tokens at the edge."
- "Each microservice still enforces fine-grained permissions for defense in depth."
- "We use a shared security starter so every service has the same baseline rules."
- "Method-level annotations keep access rules close to the business endpoints."
- "No server sessions means easy scaling and fewer security risks."

## Short 30-second interview script
- "We use Cognito for login and JWTs. The gateway validates JWTs so unauthenticated traffic is blocked early."
- "Inside EKS, each Spring Boot service still authorizes its own endpoints using scopes like orders.read."
- "We standardize the security config with a shared starter: stateless setup, JWT validation, and common header hardening."
- "That gives consistent security everywhere plus fine-grained control per service."

## Common follow-up answers
- "Does EKS handle auth?" No, EKS is just compute. Auth is handled by IdP + gateway + services.
- "Why validate JWT in service if gateway already did?" Defense in depth and internal calls can bypass edge.
- "How do services call each other?" Prefer mTLS plus service-to-service auth (service mesh or IAM).

## Pitfalls to mention
- Do not put secrets in code; use Secrets Manager with IRSA.
- Avoid broad roles; enforce least privilege per endpoint.
- Log auth failures with correlation IDs for audits.
