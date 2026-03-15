# Feature Flags System - Production Implementation Guide

> **Target**: 10+ Years Experienced Developer
> **Updated**: March 2026
> **Interview Ready**: Complete guide with code examples and ASCII diagrams

---

## 📊 Problem Statement

Design a **feature flags system** that handles:
- **50,000+ feature flags** across microservices
- **10,000 flag evaluations per second** per service instance
- **Sub-millisecond evaluation latency** (<1ms p99)
- **Real-time updates** - flag changes propagate within 5 seconds
- **Percentage rollouts** - Enable for 10%, 25%, 50%, 100% of users
- **A/B testing** - Track metrics for variant groups
- **Kill switches** - Emergency feature disable
- **Multi-tenancy** - Different flags per customer/region

---

## 🎯 Functional Requirements

### Core Features
1. **Create/Update/Delete flags** - Admin operations
2. **Evaluate flags** - Check if feature enabled for user/context
3. **Gradual rollout** - Enable for X% of users
4. **Targeting rules** - Enable for specific users/segments
5. **A/B testing** - Assign users to variants, track metrics
6. **Kill switch** - Instant disable for all users
7. **Audit trail** - Who changed what and when
8. **Flag lifecycle** - Track creation → rollout → cleanup

### Non-Functional Requirements
1. **Low Latency** - <1ms p99 evaluation time
2. **High Availability** - 99.99% uptime (flags cached locally)
3. **Consistency** - Eventual consistency acceptable (5-sec propagation)
4. **Scalability** - Handle 100K+ flags, 1M+ evaluations/sec
5. **Security** - Role-based access, audit logs
6. **Observability** - Track flag usage, impact metrics

---

## 🤔 Clarifying Questions (Interview Warm-up)

### Must Ask in Interview:
1. **Scale**: How many services? How many flags? How many evaluations/sec?
2. **Latency**: Can we cache flags locally? How fresh must they be?
3. **Rollout**: Do we need percentage rollouts? Targeted segments?
4. **A/B Testing**: Do we need metrics tracking and statistical analysis?
5. **Consistency**: Can flag state be eventually consistent?
6. **Kill Switch**: How fast must emergency disables propagate?
7. **Multi-tenancy**: Different flags per customer/region?

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  FEATURE FLAGS SYSTEM ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │              Admin Dashboard (React)                     │          │
│  │  • Create/Update/Delete flags                            │          │
│  │  • Configure targeting rules                             │          │
│  │  • View metrics and experiments                          │          │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│                         │ HTTPS (POST /flags)                           │
│                         ▼                                               │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │         Flag Management Service (Spring Boot)            │          │
│  │  • Flag CRUD operations                                  │          │
│  │  • Validation and auditing                               │          │
│  │  • Publish change events                                 │          │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│         ┌───────────────┼────────────┬──────────────┐                  │
│         │               │            │              │                  │
│         ▼               ▼            ▼              ▼                  │
│  ┌──────────┐    ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │PostgreSQL│    │  Redis   │  │  Kafka   │  │  S3/CDN  │            │
│  │          │    │  Cache   │  │  Events  │  │  Snapshot│            │
│  │Flag Defs │    │          │  │          │  │  (Backup)│            │
│  │Rules     │    │Hot Flags │  │flag-     │  │          │            │
│  │Audit Log │    │          │  │ changed  │  │flags.json│            │
│  └──────────┘    └──────────┘  └────┬─────┘  └──────────┘            │
│                                      │                                 │
│                                      │ Subscribe to events             │
│                                      ▼                                 │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │         Application Services (Consumers)                 │         │
│  │  ┌────────────────────────────────────────────────┐      │         │
│  │  │  User Service (Instance 1)                     │      │         │
│  │  │  ┌──────────────────────────────────────────┐  │      │         │
│  │  │  │  Feature Flag SDK (In-Memory)            │  │      │         │
│  │  │  │  • Local cache of flags                  │  │      │         │
│  │  │  │  • Evaluation logic                      │  │      │         │
│  │  │  │  • Listens to Kafka for updates          │  │      │         │
│  │  │  │  • Fallback to defaults on failure       │  │      │         │
│  │  │  └──────────────────────────────────────────┘  │      │         │
│  │  │                                                 │      │         │
│  │  │  if (flagService.isEnabled("new-checkout")) {  │      │         │
│  │  │      return newCheckoutFlow();                 │      │         │
│  │  │  } else {                                       │      │         │
│  │  │      return legacyCheckoutFlow();              │      │         │
│  │  │  }                                              │      │         │
│  │  └─────────────────────────────────────────────────┘      │         │
│  │                                                            │         │
│  │  (50+ service instances with SDK embedded)                │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                         │
│  EVALUATION FLOW:                                                      │
│  1. Service checks local cache (in-memory)                             │
│  2. If miss, fetch from Redis (rare, <1% of calls)                     │
│  3. Kafka updates push changes to all instances                        │
│  4. Evaluation happens locally (no network call!)                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema Design

### PostgreSQL Schema (Source of Truth)

```sql
-- Feature flags table
CREATE TABLE feature_flags (
    flag_key VARCHAR(255) PRIMARY KEY,
    flag_name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT FALSE,

    -- Rollout configuration
    rollout_percentage INTEGER DEFAULT 0,  -- 0-100
    rollout_strategy VARCHAR(50),          -- 'user_id', 'email', 'random'

    -- Targeting
    targeting_rules JSONB,                 -- Complex rules (segments, etc)

    -- A/B testing
    is_experiment BOOLEAN DEFAULT FALSE,
    experiment_variants JSONB,             -- ['control', 'variant-a', 'variant-b']

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Lifecycle
    status VARCHAR(50) DEFAULT 'active',   -- 'active', 'archived', 'deprecated'
    archived_at TIMESTAMP
);

-- Targeting rules example
CREATE TABLE flag_targeting_rules (
    rule_id SERIAL PRIMARY KEY,
    flag_key VARCHAR(255) REFERENCES feature_flags(flag_key),

    -- Rule definition
    rule_type VARCHAR(50),                 -- 'user_id', 'email_domain', 'region', 'custom'
    operator VARCHAR(50),                  -- 'in', 'not_in', 'contains', 'equals'
    values JSONB,                          -- ['user123', 'user456']

    priority INTEGER DEFAULT 0,            -- Higher priority = evaluated first
    enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit log
CREATE TABLE flag_audit_log (
    audit_id SERIAL PRIMARY KEY,
    flag_key VARCHAR(255),
    action VARCHAR(50),                    -- 'created', 'updated', 'toggled', 'deleted'
    changed_by VARCHAR(255),
    old_value JSONB,
    new_value JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- A/B test metrics
CREATE TABLE experiment_metrics (
    metric_id SERIAL PRIMARY KEY,
    flag_key VARCHAR(255),
    variant VARCHAR(50),
    user_id VARCHAR(255),

    -- Metrics
    conversion BOOLEAN DEFAULT FALSE,
    revenue DECIMAL(10, 2),
    latency_ms INTEGER,

    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_flags_status ON feature_flags(status);
CREATE INDEX idx_audit_flag_key ON flag_audit_log(flag_key, timestamp DESC);
CREATE INDEX idx_experiment_metrics ON experiment_metrics(flag_key, variant, timestamp);
```

---

## 🚀 Implementation Approaches

### Approach A: SDK with Local Cache ⭐ RECOMMENDED

```java
@Service
public class FeatureFlagService {

    // In-memory cache (Caffeine)
    private final Cache<String, FeatureFlag> localCache = Caffeine.newBuilder()
        .expireAfterWrite(5, TimeUnit.MINUTES)
        .maximumSize(10_000)
        .recordStats()
        .build();

    @Autowired
    private RedisTemplate<String, FeatureFlag> redisTemplate;

    @Autowired
    private KafkaListener kafkaListener;

    // Initialize: Load all flags at startup
    @PostConstruct
    public void init() {
        loadAllFlags();
        subscribeToflagChanges();
    }

    /**
     * Primary API: Check if flag is enabled for user
     * Latency: <0.1ms (in-memory lookup)
     */
    public boolean isEnabled(String flagKey, UserContext context) {
        FeatureFlag flag = getFlag(flagKey);

        if (flag == null) {
            log.warn("Flag {} not found, returning default: false", flagKey);
            return false;
        }

        // If flag is globally disabled
        if (!flag.isEnabled()) {
            return false;
        }

        // Evaluate targeting rules
        return evaluateFlag(flag, context);
    }

    /**
     * Get variant for A/B test
     */
    public String getVariant(String flagKey, UserContext context) {
        FeatureFlag flag = getFlag(flagKey);

        if (flag == null || !flag.isExperiment()) {
            return "control";
        }

        // Consistent hashing to assign user to variant
        String userId = context.getUserId();
        int hash = Hashing.murmur3_32()
            .hashString(flagKey + ":" + userId, StandardCharsets.UTF_8)
            .asInt();

        int variantIndex = Math.abs(hash) % flag.getVariants().size();
        return flag.getVariants().get(variantIndex);
    }

    /**
     * Get flag from local cache (fast path)
     */
    private FeatureFlag getFlag(String flagKey) {
        // 1. Check local cache (99.9% hit rate)
        FeatureFlag flag = localCache.getIfPresent(flagKey);
        if (flag != null) {
            return flag;
        }

        // 2. Cache miss: fetch from Redis
        try {
            flag = redisTemplate.opsForValue().get("flag:" + flagKey);
            if (flag != null) {
                localCache.put(flagKey, flag);
                return flag;
            }
        } catch (Exception e) {
            log.error("Redis failure, using default", e);
        }

        // 3. Not found: return null (caller handles default)
        return null;
    }

    /**
     * Evaluate flag based on targeting rules and rollout %
     */
    private boolean evaluateFlag(FeatureFlag flag, UserContext context) {
        // 1. Check targeting rules first (highest priority)
        for (TargetingRule rule : flag.getTargetingRules()) {
            if (evaluateRule(rule, context)) {
                return rule.isEnabled();
            }
        }

        // 2. Check percentage rollout
        int rolloutPercentage = flag.getRolloutPercentage();
        if (rolloutPercentage == 0) {
            return false;
        }
        if (rolloutPercentage == 100) {
            return true;
        }

        // 3. Consistent hashing for gradual rollout
        String userId = context.getUserId();
        int hash = Hashing.murmur3_32()
            .hashString(flag.getFlagKey() + ":" + userId, StandardCharsets.UTF_8)
            .asInt();

        int bucket = Math.abs(hash) % 100;  // 0-99
        return bucket < rolloutPercentage;
    }

    /**
     * Evaluate individual targeting rule
     */
    private boolean evaluateRule(TargetingRule rule, UserContext context) {
        switch (rule.getRuleType()) {
            case "user_id":
                return rule.getValues().contains(context.getUserId());

            case "email_domain":
                String domain = context.getEmail().split("@")[1];
                return rule.getValues().contains(domain);

            case "region":
                return rule.getValues().contains(context.getRegion());

            case "custom_attribute":
                String attrValue = context.getCustomAttributes().get(rule.getAttributeName());
                return rule.getValues().contains(attrValue);

            default:
                log.warn("Unknown rule type: {}", rule.getRuleType());
                return false;
        }
    }

    /**
     * Listen to Kafka for flag changes
     */
    @KafkaListener(topics = "flag-changes", groupId = "user-service")
    public void handleFlagChange(FlagChangeEvent event) {
        String flagKey = event.getFlagKey();

        switch (event.getAction()) {
            case "UPDATED":
                // Invalidate local cache
                localCache.invalidate(flagKey);

                // Update Redis
                FeatureFlag updatedFlag = event.getFlagData();
                redisTemplate.opsForValue().set("flag:" + flagKey, updatedFlag, 1, TimeUnit.HOURS);

                log.info("Flag {} updated: enabled={}, rollout={}%",
                         flagKey, updatedFlag.isEnabled(), updatedFlag.getRolloutPercentage());
                break;

            case "DELETED":
                localCache.invalidate(flagKey);
                redisTemplate.delete("flag:" + flagKey);
                log.info("Flag {} deleted", flagKey);
                break;
        }
    }

    /**
     * Load all flags at startup
     */
    private void loadAllFlags() {
        try {
            Set<String> flagKeys = redisTemplate.keys("flag:*");
            log.info("Loading {} flags from Redis", flagKeys.size());

            for (String key : flagKeys) {
                String flagKey = key.replace("flag:", "");
                FeatureFlag flag = redisTemplate.opsForValue().get(key);
                localCache.put(flagKey, flag);
            }
        } catch (Exception e) {
            log.error("Failed to load flags, will fetch on-demand", e);
        }
    }
}
```

**UserContext Class:**

```java
@Data
@Builder
public class UserContext {
    private String userId;
    private String email;
    private String region;
    private Map<String, String> customAttributes;

    // For A/B testing
    private String sessionId;
    private String ipAddress;
}
```

**Usage in Application Code:**

```java
@RestController
@RequestMapping("/checkout")
public class CheckoutController {

    @Autowired
    private FeatureFlagService flagService;

    @PostMapping("/process")
    public CheckoutResponse processCheckout(@RequestBody CheckoutRequest request) {
        UserContext context = UserContext.builder()
            .userId(request.getUserId())
            .email(request.getEmail())
            .region(request.getRegion())
            .build();

        // Check feature flag
        if (flagService.isEnabled("new-checkout-flow", context)) {
            log.info("Using new checkout flow for user {}", request.getUserId());
            return newCheckoutService.process(request);
        } else {
            log.info("Using legacy checkout flow for user {}", request.getUserId());
            return legacyCheckoutService.process(request);
        }
    }

    @GetMapping("/payment-options")
    public PaymentOptionsResponse getPaymentOptions(@RequestParam String userId) {
        UserContext context = UserContext.builder()
            .userId(userId)
            .build();

        // A/B test: Show different payment options
        String variant = flagService.getVariant("payment-options-test", context);

        switch (variant) {
            case "variant-a":
                return PaymentOptionsResponse.builder()
                    .options(Arrays.asList("credit-card", "paypal", "apple-pay"))
                    .build();

            case "variant-b":
                return PaymentOptionsResponse.builder()
                    .options(Arrays.asList("credit-card", "paypal", "google-pay", "crypto"))
                    .build();

            default:  // control
                return PaymentOptionsResponse.builder()
                    .options(Arrays.asList("credit-card", "paypal"))
                    .build();
        }
    }
}
```

---

## 🎨 LaunchDarkly Integration (Production SaaS)

### LaunchDarkly SDK Integration

```xml
<!-- pom.xml -->
<dependency>
    <groupId>com.launchdarkly</groupId>
    <artifactId>launchdarkly-java-server-sdk</artifactId>
    <version>6.2.1</version>
</dependency>
```

```java
@Configuration
public class LaunchDarklyConfig {

    @Value("${launchdarkly.sdk-key}")
    private String sdkKey;

    @Bean
    public LDClient ldClient() {
        LDConfig config = new LDConfig.Builder()
            .events(Components.sendEvents()
                .flushInterval(Duration.ofSeconds(5)))
            .dataStore(Components.persistentDataStore(
                Redis.dataStore()
                    .uri(URI.create("redis://localhost:6379"))
            ))
            .build();

        return new LDClient(sdkKey, config);
    }
}

@Service
public class LaunchDarklyFeatureFlagService {

    @Autowired
    private LDClient ldClient;

    public boolean isEnabled(String flagKey, String userId, String email) {
        LDContext context = LDContext.builder(userId)
            .set("email", email)
            .set("country", "US")
            .build();

        return ldClient.boolVariation(flagKey, context, false);
    }

    public String getStringVariant(String flagKey, String userId) {
        LDContext context = LDContext.builder(userId).build();
        return ldClient.stringVariation(flagKey, context, "control");
    }

    @PreDestroy
    public void cleanup() {
        ldClient.close();
    }
}
```

---

## 📊 A/B Testing & Statistical Significance

### Tracking Metrics

```java
@Service
public class ExperimentMetricsService {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private FeatureFlagService flagService;

    /**
     * Track conversion event for A/B test
     */
    public void trackConversion(String flagKey, String userId, boolean converted, Double revenue) {
        String variant = flagService.getVariant(flagKey,
            UserContext.builder().userId(userId).build());

        String sql = """
            INSERT INTO experiment_metrics (flag_key, variant, user_id, conversion, revenue, timestamp)
            VALUES (?, ?, ?, ?, ?, NOW())
        """;

        jdbcTemplate.update(sql, flagKey, variant, userId, converted, revenue);
    }

    /**
     * Get experiment results with statistical significance
     */
    public ExperimentResults getResults(String flagKey) {
        String sql = """
            SELECT
                variant,
                COUNT(*) as sample_size,
                SUM(CASE WHEN conversion THEN 1 ELSE 0 END) as conversions,
                AVG(CASE WHEN conversion THEN 1.0 ELSE 0.0 END) as conversion_rate,
                AVG(revenue) as avg_revenue
            FROM experiment_metrics
            WHERE flag_key = ?
            GROUP BY variant
        """;

        List<VariantMetrics> variants = jdbcTemplate.query(sql,
            (rs, rowNum) -> VariantMetrics.builder()
                .variant(rs.getString("variant"))
                .sampleSize(rs.getInt("sample_size"))
                .conversions(rs.getInt("conversions"))
                .conversionRate(rs.getDouble("conversion_rate"))
                .avgRevenue(rs.getDouble("avg_revenue"))
                .build(),
            flagKey);

        // Calculate statistical significance (Z-test)
        if (variants.size() >= 2) {
            VariantMetrics control = variants.stream()
                .filter(v -> "control".equals(v.getVariant()))
                .findFirst()
                .orElse(variants.get(0));

            for (VariantMetrics variant : variants) {
                if (!"control".equals(variant.getVariant())) {
                    double zScore = calculateZScore(control, variant);
                    double pValue = calculatePValue(zScore);
                    variant.setZScore(zScore);
                    variant.setPValue(pValue);
                    variant.setSignificant(pValue < 0.05);
                }
            }
        }

        return ExperimentResults.builder()
            .flagKey(flagKey)
            .variants(variants)
            .build();
    }

    /**
     * Z-test for proportion difference
     */
    private double calculateZScore(VariantMetrics control, VariantMetrics variant) {
        double p1 = control.getConversionRate();
        double p2 = variant.getConversionRate();
        double n1 = control.getSampleSize();
        double n2 = variant.getSampleSize();

        double pooledP = (control.getConversions() + variant.getConversions()) / (n1 + n2);
        double se = Math.sqrt(pooledP * (1 - pooledP) * (1/n1 + 1/n2));

        return (p2 - p1) / se;
    }

    /**
     * Convert Z-score to p-value (two-tailed)
     */
    private double calculatePValue(double zScore) {
        NormalDistribution normal = new NormalDistribution();
        return 2 * (1 - normal.cumulativeProbability(Math.abs(zScore)));
    }
}
```

---

## 🎯 Percentage Rollout Strategy

### Consistent Hashing for User Assignment

```java
public class RolloutStrategy {

    /**
     * Determine if user is in rollout percentage
     * Uses consistent hashing to ensure same user always gets same result
     */
    public static boolean isInRollout(String flagKey, String userId, int percentage) {
        if (percentage == 0) return false;
        if (percentage == 100) return true;

        // Hash user ID with flag key (prevents correlation across flags)
        int hash = Hashing.murmur3_32()
            .hashString(flagKey + ":" + userId, StandardCharsets.UTF_8)
            .asInt();

        // Map to 0-99 bucket
        int bucket = Math.abs(hash) % 100;

        // User is in rollout if bucket < percentage
        return bucket < percentage;
    }

    /**
     * Example: Gradual rollout over time
     * Day 1: 10%, Day 2: 25%, Day 3: 50%, Day 4: 100%
     */
    public static void gradualRolloutExample() {
        String flagKey = "new-search-algorithm";

        // Day 1: Enable for 10%
        updateFlag(flagKey, 10);

        // Monitor metrics for 24 hours...

        // Day 2: Increase to 25%
        if (metricsLookGood()) {
            updateFlag(flagKey, 25);
        }

        // Day 3: Increase to 50%
        if (metricsLookGood()) {
            updateFlag(flagKey, 50);
        }

        // Day 4: Full rollout
        if (metricsLookGood()) {
            updateFlag(flagKey, 100);
        }
    }
}
```

---

## ⚠️ Edge Cases & Failure Scenarios

### 1. Flag Service Down

**Problem**: Flag management service crashes, can't update flags

**Solution**:
```java
// Services continue using cached flags (local + Redis)
// No impact on application availability
@Override
public boolean isEnabled(String flagKey, UserContext context) {
    try {
        return evaluateFlag(flagKey, context);
    } catch (Exception e) {
        // Fallback to safe default
        log.error("Flag evaluation failed for {}, using default: false", flagKey, e);
        return getDefaultValue(flagKey);  // From config file
    }
}
```

### 2. Kafka Lag / Consumer Slowness

**Problem**: Kafka events delayed, flag changes take 30 seconds to propagate

**Solution**:
```java
// Acceptable: Eventual consistency is fine for flags
// For critical kill switches, provide HTTP endpoint for instant refresh

@PostMapping("/flags/refresh")
public void forceRefresh(@RequestParam String flagKey) {
    localCache.invalidate(flagKey);
    loadFlagFromRedis(flagKey);
    log.info("Flag {} force-refreshed", flagKey);
}
```

### 3. Targeting Rule Conflict

**Problem**: User matches multiple targeting rules with different results

**Solution**:
```java
// Evaluate rules by priority (highest first)
List<TargetingRule> sortedRules = flag.getTargetingRules().stream()
    .sorted(Comparator.comparingInt(TargetingRule::getPriority).reversed())
    .toList();

for (TargetingRule rule : sortedRules) {
    if (evaluateRule(rule, context)) {
        return rule.isEnabled();  // First match wins
    }
}
```

### 4. A/B Test Contamination

**Problem**: User sees variant A, then variant B (inconsistent experience)

**Solution**:
```java
// Use consistent hashing based on user ID
// Same user ALWAYS gets same variant for duration of experiment

private String assignVariant(String flagKey, String userId, List<String> variants) {
    int hash = Hashing.murmur3_32()
        .hashString(flagKey + ":" + userId, StandardCharsets.UTF_8)
        .asInt();

    int index = Math.abs(hash) % variants.size();
    return variants.get(index);
}
```

---

## 📊 Monitoring & Metrics

### Key Metrics to Track

```yaml
Flag Evaluation Metrics:
  - flag_evaluation_latency_p99: <1ms
  - flag_cache_hit_rate: >99%
  - flag_evaluation_errors: <0.01%

Flag Usage Metrics:
  - flags_evaluated_per_second: 10,000+
  - unique_flags_active: 5,000
  - stale_flags (>90 days): <100

A/B Test Metrics:
  - experiment_sample_size: >10,000 per variant
  - experiment_duration_days: 7-14
  - statistical_significance: p-value <0.05

System Health:
  - kafka_consumer_lag: <1,000 messages
  - redis_hit_rate: >95%
  - flag_update_propagation_time: <5 seconds
```

---

## 📋 Interview Q&A

### Q1: How do you ensure flag changes propagate quickly?

**Answer:**
```
1. Kafka event streaming (5-second propagation)
2. Local cache with 5-min TTL (balances freshness vs load)
3. Redis for shared cache (sub-100ms fetch)
4. For emergency kill switches: HTTP push endpoint
5. Monitor propagation time with metrics
```

### Q2: How do you prevent flag evaluation from adding latency?

**Answer:**
```
1. Evaluate flags in-memory (cached locally)
2. No network calls during evaluation (<1ms)
3. Load flags at startup and keep in memory
4. Async Kafka updates refresh cache
5. Fallback to Redis only on cache miss (<1% of calls)
```

### Q3: How do you implement percentage rollout?

**Answer:**
```
1. Use consistent hashing: hash(flagKey + userId) % 100
2. If hash < rolloutPercentage → enabled
3. Same user always gets same result (consistent)
4. Gradual increase: 10% → 25% → 50% → 100%
5. Monitor metrics at each stage before increasing
```

### Q4: How do you handle A/B testing?

**Answer:**
```
1. Assign users to variants using consistent hashing
2. Track conversion events to experiment_metrics table
3. Calculate statistical significance (Z-test)
4. Require p-value <0.05 and >10K sample size
5. Run for 7-14 days minimum
6. Rollout winning variant gradually
```

### Q5: What if the flag service goes down?

**Answer:**
```
1. Services continue using cached flags (no impact)
2. Local cache (Caffeine) + Redis cache
3. Fallback to default values from config
4. Flag management down ≠ flag evaluation down
5. Decouple evaluation (fast) from management (admin)
```

### Q6: How do you clean up old flags?

**Answer:**
```
1. Track flag last_used timestamp
2. Mark flags >90 days unused as "deprecated"
3. Notify owners to remove flag code
4. Archive flags after 180 days
5. Enforce: New features must have flag removal plan
6. Code review: Check for flag cleanup
```

### Q7: How do you handle multi-tenancy?

**Answer:**
```
1. Add tenant_id to targeting rules
2. Example: Enable "new-ui" only for tenant "acme-corp"
3. Evaluate tenant context during flag check
4. Support tenant-level rollout percentages
5. Allows per-customer feature enablement
```

### Q8: How do you test flag changes before production?

**Answer:**
```
1. Stage environment with prod flag sync
2. "Employee-only" targeting rule (test in prod)
3. Rollout 1% → monitor → increase
4. Canary deployment: 1 instance → all instances
5. Kill switch ready for instant rollback
```

### Q9: What metrics prove an A/B test winner?

**Answer:**
```
1. Statistical significance: p-value <0.05
2. Minimum sample size: >10,000 per variant
3. Minimum duration: 7 days (account for weekly patterns)
4. Positive impact on key metric (conversion, revenue)
5. No regression on secondary metrics (latency, errors)
```

### Q10: How do you handle flag evaluation at high scale?

**Answer:**
```
1. In-memory evaluation (no DB/network)
2. Pre-compute complex rules at flag update time
3. Cache evaluation results for repeat checks
4. Horizontal scaling: Each instance has full flag set
5. Async background refresh (Kafka)
6. Monitor: 10K+ evaluations/sec per instance
```

---

## 🎯 The Perfect 2-Minute Interview Answer

> **Interviewer:** "Design a feature flags system for a large-scale application."

**Your Answer:**

"A feature flags system enables/disables features without deployments, supporting gradual rollouts and A/B testing.

**Architecture (3 layers):**

**1. Flag Management Service**
- Admin UI for flag CRUD operations
- Stores flags in PostgreSQL (source of truth)
- Publishes changes to Kafka
- Audit logs for compliance

**2. Distribution Layer**
- Kafka streams flag changes to all services
- Redis caches hot flags
- S3/CDN hosts flag snapshots for disaster recovery

**3. Evaluation SDK (embedded in services)**
- In-memory cache (Caffeine) of all flags
- Evaluation logic runs locally (<1ms latency)
- Listens to Kafka for updates (5-sec propagation)
- Fallback to Redis on cache miss

**Key Features:**

**Percentage Rollout**: Hash(flagKey + userId) % 100 → Gradual 10% → 50% → 100%

**A/B Testing**: Consistent hashing assigns variants, track metrics, Z-test for significance

**Targeting Rules**: Enable for specific users/segments (evaluated by priority)

**Kill Switch**: Kafka event instantly disables for all users

**Trade-offs:**
- Eventual consistency (5-sec propagation) for low latency (<1ms evaluation)
- In-memory cache duplicates data but eliminates network calls
- Flag service down ≠ evaluation down (cached locally)

**Scale:** 10K evaluations/sec per instance, 50K+ flags, 99.9% cache hit rate

This design prioritizes ultra-low latency evaluation while maintaining flexibility for rollouts and experiments."

---

**Last Updated**: March 2026
**Status**: ✅ Production Ready
**For**: 10+ Years Experienced Developer
