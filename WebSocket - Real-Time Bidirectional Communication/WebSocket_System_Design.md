# WebSocket - Real-Time Bidirectional Communication

## What is WebSocket?

**WebSocket** is a communication protocol that provides **full-duplex** (two-way) communication channels over a single TCP connection. Unlike HTTP, which is request-response, WebSocket allows both client and server to send messages independently.

---

## HTTP vs WebSocket

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        HTTP (Request-Response)                           │
└─────────────────────────────────────────────────────────────────────────┘

Client                                                        Server
  │                                                              │
  │─────────── Request (GET /messages) ──────────────────────▶  │
  │                                                              │
  │  ◀─────────── Response (200 OK, messages) ─────────────────┤
  │                                                              │
  │─────────── Request (GET /messages) ──────────────────────▶  │
  │                                                              │
  │  ◀─────────── Response (200 OK, no new messages) ──────────┤
  │                                                              │
  │─────────── Request (GET /messages) ──────────────────────▶  │
  │                                                              │
  │  ◀─────────── Response (200 OK, new message!) ─────────────┤
  │                                                              │

Problems:
─────────
✗ Client must poll repeatedly (polling overhead)
✗ New TCP connection for each request
✗ HTTP headers overhead (~500-1000 bytes each request)
✗ Latency (must wait for client to poll)
✗ Server can't push data to client


┌─────────────────────────────────────────────────────────────────────────┐
│                          WebSocket (Full-Duplex)                         │
└─────────────────────────────────────────────────────────────────────────┘

Client                                                        Server
  │                                                              │
  │─────── HTTP Upgrade Request (Handshake) ───────────────▶    │
  │  GET /chat HTTP/1.1                                          │
  │  Upgrade: websocket                                          │
  │  Connection: Upgrade                                         │
  │                                                              │
  │  ◀───── HTTP 101 Switching Protocols ──────────────────────┤
  │  (Connection upgraded to WebSocket)                          │
  │                                                              │
  │═══════════════════════════════════════════════════════════  │
  │            Persistent WebSocket Connection                   │
  │═══════════════════════════════════════════════════════════  │
  │                                                              │
  │─────── Message: "Hello" ────────────────────────────────▶   │
  │                                                              │
  │  ◀───── Message: "Welcome!" ───────────────────────────────┤
  │                                                              │
  │  ◀───── Message: "New notification" ───────────────────────┤
  │  (Server pushes without client request!)                    │
  │                                                              │
  │─────── Message: "Thanks" ───────────────────────────────▶   │
  │                                                              │
  │  ◀───── Message: "Anytime" ────────────────────────────────┤
  │                                                              │

Benefits:
─────────
✓ Single persistent TCP connection
✓ Bidirectional (both can send anytime)
✓ Low overhead (2-6 bytes per frame vs 500+ bytes HTTP)
✓ Real-time (no polling delay)
✓ Server can push to client
```

---

## WebSocket Handshake Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET HANDSHAKE (Upgrade)                         │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: Client Initiates HTTP Request
──────────────────────────────────────

GET /chat HTTP/1.1
Host: example.com
Upgrade: websocket                    ← Request protocol upgrade
Connection: Upgrade                   ← Connection should be upgraded
Sec-WebSocket-Key: dGhlIHNhbXBsZQ==  ← Random base64 key
Sec-WebSocket-Version: 13             ← WebSocket protocol version
Origin: http://example.com


Step 2: Server Accepts and Upgrades
────────────────────────────────────

HTTP/1.1 101 Switching Protocols      ← Success status
Upgrade: websocket                    ← Protocol upgraded
Connection: Upgrade                   ← Connection upgraded
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
                    ▲
                    └─ Hash of client key (proves server understands WebSocket)


Step 3: WebSocket Connection Established
─────────────────────────────────────────

        Client ═══════════════════════════ Server
             (Persistent TCP Connection)

Now both can send/receive messages freely!


┌─────────────────────────────────────────────────────────────────────────┐
│                       CONNECTION LIFECYCLE                               │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐                                           ┌──────────┐
  │  Client  │                                           │  Server  │
  └─────┬────┘                                           └────┬─────┘
        │                                                     │
        │────────────────────────────────────────────────────│
        │               1. HANDSHAKE                         │
        │    GET /ws HTTP/1.1 (Upgrade: websocket)           │
        │───────────────────────────────────────────────────▶│
        │                                                     │
        │◀───────────────────────────────────────────────────│
        │    HTTP/1.1 101 Switching Protocols                │
        │                                                     │
        │════════════════════════════════════════════════════│
        │               2. OPEN (Connected)                  │
        │════════════════════════════════════════════════════│
        │                                                     │
        │─────────── Text Frame: "Hello" ───────────────────▶│
        │                                                     │
        │◀────────── Text Frame: "Hi there!" ────────────────│
        │                                                     │
        │────────────── Binary Frame (image) ───────────────▶│
        │                                                     │
        │◀────────────────── Ping ───────────────────────────│
        │                                                     │
        │──────────────────── Pong ─────────────────────────▶│
        │                    (heartbeat)                      │
        │                                                     │
        │════════════════════════════════════════════════════│
        │              3. CLOSING (Graceful)                 │
        │════════════════════════════════════════════════════│
        │                                                     │
        │────────── Close Frame (code: 1000) ───────────────▶│
        │                                                     │
        │◀───────── Close Frame (code: 1000) ────────────────│
        │                                                     │
        │════════════════════════════════════════════════════│
        │                4. CLOSED                           │
        │════════════════════════════════════════════════════│
```

---

## WebSocket Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET SERVER ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────┘

                        ┌─────────────────────────┐
                        │   Load Balancer         │
                        │   (with sticky session) │
                        └────────┬────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
        ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
        │ WS Server 1      │ │ WS Server 2      │ │ WS Server 3      │
        │                  │ │                  │ │                  │
        │ Active Conns:    │ │ Active Conns:    │ │ Active Conns:    │
        │ ┌──────────────┐ │ │ ┌──────────────┐ │ │ ┌──────────────┐ │
        │ │ User1: ws123 │ │ │ │ User2: ws456 │ │ │ │ User3: ws789 │ │
        │ │ User4: ws124 │ │ │ │ User5: ws457 │ │ │ │ User6: ws790 │ │
        │ └──────────────┘ │ │ └──────────────┘ │ │ └──────────────┘ │
        └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
                 │                    │                     │
                 └────────────────────┼─────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │   Message Broker        │
                        │   (Redis Pub/Sub)       │
                        │                         │
                        │   Channel: chat-room-1  │
                        │   Subscribers: WS1,2,3  │
                        └─────────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │   Database              │
                        │   (Message History)     │
                        └─────────────────────────┘


FLOW: User1 sends message to chat-room-1
─────────────────────────────────────────
1. User1 → WS Server 1 (via WebSocket)
2. WS Server 1 → Redis Pub/Sub (publish to channel)
3. Redis → All WS Servers (WS1, WS2, WS3)
4. WS Server 2 → User2 (connected to WS2)
5. WS Server 3 → User3 (connected to WS3)

Result: All users in room receive message!
```

---

## Real-World Example: Chat Application

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CHAT APPLICATION FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

User A                  WebSocket Server             User B
(Browser)              (Node.js/Socket.io)          (Mobile App)
   │                           │                          │
   │───── Connect ────────────▶│                          │
   │  ws://chat.com/ws         │                          │
   │                           │                          │
   │◀──── Connected ───────────│                          │
   │  connection_id: "abc123"  │                          │
   │                           │                          │
   │                           │◀──── Connect ────────────│
   │                           │  ws://chat.com/ws        │
   │                           │                          │
   │                           │────── Connected ────────▶│
   │                           │  connection_id: "xyz789" │
   │                           │                          │
   │                           │                          │
   │── Send Message ──────────▶│                          │
   │  {                        │                          │
   │    type: "message",       │                          │
   │    room: "general",       │                          │
   │    text: "Hello!"         │                          │
   │  }                        │                          │
   │                           │                          │
   │                           │ (Broadcast to room)      │
   │                           │                          │
   │◀─── Receive Message ──────│─── Receive Message ─────▶│
   │  {                        │  {                       │
   │    from: "UserA",         │    from: "UserA",        │
   │    text: "Hello!",        │    text: "Hello!",       │
   │    timestamp: "..."       │    timestamp: "..."      │
   │  }                        │  }                       │
   │                           │                          │
   │                           │                          │
   │                           │◀──── Send Message ───────│
   │                           │  "Hi UserA!"             │
   │                           │                          │
   │◀─── Receive Message ──────│                          │
   │  "Hi UserA!"              │                          │
   │                           │                          │
   │                           │                          │
   │──── Typing Indicator ────▶│                          │
   │  { typing: true }         │                          │
   │                           │                          │
   │                           │─── Typing Indicator ────▶│
   │                           │  "UserA is typing..."    │
   │                           │                          │
   │                           │                          │
   │──── Disconnect ──────────▶│                          │
   │                           │                          │
   │                           │─── User Left Event ─────▶│
   │                           │  "UserA left the chat"   │
```

---

## WebSocket Frame Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       WEBSOCKET FRAME FORMAT                             │
└─────────────────────────────────────────────────────────────────────────┘

 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - - +
:                     Payload Data continued ...                :
+ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
|                     Payload Data continued ...                |
+---------------------------------------------------------------+


Field Breakdown:
────────────────

┌──────────────┬─────────┬──────────────────────────────────────┐
│ Field        │ Size    │ Description                          │
├──────────────┼─────────┼──────────────────────────────────────┤
│ FIN          │ 1 bit   │ 1 = final fragment, 0 = more coming  │
│ RSV1-3       │ 3 bits  │ Reserved (must be 0)                 │
│ Opcode       │ 4 bits  │ Frame type (see below)               │
│ MASK         │ 1 bit   │ 1 = payload masked (client→server)   │
│ Payload Len  │ 7 bits  │ Length of payload data               │
│ Masking Key  │ 32 bits │ Used to unmask payload (if MASK=1)   │
│ Payload      │ Variable│ Actual message data                  │
└──────────────┴─────────┴──────────────────────────────────────┘


Opcodes:
────────
0x0 - Continuation frame
0x1 - Text frame (UTF-8)
0x2 - Binary frame
0x8 - Close connection
0x9 - Ping
0xA - Pong


Example: Sending "Hi"
─────────────────────
Text: "Hi" (2 bytes)

Frame:
┌────┬─────┬──────┬──────────┬─────────┐
│FIN │OpCd │ Len  │ Mask Key │ Payload │
│ 1  │ 0x1 │  2   │ (4 bytes)│  "Hi"   │
└────┴─────┴──────┴──────────┴─────────┘

Total overhead: 6-10 bytes (vs HTTP 500+ bytes!)
```

---

## Implementation Example

### Client-Side (JavaScript)

```javascript
// Client-side WebSocket
const socket = new WebSocket('ws://localhost:8080/chat');

// Connection opened
socket.addEventListener('open', (event) => {
    console.log('Connected to server');
    socket.send(JSON.stringify({
        type: 'join',
        room: 'general',
        username: 'Alice'
    }));
});

// Receive messages
socket.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    console.log('Message from server:', data);

    if (data.type === 'message') {
        displayMessage(data.from, data.text);
    } else if (data.type === 'user_joined') {
        showNotification(`${data.username} joined`);
    }
});

// Send message
function sendMessage(text) {
    socket.send(JSON.stringify({
        type: 'message',
        text: text,
        timestamp: Date.now()
    }));
}

// Handle errors
socket.addEventListener('error', (error) => {
    console.error('WebSocket error:', error);
});

// Handle close
socket.addEventListener('close', (event) => {
    console.log('Disconnected:', event.code, event.reason);

    // Reconnect logic
    setTimeout(() => {
        connectWebSocket();
    }, 3000);
});

// Heartbeat (ping/pong)
setInterval(() => {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000); // Every 30 seconds
```

### Server-Side (Node.js + ws library)

```javascript
const WebSocket = require('ws');
const http = require('http');

const server = http.createServer();
const wss = new WebSocket.Server({ server });

// Store active connections
const rooms = new Map(); // room -> Set of clients

wss.on('connection', (ws, req) => {
    console.log('New client connected');

    let currentRoom = null;
    let username = null;

    // Handle incoming messages
    ws.on('message', (data) => {
        const message = JSON.parse(data);

        switch (message.type) {
            case 'join':
                currentRoom = message.room;
                username = message.username;

                // Add to room
                if (!rooms.has(currentRoom)) {
                    rooms.set(currentRoom, new Set());
                }
                rooms.get(currentRoom).add(ws);

                // Notify others
                broadcast(currentRoom, {
                    type: 'user_joined',
                    username: username
                }, ws);
                break;

            case 'message':
                // Broadcast to all in room
                broadcast(currentRoom, {
                    type: 'message',
                    from: username,
                    text: message.text,
                    timestamp: Date.now()
                }, ws);
                break;

            case 'ping':
                ws.send(JSON.stringify({ type: 'pong' }));
                break;
        }
    });

    // Handle disconnect
    ws.on('close', () => {
        if (currentRoom && rooms.has(currentRoom)) {
            rooms.get(currentRoom).delete(ws);

            broadcast(currentRoom, {
                type: 'user_left',
                username: username
            }, ws);
        }
    });

    // Error handling
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
});

// Broadcast to all clients in room (except sender)
function broadcast(room, message, sender) {
    if (!rooms.has(room)) return;

    const data = JSON.stringify(message);
    rooms.get(room).forEach((client) => {
        if (client !== sender && client.readyState === WebSocket.OPEN) {
            client.send(data);
        }
    });
}

server.listen(8080, () => {
    console.log('WebSocket server listening on port 8080');
});
```

---

## Scaling WebSocket Servers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  HORIZONTAL SCALING WITH REDIS PUB/SUB                   │
└─────────────────────────────────────────────────────────────────────────┘

   User A                    User B                      User C
     │                         │                           │
     │  ws://server1           │  ws://server2             │  ws://server3
     ▼                         ▼                           ▼
┌──────────────┐         ┌──────────────┐           ┌──────────────┐
│ WS Server 1  │         │ WS Server 2  │           │ WS Server 3  │
│ Port: 8001   │         │ Port: 8002   │           │ Port: 8003   │
│              │         │              │           │              │
│ Connections: │         │ Connections: │           │ Connections: │
│  • UserA     │         │  • UserB     │           │  • UserC     │
└──────┬───────┘         └──────┬───────┘           └──────┬───────┘
       │                        │                          │
       │                        │                          │
       └────────────────────────┼──────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Redis Pub/Sub       │
                    │                       │
                    │  Channel: room-123    │
                    │  Subscribers:         │
                    │   - WS Server 1       │
                    │   - WS Server 2       │
                    │   - WS Server 3       │
                    └───────────────────────┘


Flow: UserA sends message
─────────────────────────
1. UserA → WS Server 1 (WebSocket)
2. WS Server 1 → Redis PUBLISH room-123 "Hello"
3. Redis → All subscribed servers (1, 2, 3)
4. WS Server 2 → UserB (WebSocket)
5. WS Server 3 → UserC (WebSocket)


Redis Pub/Sub Code:
───────────────────
const redis = require('redis');
const subscriber = redis.createClient();
const publisher = redis.createClient();

// Subscribe to room
subscriber.subscribe('room-123');

// Receive from Redis
subscriber.on('message', (channel, message) => {
    // Broadcast to local WebSocket clients
    broadcastToLocalClients(channel, message);
});

// Publish to Redis
function sendToRoom(room, message) {
    publisher.publish(room, JSON.stringify(message));
}
```

---

## WebSocket vs Alternatives

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   REAL-TIME COMMUNICATION COMPARISON                     │
└─────────────────────────────────────────────────────────────────────────┘

╔═══════════════╦═══════════╦═══════════╦═══════════╦═══════════╗
║   Feature     ║ WebSocket ║   SSE     ║  Polling  ║ Long Poll ║
╠═══════════════╬═══════════╬═══════════╬═══════════╬═══════════╣
║ Direction     ║ Bi-dir    ║ Server→   ║ Client→   ║ Client→   ║
║               ║ (2-way)   ║ Client    ║ Server    ║ Server    ║
╠═══════════════╬═══════════╬═══════════╬═══════════╬═══════════╣
║ Protocol      ║ ws:// or  ║ HTTP      ║ HTTP      ║ HTTP      ║
║               ║ wss://    ║           ║           ║           ║
╠═══════════════╬═══════════╬═══════════╬═══════════╬═══════════╣
║ Overhead      ║ Very Low  ║ Low       ║ High      ║ Medium    ║
║               ║ (2-6B)    ║           ║ (500B+)   ║           ║
╠═══════════════╬═══════════╬═══════════╬═══════════╬═══════════╣
║ Browser       ║ All modern║ All modern║ All       ║ All       ║
║ Support       ║           ║ (no IE)   ║           ║           ║
╠═══════════════╬═══════════╬═══════════╬═══════════╬═══════════╣
║ Reconnection  ║ Manual    ║ Automatic ║ N/A       ║ N/A       ║
╠═══════════════╬═══════════╬═══════════╬═══════════╬═══════════╣
║ Use Case      ║ Chat,     ║ News feed,║ Simple    ║ Simple    ║
║               ║ Gaming,   ║ Stocks,   ║ status    ║ updates   ║
║               ║ Collab    ║ Notifs    ║ check     ║           ║
╚═══════════════╩═══════════╩═══════════╩═══════════╩═══════════╝


SERVER-SENT EVENTS (SSE) Example:
──────────────────────────────────
// Client
const eventSource = new EventSource('/events');
eventSource.onmessage = (event) => {
    console.log(event.data);
};

// Server (Node.js)
res.setHeader('Content-Type', 'text/event-stream');
res.write('data: Hello\n\n');  // ← Only server can send


SHORT POLLING:
──────────────
Client                           Server
  │                                │
  │─── GET /messages ─────────────▶│
  │◀─── 200 (no new messages) ─────│
  │                                │
  (wait 5 seconds)
  │                                │
  │─── GET /messages ─────────────▶│
  │◀─── 200 (no new messages) ─────│
  │                                │

✗ Wastes bandwidth (empty responses)
✗ High latency (up to polling interval)


LONG POLLING:
─────────────
Client                           Server
  │                                │
  │─── GET /messages ─────────────▶│
  │                                │ (holds request open)
  │                                │ (waiting for new data...)
  │                                │
  │                                │ (new message arrives!)
  │◀─── 200 (new message) ─────────│
  │                                │
  │─── GET /messages ─────────────▶│ (immediate reconnect)

✓ Lower latency than short polling
✗ Still creates new connection each time
```

---

## Use Cases

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET USE CASES                           │
└─────────────────────────────────────────────────────────────────┘

1. CHAT APPLICATIONS
────────────────────
   • Instant messaging (WhatsApp Web, Slack)
   • Customer support chat
   • Gaming chat

2. REAL-TIME GAMING
───────────────────
   • Multiplayer games
   • Live game state synchronization
   • Real-time leaderboards

3. COLLABORATIVE EDITING
────────────────────────
   • Google Docs (simultaneous editing)
   • Figma (design collaboration)
   • Code editors (VS Code Live Share)

4. LIVE SPORTS/TRADING
──────────────────────
   • Stock price updates
   • Sports score updates
   • Cryptocurrency exchanges

5. LIVE NOTIFICATIONS
─────────────────────
   • Push notifications
   • Social media updates (likes, comments)
   • Order status updates

6. IOT/MONITORING
─────────────────
   • Device status monitoring
   • Sensor data streaming
   • Real-time dashboards


When NOT to use WebSocket:
───────────────────────────
✗ Simple request-response (use REST)
✗ One-way updates (use SSE instead)
✗ Large file transfers (use HTTP/2)
✗ SEO-critical content (use server-rendered HTML)
```

---

## System Design Interview Answer

**Q: Design a real-time chat system using WebSocket**

```
1. REQUIREMENTS
───────────────
• 1M concurrent users
• 100M messages/day
• Real-time delivery (<100ms)
• Message history
• Group chat (up to 100 users)

2. ARCHITECTURE
───────────────
┌──────────┐
│  Client  │
└────┬─────┘
     │ WebSocket
     ▼
┌──────────────────┐
│  Load Balancer   │ (Sticky Session / Consistent Hashing)
└────┬─────────────┘
     │
┌────┴─────────────────────────────┐
│                                  │
▼                                  ▼
┌──────────────┐           ┌──────────────┐
│ WS Server 1  │           │ WS Server 2  │
│ (10k conns)  │◀────────▶│ (10k conns)  │
└──────┬───────┘  Redis    └──────┬───────┘
       │         Pub/Sub          │
       └──────────┬────────────────┘
                  │
                  ▼
          ┌──────────────┐
          │    Redis     │ (In-memory for real-time)
          │   Pub/Sub    │
          └──────────────┘
                  │
                  ▼
          ┌──────────────┐
          │  PostgreSQL  │ (Message history)
          │   Cassandra  │ (Time-series, scalable)
          └──────────────┘

3. DATA FLOW
────────────
• User A sends message → WS Server 1
• WS Server 1 → Redis Pub/Sub (channel: room-123)
• Redis → All WS Servers subscribed to room-123
• WS Servers → Connected users in room

4. SCALING
──────────
• Horizontal: 100 WS servers (10k connections each = 1M)
• Redis Cluster: Partition channels by room
• Database: Shard by room_id or time

5. OPTIMIZATIONS
────────────────
• Message queue for persistence (async)
• Compress messages (gzip)
• Rate limiting (per user, per room)
• Reconnection with exponential backoff
• Message batching (combine multiple sends)
```

---

## Key Takeaways

✓ **Bidirectional**: Both client and server can send anytime
✓ **Low Latency**: Real-time communication
✓ **Efficient**: 2-6 bytes overhead (vs HTTP 500+ bytes)
✓ **Persistent**: Single long-lived TCP connection
✓ **Push Capable**: Server can push without client request

---

## When to Use WebSocket

**Use When:**
- Real-time bidirectional communication
- High frequency of messages
- Low latency requirements (<100ms)
- Server needs to push to client
- Chat, gaming, collaborative editing

**Don't Use When:**
- Simple request-response (use REST)
- One-way server→client (use SSE)
- Infrequent updates (use polling)
- SEO matters (use server-side rendering)
