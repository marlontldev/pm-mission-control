# 🤖 AGENTS.md: Autonomous System Architecture

## 1. Concept & Purpose

This system implements a **multi-agent architecture** designed to solve complex project management problems by separating "reactive monitoring" from "deliberative reasoning."

### Why is this required?
In traditional automation, a single script might handle both monitoring and logic. However, in complex domains like Project Management:
- **Monitoring** needs to be fast, constant, and low-cost (the "Nervous System").
- **Reasoning** needs to be deep, context-aware, and intelligent (the "Brain"), which is often slower and more expensive (e.g., LLM calls).

By splitting these functions into two distinct agents, the system achieves:
1. **Efficiency:** The expensive "Brain" is only triggered when the "Nervous System" detects a genuine problem.
2. **Scalability:** You can monitor thousands of data points with lightweight agents while focusing heavy compute on the critical few issues.
3. **Resilience:** If the reasoning engine fails or is slow, the monitoring system continues to function.

---

## 2. The Agents

### 🕵️ Agent A: The Sentinel (Reactive Layer)
**"The Nervous System"**

- **Role:** Continuous monitoring and event detection.
- **Behavior:** It "feels" the pulse of the project. It consumes raw data streams (logs, metrics) and applies fast, deterministic rules to detect anomalies.
- **Trigger:** High-frequency events (e.g., every log line, every metric update).
- **Logic:** `IF CPI < 0.9 THEN Alert`. No LLM is used here to save cost and latency.
- **Output:** A structured "Risk Alert" sent to the Strategist.
- **Location:** `src/sentinel/`

### 🧠 Agent B: The Strategist (Deliberative Layer)
**"The Brain"**

- **Role:** Data retrieval, context analysis, and strategy generation.
- **Behavior:** It "thinks" about the problem. When alerted by the Sentinel, it wakes up, gathers context (e.g., "What caused the delay?"), and consults an LLM (Vertex AI) to formulate a detailed plan.
- **Trigger:** Specific alerts from the Sentinel.
- **Logic:** Complex reasoning using Generative AI (Gemini 1.5).
- **Output:** A strategic plan or corrective action recommendation for the Project Manager.
- **Location:** `src/strategist/`

---

## 3. Interaction Flow

```mermaid
graph TD
    User([Project Data Source]) -->|Stream Data| Sentinel
    
    subgraph "Fast Loop (Reactive)"
        Sentinel{Risk Detected?}
        Sentinel -->|No| Log[Log & Sleep]
        Sentinel -->|Yes| Alert[Trigger Alert]
    end
    
    Alert -->|HTTP / PubSub| Strategist
    
    subgraph "Slow Loop (Deliberative)"
        Strategist[Strategist Agent]
        Strategist -->|1. Gather Context| DB[(Project DB)]
        Strategist -->|2. Request Plan| AI[Vertex AI (Gemini)]
        AI -- Recover Strategy --> Strategist
    end
    
    Strategist -->|Action Plan| User
```

## 4. Current Implementation Status

- **Sentinel:** Implemented in `src/sentinel/`. Checks financial metrics (CPI, SPI).
- **Strategist:** Implemented in `src/strategist/`. profound integration with Vertex AI for advice.
- **Orchestrator:** `mission_control.py` acts as a local simulation harness to run these agents in a loop for testing and demonstration.
