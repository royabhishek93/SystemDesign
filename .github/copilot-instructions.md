# System Design Interview Preparation Repository

This is a **documentation-focused repository** for system design interview preparation, not a source code project. Content targets senior engineers (5+ years) preparing for technical interviews.

## Repository Structure

- **Topic Folders**: Self-contained guides with multiple chapters (`OTT system design/`, `Youtube SystemDesign/`)
- **Standalone Guides**: Single-file deep-dives at root level (e.g., `distributed-scheduler-locking.md`)
- **Diagrams**: Mermaid (`.mmd`), PlantUML (`.puml`), and ASCII art in markdown
- **Assets**: Exported PNGs from diagrams stored alongside source files

## Content Organization Patterns

### Multi-Chapter Topics
Follow sequential numbering for comprehensive guides:
```
00-{Topic}-Overview.md          # Big picture and key concepts
01-Requirements-and-Clarity.md  # Interview clarification questions
02-{Component}.md               # Architecture components
...
06-Interview-Cheat-Sheet.md     # Quick reference for interviews
```

Example: [OTT system design/00-OTT-Overview.md](OTT system design/00-OTT-Overview.md) introduces the topic; chapters build progressively to [OTT system design/06-Interview-Cheat-Sheet.md](OTT system design/06-Interview-Cheat-Sheet.md).

### Experience-Level Targeting
Content explicitly targets different career stages (see [README.md](README.md#🎓-interview-levels)):
- **Junior (1-3 years)**: Basic concepts, 1-2 solutions
- **Mid (3-5)**: All solutions, basic cross-questions  
- **Senior (5-7)**: Advanced patterns, production scenarios
- **Staff+ (7+)**: Consensus algorithms, CAP theorem, architectural trade-offs

When creating content, explicitly state the target level and adjust depth accordingly.

## Diagram Conventions

### Mermaid Diagrams
- Place in `{topic}/mermaid/` subdirectories
- Use descriptive names: `demo-architecture.mmd`, `demo-sequence.mmd`
- Common types: sequence diagrams (user flows), architecture diagrams (components)
- Example: [Youtube SystemDesign/mermaid/demo-sequence.mmd](Youtube SystemDesign/mermaid/demo-sequence.mmd) shows control/data plane separation

### PlantUML Diagrams  
- Stored as `.puml` files in topic directories
- Used for detailed sequence diagrams with multiple participants
- Follow consistent naming: `Interview-Steps-Diagram.puml`, `OTT ER Diagram PlantUML`
- See [OTT system design/Interview-Steps-Diagram.puml](OTT system design/Interview-Steps-Diagram.puml) for typical structure

### ASCII Diagrams
Inline in markdown for simple flows (e.g., [Youtube SystemDesign/README.md](Youtube SystemDesign/README.md) shows control/data plane split with ASCII boxes).

## Interview-Specific Content Patterns

### Cross-Questions Format
Present common follow-up questions with wrong vs. correct answers:
```markdown
❌ **Wrong**: "We use Redis for caching"  
✅ **Correct**: "We use Redis with TTL-based expiration and LRU eviction..."
```

### Production Templates (STAR Format)
Include real-world scenarios using Situation-Task-Action-Result structure. Example from [distributed-scheduler-locking.md](distributed-scheduler-locking.md):
- **Situation**: "5 EC2 instances behind load balancer"
- **Task**: "Ensure scheduled job executes only once"
- **Action**: "Implemented ShedLock with PostgreSQL backend"
- **Result**: Specific metrics and outcomes

### Technology Comparisons
Use tables comparing solutions (pros/cons, when to use). See [distributed-scheduler-locking.md](distributed-scheduler-locking.md) for SELECT FOR UPDATE vs ShedLock vs Redis locks.

## Technical Stack References

Guides assume familiarity with:
- **Backend**: Spring Boot, Java, microservices patterns
- **Databases**: PostgreSQL (pessimistic locks), Redis (distributed locks)
- **Cloud**: AWS (EC2, S3, SQS), Kubernetes (pods, leader election)
- **Streaming**: HLS/DASH, CDN patterns, adaptive bitrate
- **Auth**: Cognito, security best practices

When documenting solutions, include concrete code snippets (Java `@Scheduled`, SQL query patterns) rather than pseudocode.

## Creating New Content

1. **Start with Overview**: Define problem statement, stakeholders, and high-level flow
2. **Add Requirements**: List clarifying questions an interviewer might ask
3. **Present Multiple Solutions**: Include at least 3 approaches with trade-offs
4. **Include Diagrams**: Visual representation of data flows and components
5. **Add Cross-Questions**: 10-15 follow-up questions with detailed answers
6. **Provide Cheat Sheet**: Distilled reference for quick interview prep
7. **Link Technologies**: Reference specific frameworks/tools used in production

## Common Patterns to Follow

- **Numbered Lists**: For sequential processes (upload → process → serve)
- **Tables**: For comparisons, metrics, and decision matrices
- **Code Blocks**: Always specify language (```java, ```sql, ```bash)
- **Bold Keywords**: Highlight important terms on first use
- **Inline Links**: Cross-reference related sections within guides
- **Emoji Headers**: Use sparingly for visual scanning (📋, 🎯, ✅)

## What NOT to Include

- Generic interview advice (focus on system design specifics)
- Aspirational practices without concrete examples
- Code that needs to compile/run (this is documentation, not implementation)
- One-size-fits-all solutions (always show multiple approaches with trade-offs)
