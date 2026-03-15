# Notification System - Production Implementation Guide

> **Target**: 10+ Years Experienced Developer
> **Updated**: March 2026
> **Interview Ready**: Complete guide with queue architecture and code examples

---

## 📊 Problem Statement

Design a **notification system** that handles:
- **100 million notifications per day** (~1,200 notifications/second)
- **Peak traffic**: 10,000 notifications/second (flash sales, breaking news)
- **Multi-channel**: Email, SMS, Push (iOS/Android), Webhooks, In-app
- **Real-time delivery**: <5 seconds for critical notifications
- **Delivery guarantee**: At-least-once delivery with idempotency
- **User preferences**: Opt-in/opt-out per channel
- **Cost optimization**: SMS is expensive (balance cost vs delivery)
- **Analytics**: Track delivery, open rates, click-through rates

---

## 🎯 Functional Requirements

### Core Features
1. **Send notification** - Trigger via API or event
2. **Multi-channel routing** - Email + SMS + Push for same event
3. **Template management** - Centralized templates with variables
4. **User preferences** - Opt-in/opt-out per channel
5. **Priority levels** - Critical vs normal vs low
6. **Retry logic** - Exponential backoff for failures
7. **Idempotency** - Prevent duplicate sends
8. **Delivery tracking** - Sent, delivered, opened, clicked
9. **Rate limiting** - Per channel, per user quotas
10. **Dead letter queue** - Handle permanent failures

### Non-Functional Requirements
1. **High Throughput** - 10,000 notifications/sec
2. **Low Latency** - <5 sec for critical, <1 min for normal
3. **High Availability** - 99.9% uptime
4. **Scalability** - Handle 10x traffic spikes
5. **Cost Efficiency** - Optimize SMS usage (most expensive)
6. **Auditability** - Track all notifications sent

---

## 🤔 Clarifying Questions (Interview Warm-up)

### Must Ask in Interview:
1. **Channels**: Which channels? (Email, SMS, Push, Webhook)
2. **Volume**: How many notifications per day? Peak traffic?
3. **Latency**: Real-time (<5s) or can tolerate delay (<5min)?
4. **Delivery guarantee**: At-least-once, at-most-once, or exactly-once?
5. **User preferences**: Can users opt-out? Per-channel or global?
6. **Cost**: What's the SMS budget? (SMS most expensive)
7. **Analytics**: Need delivery tracking? Open rates? Click rates?
8. **Multi-tenancy**: Different tenants with different providers?

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  NOTIFICATION SYSTEM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │        Application Services (Triggers)                   │          │
│  │  • Order Service: "Order confirmed"                      │          │
│  │  • Payment Service: "Payment failed"                     │          │
│  │  • Marketing Service: "Weekly digest"                    │          │
│  └───────────────────┬──────────────────────────────────────┘          │
│                      │                                                  │
│                      │ POST /notifications/send                         │
│                      ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │         Notification Gateway Service                     │          │
│  │  • Validate request                                      │          │
│  │  • Check user preferences (opt-out?)                     │          │
│  │  • Render template with variables                        │          │
│  │  • Determine channels (email, SMS, push)                 │          │
│  │  • Publish to Kafka                                      │          │
│  └───────────────────┬──────────────────────────────────────┘          │
│                      │                                                  │
│                      ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │           Kafka Topics (Multi-Channel)                   │          │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │          │
│  │  │ notifications│  │ notifications│  │ notifications│   │          │
│  │  │   -email     │  │    -sms      │  │    -push     │   │          │
│  │  │              │  │              │  │              │   │          │
│  │  │ Priority:    │  │ Priority:    │  │ Priority:    │   │          │
│  │  │ - critical   │  │ - critical   │  │ - critical   │   │          │
│  │  │ - normal     │  │ - normal     │  │ - normal     │   │          │
│  │  │ - low        │  │ - low        │  │ - low        │   │          │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │          │
│  └──────────────────────┬───────────────────────────────────┘          │
│                         │                                               │
│         ┌───────────────┼────────────────┬──────────────┐              │
│         ▼               ▼                ▼              ▼              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐   ┌──────────┐         │
│  │  Email   │    │   SMS    │    │   Push   │   │ Webhook  │         │
│  │  Worker  │    │  Worker  │    │  Worker  │   │  Worker  │         │
│  │  (10     │    │  (5      │    │  (5      │   │  (3      │         │
│  │instances)│    │instances)│    │instances)│   │instances)│         │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘   └────┬─────┘         │
│       │               │               │              │                │
│       │ Retry         │ Retry         │ Retry        │ Retry          │
│       │ (3 times)     │ (3 times)     │ (3 times)    │ (3 times)      │
│       ▼               ▼               ▼              ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐   ┌──────────┐         │
│  │ SendGrid │    │  Twilio  │    │ Firebase │   │  Custom  │         │
│  │   API    │    │   API    │    │   FCM    │   │ Webhook  │         │
│  └──────────┘    └──────────┘    └──────────┘   └──────────┘         │
│       │               │               │              │                │
│       ▼               ▼               ▼              ▼                │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │         Delivery Status Tracking (PostgreSQL)            │         │
│  │  ┌────────────────────────────────────────────────┐      │         │
│  │  │  notification_id | status  | channel | sent_at │      │         │
│  │  │  uuid-1234       | sent    | email   | t1      │      │         │
│  │  │  uuid-1234       | delivered| email  | t2      │      │         │
│  │  │  uuid-1234       | opened  | email   | t3      │      │         │
│  │  └────────────────────────────────────────────────┘      │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │         Dead Letter Queue (DLQ)                          │         │
│  │  • Failed notifications after 3 retries                  │         │
│  │  • Manual review and reprocessing                        │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema Design

### PostgreSQL Schema

```sql
-- Users' notification preferences
CREATE TABLE user_notification_preferences (
    user_id BIGINT PRIMARY KEY,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,
    webhook_enabled BOOLEAN DEFAULT FALSE,

    -- Per-category preferences
    marketing_emails BOOLEAN DEFAULT TRUE,
    transactional_emails BOOLEAN DEFAULT TRUE,

    -- Contact info
    email VARCHAR(255),
    phone_number VARCHAR(20),
    push_tokens JSONB,  -- Multiple device tokens
    webhook_url VARCHAR(500),

    updated_at TIMESTAMP DEFAULT NOW()
);

-- Notification templates
CREATE TABLE notification_templates (
    template_id VARCHAR(100) PRIMARY KEY,
    template_name VARCHAR(255),

    -- Template content per channel
    email_subject TEXT,
    email_body TEXT,
    sms_body TEXT,
    push_title TEXT,
    push_body TEXT,

    -- Variables expected (for validation)
    variables JSONB,  -- ['user_name', 'order_id', 'amount']

    -- Metadata
    category VARCHAR(50),  -- 'transactional', 'marketing', 'alerts'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Notification log (delivery tracking)
CREATE TABLE notification_log (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    template_id VARCHAR(100),

    -- Delivery details
    channel VARCHAR(20),  -- 'email', 'sms', 'push', 'webhook'
    priority VARCHAR(20),  -- 'critical', 'normal', 'low'
    status VARCHAR(20),  -- 'queued', 'sent', 'delivered', 'failed', 'opened', 'clicked'

    -- Content
    subject TEXT,
    body TEXT,
    variables JSONB,

    -- Tracking
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    failed_reason TEXT,

    -- Provider info
    provider_id VARCHAR(100),  -- External ID from SendGrid/Twilio
    provider_name VARCHAR(50),

    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_id_created (user_id, created_at DESC),
    INDEX idx_status (status),
    INDEX idx_channel_status (channel, status)
);

-- Dead letter queue (failed notifications)
CREATE TABLE notification_dlq (
    dlq_id SERIAL PRIMARY KEY,
    notification_id UUID,
    user_id BIGINT,
    channel VARCHAR(20),
    error_message TEXT,
    payload JSONB,  -- Full notification payload for replay
    failed_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255)
);

-- Rate limiting (prevent spam)
CREATE TABLE notification_rate_limits (
    user_id BIGINT,
    channel VARCHAR(20),
    time_window TIMESTAMP,  -- Hour bucket (2023-01-01 10:00:00)
    notification_count INTEGER DEFAULT 0,

    PRIMARY KEY (user_id, channel, time_window)
);
```

---

## 🚀 Implementation: Queue-Based Architecture

### Notification Gateway Service

```java
@RestController
@RequestMapping("/api/notifications")
public class NotificationController {

    @Autowired
    private NotificationGatewayService gatewayService;

    /**
     * Send notification (async via Kafka)
     */
    @PostMapping("/send")
    public NotificationResponse sendNotification(@RequestBody NotificationRequest request) {
        UUID notificationId = gatewayService.sendNotification(request);

        return NotificationResponse.builder()
            .notificationId(notificationId)
            .status("QUEUED")
            .message("Notification queued for delivery")
            .build();
    }

    /**
     * Get notification status
     */
    @GetMapping("/{notificationId}/status")
    public NotificationStatus getStatus(@PathVariable UUID notificationId) {
        return gatewayService.getNotificationStatus(notificationId);
    }
}
```

```java
@Service
public class NotificationGatewayService {

    @Autowired
    private UserPreferencesRepository preferencesRepo;

    @Autowired
    private TemplateService templateService;

    @Autowired
    private KafkaTemplate<String, NotificationEvent> kafkaTemplate;

    @Autowired
    private NotificationLogRepository notificationLogRepo;

    @Autowired
    private RateLimitService rateLimitService;

    /**
     * Main entry point: Send notification
     */
    @Transactional
    public UUID sendNotification(NotificationRequest request) {
        Long userId = request.getUserId();
        String templateId = request.getTemplateId();
        Map<String, Object> variables = request.getVariables();

        // 1. Check user preferences (opt-out?)
        UserNotificationPreferences prefs = preferencesRepo.findByUserId(userId)
            .orElseThrow(() -> new UserNotFoundException(userId));

        List<String> enabledChannels = getEnabledChannels(prefs, request.getChannels());

        if (enabledChannels.isEmpty()) {
            log.info("All channels disabled for user {}", userId);
            throw new NotificationBlockedException("User opted out of all channels");
        }

        // 2. Check rate limits (prevent spam)
        for (String channel : enabledChannels) {
            if (!rateLimitService.allowNotification(userId, channel)) {
                log.warn("Rate limit exceeded for user {} channel {}", userId, channel);
                enabledChannels.remove(channel);
            }
        }

        // 3. Render templates for each channel
        NotificationTemplate template = templateService.getTemplate(templateId);
        Map<String, RenderedNotification> renderedByChannel = new HashMap<>();

        for (String channel : enabledChannels) {
            RenderedNotification rendered = templateService.render(template, channel, variables);
            renderedByChannel.put(channel, rendered);
        }

        // 4. Create notification log entry
        UUID notificationId = UUID.randomUUID();
        NotificationLog log = NotificationLog.builder()
            .notificationId(notificationId)
            .userId(userId)
            .templateId(templateId)
            .status("QUEUED")
            .variables(variables)
            .createdAt(Instant.now())
            .build();
        notificationLogRepo.save(log);

        // 5. Publish to Kafka (fan-out to channels)
        for (Map.Entry<String, RenderedNotification> entry : renderedByChannel.entrySet()) {
            String channel = entry.getKey();
            RenderedNotification rendered = entry.getValue();

            NotificationEvent event = NotificationEvent.builder()
                .notificationId(notificationId)
                .userId(userId)
                .channel(channel)
                .priority(request.getPriority())
                .subject(rendered.getSubject())
                .body(rendered.getBody())
                .recipientContact(getRecipientContact(prefs, channel))
                .build();

            // Route to channel-specific topic
            String topic = "notifications-" + channel;
            kafkaTemplate.send(topic, notificationId.toString(), event);

            log.info("Published notification {} to channel {}", notificationId, channel);
        }

        return notificationId;
    }

    private List<String> getEnabledChannels(UserNotificationPreferences prefs, List<String> requestedChannels) {
        List<String> enabled = new ArrayList<>();

        if (requestedChannels.contains("email") && prefs.isEmailEnabled()) {
            enabled.add("email");
        }
        if (requestedChannels.contains("sms") && prefs.isSmsEnabled()) {
            enabled.add("sms");
        }
        if (requestedChannels.contains("push") && prefs.isPushEnabled()) {
            enabled.add("push");
        }

        return enabled;
    }

    private String getRecipientContact(UserNotificationPreferences prefs, String channel) {
        return switch (channel) {
            case "email" -> prefs.getEmail();
            case "sms" -> prefs.getPhoneNumber();
            case "push" -> prefs.getPushTokens().get(0).toString();  // First token
            default -> null;
        };
    }
}
```

---

## 📧 Email Worker with Retry Logic

```java
@Service
public class EmailNotificationWorker {

    @Autowired
    private EmailProviderClient emailProviderClient;  // SendGrid

    @Autowired
    private NotificationLogRepository notificationLogRepo;

    @Autowired
    private KafkaTemplate<String, NotificationEvent> kafkaTemplate;

    private static final int MAX_RETRIES = 3;
    private static final long[] RETRY_DELAYS_MS = {1000, 5000, 30000};  // 1s, 5s, 30s

    /**
     * Consume email notifications from Kafka
     */
    @KafkaListener(topics = "notifications-email", groupId = "email-worker")
    public void processEmail(NotificationEvent event) {
        UUID notificationId = event.getNotificationId();
        int retryCount = event.getRetryCount();

        try {
            log.info("Processing email notification {} (attempt {})", notificationId, retryCount + 1);

            // 1. Send email via provider (SendGrid)
            SendEmailRequest request = SendEmailRequest.builder()
                .to(event.getRecipientContact())
                .subject(event.getSubject())
                .body(event.getBody())
                .build();

            SendEmailResponse response = emailProviderClient.sendEmail(request);

            // 2. Update notification log
            notificationLogRepo.updateStatus(notificationId, "SENT", response.getProviderId());

            log.info("Email notification {} sent successfully: provider_id={}",
                     notificationId, response.getProviderId());

            // 3. Track delivery status via webhook (from SendGrid)
            // SendGrid will POST to /webhooks/email-delivery with status updates

        } catch (RateLimitException e) {
            log.warn("Rate limit hit for email {}, will retry", notificationId);
            retryWithBackoff(event, retryCount, e);

        } catch (TemporaryProviderException e) {
            log.error("Temporary error sending email {}, will retry", notificationId, e);
            retryWithBackoff(event, retryCount, e);

        } catch (PermanentProviderException e) {
            log.error("Permanent error sending email {}, moving to DLQ", notificationId, e);
            moveToDeadLetterQueue(event, e);
            notificationLogRepo.updateStatus(notificationId, "FAILED", e.getMessage());

        } catch (Exception e) {
            log.error("Unexpected error sending email {}", notificationId, e);
            retryWithBackoff(event, retryCount, e);
        }
    }

    /**
     * Retry with exponential backoff
     */
    private void retryWithBackoff(NotificationEvent event, int retryCount, Exception error) {
        if (retryCount >= MAX_RETRIES) {
            log.error("Max retries exceeded for notification {}, moving to DLQ",
                     event.getNotificationId());
            moveToDeadLetterQueue(event, error);
            notificationLogRepo.updateStatus(event.getNotificationId(), "FAILED",
                                            "Max retries exceeded: " + error.getMessage());
            return;
        }

        // Exponential backoff: 1s, 5s, 30s
        long delayMs = RETRY_DELAYS_MS[retryCount];

        try {
            Thread.sleep(delayMs);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        // Re-publish to Kafka with incremented retry count
        NotificationEvent retryEvent = event.toBuilder()
            .retryCount(retryCount + 1)
            .build();

        kafkaTemplate.send("notifications-email", event.getNotificationId().toString(), retryEvent);

        log.info("Retrying notification {} (attempt {})",
                 event.getNotificationId(), retryCount + 2);
    }

    /**
     * Move failed notification to Dead Letter Queue
     */
    private void moveToDeadLetterQueue(NotificationEvent event, Exception error) {
        NotificationDLQ dlq = NotificationDLQ.builder()
            .notificationId(event.getNotificationId())
            .userId(event.getUserId())
            .channel("email")
            .errorMessage(error.getMessage())
            .payload(event)
            .failedAt(Instant.now())
            .build();

        // Save to DLQ table
        notificationDLQRepository.save(dlq);

        // Publish to DLQ Kafka topic for monitoring
        kafkaTemplate.send("notifications-dlq", event.getNotificationId().toString(), event);
    }
}
```

---

## 📱 Push Notification Worker (Firebase FCM)

```java
@Service
public class PushNotificationWorker {

    @Autowired
    private FirebaseMessaging firebaseMessaging;

    @Autowired
    private NotificationLogRepository notificationLogRepo;

    @KafkaListener(topics = "notifications-push", groupId = "push-worker")
    public void processPush(NotificationEvent event) {
        UUID notificationId = event.getNotificationId();

        try {
            // 1. Build FCM message
            Message message = Message.builder()
                .setToken(event.getRecipientContact())  // Device token
                .setNotification(Notification.builder()
                    .setTitle(event.getSubject())
                    .setBody(event.getBody())
                    .build())
                .putData("notification_id", notificationId.toString())
                .build();

            // 2. Send via Firebase
            String fcmMessageId = firebaseMessaging.send(message);

            // 3. Update status
            notificationLogRepo.updateStatus(notificationId, "SENT", fcmMessageId);

            log.info("Push notification {} sent successfully: fcm_id={}",
                     notificationId, fcmMessageId);

        } catch (FirebaseMessagingException e) {
            if (e.getMessagingErrorCode() == MessagingErrorCode.UNREGISTERED) {
                // Device token invalid, remove from user preferences
                log.warn("Invalid push token for user {}, removing", event.getUserId());
                removeInvalidPushToken(event.getUserId(), event.getRecipientContact());
                notificationLogRepo.updateStatus(notificationId, "FAILED", "Invalid push token");

            } else {
                log.error("Error sending push notification {}", notificationId, e);
                retryWithBackoff(event, event.getRetryCount(), e);
            }
        }
    }
}
```

---

## 📨 SMS Worker (Twilio)

```java
@Service
public class SmsNotificationWorker {

    @Autowired
    private Twilio twilioClient;

    @Autowired
    private NotificationLogRepository notificationLogRepo;

    @KafkaListener(topics = "notifications-sms", groupId = "sms-worker")
    public void processSms(NotificationEvent event) {
        UUID notificationId = event.getNotificationId();

        try {
            // 1. Validate phone number format
            String phoneNumber = event.getRecipientContact();
            if (!isValidPhoneNumber(phoneNumber)) {
                throw new InvalidPhoneNumberException(phoneNumber);
            }

            // 2. Send SMS via Twilio
            Message smsMessage = Message.creator(
                new PhoneNumber(phoneNumber),
                new PhoneNumber(twilioFromNumber),
                event.getBody()
            ).create();

            // 3. Update status
            notificationLogRepo.updateStatus(notificationId, "SENT", smsMessage.getSid());

            log.info("SMS notification {} sent successfully: twilio_sid={}",
                     notificationId, smsMessage.getSid());

            // 4. Track cost (SMS is expensive)
            trackSmsCost(event.getUserId(), smsMessage.getPrice());

        } catch (ApiException e) {
            if (e.getCode() == 21211) {  // Invalid phone number
                log.error("Invalid phone number for notification {}", notificationId);
                notificationLogRepo.updateStatus(notificationId, "FAILED", "Invalid phone number");
            } else {
                retryWithBackoff(event, event.getRetryCount(), e);
            }
        }
    }

    private void trackSmsCost(Long userId, BigDecimal cost) {
        // Track SMS cost per user for billing/analytics
        metricService.recordSmsCost(userId, cost);
    }
}
```

---

## 🎨 Template Service with Handlebars

```java
@Service
public class TemplateService {

    @Autowired
    private NotificationTemplateRepository templateRepo;

    private final Handlebars handlebars = new Handlebars();

    /**
     * Render template with variables
     */
    public RenderedNotification render(NotificationTemplate template, String channel,
                                      Map<String, Object> variables) {
        try {
            String subject = null;
            String body = null;

            switch (channel) {
                case "email":
                    subject = renderTemplate(template.getEmailSubject(), variables);
                    body = renderTemplate(template.getEmailBody(), variables);
                    break;

                case "sms":
                    body = renderTemplate(template.getSmsBody(), variables);
                    break;

                case "push":
                    subject = renderTemplate(template.getPushTitle(), variables);
                    body = renderTemplate(template.getPushBody(), variables);
                    break;
            }

            return RenderedNotification.builder()
                .subject(subject)
                .body(body)
                .build();

        } catch (IOException e) {
            throw new TemplateRenderException("Failed to render template", e);
        }
    }

    private String renderTemplate(String templateString, Map<String, Object> variables) throws IOException {
        if (templateString == null) {
            return null;
        }

        Template template = handlebars.compileInline(templateString);
        return template.apply(variables);
    }
}
```

**Template Example:**

```sql
INSERT INTO notification_templates (template_id, template_name, email_subject, email_body, sms_body)
VALUES (
    'order-confirmed',
    'Order Confirmation',
    'Order #{{order_id}} Confirmed!',
    'Hi {{user_name}},\n\nYour order #{{order_id}} for ${{amount}} has been confirmed.\n\nEstimated delivery: {{delivery_date}}',
    'Order #{{order_id}} confirmed! Delivery by {{delivery_date}}. Track: {{tracking_url}}'
);
```

---

## 🔄 Idempotency Pattern

```java
@Service
public class IdempotencyService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    private static final long IDEMPOTENCY_TTL_HOURS = 24;

    /**
     * Check if notification already processed (prevent duplicates)
     */
    public boolean isAlreadyProcessed(UUID notificationId, String channel) {
        String key = "notification:processed:" + notificationId + ":" + channel;
        return redisTemplate.hasKey(key);
    }

    /**
     * Mark notification as processed
     */
    public void markAsProcessed(UUID notificationId, String channel) {
        String key = "notification:processed:" + notificationId + ":" + channel;
        redisTemplate.opsForValue().set(key, "1", IDEMPOTENCY_TTL_HOURS, TimeUnit.HOURS);
    }
}
```

**Usage in Worker:**

```java
@KafkaListener(topics = "notifications-email")
public void processEmail(NotificationEvent event) {
    // Check idempotency
    if (idempotencyService.isAlreadyProcessed(event.getNotificationId(), "email")) {
        log.info("Notification {} already processed, skipping", event.getNotificationId());
        return;
    }

    // Process notification...
    emailProviderClient.sendEmail(event);

    // Mark as processed
    idempotencyService.markAsProcessed(event.getNotificationId(), "email");
}
```

---

## 🚦 Rate Limiting Service

```java
@Service
public class RateLimitService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    // Limits per channel (per user, per hour)
    private static final Map<String, Integer> RATE_LIMITS = Map.of(
        "email", 100,
        "sms", 10,    // SMS is expensive
        "push", 50
    );

    /**
     * Check if user can receive notification on channel
     */
    public boolean allowNotification(Long userId, String channel) {
        String key = String.format("rate_limit:%d:%s:%s",
            userId, channel, getCurrentHourBucket());

        Long count = redisTemplate.opsForValue().increment(key);

        // Set TTL on first increment
        if (count == 1) {
            redisTemplate.expire(key, 1, TimeUnit.HOURS);
        }

        int limit = RATE_LIMITS.getOrDefault(channel, 100);
        return count <= limit;
    }

    private String getCurrentHourBucket() {
        ZonedDateTime now = ZonedDateTime.now();
        return now.truncatedTo(ChronoUnit.HOURS).toString();
    }
}
```

---

## ⚠️ Edge Cases & Failure Scenarios

### 1. Duplicate Notifications

**Problem**: Kafka redelivery causes duplicate sends

**Solution**: Idempotency check using Redis
```java
if (idempotencyService.isAlreadyProcessed(notificationId, channel)) {
    return;  // Skip duplicate
}
```

### 2. Provider Rate Limit

**Problem**: SendGrid rate limit exceeded (429 error)

**Solution**: Exponential backoff + circuit breaker
```java
catch (RateLimitException e) {
    Thread.sleep(calculateBackoff(retryCount));
    retry();
}
```

### 3. Invalid Contact Info

**Problem**: Email bounced, phone number invalid

**Solution**: Update user preferences, mark notification as failed
```java
if (error.isInvalidRecipient()) {
    disableChannelForUser(userId, channel);
    notificationLogRepo.updateStatus(id, "FAILED", "Invalid recipient");
}
```

### 4. Template Variable Missing

**Problem**: Template expects {{user_name}} but not provided

**Solution**: Validate variables before rendering
```java
Set<String> expectedVars = template.getVariables();
Set<String> providedVars = variables.keySet();

if (!providedVars.containsAll(expectedVars)) {
    throw new MissingVariablesException(expectedVars, providedVars);
}
```

---

## 📊 Monitoring & Metrics

### Key Metrics

```yaml
Throughput:
  - notifications_sent_per_second: 1,200 (avg), 10,000 (peak)
  - notifications_per_channel: email=60%, sms=10%, push=30%

Delivery:
  - delivery_rate: >98%
  - delivery_latency_p99: <5 seconds (critical), <60s (normal)
  - failure_rate: <2%

Retries:
  - retry_rate: ~5%
  - dlq_size: <1,000 messages

Cost:
  - sms_cost_per_day: $500 (track closely)
  - email_cost_per_day: $50
  - push_cost_per_day: $0 (free)

User Behavior:
  - opt_out_rate: ~10%
  - open_rate_email: ~25%
  - click_rate_email: ~5%
```

---

## 📋 Interview Q&A

### Q1: How do you prevent duplicate notifications?

**Answer:**
```
1. Idempotency check using Redis
2. Key: notification:{id}:{channel}
3. TTL: 24 hours
4. Check before processing, mark after sending
5. Kafka redelivery won't cause duplicates
```

### Q2: How do you handle retry logic?

**Answer:**
```
1. Exponential backoff: 1s, 5s, 30s
2. Max 3 retries
3. Distinguish temporary (retry) vs permanent (DLQ) errors
4. Track retry count in event payload
5. After max retries, move to Dead Letter Queue
```

### Q3: How do you optimize SMS costs?

**Answer:**
```
1. Rate limit: 10 SMS per user per hour
2. User preference: Opt-out option
3. Template length: Keep SMS <160 chars (avoid multi-part)
4. Priority: SMS only for critical notifications
5. Fallback: If SMS fails, try email
6. Track cost per user for billing
```

### Q4: How do you handle user opt-out?

**Answer:**
```
1. user_notification_preferences table
2. Per-channel opt-out (email, SMS, push)
3. Per-category opt-out (marketing, transactional)
4. Check preferences before sending
5. One-click unsubscribe link in emails (GDPR)
6. Global opt-out across all channels
```

### Q5: How do you track delivery status?

**Answer:**
```
1. notification_log table with status field
2. Statuses: queued → sent → delivered → opened → clicked
3. Webhooks from providers (SendGrid, Twilio)
4. Provider ID stored for reconciliation
5. Analytics dashboard showing funnel
6. Alert if delivery_rate drops below 95%
```

### Q6: How do you handle priority notifications?

**Answer:**
```
1. Three Kafka topics per channel:
   - notifications-email-critical
   - notifications-email-normal
   - notifications-email-low
2. More workers on critical topics
3. Critical: <5s latency, more retries
4. Low: Can wait minutes, fewer retries
5. Rate limits don't apply to critical
```

### Q7: How do you scale workers?

**Answer:**
```
Horizontal scaling:
- Add more Kafka consumer instances
- Kafka partitions enable parallel processing
- 10 email workers, 5 SMS workers, 5 push workers
- Auto-scale based on queue depth

Bottlenecks:
- SMS: Provider rate limits (100 requests/sec)
- Email: Provider rate limits (1,000 requests/sec)
- Solution: Multiple provider accounts, round-robin
```

### Q8: What if notification service goes down?

**Answer:**
```
1. Notifications queued in Kafka (persistent)
2. Workers restart, continue from last offset
3. No data loss (Kafka retention: 7 days)
4. Gateway service is stateless (can restart)
5. User preferences cached in Redis
6. Fallback: Read from DB if Redis down
```

### Q9: How do you test the notification system?

**Answer:**
```
1. Unit tests: Template rendering, rate limiting
2. Integration tests: Kafka + workers + mock providers
3. Load tests: Simulate 10K notifications/sec
4. Chaos: Kill workers, Kafka nodes, Redis
5. Dry-run mode: Log instead of sending (staging)
6. Shadow mode: Dual-send to test new provider
```

### Q10: How do you handle webhooks for delivery status?

**Answer:**
```
1. SendGrid/Twilio POST to /webhooks/delivery-status
2. Verify webhook signature (security)
3. Update notification_log with new status
4. Idempotency: Same webhook may arrive multiple times
5. Async processing: Queue webhook, respond 200 OK
6. Retry: If webhook fails, providers retry up to 3 days
```

---

## 🎯 The Perfect 2-Minute Interview Answer

> **Interviewer:** "Design a notification system that sends emails, SMS, and push notifications."

**Your Answer:**

"I'll design a scalable notification system handling 100M notifications/day across multiple channels.

**Architecture (3 layers):**

**1. Gateway Service**
- Validates requests, checks user preferences (opt-out)
- Renders templates with variables (Handlebars)
- Publishes to Kafka topics (fan-out by channel)

**2. Message Queue (Kafka)**
- 3 topics per channel: email, SMS, push
- Priority partitions: critical, normal, low
- Persistent storage (7-day retention)

**3. Workers (Kafka Consumers)**
- Email worker: SendGrid API (10 instances)
- SMS worker: Twilio API (5 instances)
- Push worker: Firebase FCM (5 instances)

**Key Features:**

**Idempotency**: Redis cache (notification_id:channel) prevents duplicates

**Retry Logic**: Exponential backoff (1s, 5s, 30s), max 3 retries, then DLQ

**Rate Limiting**: 100 emails/hour, 10 SMS/hour per user (Redis counters)

**User Preferences**: Per-channel opt-out, stored in PostgreSQL

**Delivery Tracking**: notification_log table with statuses (queued → sent → delivered → opened)

**Cost Optimization**: SMS most expensive, rate limit aggressively

**Webhooks**: Providers POST delivery status, update notification_log

**Trade-offs:**
- At-least-once delivery (idempotency handles duplicates)
- Kafka adds latency (<5s) but provides reliability
- Workers scale horizontally (add more instances)

**Scale:** 10K notifications/sec peak, >98% delivery rate, <5s p99 latency

This design is production-ready and handles failures gracefully."

---

**Last Updated**: March 2026
**Status**: ✅ Production Ready
**For**: 10+ Years Experienced Developer
