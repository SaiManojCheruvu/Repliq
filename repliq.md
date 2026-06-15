# Repliq — Business Requirements Document
> Multi-Business AI Customer Support Platform  
> Version 1.0 | June 2026

---

## 1. Executive Summary

Repliq is a white-label AI-powered customer support chatbot platform that allows
any business to configure, deploy and manage a context-aware conversational agent
without writing code. Each business gets a branded chat experience powered by
Google Gemini, grounded in their own knowledge base.

---

## 2. Stakeholders

| Role | Description |
|---|---|
| **Business Admin** | Configures the chatbot for their business |
| **End Customer** | Chats with the deployed bot |
| **Platform Owner** | Manages the Repliq platform (you) |

---

## 3. System Overview

```
Business Admin                End Customer
──────────────                ────────────
Logs in to /login             Visits /chat/:businessId
Configures persona            Chats with branded bot
Uploads knowledge base        Gets context-aware answers
Tests & deploys bot           Sees sentiment + tone
```

---

## 4. Functional Requirements

---

### 4.1 Authentication Module
> Showcases: JWT, session management

| ID | Requirement | Priority |
|---|---|---|
| AUTH-01 | Admin can log in with email and password | High |
| AUTH-02 | System issues a JWT token on successful login | High |
| AUTH-03 | JWT token expires after 8 hours | High |
| AUTH-04 | Protected routes redirect to /login if no valid token | High |
| AUTH-05 | Each admin is tied to exactly one business | High |
| AUTH-06 | /chat/:businessId is fully public — no login required | High |
| AUTH-07 | Admin can log out and token is cleared | Medium |

**Demo Accounts (hardcoded for showcase):**
```
admin@foodhub.com     / food123    → foodhub
admin@techstore.com   / tech123    → techstore
admin@rawmat.com      / raw123     → rawmaterials
```

---

### 4.2 Business Configuration Module
> Showcases: Prompt Engineering — Guidelines (Lesson 2)

| ID | Requirement | Priority |
|---|---|---|
| CFG-01 | Admin can set business name and agent name | High |
| CFG-02 | Admin can upload a business logo | Medium |
| CFG-03 | Admin can choose a primary brand color | Medium |
| CFG-04 | Admin can write a persona/bio for the agent | High |
| CFG-05 | Admin can select tone: Formal / Neutral / Casual | High |
| CFG-06 | Admin can set allowed topics (what bot can discuss) | High |
| CFG-07 | Admin can set blocked topics (what bot must avoid) | High |
| CFG-08 | Admin can set a fallback message for unknown queries | High |
| CFG-09 | Admin can set language (English / Spanish / Both) | Medium |
| CFG-10 | Config is saved per business and persists in memory | High |
| CFG-11 | Admin can preview how config affects the system prompt | High |

**Business Identity Fields:**
```
Business Name     → "FoodHub"
Agent Name        → "Bella"
Logo URL          → upload or URL
Primary Color     → #dc2626 (used to theme chat UI)
```

**Behavior Fields:**
```
Persona           → "You are Bella, a friendly FoodHub agent..."
Tone              → Formal | Neutral | Casual
Allowed Topics    → ["menu", "orders", "delivery", "refunds"]
Blocked Topics    → ["competitors", "pricing negotiation"]
Fallback Message  → "Let me connect you with our team!"
Language          → English | Spanish | Both
```

---

### 4.3 LLM Settings Module
> Showcases: Temperature control, model awareness (Lesson 7)

| ID | Requirement | Priority |
|---|---|---|
| LLM-01 | Admin can enter their Gemini API key | High |
| LLM-02 | System uses gemini-1.5-flash as default model | High |
| LLM-03 | Admin can adjust temperature (0.0 — 1.0 slider) | High |
| LLM-04 | Lower temperature = more factual, consistent answers | High |
| LLM-05 | Higher temperature = more creative, expanded answers | High |
| LLM-06 | API key is stored securely, never exposed in frontend | High |

**Temperature Guide shown in UI:**
```
0.0 ──────●──────────────── 1.0
     Factual              Creative
     (Support)            (Sales)
```

---

### 4.4 Knowledge Base Module
> Showcases: RAG, context injection, Expanding (Lesson 7)

| ID | Requirement | Priority |
|---|---|---|
| KB-01 | Admin can select a business type from a preset list | High |
| KB-02 | Business type determines suggested KB fields | High |
| KB-03 | Admin can paste raw text as knowledge base | High |
| KB-04 | Admin can upload PDF files for KB | Medium |
| KB-05 | Admin can upload CSV files for KB (products, prices) | Medium |
| KB-06 | Uploaded files are parsed and chunked automatically | Medium |
| KB-07 | KB chunks are stored in ChromaDB per business | Medium |
| KB-08 | On each chat message, relevant KB chunks are retrieved | High |
| KB-09 | Retrieved KB context is injected into the LLM prompt | High |
| KB-10 | Bot answers use real business data, not generic guesses | High |
| KB-11 | If KB has no answer, bot uses fallback message | High |

**Supported Business Types & Their KB Fields:**

| Business Type | KB Fields |
|---|---|
| 🍕 Food Store | Menu items, ingredients, allergens, prices, hours |
| 💻 Tech Store | Products, specs, pricing, warranty, availability |
| 🏗️ Raw Materials | Catalog, mix designs, safety sheets, pricing tiers |
| 🏦 Finance | Products, interest rates, fees, eligibility criteria |
| 🏥 Healthcare | Services, doctors, costs, appointment hours |
| ✏️ Custom | Free text input, any file upload |

---

### 4.5 Chat Module — Core
> Showcases: Chatbot with memory (Lesson 8)

| ID | Requirement | Priority |
|---|---|---|
| CHAT-01 | Customer visits /chat/:businessId — no login needed | High |
| CHAT-02 | Chat UI loads business branding (name, color, logo) | High |
| CHAT-03 | Customer can type and send messages | High |
| CHAT-04 | Bot responds using the configured persona and tone | High |
| CHAT-05 | Full conversation history is maintained per session | High |
| CHAT-06 | Each session is identified by a unique session ID | High |
| CHAT-07 | Session context is stored in-memory with TTL expiry | High |
| CHAT-08 | Bot answers are grounded in uploaded knowledge base | High |
| CHAT-09 | Bot respects allowed/blocked topic configuration | High |
| CHAT-10 | Typing indicator shown while bot is generating reply | Medium |
| CHAT-11 | Messages show timestamps | Low |
| CHAT-12 | Customer can reset/clear the conversation | Medium |

**Message Roles (OpenAI-style, adapted for Gemini):**
```
system    → Business persona + KB context + rules
user      → Customer message
assistant → Bot reply
```

---

### 4.6 Sentiment Inference Module
> Showcases: Inferring (Lesson 5)

| ID | Requirement | Priority |
|---|---|---|
| SENT-01 | Each customer message is analyzed for sentiment | High |
| SENT-02 | Sentiment is classified: Positive / Neutral / Negative / Angry | High |
| SENT-03 | Sentiment badge is displayed next to each customer message | High |
| SENT-04 | Topic of the message is extracted and displayed as a tag | Medium |
| SENT-05 | If sentiment is Angry, an escalation alert is triggered | High |
| SENT-06 | Escalation alert prompts admin notification (UI flag) | Medium |

**Sentiment Display:**
```
😊 Positive   → Green badge
😐 Neutral    → Grey badge
😟 Negative   → Orange badge
😡 Angry      → Red badge + ⚠️ Escalation Alert
```

**Topic Tags (auto-extracted):**
```
[Pricing]  [Delivery]  [Refund]  [Complaint]  [General]
```

---

### 4.7 Summarization Module
> Showcases: Summarizing (Lesson 4)

| ID | Requirement | Priority |
|---|---|---|
| SUM-01 | "Summarize Chat" button available in chat window | High |
| SUM-02 | Clicking it sends full conversation to Gemini for summary | High |
| SUM-03 | Summary is returned as 3-5 bullet points | High |
| SUM-04 | Summary highlights: customer issue, resolution, sentiment | High |
| SUM-05 | Summary is displayed in a modal or side panel | Medium |
| SUM-06 | Long conversations are auto-summarized to save tokens | Medium |

**Summary Output Format:**
```
📋 Conversation Summary
• Customer asked about BBQ Pizza ingredients
• Bot confirmed: chicken, BBQ sauce, red onion, mozzarella — $14.99
• Customer placed an order
• Overall sentiment: 😊 Positive
• Resolution: ✅ Resolved
```

---

### 4.8 Tone Transformation Module
> Showcases: Transforming (Lesson 6)

| ID | Requirement | Priority |
|---|---|---|
| TONE-01 | Customer can toggle between Formal and Casual tone | High |
| TONE-02 | Tone change updates the system prompt for next reply | High |
| TONE-03 | Same answer is rephrased based on selected tone | High |
| TONE-04 | Language detection: auto-detect customer's language | Medium |
| TONE-05 | Bot replies in detected language if configured | Medium |
| TONE-06 | Admin sets default tone in config; customer can override | Medium |

**Tone Examples:**
```
Same KB answer: "Pizza is $14.99"

Formal:  "The Margherita Pizza is priced at $14.99."
Casual:  "Hey! The Margherita is $14.99 — great choice! 🍕"
```

---

### 4.9 Response Expansion Module
> Showcases: Expanding (Lesson 7)

| ID | Requirement | Priority |
|---|---|---|
| EXP-01 | Short KB answers are expanded into full helpful replies | High |
| EXP-02 | Expansion includes context, suggestions, and next steps | High |
| EXP-03 | Expansion respects the configured tone | High |
| EXP-04 | Temperature setting controls creativity of expansion | High |
| EXP-05 | Expansion never adds facts not present in KB | High |

**Expansion Example:**
```
KB Data:     "Cement Mix B — $45/bag, 50kg"
Expanded:    "Cement Mix Type B is available at $45 per 50kg bag.
              It's ideal for structural foundations and load-bearing
              walls. Would you like to know about bulk pricing or
              delivery options?"
```

---

### 4.10 Iterative Prompt Testing Module
> Showcases: Iterative Prompt Development (Lesson 3)

| ID | Requirement | Priority |
|---|---|---|
| ITER-01 | Admin can view the generated system prompt in real time | High |
| ITER-02 | Admin can test the prompt with a sample user message | High |
| ITER-03 | Bot response is shown instantly in a preview panel | High |
| ITER-04 | Admin can tweak config fields and re-test immediately | High |
| ITER-05 | Admin can see token count of the current system prompt | Medium |
| ITER-06 | "Save & Deploy" only available after at least one test | Low |

**Preview Panel UI:**
```
┌─────────────────────────────────────────┐
│  🔬 Prompt Preview & Test               │
│─────────────────────────────────────────│
│  System Prompt (auto-generated):        │
│  ┌─────────────────────────────────┐   │
│  │ You are Bella, a friendly agent │   │
│  │ for FoodHub. Tone: Casual.      │   │
│  │ Topics: menu, orders, delivery  │   │
│  │ KB: [Margherita - $12.99...]    │   │
│  └─────────────────────────────────┘   │
│  Tokens: ~340                          │
│                                         │
│  Test Message: [Do you have vegan?  ]  │
│  [▶ Run Test]                          │
│                                         │
│  Response:                              │
│  "Yes! Our vegan options include..."   │
└─────────────────────────────────────────┘
```

---

## 5. Non-Functional Requirements

| ID | Requirement | Detail |
|---|---|---|
| NFR-01 | Response time | Bot reply within 3 seconds |
| NFR-02 | Session isolation | No context leak between businesses |
| NFR-03 | API key security | Keys never sent to frontend |
| NFR-04 | Context TTL | Sessions expire after 30 minutes idle |
| NFR-05 | Token management | Sliding window to keep prompts under 8k tokens |
| NFR-06 | Mobile responsive | Chat UI works on mobile screens |
| NFR-07 | CORS | Backend only accepts requests from frontend URL |

---

## 6. Screen Inventory

| Screen | Route | Auth Required | Purpose |
|---|---|---|---|
| Landing | `/` | No | App intro, links to login/demo |
| Login | `/login` | No | Admin authentication |
| Admin Config | `/admin/:businessId` | Yes (JWT) | 4-step business setup |
| Chat | `/chat/:businessId` | No | Customer-facing chatbot |

---

## 7. Admin Config — 4 Step Wizard

```
Step 1: Identity       → Name, agent name, logo, brand color
Step 2: Persona        → Bio, tone, topics, fallback, language
Step 3: LLM Settings   → API key, model, temperature
Step 4: Knowledge Base → Business type, upload files/text, test
                                    ↓
                         [Preview Prompt] → [Save & Deploy]
```

---

## 8. API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | No | Login, returns JWT |
| GET | `/config/:businessId` | Yes | Load business config |
| PUT | `/config/:businessId` | Yes | Save business config |
| POST | `/kb/:businessId` | Yes | Upload KB file or text |
| GET | `/kb/:businessId` | Yes | List KB entries |
| POST | `/chat/:businessId` | No | Send message, get reply |
| POST | `/chat/:businessId/summarize` | No | Summarize conversation |
| GET | `/health` | No | Health check |

---

## 9. Data Models

### Business Config
```json
{
  "business_id": "foodhub",
  "name": "FoodHub",
  "agent_name": "Bella",
  "logo_url": "/logos/foodhub.png",
  "primary_color": "#dc2626",
  "persona": "You are Bella, a friendly FoodHub support agent.",
  "tone": "casual",
  "allowed_topics": ["menu", "orders", "delivery", "refunds"],
  "blocked_topics": ["competitors"],
  "fallback_message": "Oops! Let me get a human to help 🙏",
  "language": "en",
  "business_type": "food_store",
  "gemini_api_key": "••••••••••••",
  "model": "gemini-1.5-flash",
  "temperature": 0.8
}
```

### Chat Message
```json
{
  "session_id": "abc123",
  "business_id": "foodhub",
  "role": "user",
  "content": "What is in the BBQ pizza?",
  "sentiment": "positive",
  "topic": "menu",
  "timestamp": "2026-06-14T10:30:00Z"
}
```

### Session Context (in-memory)
```json
{
  "session:foodhub:abc123": {
    "messages": [...],
    "business_id": "foodhub",
    "created_at": "2026-06-14T10:00:00Z",
    "last_active": "2026-06-14T10:30:00Z",
    "ttl": 1800
  }
}
```

---

## 10. Course Lesson Traceability Matrix

| Lesson | Topic | Feature | Module |
|---|---|---|---|
| 2 | Prompting Guidelines | Persona + rules builder | CFG + LLM |
| 3 | Iterative Development | Prompt preview & test panel | ITER |
| 4 | Summarizing | Summarize chat button | SUM |
| 5 | Inferring | Sentiment badge + topic tags | SENT |
| 6 | Transforming | Tone toggle + language detection | TONE |
| 7 | Expanding | Short KB → full reply expansion | EXP + LLM |
| 8 | Chatbot | Multi-turn context-aware chat engine | CHAT |

---

## 11. Out of Scope (v1)

- Real user registration / signup flow
- Billing or subscription management
- Analytics dashboard
- Email / Slack escalation integrations
- Multi-language UI (admin panel English only)
- Voice input / output
- Mobile app

---

## 12. Demo Scenario Scripts

### Demo 1 — FoodHub (Casual, Food Store)
```
Login:    admin@foodhub.com / food123
Chat URL: /chat/foodhub
Script:
  User → "hey what pizzas do you have?"
  Bot  → Lists menu items from KB (Expanding)
  User → "how much is the BBQ one?"
  Bot  → "$14.99" expanded with ingredients (KB + Expanding)
  User → "my last order was cold and i am very upset"
  Bot  → Empathetic response (Sentiment: 😡 Angry → Escalation)
  User → [Click Summarize]
  Bot  → 4-bullet summary of conversation
```

### Demo 2 — TechStore (Formal, Tech)
```
Login:    admin@techstore.com / tech123
Chat URL: /chat/techstore
Script:
  User → "What is the price of the iPhone 15 Pro?"
  Bot  → Formal reply with specs from KB
  User → "does it come with warranty?"
  Bot  → Warranty details from KB (KB grounding)
  User → [Toggle tone to Casual]
  Bot  → Same answer, casual language (Transforming)
```

### Demo 3 — RawMaterials (Technical, B2B)
```
Login:    admin@rawmat.com / raw123
Chat URL: /chat/rawmaterials
Script:
  User → "what is the mix design for grade 30 concrete?"
  Bot  → Technical specs from KB (KB grounding)
  User → "how much does a 50kg bag of cement cost?"
  Bot  → Price from KB, expanded with bulk options (Expanding)
```