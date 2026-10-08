# 🚀 NexusAI Chat Studio — Production AI Chat Application
### Module 3: LLM APIs & Application Development (Days 11 – 15)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-19%2F19%20passing-brightgreen.svg)](file:///python/tests)
[![Deployment](https://img.shields.io/badge/deploy-Vercel-black.svg)](https://vercel.com)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/manishjhcssp-prog/ai-chat-application/blob/main/colab/module3_llm_apis.ipynb)

A full-stack, production-grade conversational AI application built with **Python**, **FastAPI**, **Vanilla Modern Web Architecture**, and **Vercel Serverless Functions**. 

This repository demonstrates the end-to-end engineering lifecycle for LLM applications: multi-provider authentication, stateful multi-turn conversation memory, sliding context windows, hyperparameter calibration, structured Pydantic JSON extraction, exponential backoff resilience, and real-time token cost auditing.

---

## 🌐 Quick Links & Deliverables

| Deliverable | Link / Resource |
| :--- | :--- |
| **GitHub Repository** | [github.com/manishjhcssp-prog/ai-chat-application](https://github.com/manishjhcssp-prog/ai-chat-application) |
| **Live Web Application** | [ai-chat-application-zeta.vercel.app](https://ai-chat-application-zeta.vercel.app) |
| **Google Colab Notebook** | [Open in Google Colab](https://colab.research.google.com/github/manishjhcssp-prog/ai-chat-application/blob/main/colab/module3_llm_apis.ipynb) |
| **LinkedIn Post Announcement** | [LINKEDIN_POST.md](file:///LINKEDIN_POST.md) |
| **Technical Documentation** | [DOCUMENTATION.md](file:///DOCUMENTATION.md) |

---

## 🏛️ System Architecture

```mermaid
graph TD
    User([User / Browser]) <--> WebUI[Modern Glassmorphism Web App]
    WebUI --> APIBridge{API Router}
    
    APIBridge -->|Vercel Serverless| NodeFunc[/api/chat.js]
    APIBridge -->|FastAPI Local| PyBackend[backend/app.py]
    
    subgraph Core_Engine [Python Core LLM Engine]
        ConvMgr[Conversation Manager] -->|Sliding Window| Context[Context Pruner]
        Config[AppConfig / .env] --> Client[Unified LLM Client]
        CostMgr[Cost & Token Manager] --> Ledger[(Token & Cost Ledger)]
        ErrHandler[Error Handler & Retries] --> Client
        StructParser[Structured JSON Parser] --> Pydantic[(Pydantic Schemas)]
    end
    
    PyBackend --> Core_Engine
    NodeFunc --> ExtAPIs
    Client --> ExtAPIs{LLM Providers}
    
    ExtAPIs -->|API Key Set| OpenAI[OpenAI API - GPT-4o / Mini]
    ExtAPIs -->|API Key Set| Gemini[Google Gemini 1.5 Flash]
    ExtAPIs -->|Zero Key / Offline| MockSim[Intelligent Simulation Engine]
```

---

## ✨ Core Engineering Capabilities

### 1. Unified Multi-Provider LLM Client (`python/client.py`)
- Standardizes completions across **OpenAI** (`gpt-4o`, `gpt-4o-mini`), **Google Gemini** (`gemini-1.5-flash`), and an **Intelligent Offline Simulation Engine**.
- Gracefully functions offline or in zero-credit environments with deterministic test fixtures.

### 2. Multi-Turn Conversation & Sliding Context Window (`python/conversation_manager.py`)
- Maintains explicit role-based dialog arrays (`system`, `user`, `assistant`).
- Enforces an automated **Sliding Window Pruning Algorithm**: protects the lead system persona prompt from deletion while evicting oldest conversation pairs when approaching token context thresholds.

### 3. Hyperparameter Calibration
- Real-time dynamic tuning of:
  - **Temperature (`0.0 - 2.0`)**: Balances analytical determinism vs creative synthesis.
  - **Max Tokens (`256 - 4096`)**: Prevents run-away completion generation costs.
  - **Top-P (`0.1 - 1.0`)**: Fine-tunes nucleus sampling bounds.

### 4. Structured Responses & Schema Enforcement (`python/structured_outputs.py`)
- Employs strict Pydantic schemas for automated outputs:
  - `CodeReviewSchema`: Severity levels, issue diagnoses, optimization recommendations.
  - `ActionPlanSchema`: Step-by-step sequential tasks with time allocations.
  - `ChatMessageAnalysis`: Sentiment classification, intent routing, and urgency scoring.
- Implements self-healing regex heuristics to strip markdown fences and repair trailing JSON commas.

### 5. Resilient Error Handling & Exponential Retries (`python/error_handler.py`)
- Maps vendor-specific exceptions to domain error types: `LLMAuthenticationError`, `LLMRateLimitError`, `LLMContextLengthExceededError`, `LLMConnectionError`.
- Decorated retries (`@retry_with_backoff`) with randomized jitter to mitigate thundering herd surges under HTTP 429 rate limits.

### 6. Real-Time Token Economics & Cost Management (`python/cost_manager.py`)
- Audits both prompt (input) and completion (output) tokens with distinct price weighting per 1,000,000 tokens.
- Hard session budget caps ($0.50 default) with live visual meters and utilization warnings.

---

## 🛠️ Project Structure

```
ai-chat-application/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules protecting keys and caches
├── requirements.txt          # Python dependencies
├── package.json              # Node.js project specification
├── vercel.json               # Vercel serverless routing & CORS configuration
├── README.md                 # Complete project documentation
├── DOCUMENTATION.md          # Technical architecture & algorithmic breakdown
├── LINKEDIN_POST.md          # Ready-to-publish LinkedIn post
│
├── python/                   # Python Core LLM SDK
│   ├── __init__.py           # Package exports
│   ├── config.py             # Env loading, validation, credentials
│   ├── client.py             # Unified multi-provider LLM client
│   ├── conversation_manager.py # Multi-turn state & sliding window
│   ├── cost_manager.py       # Token counting & pricing engine
│   ├── error_handler.py      # Custom exceptions & backoff retries
│   ├── structured_outputs.py # Pydantic schemas & self-healing JSON
│   ├── cli_chat.py           # Terminal interactive chat interface
│   └── tests/                # Automated test suite
│       ├── test_config.py
│       ├── test_client.py
│       ├── test_conversation.py
│       ├── test_cost_manager.py
│       ├── test_error_handling.py
│       └── test_structured.py
│
├── api/
│   └── chat.js               # Vercel Serverless Function (/api/chat)
│
├── backend/
│   └── app.py                # FastAPI REST API & static server
│
├── public/                   # Frontend Web Application
│   ├── index.html            # Semantic HTML5 layout
│   ├── css/
│   │   └── style.css         # Dark-mode glassmorphic styling
│   ├── js/
│   │   ├── app.js            # Chat controller, sessions, markdown
│   │   ├── persona_presets.js# Predefined system instruction personas
│   │   └── cost_tracker.js   # Client-side token accounting ledger
│   └── assets/
│       └── favicon.svg       # Glowing vector logo
│
└── colab/
    └── module3_llm_apis.ipynb# Runnable Google Colab Notebook
```

---

## ⚡ Getting Started

### 1. Clone & Setup Environment

```bash
git clone https://github.com/manishjhcssp-prog/ai-chat-application.git
cd ai-chat-application
```

Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
venv\Scripts\activate     # On Windows
```

Install requirements:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Populate your keys:
```env
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
DEFAULT_MODEL=gpt-4o-mini
```
*(Note: If no keys are provided, the system seamlessly runs in intelligent simulation mode with zero cost).*

---

## 🧪 Running the Test Suite

Execute the 19 automated unit tests verifying configuration, conversation pruning, structured JSON parsing, cost calculations, and backoff retries:

```bash
python -m unittest discover -s python/tests -p "test_*.py"
```

Output:
```
Ran 19 tests in 3.2s
OK
```

---

## 💻 Running the Application

### Option A: Interactive Terminal CLI Chat
Launch the interactive CLI chat with real-time token tracking:
```bash
python -m python.cli_chat
```

Supported CLI commands:
- `/persona <text>`: Dynamically switch system prompt
- `/model <name>`: Switch active LLM engine
- `/params <temp> <tokens>`: Adjust temperature and token caps
- `/cost`: Inspect session token usage and financial spend
- `/structured`: Run code review structured JSON extraction
- `/clear`: Flush dialogue history
- `/quit`: Exit and display final financial ledger

### Option B: Local Web Server (FastAPI)
Run the full-stack web application locally:
```bash
python backend/app.py
```
Open your browser at `http://127.0.0.1:8000`.

---

## 🚀 Deployment to Vercel

The application is pre-configured for zero-configuration deployment to Vercel via `vercel.json` and `api/chat.js`:

```bash
vercel --prod
```

---

## 📝 License
MIT License. Built for portfolio submission for Module 3: LLM APIs & Application Development.
