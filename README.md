# 🤖 Daily Operations Synthesizer

### The employee doesn't write the status report.
### The agent remembers, asks, and updates the operational state.

*HackwithHyderabad 3.0 — Building AI Agents with Hindsight Memory*

---

## 🎯 Problem

In modern organizations, daily status reporting creates friction and overhead:
* **Repetitive Data Entry:** Employees spend valuable time manually writing daily status updates at the end of the work day.
* **Ignored System Signals:** Much of their progress is already recorded across engineering and activity systems (e.g., GitHub commits, PR merges, CI/CD builds, Figma exports, cloud logs), yet this data is rarely synthesized automatically.
* **Oversight Gap:** Managers still need to manually collect, reconcile, and correlate scattered reports to understand overall project progress, active blockers, and cross-team dependencies.

---

## 💡 Solution

The **Daily Operations Synthesizer** flips status reporting from **Manual Data Entry** to **Proactive Status Verification**:

1. **Combines Current Activity Signals:** Ingests automated background activity (GitHub, CI/CD, Figma, AWS logs).
2. **Recalls Historical Employee Memory:** Retrieves personal context and past blockers from Hindsight.
3. **Recalls Shared Team Context:** Cross-references shared team operational state and dependencies.
4. **Determines Known vs. Uncertain:** Distinguishes what is already established by system evidence from what remains unverified.
5. **Asks ONE Concise Question:** Formulates a single, targeted verification question requiring a 3-second response.
6. **Accepts Short Responses:** Accepts minimal confirmations (e.g., *"Yep, pushed to staging"*, *"Done"*, *"Blocked"*).
7. **Updates Operational Memory:** Converts short responses into timestamped factual statements and retains them back into Hindsight Cloud.

```text
Manual Status Reporting ──► Proactive Status Verification
```

---

## ⭐ Key Innovation

The core innovation is shifting the interaction paradigm from passive status reporting to **intelligent proactive verification**.

The agent **never** asks open-ended questions like *"What did you do today?"*. Instead, it treats background activity as evidence and memory as context to ask only about unresolved items:

* **Automated Activity as Evidence:** System events (merged PRs, successful deployments) are established as facts without asking the employee to repeat them.
* **Historical Context:** Personal task history from Hindsight guides the focus toward pending items.
* **Cross-Team Dependencies:** Shared operational memory flags unblocked or dependent tasks across team members.
* **Zero Redundancy:** Employees are never asked to re-type or summarize work already observable in activity logs.
* **Targeted Verification:** The interaction focuses strictly on unresolved status, next steps, active blockers, or final deployment confirmation.

---

## 🧠 Why Hindsight?

Hindsight serves as the persistent, biomimetic operational memory layer that enables continuous learning across check-ins.

### Memory Bank Architecture

* **`emp_alice`**: Isolated bank storing Alice's individual task history, past blockers, and check-in verifications.
* **`emp_bob`**: Isolated bank storing Bob's individual operational context and UI integration state.
* **`emp_charlie`**: Isolated bank storing Charlie's DevOps and infrastructure activity history.
* **`team_ops`**: Shared bank storing concise cross-team operational facts and dependency resolutions.

### Core Hindsight Operations

* **Recall (`client.recall()`):** Executes TEMPR multi-strategy search across personal and team memory banks to retrieve relevant operational context before generating questions.
* **Retain (`client.retain()`):** Automatically commits post-check-in updates:
  - Full context (question, response, timestamp) is stored in the employee-specific bank.
  - A concise, team-relevant operational fact is stored in `team_ops`.
* **Reflect (`client.reflect()`):** Aggregates accumulated multi-bank context to synthesize the executive manager dashboard without exposing raw conversational noise.

---

## 🏗️ System Architecture & Execution Flowchart

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DAILY OPERATIONS AGENT                                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      │                                      │                                      │
      ▼                                      ▼                                      ▼
┌──────────────┐                       ┌──────────────┐                       ┌──────────────┐
│  Days 1–9    │                       │   Day 10     │                       │   Shared     │
│  Historical  │                       │  Background  │                       │  Team Ops    │
│  Memory      │                       │   Signals    │                       │  Memory      │
│ (emp_alice)  │                       │(GitHub/CI-CD)│                       │  (team_ops)  │
└──────┬───────┘                       └──────┬───────┘                       └──────┬───────┘
       │                                      │                                      │
       │ TEMPR Recall                         │ Raw Events                           │ TEMPR Recall
       ▼                                      ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          CONTEXT FUSION ENGINE (Groq LLM)                               │
│  • Analyzes system activity as evidence                                                 │
│  • Evaluates past blockers & team dependencies                                          │
│  • Identifies what is ALREADY KNOWN vs. STILL UNCERTAIN                                 │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
                                ┌─────────────────────────┐
                                │   ONE CONCISE QUESTION  │
                                │  "Is CORS fix pushed?"  │
                                └────────────┬────────────┘
                                             │
                                             ▼
                                ┌─────────────────────────┐
                                │ 3-SEC EMPLOYEE RESPONSE │
                                │ "Yep, pushed to staging"│
                                └────────────┬────────────┘
                                             │
                                             ▼
                                ┌─────────────────────────┐
                                │ SHORT RESPONSE CONVERTER│
                                │ "Alice confirmed CORS..."│
                                └────────────┬────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
         ┌───────────────────────────┐               ┌───────────────────────────┐
         │     ISOLATED RETAIN       │               │      SHARED RETAIN        │
         │   `client.retain()` to    │               │    `client.retain()` to   │
         │        `emp_alice`        │               │        `team_ops`         │
         └─────────────┬─────────────┘               └─────────────┬─────────────┘
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                                             ▼
                                ┌─────────────────────────┐
                                │    EXECUTIVE REFLECT    │
                                │ `client.reflect()` for  │
                                │    Manager Dashboard    │
                                └─────────────────────────┘
```

---

## 🎬 Demo Scenario

### Step 1 — Historical Memory
Days 1–9 contain synthetic operational memories stored in Hindsight Cloud across `emp_alice`, `emp_bob`, `emp_charlie`, and `team_ops`.

### Step 2 — Day-10 Activity
Day-10 background signals are simulated through `mock_events.py` (e.g., GitHub PR #205 merged, CI/CD build #482 succeeded, Figma exported, AWS backup completed).

### Step 3 — Context Fusion
The agent executes TEMPR recall to retrieve employee history and cross-team dependencies.

### Step 4 — Proactive Question
Groq (`openai/gpt-oss-20b`) analyzes background activity alongside historical context to determine what is uncertain and generates exactly one targeted question.

### Step 5 — Employee Confirmation
The employee provides a minimal response (e.g., *"Yep, pushed to staging"*).

### Step 6 — Memory Update
The response is interpreted into a factual statement and retained into both the isolated employee memory bank and the shared `team_ops` memory bank.

### Step 7 — Manager View
The manager dashboard gathers updated operational context across all active memory banks via `reflect()` and generates an executive summary report.

---

## 👤 Employee Experience

The employee does **not** write a full daily status report.

Through the Streamlit interface, the employee can:
1. **Start Check-In:** Choose their profile and initiate the flow.
2. **View Current Signals:** Inspect automated background signals detected for the day.
3. **View Recalled Context:** Review personal and team memory recalled by Hindsight.
4. **Answer Contextual Question:** Read the agent's targeted verification question.
5. **Submit Short Response:** Type a brief answer or click a 3-second quick response preset.
6. **See Memory Update:** Observe the resulting factual interpretation successfully saved to Hindsight Cloud.

---

## 👔 Manager Executive Dashboard

Managers receive synthesized operational context powered by Hindsight `reflect()` and Groq reasoning, covering:
* **Completed Milestones:** Key features and PRs merged.
* **Active Blockers:** Cross-team impediments and pending reviews.
* **Dependencies:** Unblocked tasks and technical prerequisites.
* **Release Risks:** Readiness audit for production deployments.
* **Team Operational Progress:** High-level velocity and status updates.
* **Next Steps:** Actionable insights for upcoming sprints.

---

## 💻 Tech Stack & Component Overview

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Memory** | Hindsight Cloud | Retain, recall and reflect operational context |
| **LLM** | GPT-OSS-20B via Groq | Reasoning and response synthesis |
| **Backend** | Python | Agent orchestration |
| **Frontend** | Streamlit | Employee + Manager UI |
| **Activity Layer** | `mock_events.py` | Simulated Day-10 activity |
| **Configuration** | `python-dotenv` | Environment variables |

---

## 📁 Repository Structure

```text
daily-ops-agent/
│
├── agent.py              # Core AI agent and orchestration
├── app.py                # Streamlit application
├── mock_events.py        # Simulated Day-10 activity signals
├── seed_data.py          # Initializes synthetic Hindsight demo memories
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
├── .gitignore            # Git exclusions
└── .env                  # Local API configuration; not committed
```

---

## ⚡ Installation & Execution Guide

### **1. Environment Setup**
Clone the repository and create a Python virtual environment:

```bash
git clone https://github.com/your-username/daily-ops-agent.git
cd daily-ops-agent

python -m venv venv
```

**Activate Environment:**

* **Windows PowerShell:**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### **2. Configure Environment Variables (`.env`)**
Create a `.env` file in the root directory:

```env
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
GROQ_API_KEY=your_groq_api_key_here
```

> ⚠️ **Important Security Note:** The `.env` file contains sensitive API keys and **must never be committed** to version control. It is excluded via `.gitignore`.

---

### **3. Seed Historical Demo Memories**
Initialize the synthetic historical memories (Days 1–9) in Hindsight Cloud:

```bash
python seed_data.py
```

---

### **4. Run Terminal CLI Demo**
Run the core agent script to test the 10-step backend orchestration:

```bash
python agent.py
```

---

### **5. Launch Streamlit Web Application**
Start the interactive UI:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to test the Employee Check-In and Manager Executive Dashboard.

---

## 🔐 Prototype vs Production

### Current Hackathon Prototype
The current prototype:
* Uses simulated Day-10 activity signals (`mock_events.py`).
* Uses Streamlit for the employee and manager interfaces.
* Uses Hindsight Cloud for persistent operational memory.
* Uses Groq (`openai/gpt-oss-20b`) for reasoning and synthesis.
* Does **NOT** currently implement authentication or authorization.

The prototype focuses specifically on demonstrating the proactive memory-driven workflow.

### Production Extension
In a production deployment, the architecture would expand to include:
* SSO / OAuth authentication
* Role-based authorization
* Employee/team memory access controls
* Real GitHub / CI/CD / Jira integrations
* Webhook-driven activity ingestion
* Audit logging
* Secure secrets management

---

## 🔮 Future Scope

* Real GitHub and CI/CD webhooks
* Jira / Linear integration
* Slack / Microsoft Teams integration
* Role-based access control (RBAC)
* Automated scheduled check-ins
* Cross-team dependency graphs
* Blocker escalation workflows
* Historical operational analytics
* Production authentication and audit logging
