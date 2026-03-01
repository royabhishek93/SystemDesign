# Spring Boot Performance Triage Under Load

Scenario-based interview preparation for diagnosing and fixing slow Spring Boot applications under peak traffic. Organized by experience level: Interview-Basics (mid-level), Advanced (7+ years), and Case Studies.

## What each file includes
- **Simple English** explanations
- **Real examples** you can run
- **Why the problem happens**
- **Wrong vs Right code** (❌ / ✅)
- **Interview tip** with exact framing
- **Quick checklist** for recall
- **Critical pitfalls & follow-up Q&A**

## Interview-Basics (Senior 5–7 years)

Foundational workflow for the interview scenario:

- [Interview-Basics/00-Overview.md](Interview-Basics/00-Overview.md) — Problem statement and testing approach
- [Interview-Basics/01-Requirements-and-Clarity.md](Interview-Basics/01-Requirements-and-Clarity.md) — Clarifying questions + glossary
- [Interview-Basics/02-Diagnosis-Workflow.md](Interview-Basics/02-Diagnosis-Workflow.md) — 5-step diagnosis workflow
- [Interview-Basics/03-Root-Cause-Areas.md](Interview-Basics/03-Root-Cause-Areas.md) — Bottleneck domains (threads, DB, GC, dependencies)
- [Interview-Basics/04-Fix-and-Prevent.md](Interview-Basics/04-Fix-and-Prevent.md) — Short/medium/long-term fixes
- [Interview-Basics/05-Interview-Cheat-Sheet.md](Interview-Basics/05-Interview-Cheat-Sheet.md) — 30s, 60s, 2-min answers
- [Interview-Basics/06-Cross-Questions.md](Interview-Basics/06-Cross-Questions.md) — 14 common wrong vs correct answers

## Advanced (Staff+ 7+ years)

Production-grade debugging techniques:

- [Advanced/07-Advanced-Debugging-Techniques.md](Advanced/07-Advanced-Debugging-Techniques.md) — Thread dumps, flame graphs, GC logs, lock analysis, DB locking, distributed tracing, lightweight instrumentation
- [Advanced/08-Production-Debugging-Runbook.md](Advanced/08-Production-Debugging-Runbook.md) — Minute-by-minute incident response (first 10 minutes)
- [Advanced/09-Debugging-Tools-Reference.md](Advanced/09-Debugging-Tools-Reference.md) — jcmd, jstat, async-profiler, JFR, Prometheus, OpenTelemetry, and tool selection matrix

## Case Studies

Real incidents solved:

- [Case-Studies/10-Complex-Incident-Case-Studies.md](Case-Studies/10-Complex-Incident-Case-Studies.md) — 5 complex incidents: N+1 queries, thread exhaustion cascade, memory leaks, lock contention, retry storms

## Diagrams

- [mermaid/diagnosis-flow.mmd](mermaid/diagnosis-flow.mmd) — Visual workflow for diagnosis

## How to use for interviews

**For Senior (5–7 years)**:
1. Read Interview-Basics/00-Overview through 06-Cross-Questions
2. Study the "Interview tip" section in each file
3. Practice the 30-sec, 60-sec, 2-min answers
4. Reference code examples if asked for details

**For 7+ years (Staff+)**:
1. Review Interview-Basics as a refresher
2. Deep-dive into Advanced chapters
3. Study the runbook for incident response patterns
4. Reference case studies to demonstrate pattern recognition
