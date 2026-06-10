# AgentFlow — Multi-Agent Research Assistant

A multi-agent research assistant built with a pluggable LLM backend, Flask, and React. Specialized agents handle query decomposition, search, summarization, and fact-checking through a structured critique loop to improve factual grounding and reduce hallucinations.

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
| Search Agent | Retrieves relevant information and sources |
| Summarizer | Synthesizes findings into a coherent draft |
| Fact Checker | Validates claims; flags unsupported assertions for revision |

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

# Install dependencies
pip install -r requirements.txt

# Add your API key
echo LLM_API_KEY=your_key_here > .env
```

### Run

```bash
python api/app.py
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
- [ ] Orchestrator implementation
- [ ] Query decomposition logic
- [ ] Search pipeline
- [ ] Summarization workflow
- [ ] Fact-checking and critique loop
- [ ] Flask API endpoints
- [ ] React frontend and chat UI
- [ ] Render deployment
- [ ] Evaluation and benchmarking

---

## Author

**Priya Singh** — CS'27, Pranveer Singh Institute of Technology (PSIT), Kanpur

- GitHub: [@Priya220105](https://github.com/Priya220105)
- LinkedIn: [priya-singh-70b579297](https://www.linkedin.com/in/priya-singh-70b579297/)
- Portfolio: [priya-portfolio-ecru.vercel.app](https://priya-portfolio-ecru.vercel.app)
