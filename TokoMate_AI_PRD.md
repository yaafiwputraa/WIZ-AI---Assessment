# Product Requirements Document (PRD)
## TokoMate AI — AI Customer Support for Indonesian SMEs

**Document Version:** 1.0  
**Date:** 25 August 2026  
**Status:** MVP / AI Builder Challenge  
**Target Submission:** 26 August 2026

---

## 1. Product Overview

### 1.1 Product Name
**TokoMate AI**

### 1.2 Product Summary
TokoMate AI is an AI-powered customer support platform designed for Indonesian SMEs (UMKM) to automate repetitive customer inquiries while maintaining a positive customer experience.

The system allows customers to ask questions about products, prices, stock availability, order status, payment methods, shipping, and store policies through a web-based chat interface.

For simple and repetitive inquiries, the AI responds automatically using business data and predefined tools. For complex, sensitive, or high-priority cases such as complaints, refunds, damaged products, or unresolved delivery issues, the conversation can be escalated to a human customer service agent.

When escalation occurs, the AI automatically generates a concise conversation summary so the human agent can understand the issue without requiring the customer to repeat the entire conversation.

---

## 2. Problem Statement

Many Indonesian SMEs receive large volumes of customer inquiries through channels such as WhatsApp, Instagram, Shopee, and TikTok Shop.

Common inquiries include:

- Product information
- Price questions
- Stock availability
- Order tracking
- Payment methods
- Shipping information
- Return and refund policies
- Complaints

These repetitive inquiries consume significant customer service time and may lead to:

- Slow response times
- Repetitive manual work
- Inconsistent responses
- Increased workload for business owners or customer service agents
- Poor customer experience during peak periods

At the same time, fully automating all customer support conversations may create poor experiences when customers face complex or sensitive problems.

TokoMate AI addresses this by combining automated AI assistance with human escalation.

---

## 3. Product Goal

Build a working AI customer support prototype that can:

1. Understand customer inquiries in natural Indonesian language.
2. Retrieve relevant business information.
3. Use backend tools to check products, stock, and order status.
4. Answer common customer questions automatically.
5. Detect situations that require human assistance.
6. Escalate conversations to a human agent.
7. Generate AI summaries for escalated conversations.
8. Provide an agent dashboard for managing escalated cases.

---

## 4. Target Users

### 4.1 Primary User — Customer

Customers who interact with an SME and need quick answers about:

- Products
- Prices
- Stock
- Orders
- Shipping
- Payments
- Returns or refunds

### 4.2 Secondary User — SME Customer Service Agent

Customer service staff or business owners who need to:

- Monitor escalated conversations
- Understand customer issues quickly
- Review AI-generated summaries
- Take over conversations when needed

---

## 5. User Personas

### Persona 1 — Customer

**Name:** Budi  
**Goal:** Get fast information about products and orders.  
**Pain Points:**
- Waiting too long for responses
- Repeating information
- Unclear order status

### Persona 2 — Customer Service Agent

**Name:** Sari  
**Role:** Customer Support Staff  
**Goal:** Focus on complex customer cases instead of repetitive questions.  
**Pain Points:**
- Large number of repetitive chats
- Must read long conversation histories
- Difficult to prioritize urgent complaints

---

## 6. MVP Scope

The MVP will include two main interfaces:

### 6.1 Customer Chat Interface

A web-based chat interface where customers can communicate with the AI assistant.

The AI should support:

- Product search
- Product information
- Price checking
- Stock checking
- Order tracking
- FAQ and policy questions
- Complaint detection
- Human escalation

### 6.2 Agent Dashboard

A dashboard for customer service agents that displays escalated conversations.

The dashboard should show:

- Customer name
- Conversation ID
- Order ID if available
- Issue category
- Priority level
- Conversation status
- AI-generated summary
- Full conversation history
- Take Over button

---

## 7. Core Features

### 7.1 AI Chat Assistant

The AI assistant receives natural language messages from customers and determines the appropriate response or action.

Example:

**Customer**
> Kak, Adidas Samba size 42 masih ada?

The AI should identify:

- Product: Adidas Samba
- Size: 42
- Intent: Stock inquiry

The AI then calls the appropriate stock-checking tool.

---

### 7.2 Product Search

The AI can search the product catalog.

Example user queries:

- "Ada sepatu lari?"
- "Ada Adidas Samba?"
- "Sepatu hitam di bawah 700 ribu ada?"

Suggested backend function:

```python
search_products(query)
```

---

### 7.3 Product Price and Stock Check

The AI can retrieve current product information such as:

- Product name
- Price
- Stock
- Variant
- Size
- Color

Suggested backend function:

```python
check_product_stock(product_id, variant=None)
```

---

### 7.4 Order Status Tracking

Customers can provide an order ID and ask for the current order status.

Example:

**Customer**
> ORD-192 saya sudah sampai mana?

Suggested backend function:

```python
check_order_status(order_id)
```

Possible result:

```json
{
  "order_id": "ORD-192",
  "status": "Shipped",
  "courier": "JNE",
  "tracking_number": "JNE123456",
  "estimated_delivery": "26 August 2026"
}
```

---

### 7.5 FAQ and Store Policy

The AI can answer frequently asked questions about:

- Payment methods
- Shipping
- Returns
- Refunds
- Exchange policies
- Store operating hours

For the MVP, FAQ data may be stored in JSON or a simple database.

Optional implementation:

- Keyword retrieval
- Vector search / RAG

Suggested function:

```python
search_faq(query)
```

---

### 7.6 Human Escalation

The AI should escalate a conversation when the issue requires human intervention.

Example triggers:

- Refund requests
- Damaged products
- Angry or dissatisfied customers
- Repeated unresolved complaints
- Missing orders
- Payment disputes
- AI uncertainty
- Customer explicitly requests a human agent

Suggested function:

```python
escalate_to_human(conversation_id, reason, priority)
```

Example output:

```json
{
  "status": "escalated",
  "priority": "high",
  "reason": "Damaged product refund request"
}
```

---

### 7.7 AI Conversation Summary

When a conversation is escalated, the system generates a short summary for the customer service agent.

Example:

```text
Customer ordered Adidas Samba size 42 under order ORD-192.

The customer reports that the product arrived damaged.
The customer has already contacted support twice and is requesting a refund.

Current sentiment: Negative
Priority: High

Suggested action:
Review refund eligibility and contact the customer.
```

The purpose of this feature is to reduce the time agents spend reading long conversation histories.

---

### 7.8 Priority Detection

Escalated tickets can have priority levels:

- Low
- Medium
- High

Example rules:

**High Priority**
- Angry customer
- Payment dispute
- Missing order
- Multiple failed support attempts
- Damaged product

**Medium Priority**
- Delivery delay
- Product exchange
- General complaint

**Low Priority**
- Customer requests additional clarification

---

## 8. User Flow

### 8.1 Normal Automated Flow

```text
Customer
   ↓
Send Message
   ↓
AI understands intent
   ↓
AI selects appropriate tool
   ↓
Business data retrieved
   ↓
AI generates response
   ↓
Customer receives answer
```

### 8.2 Escalation Flow

```text
Customer
   ↓
Send complaint / complex request
   ↓
AI detects escalation condition
   ↓
AI collects relevant information
   ↓
Conversation escalated
   ↓
AI generates summary
   ↓
Ticket appears in Agent Dashboard
   ↓
Human agent reviews summary
   ↓
Human agent takes over
```

---

## 9. Example Conversation

### Product Inquiry

**Customer**
> Kak Adidas Samba size 42 warna hitam ada?

**AI**
> Ada kak. Adidas Samba warna hitam size 42 masih tersedia 3 pasang dengan harga Rp1.499.000.

---

### Order Tracking

**Customer**
> ORD-192 saya udah dimana?

**AI**
> Pesanan ORD-192 sudah dikirim menggunakan JNE. Nomor resinya JNE123456 dan estimasi tiba 26 Agustus 2026.

---

### Complaint Escalation

**Customer**
> Barang saya datang rusak dan saya sudah komplain dua kali. Saya mau refund.

**AI**
> Maaf atas kendalanya. Saya akan meneruskan kasus ini ke customer service agar dapat ditangani lebih lanjut.

System creates:

```text
Status: Escalated
Priority: High
Issue: Damaged Product / Refund
```

---

## 10. Functional Requirements

### FR-01 — Send Chat Message
Customer can send text messages through the chat interface.

### FR-02 — AI Response
System generates context-aware responses using an LLM.

### FR-03 — Product Search
System can retrieve products matching customer queries.

### FR-04 — Stock Lookup
System can retrieve stock information.

### FR-05 — Order Lookup
System can retrieve order status based on order ID.

### FR-06 — FAQ Retrieval
System can retrieve relevant FAQ or policy information.

### FR-07 — Intent Detection
System identifies the customer request category.

Possible intents:

- Product Inquiry
- Stock Inquiry
- Price Inquiry
- Order Tracking
- Payment Question
- Shipping Question
- Return / Refund
- Complaint
- Human Agent Request

### FR-08 — Escalation
System can mark a conversation as escalated.

### FR-09 — Summary Generation
System generates a summary when escalation occurs.

### FR-10 — Agent Dashboard
Human agents can view escalated tickets.

### FR-11 — Conversation History
System stores chat messages for each conversation.

### FR-12 — Human Takeover
Agent can mark a conversation as being handled by a human.

---

## 11. Non-Functional Requirements

### NFR-01 — Response Time
Normal AI responses should ideally be returned within a few seconds.

### NFR-02 — Usability
Chat interface should be simple and familiar to users accustomed to messaging applications.

### NFR-03 — Reliability
Business information should be retrieved from structured data rather than invented by the LLM.

### NFR-04 — Safety
The AI should not invent order status, stock quantities, prices, or refund decisions.

### NFR-05 — Maintainability
Business data and AI tools should be modular and easy to update.

---

## 12. Proposed Technology Stack

### Frontend

**Next.js / React**

Responsibilities:

- Customer chat interface
- Agent dashboard

### Backend

**FastAPI**

Responsibilities:

- API endpoints
- Conversation management
- Tool execution
- Database access
- AI orchestration

### AI

**OpenAI API**

Responsibilities:

- Natural language understanding
- Tool selection
- Response generation
- Conversation summarization
- Intent / escalation reasoning

### Database

**Supabase PostgreSQL**

Suggested tables:

- products
- product_variants
- orders
- conversations
- messages
- escalations
- faq

### Optional AI Retrieval

**pgvector / Supabase Vector**

Used for:

- FAQ retrieval
- Store policies
- Knowledge base search

---

## 13. Proposed System Architecture

```text
                  CUSTOMER

                     ↓
              Next.js Chat UI
                     ↓
               FastAPI Backend
                     ↓
              AI Orchestrator
                     ↓
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
 Product Tools   Order Tools    FAQ Search
       ↓             ↓             ↓
            PostgreSQL / Vector DB
                     ↓
               AI Response
                     ↓
            ┌────────┴────────┐
            ↓                 ↓
       Auto Resolve       Escalation
                              ↓
                       AI Summary
                              ↓
                       Agent Dashboard
                              ↓
                       Human Takeover
```

---

## 14. Suggested Database Entities

### Product

```text
id
name
description
category
price
```

### ProductVariant

```text
id
product_id
size
color
stock
```

### Order

```text
id
customer_name
status
courier
tracking_number
estimated_delivery
```

### Conversation

```text
id
customer_name
status
created_at
updated_at
```

Possible status:

- ai_active
- escalated
- human_active
- resolved

### Message

```text
id
conversation_id
sender
message
created_at
```

### Escalation

```text
id
conversation_id
reason
priority
summary
status
created_at
```

---

## 15. API Endpoints

Possible MVP API design:

### Chat

```http
POST /api/chat
```

### Conversations

```http
GET /api/conversations/{conversation_id}
```

### Escalations

```http
GET /api/escalations
```

### Escalation Detail

```http
GET /api/escalations/{id}
```

### Human Takeover

```http
POST /api/escalations/{id}/takeover
```

### Products

```http
GET /api/products
```

### Orders

```http
GET /api/orders/{order_id}
```

---

## 16. AI Tools

The LLM may access the following tools:

```python
search_products(query)

check_product_stock(product_name, size=None, color=None)

get_product_price(product_name)

check_order_status(order_id)

search_faq(query)

escalate_to_human(
    conversation_id,
    reason,
    priority
)
```

The LLM should not directly invent business data.

---

## 17. MVP UI Pages

### Page 1 — Customer Chat

Route:

```text
/chat
```

Components:

- Store name
- Chat message list
- Customer input box
- Send button
- AI typing/loading indicator
- Escalation notification

---

### Page 2 — Agent Dashboard

Route:

```text
/dashboard
```

Display:

- Number of active conversations
- Number of AI-resolved conversations
- Number of escalated conversations
- List of escalated tickets

Ticket fields:

- Customer
- Issue
- Priority
- Status
- Timestamp

---

### Page 3 — Escalation Detail

Route:

```text
/dashboard/conversation/{id}
```

Display:

- Customer information
- AI summary
- Priority
- Escalation reason
- Full conversation history
- Take Over button

---

## 18. Out of Scope for MVP

The following features are intentionally excluded from the first prototype:

- Real WhatsApp Business API integration
- Shopee API integration
- TikTok Shop API integration
- Instagram integration
- Real payment processing
- Real courier API
- Production-grade authentication
- Multi-tenant SaaS architecture
- Voice calling
- Full CRM integration

These features may be added in future versions.

---

## 19. Future Development

Possible future improvements:

### Omnichannel Integration

Connect the same AI backend to:

- WhatsApp
- Instagram
- Shopee
- TikTok Shop
- Web Chat

Architecture:

```text
WhatsApp ────┐
Instagram ───┤
Shopee ──────┼── AI Customer Service Backend
TikTok ──────┤
Web Chat ────┘
```

### Customer Memory

Remember:

- Previous purchases
- Product preferences
- Previous complaints

### Analytics

Dashboard metrics:

- AI resolution rate
- Escalation rate
- Average response time
- Common inquiry types
- Customer sentiment
- Most requested products

### Multilingual Support

Support:

- Bahasa Indonesia
- English
- Informal Indonesian / slang

---

## 20. Success Metrics

For the prototype, success can be demonstrated using test scenarios.

### Technical Metrics

- AI successfully identifies customer intent.
- Correct tool is called for product and order requests.
- AI does not hallucinate order or stock information.
- Escalation is triggered for defined complex cases.
- AI summary accurately represents the conversation.

### Business Metrics

Potential production metrics:

- AI Resolution Rate
- Human Escalation Rate
- Average Response Time
- Customer Service Workload Reduction
- Average Handling Time after Escalation

Example hypothesis:

If an SME receives 300 customer conversations per day and 70% are repetitive inquiries, the AI system could potentially handle approximately 210 conversations automatically, allowing human agents to focus on the remaining complex cases.

This is an estimated business-impact scenario and not a measured result of the prototype.

---

## 21. Demo Scenario

The challenge demo should demonstrate three flows.

### Scenario 1 — Product Inquiry

Customer asks:

> Adidas Samba hitam size 42 masih ada?

AI:

1. Detects product inquiry.
2. Calls product / stock tool.
3. Retrieves stock.
4. Responds naturally.

---

### Scenario 2 — Order Tracking

Customer asks:

> ORD-192 saya sudah sampai mana?

AI:

1. Detects order tracking intent.
2. Calls order tool.
3. Retrieves shipping information.
4. Responds with status.

---

### Scenario 3 — Human Escalation

Customer says:

> Barang saya rusak dan saya sudah komplain dua kali. Saya mau refund.

AI:

1. Detects complaint.
2. Assigns high priority.
3. Escalates conversation.
4. Generates AI summary.
5. Ticket appears on Agent Dashboard.
6. Human agent clicks Take Over.

This scenario should be the main highlight of the demo.

---

## 22. Business Value Proposition

TokoMate AI is designed to help SMEs:

- Respond to customers faster
- Automate repetitive inquiries
- Reduce manual customer support work
- Maintain consistent business information
- Prioritize complex cases
- Improve human-agent productivity
- Avoid forcing customers to repeat information after escalation
- Provide scalable customer support without immediately increasing headcount

The core principle is:

> **Automate routine support, preserve human attention for situations where it matters most.**

---

## 23. MVP Definition of Done

The MVP is considered complete when:

- [ ] Customer can send messages from the web chat.
- [ ] AI can answer using the OpenAI API.
- [ ] AI can call at least three business tools.
- [ ] Product information can be retrieved from stored data.
- [ ] Order status can be retrieved using an order ID.
- [ ] FAQ information can be retrieved.
- [ ] Complex conversations can be escalated.
- [ ] AI generates a conversation summary.
- [ ] Escalated conversations appear on the agent dashboard.
- [ ] Human agent can mark a conversation as taken over.
- [ ] Three end-to-end demo scenarios work reliably.
- [ ] Business impact explanation is included in the final presentation or demo video.

---

## 24. Recommended Build Priority

### Priority 1 — Core AI Flow

1. Customer chat UI
2. FastAPI chat endpoint
3. OpenAI integration
4. Product and order tools

### Priority 2 — Differentiating Features

5. Human escalation
6. AI conversation summary
7. Agent dashboard

### Priority 3 — Optional Improvements

8. FAQ RAG
9. Sentiment / priority detection
10. Analytics
11. WhatsApp integration

---

## 25. Final Product Positioning

**TokoMate AI is an AI customer support platform for Indonesian SMEs that automates repetitive inquiries, connects AI with real business data through tool calling, and intelligently hands complex customer cases to human agents with AI-generated summaries.**
