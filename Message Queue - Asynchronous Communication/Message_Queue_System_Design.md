# Message Queue - Asynchronous Communication System Design

## What is a Message Queue?

A Message Queue is an **asynchronous communication pattern** where messages are sent between services without requiring immediate response. It decouples producers (senders) from consumers (receivers).

---

## Complete Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE QUEUE ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────────────────────┐         ┌──────────────┐
│   Producer   │         │       Message Broker         │         │   Consumer   │
│   Service    │────────▶│                              │────────▶│   Service    │
│              │  Send   │  ┌────────────────────────┐  │  Poll   │              │
│  - API       │  Msg    │  │      Topic/Queue       │  │  Msg    │  - Worker    │
│  - Upload    │         │  │                        │  │         │  - Processor │
│  - Order     │         │  │  [M1][M2][M3][M4][M5]  │  │         │  - Emailer   │
└──────────────┘         │  │                        │  │         └──────────────┘
                         │  └────────────────────────┘  │
┌──────────────┐         │                              │         ┌──────────────┐
│   Producer   │         │  ┌────────────────────────┐  │         │   Consumer   │
│   Service    │────────▶│  │   Another Topic/Queue  │  │────────▶│   Service    │
│              │         │  │                        │  │         │              │
└──────────────┘         │  │  [M6][M7][M8]          │  │         └──────────────┘
                         │  │                        │  │
                         │  └────────────────────────┘  │         ┌──────────────┐
                         │                              │────────▶│   Consumer   │
                         │  Persistence (Disk/Memory)   │         │   Service    │
                         │  Replication (HA)            │         │              │
                         │  Partitioning (Scale)        │         └──────────────┘
                         └──────────────────────────────┘
```

---

## Message Flow - Step by Step

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MESSAGE LIFECYCLE                                │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: PRODUCE                    Step 2: STORE                    Step 3: CONSUME
─────────────────                  ──────────────                   ────────────────

┌──────────┐                       ┌──────────┐                     ┌──────────┐
│ Producer │  Publish Message      │  Broker  │  Consumer Polls     │ Consumer │
│          │──────────────────────▶│          │────────────────────▶│          │
│          │  {                     │  Queue:  │  {                  │          │
│          │    id: "123"           │  ┌─────┐ │    id: "123"        │          │
│          │    type: "order"       │  │ MSG │ │    type: "order"    │          │
│          │    data: {...}         │  └─────┘ │    data: {...}      │          │
│          │  }                     │          │  }                  │          │
└──────────┘                       └──────────┘                     └──────────┘
     │                                   │                                │
     │                                   │                                │
     ▼                                   ▼                                ▼
Async Return                      Persist to Disk              Process Message
(Non-blocking)                    Replicate to HA              Send ACK/NACK


Step 4: ACKNOWLEDGMENT             Step 5: REMOVE/RETRY
──────────────────────             ────────────────────

┌──────────┐                       ┌──────────┐
│ Consumer │  Success: ACK         │  Broker  │  Message Deleted
│          │──────────────────────▶│          │
│          │                       │          │  OR
│          │  Failure: NACK        │          │
│          │──────────────────────▶│          │  Move to DLQ
└──────────┘                       └──────────┘  (Dead Letter Queue)
```

---

## Message Queue Patterns

### 1. Point-to-Point (Queue)

```
┌─────────────────────────────────────────────────────────────┐
│              POINT-TO-POINT PATTERN (Queue)                  │
└─────────────────────────────────────────────────────────────┘

Producer 1 ─────┐
                │
Producer 2 ─────┼─────▶ ┌─────────────────┐ ─────┐
                │       │   Order Queue   │      │  ONE consumer
Producer 3 ─────┘       │  [M1][M2][M3]   │      │  processes each
                        └─────────────────┘ ─────┴─▶ Consumer 1
                                                      (gets M1, M2, M3)

✓ Each message consumed by ONE consumer only
✓ Load balancing across multiple consumers
✓ Use case: Order processing, job queue
```

### 2. Publish-Subscribe (Topic)

```
┌─────────────────────────────────────────────────────────────┐
│           PUBLISH-SUBSCRIBE PATTERN (Topic)                  │
└─────────────────────────────────────────────────────────────┘

                        ┌─────────────────┐
Producer ──────────────▶│  User.Created   │
                        │     Topic       │
                        │  [M1][M2][M3]   │
                        └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
              Consumer 1    Consumer 2  Consumer 3
              (Email)       (Analytics) (Audit Log)
              M1,M2,M3      M1,M2,M3    M1,M2,M3

✓ Each message consumed by ALL subscribers
✓ Multiple consumers get same message
✓ Use case: Event broadcasting, notifications
```

---

## Kafka Architecture (Popular Message Queue)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      KAFKA CLUSTER ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────┐         ┌──────────────────────────────────────────┐
│  Producers  │         │           KAFKA CLUSTER                  │
│             │         │                                          │
│  - App 1    │────────▶│  Topic: user-events (3 partitions)      │
│  - App 2    │         │                                          │
│  - App 3    │         │  ┌─────────────┐  ┌─────────────┐       │
└─────────────┘         │  │ Partition 0 │  │ Partition 1 │       │
                        │  │ Broker 1    │  │ Broker 2    │       │
                        │  │ [M1][M4]    │  │ [M2][M5]    │       │
                        │  │ [M7]        │  │ [M8]        │       │
                        │  └─────────────┘  └─────────────┘       │
                        │                                          │
                        │  ┌─────────────┐                        │
                        │  │ Partition 2 │  Replication Factor: 2 │
                        │  │ Broker 3    │  (High Availability)   │
                        │  │ [M3][M6]    │                        │
                        │  │ [M9]        │  Retention: 7 days     │
                        │  └─────────────┘  (Persistent Storage)  │
                        │                                          │
                        └──────────────────────────────────────────┘
                                        │
                        ┌───────────────┼───────────────┐
                        ▼               ▼               ▼
                 ┌────────────┐  ┌────────────┐  ┌────────────┐
                 │ Consumer   │  │ Consumer   │  │ Consumer   │
                 │ Group A    │  │ Group A    │  │ Group B    │
                 │ (Part 0,1) │  │ (Part 2)   │  │ (All Parts)│
                 └────────────┘  └────────────┘  └────────────┘

                 Same Group = Load Balance
                 Different Group = Broadcast
```

---

## Message Delivery Guarantees

```
┌─────────────────────────────────────────────────────────────────┐
│                   DELIVERY GUARANTEES                            │
└─────────────────────────────────────────────────────────────────┘

1. AT-MOST-ONCE (Fire and Forget)
──────────────────────────────────
Producer ─────▶ Broker ─────▶ Consumer
          Send         Deliver
          (no ACK)     (no ACK)

✓ Fast, no confirmation
✗ May lose messages
Use: Metrics, logs


2. AT-LEAST-ONCE (Retry Until Success)
───────────────────────────────────────
Producer ─────▶ Broker ─────▶ Consumer
          Send▲        Deliver▲        │
              │ACK            │ACK     │
              └───────────────────────┘
              Retry on failure

✓ No data loss
✗ Possible duplicates
Use: Order processing, payments (with idempotency)


3. EXACTLY-ONCE (Guaranteed Single Delivery)
─────────────────────────────────────────────
Producer ─────▶ Broker ─────▶ Consumer
          Send▲        Deliver▲        │
              │TX            │TX      │
              └──────────────────────┘
              Transactional

✓ No loss, no duplicates
✗ Slower, complex
Use: Financial transactions, critical systems
```

---

## Real-World Example: E-commerce Order Processing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  E-COMMERCE ORDER FLOW WITH QUEUES                       │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────┐    Order        ┌──────────────┐
│   API    │  Created Event  │ Order Queue  │
│ Gateway  │────────────────▶│              │
└──────────┘                 └──────────────┘
     │                              │
     │                              ├─────▶ Inventory Service
     │                              │       ├─▶ Check Stock
     │                              │       └─▶ Reserve Items
     │                              │
     │                              ├─────▶ Payment Service
     │                              │       ├─▶ Charge Card
     │                              │       └─▶ Verify Payment
     │                              │
     │                              ├─────▶ Notification Service
     │                              │       ├─▶ Send Email
     │                              │       └─▶ Send SMS
     │                              │
     │                              └─────▶ Analytics Service
     │                                      └─▶ Track Metrics
     │
     ▼
Return Immediately
(Order Accepted - 202)


TIMELINE:
─────────
t=0ms    User places order
t=10ms   API returns "Order Accepted"
t=100ms  Inventory reserved
t=500ms  Payment processed
t=600ms  Email sent
t=1000ms All processing complete

✓ User doesn't wait for slow operations
✓ Services can fail and retry independently
✓ System scales horizontally
```

---

## Message Queue Technologies Comparison

```
┌────────────────────────────────────────────────────────────────────┐
│              MESSAGE QUEUE TECHNOLOGY COMPARISON                    │
└────────────────────────────────────────────────────────────────────┘

╔══════════╦═════════════╦═════════════╦════════════╦══════════════╗
║ Feature  ║   Kafka     ║ RabbitMQ    ║    AWS     ║    Redis     ║
║          ║             ║             ║    SQS     ║    Streams   ║
╠══════════╬═════════════╬═════════════╬════════════╬══════════════╣
║ Type     ║ Log-based   ║ Traditional ║ Managed    ║ In-memory    ║
║          ║ distributed ║ message     ║ Queue      ║ log          ║
║          ║ log         ║ broker      ║            ║              ║
╠══════════╬═════════════╬═════════════╬════════════╬══════════════╣
║ Through- ║ Very High   ║ Medium      ║ Medium     ║ Very High    ║
║ put      ║ (millions/s)║ (10k-100k/s)║ (3000/s)   ║ (millions/s) ║
╠══════════╬═════════════╬═════════════╬════════════╬══════════════╣
║ Persist- ║ Disk        ║ Disk/Memory ║ Managed    ║ Memory+Disk  ║
║ ence     ║ (days/weeks)║ (optional)  ║ (14 days)  ║ (AOF)        ║
╠══════════╬═════════════╬═════════════╬════════════╬══════════════╣
║ Order    ║ Partition   ║ Queue       ║ FIFO Queue ║ Stream       ║
║ Guarantee║ level       ║ level       ║ (ordered)  ║ level        ║
╠══════════╬═════════════╬═════════════╬════════════╬══════════════╣
║ Use Case ║ Event       ║ Task Queue  ║ Simple     ║ Fast event   ║
║          ║ streaming,  ║ RPC-style   ║ queuing,   ║ stream,      ║
║          ║ Big data    ║ messaging   ║ Serverless ║ Real-time    ║
╚══════════╩═════════════╩═════════════╩════════════╩══════════════╝
```

---

## Kafka Implementation Example

```python
# Producer (Python - Kafka)
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send message
order = {
    'order_id': '12345',
    'user_id': 'user_789',
    'items': [{'product': 'laptop', 'price': 999}],
    'timestamp': '2024-03-15T10:00:00Z'
}

# Asynchronous send
future = producer.send('order-created', value=order)
print("Order sent, not waiting for confirmation")

# Or wait for confirmation
result = future.get(timeout=10)
print(f"Message sent to partition {result.partition}")


# Consumer (Python - Kafka)
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'order-created',
    bootstrap_servers=['localhost:9092'],
    group_id='payment-service',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',  # Start from beginning
    enable_auto_commit=True
)

# Poll messages
for message in consumer:
    order = message.value
    print(f"Processing order: {order['order_id']}")

    try:
        # Process payment
        process_payment(order)
        # Auto-commit on success
    except Exception as e:
        print(f"Payment failed: {e}")
        # Message will be reprocessed
```

---

## Advanced Patterns

### 1. Dead Letter Queue (DLQ)

```
┌─────────────────────────────────────────────────────────────┐
│                  DEAD LETTER QUEUE PATTERN                   │
└─────────────────────────────────────────────────────────────┘

Producer ──▶ ┌──────────────┐ ──▶ Consumer
             │ Main Queue   │      Process ✓
             │ [M1][M2][M3] │
             └──────────────┘
                    │
                    │ After 3 retries
                    │ or processing fails
                    ▼
             ┌──────────────┐      Manual Review
             │  Dead Letter │      Fix & Replay
             │    Queue     │ ──▶  Alert Team
             │ [M4][M5]     │      Investigate
             └──────────────┘

Use: Poison messages, permanent failures
```

### 2. Message Priority

```
┌─────────────────────────────────────────────────────────────┐
│                    PRIORITY QUEUES                           │
└─────────────────────────────────────────────────────────────┘

Producer ──┬──▶ ┌────────────────┐
           │    │ High Priority  │ ──▶ Consumer (processes first)
           │    │ [VIP Orders]   │
           │    └────────────────┘
           │
           ├──▶ ┌────────────────┐
           │    │ Medium Priority│ ──▶ Consumer (processes second)
           │    │ [Regular]      │
           │    └────────────────┘
           │
           └──▶ ┌────────────────┐
                │ Low Priority   │ ──▶ Consumer (processes last)
                │ [Batch Jobs]   │
                └────────────────┘
```

### 3. Message Filtering

```
┌─────────────────────────────────────────────────────────────┐
│                    MESSAGE FILTERING                         │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
Producer ──────────▶│ Events Topic │
                    │ [All Events] │
                    └──────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         Filter:       Filter:      Filter:
         type=ORDER   region=US    amount>1000
              │            │            │
              ▼            ▼            ▼
         Consumer 1    Consumer 2   Consumer 3
         (Orders)      (US Only)    (High Value)
```

---

## System Design Interview Answer

**Q: Design a message queue system for an e-commerce platform**

```
1. REQUIREMENTS
───────────────
• 1M orders/day (~12 orders/second, peak 100/second)
• Multiple consumers (payment, inventory, notification)
• Reliable delivery (no order loss)
• Support retry on failure
• Monitor processing status

2. ARCHITECTURE
───────────────
┌─────────┐     ┌──────────────┐     ┌──────────┐
│   API   │────▶│ Kafka Cluster│────▶│ Services │
│ Gateway │     │ (3 brokers)  │     │ (scaled) │
└─────────┘     └──────────────┘     └──────────┘
                      │
                      ├─ orders-topic (3 partitions)
                      ├─ payments-topic (1 partition)
                      └─ notifications-topic (5 partitions)

3. DATA FLOW
────────────
Order Created → Kafka → [Payment, Inventory, Email] → Complete

4. SCALING
──────────
• Horizontal: Add consumers (consumer groups)
• Partitioning: 3 partitions = 3 parallel consumers
• Replication Factor: 2 (high availability)

5. RELIABILITY
──────────────
• At-least-once delivery
• Idempotent consumers (check order_id)
• Dead letter queue for failures
• Monitoring: Lag, throughput, error rate
```

---

## Key Takeaways

✓ **Decoupling**: Producers and consumers independent
✓ **Scalability**: Process messages in parallel
✓ **Reliability**: Persistent storage, retry logic
✓ **Asynchronous**: Non-blocking operations
✓ **Load Leveling**: Handle traffic spikes

---

## When to Use Message Queues

**Use When:**
- Long-running operations (video processing, batch jobs)
- Decoupling microservices
- Event-driven architecture
- Need to handle traffic spikes
- Multiple consumers need same data

**Don't Use When:**
- Need immediate response (use REST/gRPC)
- Simple CRUD operations
- Real-time user interaction required
- Tight coupling is acceptable
