# How Does WhatsApp Handle Billions of Messages Daily?

## 1. The Challenge

WhatsApp handles:
- **100+ billion messages per day**
- **2+ billion active users**
- **Real-time message delivery**
- **End-to-end encryption**
- **Message persistence**
- **Read receipts and typing indicators**

## 2. High-Level Architecture

### Visual: Complete WhatsApp Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│              WHATSAPP MESSAGING ARCHITECTURE                           │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                 │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ User A   │  │ User B   │  │ User C   │  │ User N   │          │
│  │ (Sender) │  │(Receiver)│  │(Receiver)│  │          │          │
│  │          │  │          │  │          │  │          │          │
│  │ Mobile   │  │ Mobile   │  │ Mobile   │  │ Mobile   │          │
│  │ App      │  │ App      │  │ App      │  │ App      │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
└───────┼─────────────┼─────────────┼─────────────┼─────────────────┘
        │             │             │             │
        │ HTTPS/WSS   │ WebSocket   │ WebSocket   │
        │ Connection  │ Connection  │ Connection  │
        ↓             ↓             ↓             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     LOAD BALANCER LAYER                             │
│                                                                     │
│  Routes connections to available servers                            │
│  Handles millions of concurrent connections                         │
└────┬──────────────┬──────────────┬──────────────┬──────────────────┘
     │              │              │              │
     ↓              ↓              ↓              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   WHATSAPP SERVER LAYER                             │
│                   (Erlang/Elixir Servers)                           │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Chat     │  │ Chat     │  │ Chat     │  │ Chat     │          │
│  │ Server 1 │  │ Server 2 │  │ Server 3 │  │ Server N │          │
│  │          │  │          │  │          │  │          │          │
│  │ Handles  │  │ Handles  │  │ Handles  │  │ Handles  │          │
│  │ Message  │  │ Message  │  │ Message  │  │ Message  │          │
│  │ Routing  │  │ Routing  │  │ Routing  │  │ Routing  │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
└───────┼─────────────┼─────────────┼─────────────┼─────────────────┘
        │             │             │             │
        │             │             │             │
        ↓             ↓             ↓             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     MESSAGE QUEUE LAYER                             │
│                     (Kafka / Custom Queue)                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  Message Queue                                           │      │
│  │  • Buffering messages                                    │      │
│  │  • Guaranteed delivery                                   │      │
│  │  • Message ordering                                      │      │
│  │  • Retry mechanism                                       │      │
│  └──────────────────────────────────────────────────────────┘      │
└────┬──────────────┬──────────────┬──────────────┬──────────────────┘
     │              │              │              │
     ↓              ↓              ↓              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                                   │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   CASSANDRA     │  │   POSTGRESQL    │  │   CACHE LAYER   │    │
│  │                 │  │                 │  │   (Redis)       │    │
│  │ Message Store   │  │ User Profiles   │  │                 │    │
│  │ • Chat history  │  │ • User data     │  │ • Online status │    │
│  │ • Media files   │  │ • Contacts      │  │ • Last seen     │    │
│  │ • Encryption    │  │ • Groups        │  │ • Typing status │    │
│  │   keys          │  │ • Settings      │  │ • Recent msgs   │    │
│  │                 │  │                 │  │                 │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Message Flow - Step by Step

### Visual: Complete Message Journey

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MESSAGE FLOW (User A → User B)                       │
└────────────────────────────────────────────────────────────────────────┘

STEP 1: User A Types Message
─────────────────────────────

┌──────────────────┐
│   User A Device  │
│                  │
│  1. Type message │
│     "Hello!"     │
│                  │
│  2. Encrypt with │
│     User B's     │
│     public key   │
│                  │
│  Encrypted msg:  │
│  xJ9k2mN8p...    │
└────────┬─────────┘
         │
         │ Send via WebSocket
         ↓


STEP 2: Message Reaches Server
───────────────────────────────

┌──────────────────────────────────┐
│   WhatsApp Chat Server           │
│                                  │
│  3. Receive encrypted message    │
│     (Server cannot decrypt!)     │
│                                  │
│  4. Check:                       │
│     ✅ Valid sender?             │
│     ✅ User B exists?            │
│     ✅ Rate limit OK?            │
│                                  │
│  5. Generate Message ID          │
│     msg_id: 12345678             │
│                                  │
│  6. Send ACK to User A           │
│     ✅ "Message received"        │
└────────┬─────────────────────────┘
         │
         │ Route to User B
         ↓


STEP 3: Check User B's Status
──────────────────────────────

┌──────────────────────────────────┐
│   Connection Manager             │
│                                  │
│  7. Check User B status:         │
│                                  │
│     Is User B online?            │
│     ├─ YES → Send immediately    │
│     └─ NO  → Queue for later     │
│                                  │
│  8. User B is ONLINE             │
│     Find User B's connection     │
│     Server: chat-server-42       │
└────────┬─────────────────────────┘
         │
         │ Forward message
         ↓


STEP 4: Deliver to User B
──────────────────────────

┌──────────────────────────────────┐
│   User B's Chat Server           │
│   (chat-server-42)               │
│                                  │
│  9. Push message to User B       │
│     via WebSocket                │
│                                  │
│  10. User B receives encrypted   │
│      message                     │
└────────┬─────────────────────────┘
         │
         │ Deliver via WebSocket
         ↓

┌──────────────────┐
│   User B Device  │
│                  │
│  11. Receive msg │
│      xJ9k2mN8p.. │
│                  │
│  12. Decrypt with│
│      User B's    │
│      private key │
│                  │
│  13. Display:    │
│      "Hello!"    │
│                  │
│  14. Send        │
│      delivery    │
│      receipt     │
└────────┬─────────┘
         │
         │ Send receipt
         ↓


STEP 5: Delivery Receipt
─────────────────────────

┌──────────────────────────────────┐
│   WhatsApp Server                │
│                                  │
│  15. Receive delivery receipt    │
│      from User B                 │
│                                  │
│  16. Forward receipt to User A   │
│      (Single checkmark ✓)        │
│                                  │
│  17. User B reads message        │
│      Forward read receipt        │
│      (Double checkmark ✓✓)       │
└──────────────────────────────────┘


STEP 6: Persistence
───────────────────

┌──────────────────────────────────┐
│   Storage Layer (Cassandra)      │
│                                  │
│  18. Store message:              │
│      • Message ID                │
│      • Encrypted content         │
│      • Timestamp                 │
│      • Sender ID                 │
│      • Receiver ID               │
│      • Delivery status           │
│                                  │
│  19. Replicate to backup         │
│      servers                     │
└──────────────────────────────────┘


TIMELINE VIEW
─────────────

Time    User A              Server              User B
────    ──────              ──────              ──────
T0      Type "Hello!"
        │
T1      Encrypt message
        │
T2      Send ────────────→ Receive
        │                   │
T3      Receive ACK ←────── Send ACK
        │                   │
T4      Show ✓              Check User B status
        │                   │
T5                          User B online?
                            │
T6                          Route to server ──→ Push message
                            │                   │
T7                                              Receive
                                                │
T8                                              Decrypt
                                                │
T9                                              Display "Hello!"
                                                │
T10                         Receive receipt ←── Send receipt
                            │
T11     Show ✓✓ ←────────── Forward receipt
        │
T12                         Store in DB
                            (Cassandra)


VISUAL FLOW DIAGRAM
───────────────────

User A                          Server                          User B
  │                               │                               │
  │─────── "Hello!" ─────────────→│                               │
  │        (encrypted)            │                               │
  │                               │                               │
  │←────── ACK ✓ ────────────────│                               │
  │                               │                               │
  │                               │─────── Forward ──────────────→│
  │                               │        (encrypted)            │
  │                               │                               │
  │                               │←────── Delivered ─────────────│
  │←────── ✓✓ ───────────────────│                               │
  │        (delivered)            │                               │
  │                               │                               │
  │                               │←────── Read ──────────────────│
  │←────── ✓✓ (blue) ────────────│                               │
  │        (read)                 │                               │
  │                               │                               │
  │                               ↓                               │
  │                         [Store in DB]                         │
  │                         [Replicate]                           │
```

## 4. Offline Message Handling

### Visual: What Happens When User is Offline

```
┌────────────────────────────────────────────────────────────────────────┐
│                    OFFLINE MESSAGE HANDLING                            │
└────────────────────────────────────────────────────────────────────────┘

SCENARIO: User B is Offline
────────────────────────────

┌──────────────┐
│   User A     │
│   (Online)   │
│              │
│ Send message │
│  "Hello!"    │
└──────┬───────┘
       │
       │ Send encrypted message
       ↓
┌───────────────────────────────────────┐
│   WhatsApp Server                     │
│                                       │
│  1. Receive message                   │
│  2. Check User B status               │
│     └─ OFFLINE ❌                     │
│                                       │
│  3. Send ACK to User A                │
│     └─ "Message sent ✓"              │
│                                       │
│  4. Queue message for User B          │
└───────┬────────────┬──────────────────┘
        │            │
        │            │
        ↓            ↓
┌───────────────┐  ┌──────────────────┐
│  Message      │  │   Database       │
│  Queue        │  │   (Cassandra)    │
│               │  │                  │
│  Store in     │  │  Persist message │
│  temporary    │  │  with:           │
│  queue        │  │  • Encrypted data│
│               │  │  • Timestamp     │
│  Retry logic: │  │  • Sender ID     │
│  • Check User │  │  • Receiver ID   │
│    B status   │  │  • Status: QUEUED│
│  • Every 30s  │  │                  │
│  • Max 30 days│  │  ✅ Stored       │
└───────┬───────┘  └──────────────────┘
        │
        │ Wait for User B to come online
        ↓
    [Polling every 30 seconds]
        │
        │
        ↓
┌───────────────────────────────────────┐
│   User B comes online!                │
│                                       │
│  1. User B opens WhatsApp             │
│  2. Establishes WebSocket connection  │
│  3. Server detects: User B ONLINE     │
└───────┬───────────────────────────────┘
        │
        │ Trigger message delivery
        ↓
┌───────────────────────────────────────┐
│   Message Delivery Service            │
│                                       │
│  1. Check queue for User B            │
│  2. Found 1 pending message           │
│  3. Send to User B                    │
│  4. Remove from queue                 │
│  5. Update status: DELIVERED          │
└───────┬───────────────────────────────┘
        │
        │ Push to User B
        ↓
┌──────────────┐
│   User B     │
│   (Online)   │
│              │
│ Receive:     │
│  "Hello!"    │
│              │
│ Send receipt │
└──────┬───────┘
       │
       │ Delivery receipt
       ↓
┌───────────────────────────────────────┐
│   WhatsApp Server                     │
│                                       │
│  Forward receipt to User A            │
│  Update: ✓ → ✓✓                      │
└───────┬───────────────────────────────┘
        │
        ↓
┌──────────────┐
│   User A     │
│              │
│ See: ✓✓      │
│ (delivered)  │
└──────────────┘


QUEUE PRIORITY SYSTEM
──────────────────────

┌─────────────────────────────────────────────────────────┐
│               Message Queue (Per User)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  User B's Queue:                                        │
│                                                         │
│  [Message 1] ← Oldest (30 days old)                     │
│  [Message 2]                                            │
│  [Message 3]                                            │
│  [Message 4]                                            │
│  [Message 5] ← Newest (just received)                   │
│                                                         │
│  When User B comes online:                              │
│  → Deliver in order (FIFO)                              │
│  → Mark each as delivered                               │
│  → Remove from queue                                    │
│                                                         │
│  Retention Policy:                                      │
│  • Keep for max 30 days                                 │
│  • After 30 days: Discard                               │
│  • User will miss messages if offline > 30 days         │
│                                                         │
└─────────────────────────────────────────────────────────┘


MULTI-DEVICE SUPPORT
────────────────────

User has 3 devices:
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Phone   │  │ Tablet  │  │ Desktop │
│ ONLINE  │  │ OFFLINE │  │ ONLINE  │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     │            │            │
     └────────────┼────────────┘
                  │
                  ↓
          ┌───────────────┐
          │ WhatsApp      │
          │ Server        │
          │               │
          │ Send message  │
          │ to ALL active │
          │ sessions      │
          └───┬───────┬───┘
              │       │
              ↓       ↓
          ┌─────┐ ┌────────┐
          │Phone│ │Desktop │
          │✅    │ │✅      │
          └─────┘ └────────┘

When tablet comes online:
→ Sync all messages
→ Mark as delivered
→ Show on tablet
```

## 5. Group Chat Handling

### Visual: Group Message Distribution

```
┌────────────────────────────────────────────────────────────────────────┐
│                    GROUP CHAT MESSAGE FLOW                             │
└────────────────────────────────────────────────────────────────────────┘

SCENARIO: User A sends message to Group (5 members)
───────────────────────────────────────────────────

┌──────────────┐
│   User A     │
│   (Sender)   │
│              │
│ Send to      │
│ "Friends"    │
│ group        │
│              │
│ Message:     │
│ "Hey guys!"  │
└──────┬───────┘
       │
       │ Single message upload
       ↓
┌───────────────────────────────────────────────────────────┐
│   WhatsApp Server                                         │
│                                                           │
│  1. Receive message                                       │
│  2. Verify: User A is in group                            │
│  3. Get group members:                                    │
│     • User B                                              │
│     • User C                                              │
│     • User D                                              │
│     • User E                                              │
│     Total: 4 recipients (excluding sender)                │
│                                                           │
│  4. Fan-out: Create 4 individual deliveries               │
└───┬───────┬───────┬───────┬───────────────────────────────┘
    │       │       │       │
    │       │       │       │
    ↓       ↓       ↓       ↓
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│User B │ │User C │ │User D │ │User E │
│ONLINE │ │ONLINE │ │OFFLINE│ │ONLINE │
│       │ │       │ │       │ │       │
│✅ Got │ │✅ Got │ │📥Queue│ │✅ Got │
│message│ │message│ │message│ │message│
└───────┘ └───────┘ └───────┘ └───────┘


FAN-OUT PROCESS
───────────────

Step 1: Single Upload
┌──────────────┐
│   User A     │
└──────┬───────┘
       │ 1 message
       ↓
┌──────────────┐
│   Server     │
└──────┬───────┘
       │
       │ Fan-out to N recipients
       ↓

Step 2: Multiple Deliveries
┌──────────────────────────────────────────────────────┐
│                Server Creates:                       │
│                                                      │
│  Delivery 1: User A → User B (msg_id: 12345)        │
│  Delivery 2: User A → User C (msg_id: 12346)        │
│  Delivery 3: User A → User D (msg_id: 12347)        │
│  Delivery 4: User A → User E (msg_id: 12348)        │
│                                                      │
│  Each delivery tracked independently                 │
└──────────────────────────────────────────────────────┘


DELIVERY RECEIPTS IN GROUPS
────────────────────────────

User A's View:
┌─────────────────────────────────────┐
│  Friends Group                      │
│                                     │
│  User A: Hey guys!                  │
│                                     │
│  Status:                            │
│  ✓   Message sent                   │
│  ✓✓  Delivered to: 3/4 members      │
│       • User B ✅                   │
│       • User C ✅                   │
│       • User D ⏳ (pending)         │
│       • User E ✅                   │
│                                     │
│  ✓✓ (Blue) Read by: 2/4 members     │
│       • User B ✅                   │
│       • User E ✅                   │
└─────────────────────────────────────┘


LARGE GROUP OPTIMIZATION
────────────────────────

Problem: Group with 256 members

Naive Approach (Inefficient):
┌──────────────┐
│   User A     │
└──────┬───────┘
       │
       │ Send to 256 members
       ↓
┌─────────────────────────────────┐
│   Server                        │
│                                 │
│  Fan-out to 256 users           │
│  → 256 individual deliveries    │
│  → High load                    │
│  → Slow                         │
└─────────────────────────────────┘

Optimized Approach (Efficient):
┌──────────────┐
│   User A     │
└──────┬───────┘
       │
       │ Single message
       ↓
┌────────────────────────────────────────┐
│   Server                               │
│                                        │
│  1. Store message once                 │
│  2. Create group message pointer       │
│  3. Each user gets pointer, not copy   │
│  4. Lazy fan-out (only to online)      │
│  5. Offline users: queue pointer       │
│                                        │
│  Storage:                              │
│  • 1 message stored                    │
│  • 256 pointers (tiny)                 │
│  • Much more efficient                 │
└────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│          Cassandra Storage                          │
│                                                     │
│  Messages Table:                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ msg_id: 12345                                │  │
│  │ content: [encrypted]                         │  │
│  │ group_id: G789                               │  │
│  │ sender: UserA                                │  │
│  │ timestamp: 2024-03-15 10:30:00              │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Group Deliveries Table:                            │
│  ┌──────────────────────────────────────────────┐  │
│  │ group_id: G789                               │  │
│  │ msg_id: 12345                                │  │
│  │ user_b: delivered, read                      │  │
│  │ user_c: delivered, not_read                  │  │
│  │ user_d: queued                               │  │
│  │ user_e: delivered, read                      │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 6. Scalability Techniques

### Visual: How WhatsApp Scales

```
┌────────────────────────────────────────────────────────────────────────┐
│                   WHATSAPP SCALABILITY TECHNIQUES                      │
└────────────────────────────────────────────────────────────────────────┘

TECHNIQUE 1: CONNECTION POOLING
────────────────────────────────

Each server handles millions of WebSocket connections

┌──────────────────────────────────────────────────────┐
│   Single Erlang Server (One Machine)                 │
│                                                      │
│   Capacity: ~2 million concurrent connections       │
│                                                      │
│   ┌────────────────────────────────────────────┐    │
│   │  Connection Pool                           │    │
│   │                                            │    │
│   │  WebSocket 1 ←→ User A                     │    │
│   │  WebSocket 2 ←→ User B                     │    │
│   │  WebSocket 3 ←→ User C                     │    │
│   │  ...                                       │    │
│   │  WebSocket 2M ←→ User N                    │    │
│   │                                            │    │
│   │  Each connection:                          │    │
│   │  • Minimal memory (few KB)                 │    │
│   │  • Lightweight process                     │    │
│   │  • Async I/O                               │    │
│   └────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘

Why Erlang?
✅ Designed for telecom (millions of connections)
✅ Lightweight processes
✅ Built-in fault tolerance
✅ Hot code reloading (no downtime)


TECHNIQUE 2: SHARDING BY USER ID
─────────────────────────────────

Users distributed across multiple servers

User ID → Server Mapping:
┌───────────────────────────────────────────────────┐
│  Hash(UserID) % Number_of_Servers = Server_ID    │
└───────────────────────────────────────────────────┘

┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Server 1   │ │  Server 2   │ │  Server 3   │ │  Server N   │
│             │ │             │ │             │ │             │
│ Users:      │ │ Users:      │ │ Users:      │ │ Users:      │
│ • UserID%4=0│ │ • UserID%4=1│ │ • UserID%4=2│ │ • UserID%4=3│
│             │ │             │ │             │ │             │
│ • User 1000 │ │ • User 1001 │ │ • User 1002 │ │ • User 1003 │
│ • User 1004 │ │ • User 1005 │ │ • User 1006 │ │ • User 1007 │
│ • User 1008 │ │ • User 1009 │ │ • User 1010 │ │ • User 1011 │
│             │ │             │ │             │ │             │
│ 2M conns    │ │ 2M conns    │ │ 2M conns    │ │ 2M conns    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

Benefit: Each server handles a subset of users


TECHNIQUE 3: MESSAGE QUEUE FOR BUFFERING
─────────────────────────────────────────

Handles traffic spikes and ensures delivery

┌──────────────────────────────────────────────────────┐
│                   Message Flow                       │
└──────────────────────────────────────────────────────┘

Sender → Chat Server → Queue → Receiver

Normal Load:
┌─────────┐      ┌─────────┐      ┌─────────┐
│ Senders │ ───→ │  Queue  │ ───→ │Receivers│
│ 1000/s  │      │  (Fast) │      │ 1000/s  │
└─────────┘      └─────────┘      └─────────┘
                 Queue size: 0
                 ✅ Direct delivery

Traffic Spike:
┌─────────┐      ┌─────────┐      ┌─────────┐
│ Senders │ ───→ │  Queue  │ ─X→  │Receivers│
│ 10000/s │      │(Buffering)     │ 1000/s  │
└─────────┘      └────┬────┘      └─────────┘
                      │
                      │ Queue fills up
                      ↓
              [10,000 messages]
              [Buffered safely]
                      │
                      │ Process gradually
                      ↓
                 ┌─────────┐
                 │Receivers│
                 │ 1000/s  │
                 └─────────┘

Benefit: Smooth out traffic spikes, no message loss


TECHNIQUE 4: CASSANDRA FOR MESSAGE STORAGE
───────────────────────────────────────────

Distributed NoSQL database for high write throughput

┌────────────────────────────────────────────────────────┐
│            Cassandra Cluster                           │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Data distributed across multiple nodes                │
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Node 1   │  │ Node 2   │  │ Node 3   │           │
│  │          │  │          │  │          │           │
│  │ Messages │  │ Messages │  │ Messages │           │
│  │ 1-100M   │  │ 100-200M │  │ 200-300M │           │
│  │          │  │          │  │          │           │
│  │ Replica  │  │ Replica  │  │ Replica  │           │
│  │ of 2,3   │  │ of 1,3   │  │ of 1,2   │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                        │
│  Write Performance: 100,000+ writes/second            │
│  Read Performance: 100,000+ reads/second              │
│  Replication Factor: 3 (data copied to 3 nodes)       │
│                                                        │
└────────────────────────────────────────────────────────┘

Why Cassandra?
✅ Handles billions of messages
✅ Linear scalability (add nodes = more capacity)
✅ No single point of failure
✅ Fast writes
✅ Time-series data (chat history)


TECHNIQUE 5: CACHING WITH REDIS
────────────────────────────────

Fast access to frequently needed data

┌────────────────────────────────────────────────────────┐
│                 Redis Cache Layer                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Cached Data:                                          │
│  • Online/offline status (key: user:123:status)        │
│  • Last seen timestamp (key: user:123:last_seen)       │
│  • Typing indicators (key: chat:456:typing)            │
│  • Recent messages (key: chat:456:recent, last 50)     │
│  • User presence (key: user:123:presence)              │
│  • Group member list (key: group:789:members)          │
│                                                        │
│  TTL (Time To Live):                                   │
│  • Status: 30 seconds                                  │
│  • Last seen: 5 minutes                                │
│  • Typing: 10 seconds                                  │
│  • Recent messages: 1 hour                             │
│                                                        │
└────────────────────────────────────────────────────────┘

Flow:
┌─────────┐      ┌─────────┐      ┌──────────┐
│ Request │ ───→ │  Redis  │ ───→ │ Response │
│         │      │  Cache  │      │          │
└─────────┘      └────┬────┘      └──────────┘
                      │
                      │ Cache miss?
                      ↓
                 ┌─────────┐
                 │Database │
                 │(Cassandra)
                 └────┬────┘
                      │
                      │ Update cache
                      ↓
                 ┌─────────┐
                 │  Redis  │
                 │  Cache  │
                 └─────────┘

Benefit: 10-100x faster than database queries
```

## 7. End-to-End Encryption

### Visual: Signal Protocol (E2EE)

```
┌────────────────────────────────────────────────────────────────────────┐
│              END-TO-END ENCRYPTION (Signal Protocol)                   │
└────────────────────────────────────────────────────────────────────────┘

KEY EXCHANGE (One-time setup)
──────────────────────────────

User A                          Server                          User B
  │                               │                               │
  │ Generate key pair             │                               │
  │ • Private key (kept secret)   │                               │
  │ • Public key                  │                               │
  │                               │             Generate key pair │
  │                               │             • Private key     │
  │                               │             • Public key      │
  │                               │                               │
  │────── Upload public key ─────→│                               │
  │                               │←──── Upload public key ───────│
  │                               │                               │
  │                         [Store public keys]                   │
  │                               │                               │
  │←──── User B's public key ─────│                               │
  │                               │──── User A's public key ─────→│
  │                               │                               │


MESSAGE ENCRYPTION
──────────────────

User A wants to send: "Hello!"

┌──────────────────────────────────────────────────────┐
│  User A's Device                                     │
│                                                      │
│  Step 1: Plaintext                                   │
│  "Hello!"                                            │
│                                                      │
│  Step 2: Encrypt with User B's public key           │
│  plaintext + User_B_public_key = ciphertext         │
│                                                      │
│  Step 3: Encrypted message                           │
│  xJ9k2mN8pL3qR5sT7uV9wX...                          │
│  (No one can read this without User B's private key) │
└──────────────────────────────────────────────────────┘
       │
       │ Send encrypted message
       ↓
┌──────────────────────────────────────────────────────┐
│  WhatsApp Server                                     │
│                                                      │
│  Receives: xJ9k2mN8pL3qR5sT7uV9wX...                │
│                                                      │
│  ❌ CANNOT decrypt!                                  │
│  ❌ Does not have User B's private key               │
│                                                      │
│  Can only:                                           │
│  ✅ See sender (User A)                              │
│  ✅ See receiver (User B)                            │
│  ✅ See timestamp                                    │
│  ✅ Route message                                    │
│  ❌ Cannot see content!                              │
└──────────────────────────────────────────────────────┘
       │
       │ Forward encrypted message
       ↓
┌──────────────────────────────────────────────────────┐
│  User B's Device                                     │
│                                                      │
│  Step 1: Receives encrypted                          │
│  xJ9k2mN8pL3qR5sT7uV9wX...                          │
│                                                      │
│  Step 2: Decrypt with User B's private key           │
│  ciphertext + User_B_private_key = plaintext         │
│                                                      │
│  Step 3: Plaintext                                   │
│  "Hello!"                                            │
│                                                      │
│  ✅ Only User B can decrypt!                         │
└──────────────────────────────────────────────────────┘


SECURITY GUARANTEES
───────────────────

┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Who can read the message?                              │
│                                                         │
│  ✅ User A (sender) - has plaintext                     │
│  ✅ User B (receiver) - can decrypt with private key    │
│  ❌ WhatsApp servers - CANNOT decrypt                   │
│  ❌ Hackers - CANNOT decrypt                            │
│  ❌ Government - CANNOT decrypt                         │
│  ❌ WhatsApp employees - CANNOT decrypt                 │
│                                                         │
│  Even if WhatsApp is hacked:                            │
│  → Encrypted messages are useless                       │
│  → Private keys never leave devices                     │
│  → Messages remain secure                               │
│                                                         │
└─────────────────────────────────────────────────────────┘


VISUAL: DATA IN TRANSIT
────────────────────────

User A                  Server                  User B
Device                                          Device
  │                       │                       │
  │  Plaintext:           │                       │
  │  "Hello!"             │                       │
  │                       │                       │
  │  ↓ Encrypt            │                       │
  │                       │                       │
  │  Ciphertext:          │                       │
  │  xJ9k2mN8p...         │                       │
  │                       │                       │
  │───────────────────────→│                       │
  │  (encrypted)          │                       │
  │                       │                       │
  │                       │  Cannot read!         │
  │                       │  Just forwards it     │
  │                       │                       │
  │                       │───────────────────────→│
  │                       │  (still encrypted)    │
  │                       │                       │
  │                       │                       │  Ciphertext:
  │                       │                       │  xJ9k2mN8p...
  │                       │                       │
  │                       │                       │  ↓ Decrypt
  │                       │                       │
  │                       │                       │  Plaintext:
  │                       │                       │  "Hello!"
```

## 8. System Design Interview Answer

### Short Answer (2-3 minutes):

> WhatsApp handles billions of messages daily using a distributed architecture built on Erlang servers, which can handle millions of concurrent WebSocket connections per server.
>
> When User A sends a message, it's encrypted on their device using end-to-end encryption with User B's public key. The encrypted message is sent to WhatsApp servers, which cannot decrypt it. The server checks if User B is online - if yes, it immediately routes the message to User B's connected server. If User B is offline, the message is queued and stored in Cassandra for up to 30 days.
>
> For group chats, WhatsApp uses a fan-out mechanism where a single message is replicated to all group members. To optimize storage, they store one copy of the message and create pointers for each recipient.
>
> The system scales through sharding users across multiple Erlang servers, using Cassandra for persistent storage (billions of messages), and Redis for caching online status, typing indicators, and recent messages. Message queues handle traffic spikes and ensure guaranteed delivery.
>
> The key to WhatsApp's efficiency is using lightweight Erlang processes for connections, end-to-end encryption for security, and distributed storage for scalability.

---

## Key Technologies:
- **Erlang/Elixir**: Server-side (2M connections per server)
- **Cassandra**: Message storage (billions of messages)
- **Redis**: Caching (status, presence)
- **Protocol Buffers**: Efficient serialization
- **Signal Protocol**: End-to-end encryption
- **WebSockets**: Real-time bidirectional communication
