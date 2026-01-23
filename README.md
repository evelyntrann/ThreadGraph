# Deterministic Context Control Plane for LLMs

A **deterministic context system** that continuously ingests **Gmail + Calendar** data, normalizes signals, and enforces **policy + freshness + provenance** to return a **Context Pack** for any chat client (**Gemini / ChatGPT / Claude / custom UI**).

> **Core principle:** The LLM is replaceable.  
> This system controls **retrieval and grounding**.

This is **not another RAG system** — it’s a **context control plane** that sits between your data sources and any LLM, ensuring assistants have **accurate, timely, policy-compliant context** for every interaction.

---

## I. What this product is

- Deterministic ingestion + retrieval for personal/work context (Gmail + Calendar first)
- Provider-agnostic: works with OpenAI / Gemini / Claude
- Produces a **Context Pack** with **citations + provenance + freshness guarantees**

---

## II. Problem Statement

### 1) Hallucination & Fabrication
LLMs invent plausible "facts" when context is missing or ambiguous, leading to incorrect responses about schedule, commitments, and communications.

**Example**
- User query: `Gather updated information about GPU use for me`
- Failure mode: LLM does not know the **search context window**
- Result: it retrieves **1-year-old information** and returns stale insights

### 2) Noise Overwhelms Signal
Email inboxes contain **70–90%** promotional content, newsletters, and irrelevant messages. Without intelligent filtering, LLMs waste tokens on spam and miss critical action items.

### 3) No Provenance or Citations
When an LLM claims: “you have a meeting with Sarah on Thursday,” there’s no way to verify:
- source (email ID / calendar event ID)
- confidence level
- whether it’s current / superseded

### 4) Vendor Lock-in
Tightly coupled implementations force a rebuild when switching from OpenAI → Gemini → Claude.

---

## III. Product Goals

### Goals
- **Deterministic Retrieval**  
  Given the same query and data state, always return the same deterministic response.

- **Citation-First Answer**  
  Every claim must be grounded with evidence (message ID, timestamps, event ID, etc.).

- **Noise Suppression**  
  Automatically classify and filter promotional emails, low-priority threads, and irrelevant content before it reaches the LLM.

- **Freshness Enforcement**  
  Apply time-decay and supersession logic so stale information doesn't pollute decisions. Recent messages override older ones in the same thread.

### Success Metrics

| Metric | Target |
|---|---:|
| Precision@10 | ≥ 0.85 |
| Stale Context Rate | < 5% |
| Unsupported Claim Rate | < 2% |
| P95 Latency | < 500ms |
| Promo Filter Recall | ≥ 0.95 |

---

## IV. Use Cases & Scenarios

### Use Case 1: Email Reply Drafting
**Scenario:** User asks “Draft a reply to Cheryl confirming my availability”

**Flow**
1. Retrieve the most recent email thread with Cheryl
2. Extract action items: “Cheryl requested confirmation by Jan 16, 5pm”
3. Check calendar for upcoming conflicts in next 14 days
4. Filter out promotional emails in the same time period
5. Build a Context Pack with:
   - Cheryl’s request (**message ID**)
   - Availability windows from calendar
   - Conversation history (last 3 messages in thread)

**Policy Applied**
- Time horizon: **30 days history**, **14 days future**
- Sources: **Gmail thread + Calendar only**
- Redaction: CC email addresses masked

---

### Use Case 2: Meeting Conflict Detection
**Scenario:** User asks “Do I have any conflicts if I accept the 2pm meeting on Thursday?”

**Flow**
1. Resolve “Thursday” → next occurring Thursday (e.g., **Jan 23**)
2. Retrieve calendar events for **Jan 23, 1pm–3pm**
3. Find existing meeting: “Product Review, 2–3pm”
4. Check email thread for context on both meetings
5. Build Context Pack showing:
   - Existing meeting (event ID, attendees, priority)
   - New meeting request details
   - Relevant email context

**Result**
- “Yes, conflict detected with Product Review meeting”
- Citations point to the calendar event ID and related email

---

### Use Case 3: Action Item Extraction
**Scenario:** User asks “What do I need to do before Friday?”

**Flow**
1. Retrieve Gmail + Calendar for last 7 days
2. Run extraction worker to identify action items with deadlines
3. Filter out:
   - Promotional emails
   - Low-priority threads
   - Completed/superseded tasks
4. Build Context Pack with open action items, each including:
   - source
   - deadline
   - confidence
   - priority

---

## V. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
│                    Gmail API    Calendar API                     │
└────────────┬────────────────────────────┬─────────────────────┘
             │                            │
             ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CONNECTORS                               │
│           OAuth + Push Notifications + Polling                   │
└────────────┬────────────────────────────┬─────────────────────┘
             │                            │
             ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION WORKER                              │
│    Near-real-time sync • Idempotent upsert • Change detection   │
│         Watermark tracking • Deduplication by hash               │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CANONICAL STORE (Postgres)                   │
│   raw_event • extraction • entity • watermark • audit_log        │
│      "Source of truth for all ingested data"                     │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ENRICHMENT WORKER                             │
│   Structure Extraction (rules + LLM) • Embedding Generation      │
│     Entity Recognition • Classification (promo/action/info)      │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL STORE                               │
│   pgvector (semantic) • C++ Lexical Index (BM25) • Redis Cache   │
│      "Read-optimized view for fast hybrid retrieval"             │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT SERVICE (FastAPI)                     │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Retrieval  │→ │    Policy    │→ │   Context    │          │
│  │ Orchestrator │  │    Engine    │  │   Builder    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         ↓                  ↓                  ↓                  │
│    Hybrid Search    Access Control     Context Pack             │
│    Lex + Semantic   Redaction Layer    JSON Schema              │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       LLM GATEWAY                                │
│      OpenAI Adapter • Gemini Adapter • Claude Adapter            │
│           "Provider-agnostic interface to LLMs"                  │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                  │
│    CLI • Browser Extension • Gmail Add-on • Custom UI            │
└─────────────────────────────────────────────────────────────────┘

```

## API Endpoints

This service exposes **read-only user endpoints** and **admin/internal endpoints** used for ingestion, testing, and debugging.

The core design principle is:

> Canonical facts are ingested once, meaning is derived deterministically, and context is assembled in a bounded, auditable way.

---

### User Endpoints

#### `GET /events/recent`

Retrieve recently ingested canonical events from the `raw_event` table.

This endpoint is intended for **inspection and debugging**, for example to verify ingestion or to obtain internal event IDs used by downstream layers.

**Query Parameters**
- `limit` (optional, default: `10`): Maximum number of events to return.

**Response**
```json
[
  {
    "id": "df42c998-a8d2-4eaf-8100-d53d86ab3e66",
    "source": "gmail",
    "source_id": "msg-001",
    "occurred_at": "2026-01-14T13:02:00-08:00",
    "payload": {
      "subject": "Re: Interview availability",
      "from": "cheryl@tcu.edu",
      "to": "you@tcu.edu",
      "snippet": "Are you available Tuesday or Thursday?",
      "thread_id": "thread-123"
    }
  }
]
```
---

#### `POST /context`

Build a **Context Pack** for a given user query.

This is the **primary output endpoint** of the context pipeline.  
It performs retrieval, policy filtering, and context assembly, but **never mutates state**.

**Key Guarantees**
- Uses only grounded facts from the database
- Applies freshness, confidence, and promo filters
- Returns bounded, explainable context
- Empty context is valid; hallucinated facts are not

**Request Body**

```json
{
  "query": "Draft a reply to Cheryl confirming my schedule"
}
Response
{
  "query": "Draft a reply to Cheryl confirming my schedule",
  "intent": "draft_reply",
  "policy": {
    "max_days": 14,
    "min_confidence": 0.55,
    "allow_promo": false,
    "max_items": 20
  },
  "facts": [
    {
      "text": "Are you available Tuesday or Thursday?",
      "source": "gmail:msg-001",
      "occurred_at": "2026-01-14T13:02:00-08:00",
      "confidence": 0.8,
      "intent": "schedule"
    }
  ],
  "open_actions": [
    {
      "text": "Respond with availability",
      "source": "gmail:msg-001",
      "confidence": 0.8
    }
  ]
}
```
