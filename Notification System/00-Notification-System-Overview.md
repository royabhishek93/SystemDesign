# Notification System - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is a Notification System?
A notification system sends messages to users through different channels (email, SMS, push, in-app). It handles delivery, retries, preferences, and tracking.

## 2) Clarifying Questions (Interview Warm-up)
- What channels (email, SMS, push, webhook)?
- Expected volume per day/hour?
- Real-time or can be delayed?
- Do we need user preferences and opt-out?
- Delivery guarantees and tracking?

## 3) Approaches to Implement Notifications

### Approach A: Direct Send (Synchronous)
What it is:
- Service directly calls email/SMS provider.

Pros:
- Simple for low volume

Cons:
- User waits for send
- No retry on failure

### Approach B: Queue-Based (Async)
What it is:
- Push notifications to queue, workers send them.

Pros:
- Decouples sender from delivery
- Better resilience

Cons:
- Adds latency

### Approach C: Priority Queues
What it is:
- Separate queues for critical vs normal notifications.

Pros:
- Critical messages first

Cons:
- More queues to manage

### Approach D: Fan-Out Pattern
What it is:
- One event triggers multiple notification types.

Pros:
- Good for multi-channel

Cons:
- Complexity in orchestration

### Approach E: Template Service
What it is:
- Centralized template store with variable substitution.

Pros:
- Consistent messaging
- Easy updates

Cons:
- Template versioning needed

### Approach F: User Preference Engine
What it is:
- Check user prefs before sending.

Pros:
- Respects opt-outs

Cons:
- Extra lookup per notification

### Approach G: Notification Gateway
What it is:
- Single API routes to all channels.

Pros:
- Clean abstraction

Cons:
- Gateway becomes critical

### Approach H: Multi-Tenant Notifications
What it is:
- Separate channels/quotas per tenant.

Pros:
- SaaS isolation

Cons:
- More config complexity

## 4) Common Technologies
- Queue: SQS, Kafka
- Providers: SendGrid, Twilio, Firebase Cloud Messaging
- Templates: Handlebars, Mustache
- Tracking: Segment, Mixpanel

## 5) Key Concepts (Interview Must-Know)
- Idempotency (avoid duplicate sends)
- Rate limiting per channel
- DLQ for failed notifications
- Delivery status tracking

## 6) Production Checklist
- Retry logic with exponential backoff
- Respect opt-out preferences
- Monitor delivery rates per channel
- Cost controls for SMS/push

## 7) Quick Interview Answer (30 seconds)
"A notification system sends messages across channels like email, SMS, and push. The best approach is queue-based with workers, templates, and user preferences. Multi-channel fan-out handles complex use cases. At scale, use priority queues, rate limits, and centralized gateways for reliability."
