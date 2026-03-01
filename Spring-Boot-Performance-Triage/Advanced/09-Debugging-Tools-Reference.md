# Debugging Tools Reference (7+ years)

**Target level**: Staff+ (7+ years), 2026

## Introduction
Tools that every 7+ year engineer should know and use in production.

## Simple English
These are the tools that give you X-ray vision into what your app is really doing.

---

## 1) jcmd (Java commands - built-in)
**What it does**: Run diagnostic commands on a running JVM without overhead.

**Common uses**:
```bash
# List threads
jcmd <pid> Thread.print

# Get heap dump
jcmd <pid> GC.heap_dump /tmp/heap.bin

# Start JFR (Java Flight Recorder)
jcmd <pid> JFR.start duration=60s filename=recording.jfr

# View system properties
jcmd <pid> VM.system_properties

# Get current JVM version
jcmd <pid> VM.version

# Force garbage collection
jcmd <pid> GC.run
```

**Why use it**: Built-in, no overhead, no agent needed.

**Limitations**: Cannot capture continuous data, only snapshots.

---

## 2) jstat (JVM statistics)
**What it does**: Real-time JVM memory and GC statistics.

```bash
# Watch garbage collection in real-time
jstat -gc -h10 <pid> 1000

# Output:
#  S0C    S1C    S0U    S1U      EC       EU        OC         OU       MC     MU    CCSC   CCSU
# 10752  10752   0     10752   87040    87040    699392    560000    58368  57056  7744   7560

# S0C = Survivor 0 capacity
# S0U = Survivor 0 used
# EC = Eden capacity
# EU = Eden used
# OC = Old generation capacity
# OU = Old generation used

# If OU keeps rising, you have a memory leak
# If GC collects but OU does not drop, objects are not being freed
```

**Why use it**: Real-time, safe, shows trends.

---

## 3) jstack (Thread stack)
**What it does**: Captures stack trace of all threads at one moment.

```bash
# Capture threads (same as jcmd Thread.print, different format)
jstack <pid> > /tmp/threads.txt

# Find threads waiting on lock
grep -B 5 "parking to wait" /tmp/threads.txt | head -20

# Count threads by state
grep "java.lang.Thread.State:" /tmp/threads.txt | sort | uniq -c
```

**Output example**:
```
"http-nio-8080-exec-5" #45 daemon prio=5 os_prio=0 tid=0x00007f8b2c0b4000 nid=0x5c4f waiting on condition
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for <0x00000000c1f2b7c0> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
```

**Why use it**: Shows exact stack and lock IDs, easier to correlate threads.

---

## 4) jps (Java process status)
**What it does**: List all running JVMs on the system.

```bash
# List all Java processes
jps -l
# Output: 1234 com.example.Application

# With JVM arguments
jps -v
```

**Why use it**: Find the PID of the app you want to debug.

---

## 5) async-profiler (CPU and memory profiling)
**What it does**: Low-overhead profiling using sampling, produces flame graphs.

**Installation**:
```bash
git clone https://github.com/async-profiler/async-profiler.git
cd async-profiler
make
```

**Usage**:
```bash
# CPU profiling for 30 seconds
./profiler.sh -d 30 -e cpu -f flamegraph.html <pid>

# Memory allocation profiling
./profiler.sh -d 30 -e alloc -f flamegraph.html <pid>

# Lock contention
./profiler.sh -d 30 -e lock -f flamegraph.html <pid>

# Wall-clock time (includes sleep, waiting)
./profiler.sh -d 30 -e wall -f flamegraph.html <pid>
```

**Output**: HTML flame graph showing where time is spent.

**Why use it**: 
- Safe for production (uses sampling)
- Produces visual representation
- Shows exact code paths

**Limitations**: Requires native library, not available on all systems.

---

## 6) JFR (Java Flight Recorder - built-in since Java 8)
**What it does**: Continuous, low-overhead recording of JVM events.

**Usage**:
```bash
# Start recording
jcmd <pid> JFR.start duration=60s filename=/tmp/recording.jfr

# Check status
jcmd <pid> JFR.check

# Stop if needed
jcmd <pid> JFR.stop name=1

# Analyze (download recording, analyze in JDK or third-party tools)
java -jar jdk.jfr.jar print --json /tmp/recording.jfr > recording.json
```

**Analysis with JDK Mission Control**:
```bash
# On your laptop, analyze the .jfr file
# Shows:
# - Method execution times
# - GC events and pauses
# - Lock contention
# - Thread allocation
# - Memory leaks
```

**Why use it**: 
- Built-in, no overhead
- Comprehensive event capture
- Integrates with JDK tools

---

## 7) Perfstat (Linux only)
**What it does**: Low-level system profiling (CPU cache misses, branch mispredictions).

```bash
# CPU profiling at system level
perf record -F 99 -p <pid> -g -- sleep 30
perf report

# Or generate flame graph
perf record -F 99 -p <pid> -g -- sleep 30
perf script | ~/FlameGraph/stackcollapse-perf.pl | ~/FlameGraph/flamegraph.pl > out.svg
```

**Why use it**: System-level insights, CPU cache behavior.

**Limitations**: Linux only, requires kernel symbols.

---

## 8) Spring Boot Actuator endpoints
**What it does**: Built-in diagnostics endpoint (no agent needed).

**Usage**:
```bash
# List available endpoints
curl http://localhost:8080/actuator

# Thread metrics
curl http://localhost:8080/actuator/metrics/jvm.threads.peak

# Memory
curl http://localhost:8080/actuator/metrics/jvm.memory.used

# GC
curl http://localhost:8080/actuator/metrics/jvm.gc.memory.allocated

# HTTP requests
curl http://localhost:8080/actuator/metrics/http.server.requests

# Custom metric
curl "http://localhost:8080/actuator/metrics/http.server.requests?tag=method:GET&tag=status:200"
```

**Enable in application.properties**:
```properties
management.endpoints.web.exposure.include=*
management.endpoint.health.show-details=always
```

**Why use it**: 
- No overhead
- Real-time metrics
- Easy integration with Prometheus

---

## 9) Micrometer (metrics library)
**What it does**: Application-level metrics with minimal overhead.

**Example**:
```java
@RestController
public class OrderController {
    private final MeterRegistry meterRegistry;
    
    @PostMapping("/orders")
    public OrderResponse createOrder(@RequestBody OrderRequest request) {
        long startTime = System.nanoTime();
        
        try {
            Order order = service.createOrder(request);
            meterRegistry.counter("orders.created").increment();
            return toResponse(order);
        } catch (Exception e) {
            meterRegistry.counter("orders.failed").increment();
            throw e;
        } finally {
            long duration = (System.nanoTime() - startTime) / 1_000_000;
            meterRegistry.timer("orders.latency").record(duration, TimeUnit.MILLISECONDS);
        }
    }
}
```

**Why use it**: 
- Custom metrics
- Low overhead
- Integrates with Prometheus/Grafana

---

## 10) Prometheus + Grafana (monitoring stack)
**What it does**: Collect and visualize metrics.

**Query examples**:
```promql
# p95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Thread pool saturation
jvm_threads_live_threads / jvm_threads_peak_threads

# GC pause time
rate(jvm_gc_pause_seconds_sum[5m]) / rate(jvm_gc_pause_seconds_count[5m])
```

**Why use it**: 
- Aggregates metrics across instances
- Alerting
- Historical data

---

## 11) Loki + Promtail (log aggregation)
**What it does**: Centralize logs for correlation.

**Query example**:
```logql
{job="app-server"} | json | latency_ms > 500
```

**Why use it**: 
- Find slow requests
- Correlate with metrics
- Alert on patterns

---

## 12) OpenTelemetry (distributed tracing)
**What it does**: Trace requests across microservices.

**Example setup**:
```java
@Configuration
public class TracingConfig {
    @Bean
    public OpenTelemetry openTelemetry(MeterProvider meterProvider, LoggerProvider loggerProvider) {
        return OpenTelemetrySdk.builder()
            .setTracerProvider(TracerProvider.builder().build())
            .setMeterProvider(meterProvider)
            .setLoggerProvider(loggerProvider)
            .buildAndRegisterGlobal();
    }
}

@RestController
public class OrderController {
    private final Tracer tracer;
    
    @PostMapping("/orders")
    public OrderResponse createOrder(@RequestBody OrderRequest request) {
        Span span = tracer.spanBuilder("create_order").startSpan();
        try (Scope scope = span.makeCurrent()) {
            // Your code here
            // Trace ID automatically propagated to DB, cache, external APIs
        } finally {
            span.end();
        }
    }
}
```

**Why use it**: 
- Full request path across services
- Latency breakdown per service

---

## 13) Database profiling (PostgreSQL)
**Built-in tools**:
```sql
-- Enable slow query log
ALTER SYSTEM SET log_min_duration_statement = 100;  -- 100ms threshold

-- Check query statistics
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- EXPLAIN ANALYZE shows execution plan
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE status = 'PENDING';
```

---

## Quick tool selection matrix

| Problem | Tool | Why |
| --- | --- | --- |
| Threads blocked? | jcmd Thread.print, jstack | Shows exact lock IDs and stack traces |
| CPU hot spot? | async-profiler, perf | Flame graph shows where time is spent |
| Memory leak? | JFR, jstat | Shows allocation rate and objects retained |
| DB slow? | EXPLAIN ANALYZE, pg_stat_statements | Query plan and timing |
| GC pauses? | jstat, JFR | Shows pause frequency and triggers |
| Latency spike? | Spring Actuator, Prometheus query | Real-time metrics and trends |
| Cross-service latency? | OpenTelemetry | Full trace path |

---

## Interview tip
"I select tools based on the evidence. For thread issues, I use thread dumps and JFR. For CPU, I use async-profiler or perf. For memory, I use jstat and heap analysis. The key is not knowing all tools, but knowing which one answers the question fastest."

---

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Using heavy profilers without sampling
- Enabling all logging without bounds
- Not collecting baseline metrics before problems occur

**Follow-up Q&A**:
**Q**: Should you enable continuous profiling in production?
**A**: No. Use lightweight metrics (Actuator, Micrometer) continuously, and enable detailed profiling only during incidents with careful sampling.

**Q**: What if you do not have direct SSH access to production?
**A**: Use Spring Boot Actuator, JMX remote, or sidecar agents to access diagnostics.

**Q**: How do you balance monitoring overhead with visibility?
**A**: Instrument hot paths with lightweight metrics. Use sampling for detailed tracing. Reserve heavy profilers for incident response.
