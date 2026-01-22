 I. What this product is 

A deterministic context system that continuously ingests Gmail + Calendar data, normalizes signals, and enforces policy + freshness + provenance to return a Context Pack for any chat client (Gemini / ChatGPT / Claude / custom UI).

Core principle: The LLM is replaceable. Your system controls retrieval and grounding.

This is not another RAG system—it's a context control plane that sits between your data sources and any LLM, ensuring that AI assistants have accurate, timely, and policy-compliant context for every interaction.

II. Problems Statement

- Hallucination & Fabrication: LLMs invent plausible-sounding "facts" when context is missing or ambiguous, leading to incorrect responses about your schedule, commitments, and communications.
Example: You are searching the query "Gather updated information about GPU use for me" but then the LLM does not know the search context window. It's searching info from 1 year ago which is not updated and provides inside from this retrieval knowledge. 

- Noise Overwhelms Signal: Email inboxes contain 70-90% promotional content, newsletters, and irrelevant messages. Without intelligent filtering, LLMs waste tokens on spam and miss critical action items.

- No Provenance or Citations: When an LLM claims "you have a meeting with Sarah on Thursday," there's no way to verify the source, confidence level, or whether that information is current. We should have a context package that clarify the meeting calendar is up-to-date. 

- Vendor Lock-in: Tightly coupled implementations force you to rebuild everything when switching from OpenAI to Gemini to Claude.

III. Product Goals

- Deterministic Retrieval: Give the same query and data state, always return the same deterministic response. Avoid black-box magic.

- Citation First Answer: Every claim in LLM must be grounded from the truth with proved evidence (email ID, date and time, etc.)

- Noise Suppression: Automatically classify and filter promotional emails, low-priority threads, and irrelevant content before it reaches the LLM.

- Freshness Enforcement: Apply time-decay and supersession logic so stale information doesn't pollute decisions. Recent messages override older ones in the same thread.

Success Metrics

Precision@10 ≥ 0.85: Top 10 retrieved items are relevant to the query
Stale Context Rate < 5%: Retrieved items respect freshness policies
Unsupported Claim Rate < 2%: LLM responses stay grounded in provided facts
P95 Latency < 500ms: Context retrieval completes in under half a second
Promo Filter Recall ≥ 0.95: Catch 95%+ of promotional/spam content

IV. Use Case and Scenarios
Use Case 1: Email Reply Drafting
Scenario: User asks "Draft a reply to Cheryl confirming my availability"
Flow:

System retrieves the most recent email thread with Cheryl
Extracts action items: "Cheryl requested confirmation by Jan 16, 5pm"
Checks calendar for upcoming conflicts in next 14 days
Filters out 47 promotional emails from the same time period
Builds Context Pack with:

Cheryl's original request (with message ID)
User's availability windows from calendar
Conversation history (last 3 messages in thread)


LLM generates reply grounded in this specific context
Response includes citations showing which email prompted the reply

Policy Applied:

Time horizon: 30 days history, 14 days future
Sources: Gmail thread + Calendar only
Redaction: Email addresses of CC'd recipients masked

Use Case 2: Meeting Conflict Detection
Scenario: User asks "Do I have any conflicts if I accept the 2pm meeting on Thursday?"
Flow:

System identifies "Thursday" as next occurring Thursday (Jan 23)
Retrieves calendar events for Jan 23, 1pm-3pm window
Finds existing meeting: "Product Review, 2-3pm"
Checks email thread for context on both meetings
Builds Context Pack showing:

Existing meeting (with event ID, attendees, priority)
New meeting request details
Relevant email context for both


LLM responds: "Yes, conflict detected with Product Review meeting"
Citations point to specific calendar event ID and confirmation email

Use Case 3: Action Item Extraction
Scenario: User asks "What do I need to do before Friday?"
Flow:

System retrieves Gmail + Calendar for last 7 days
Runs extraction worker to identify action items with deadlines
Filters out:

Promotional emails (78 removed)
Low-priority threads (15 removed)
Completed/superseded tasks (3 removed)


Builds Context Pack with 5 open action items:

"Submit expense report by Thu 5pm" (from manager email)
"Review design doc" (from Slack sync, if integrated)
"Reply to Cheryl re: availability by Fri 5pm"


Each item includes: source, deadline, confidence, priority
LLM formats response as prioritized list with context

V. High Level Architecture

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

Data Flow: (Query Path)
User Query: "Draft reply to Cheryl"
      ↓
Context Service receives request
      ↓
├─→ Intent Detection ("draft_reply")
│
├─→ Policy Engine applies rules:
│   • Time horizon: 30d past, 14d future
│   • Sources: Gmail thread + Calendar
│   • Redaction: mask email addresses
│
├─→ Retrieval Orchestrator:
│   ├─→ Lexical Search (C++ BM25): "Cheryl" → 20 results
│   ├─→ Semantic Search (pgvector): embed query → 20 results
│   └─→ Merge + Rerank → Top 10 events
│
├─→ Context Builder:
│   • Fetch full event details from Canonical Store
│   • Apply freshness decay & supersession logic
│   • Filter out promo emails (12 dropped)
│   • Format as Context Pack JSON
│
├─→ LLM Gateway:
│   • Select adapter (e.g., Claude)
│   • Inject system prompt: "Use only provided facts"
│   • Send Context Pack + user query
│
└─→ LLM Response with citations
      ↓
Return to client with Context Pack attached


Data Flow (Ingestion Path):
Gmail Push Notification
      ↓
Connector receives historyId
      ↓
Ingestion Worker:
├─→ Fetch changed messages via Gmail API
├─→ Check watermark (last historyId)
├─→ Compute content_hash for deduplication
├─→ Upsert into raw_event table (idempotent)
└─→ Update watermark
      ↓
Enrichment Worker (async):
├─→ Extract structure (rules + LLM):
│   • Intent: reply/schedule/task/info
│   • Action items with deadlines
│   • Entities: people, companies, projects
│   • Classification: is_promo, priority
│
├─→ Generate embeddings (model: text-embedding-3-small)
│
└─→ Update Retrieval Store:
    • Insert into embedding table
    • Rebuild C++ lexical index (incremental)
    • Invalidate Redis cache for affected threads

Storage Layer Details
Canonical Store (Postgres)

Purpose: Long-term memory, source of truth
Tables: raw_event, extraction, entity, watermark
Guarantees: Strong consistency, durability, auditability

Retrieval Store (pgvector + C++ index)

Purpose: Fast recall for semantic + lexical search
Data: Read-optimized denormalized views
Update: Async after canonical store write

Cache (Redis)

Purpose: Short-term working memory
Cached: LLM extractions, embeddings, retrieval results
TTL: 1 hour for retrieval, 24 hours for extractions

VI. API Endpoint Design

VII. Data Models/ Schemas
