# AgentFlow — Multi-Agent Research Assistant

A multi-agent research assistant built with a pluggable LLM backend, Flask, and React. Specialized agents handle query decomposition, search, summarization, and fact-checking through a structured critique loop to improve factual grounding and reduce hallucinations.

**Status: Core pipeline complete.** All five agents (Orchestrator, Decomposer, Search, Summarizer, Fact Checker) are implemented and running end-to-end, with a live UI that visualizes each pipeline stage and exposes the full execution trace (per-step latency, iteration count) for every query.

---

## Demo

Given a multi-part query like *"What were the causes, economic impacts, and long-term consequences of the 2008 financial crisis?"*, AgentFlow:

1. Decomposes it into sub-questions
2. Runs parallel search passes for each sub-question
3. Drafts a synthesized answer
4. Fact-checks the draft against retrieved sources, iterating if claims are unsupported
5. Returns the final answer alongside a full trace of every step and its latency

The UI shows each agent lighting up as it runs, plus a collapsible trace log (e.g. `orchestrator`, `decomposer`, three parallel `search_agent` calls, `summarizer`, `fact_checker · iter 1`) so the reasoning process isn't a black box.

---

## Architecture

```
User Query
     │
     ▼
┌─────────────────────┐
│  Orchestrator Agent │  ← coordinates the full pipeline
└─────────────────────┘
        │
   ┌────┴────┐
   ▼         ▼
┌──────────┐  ┌────────────┐
│ Search   │  │ Decomposer │
│ Agent    │  │ Agent      │
└──────────┘  └────────────┘
      │            │
      └─────┬──────┘
            ▼
     ┌────────────┐
     │ Summarizer │
     │ Agent      │
     └────────────┘
            │
            ▼
     ┌────────────┐
     │ Fact Check │  ← critique loop: flags unsupported claims
     │ Agent      │      and returns draft for revision
     └────────────┘
            │
            ▼
      Final Response
```

### Agent Roles

| Agent | Role |
|---|---|
| Orchestrator | Receives user query and coordinates agent pipeline |
| Decomposer | Breaks complex questions into sub-problems |
| Search Agent | Retrieves relevant information and sources (runs in parallel per sub-question) |
| Summarizer | Synthesizes findings into a coherent draft |
| Fact Checker | Validates claims; flags unsupported assertions and triggers revision iterations |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Pluggable backend (Claude / Gemini) |
| Backend | Python, Flask |
| Frontend | React |
| HTTP | httpx, httpcore |
| Deployment | Render (planned) |

Full dependency list: [`requirements.txt`](./requirements.txt)

---

## Project Structure

```
AgentFlow/
│
├── agents/
│   ├── orchestrator.py
│   ├── decomposer.py
│   ├── search_agent.py
│   ├── summarizer.py
│   └── fact_checker.py
│
├── api/
│   └── app.py
│
├── frontend/
│
├── utils/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js (for the React frontend)
- An LLM API key (Claude or Gemini)

### Setup

```bash
# Clone the repository
git clone https://github.com/Priya220105/AgentFlow-Multi-Agent-Research-Assistant.git
cd AgentFlow-Multi-Agent-Research-Assistant

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Add your API key
echo LLM_API_KEY=your_key_here > .env
```

### Run

```bash
# Start the backend
python api/app.py

# In a separate terminal, start the frontend
cd frontend && npm start
```

---

## Design Motivation

Most AI pipelines send a single prompt to a single model. AgentFlow explores whether separating responsibilities across specialized agents — decomposition, retrieval, synthesis, validation — improves response quality and factual reliability.

The critique loop is the core contribution: the Fact Checker receives the Summarizer's draft alongside its source documents, flags unsupported claims, and returns the draft for revision. This continues until a confidence threshold is reached or a maximum iteration count is hit.

**Research questions this project investigates:**
- Can specialized agents outperform single-prompt reasoning on multi-hop questions?
- Do critique loops measurably reduce hallucination rate?
- What are the latency and cost trade-offs of orchestrated multi-agent pipelines?

---

## Roadmap

- [x] Repository setup and folder structure
- [x] Agent module templates
- [x] Environment and dependency configuration
- [x] Orchestrator implementation
- [x] Query decomposition logic
- [x] Search pipeline (parallel sub-query retrieval)
- [x] Summarization workflow
- [x] Fact-checking and critique loop
- [x] Flask API endpoints
- [x] React frontend and chat UI with live pipeline visualization
- [ ] Render deployment
- [ ] Evaluation and benchmarking (hallucination rate, latency/cost trade-offs)

---

## Author

**Priya Singh** — CS'27, Pranveer Singh Institute of Technology (PSIT), Kanpur

- GitHub: [@Priya220105](https://github.com/Priya220105)
- LinkedIn: [priya-singh-70b579297](https://www.linkedin.com/in/priya-singh-70b579297/)
- Portfolio: [priya-portfolio-ecru.vercel.app](https://priya-portfolio-ecru.vercel.app)
