# ⚛️ QuantumForge AI

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18%2B-61dafb)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Autonomous AI Engineering Platform** — A production-grade multi-agent system that writes, executes, debugs, and evolves Python code using Large Language Models.

![QuantumForge Dashboard](docs/images/dashboard.png)

## 🚀 Features

- **Multi-Agent Architecture**: Planner, Executor, Evaluator, and Fixer agents working collaboratively
- **Parallel Execution**: Competitive candidate generation with Ray distributed computing
- **Self-Healing Code**: Automatic error detection, debugging, and retry loops
- **Multi-Provider LLM Support**: OpenAI, Groq, Anthropic, and local models with intelligent routing
- **Vector Memory (RAG)**: FAISS-based retrieval of past successful solutions
- **Prompt Evolution**: Genetic algorithm optimization of prompts based on success rates
- **Real-time Monitoring**: WebSocket-based live updates with React dashboard
- **Sandboxed Execution**: Secure subprocess-based code isolation with resource limits

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🎯 Quick Start

### Prerequisites

```bash
# Required
Python 3.11+
Node.js 20+
Git

# Optional (for cloud LLMs)
export OPENAI_API_KEY="sk-..."
export GROQ_API_KEY="gsk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

Run with Docker (Recommended)
git clone https://github.com/yourusername/quantumforge-ai.git
cd quantumforge-ai

# Create environment file
cp .env.example .env
# Edit .env with your API keys

docker-compose up --build
Access: - 🌐 UI: http://localhost - 📚 API Docs: http://localhost:8000/docs - 🔌 WebSocket: ws://localhost:8000/ws/tasks
Manual Setup
Backend:
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export LLM_PROVIDERS='["groq","fallback"]'
export GROQ_API_KEY="your-key"

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
Frontend:
cd frontend
npm install
npm run dev
🏗️ Architecture
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Dashboard│ │ Code     │ │ Task     │ │ Provider │      │
│  │          │ │ Editor   │ │ Monitor  │ │ Status   │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼────────────┼────────────┼────────────┼────────────┘
        │            │            │            │
        └────────────┴─────┬──────┴────────────┘
                           │ WebSocket/HTTP
┌──────────────────────────┼──────────────────────────────────┐
│                   FastAPI Backend                          │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │   Planner    │  │   Executor   │  │   Evaluator    │   │
│  │   Agent      │  │   Agent      │  │   Agent        │   │
│  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘   │
│         │                 │                  │             │
│         └────────┬────────┴────────┬─────────┘             │
│                  │                 │                        │
│         ┌────────▼────────┐ ┌──────▼──────┐               │
│         │  Prompt Router  │ │ Code Sandbox│               │
│         │  (OpenAI/Groq)  │ │ (subprocess)│               │
│         └─────────────────┘ └─────────────┘               │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │    FAISS     │  │    Ray       │  │   Evolution    │   │
│  │  Vector DB   │  │  Distributed │  │   Engine       │   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
└────────────────────────────────────────────────────────────┘
Agent Flow
User Request → Planner (decomposition)
     ↓
Executor (parallel candidates) → Sandbox (execution)
     ↓
Evaluator (scoring) < 0.8?
     ↓ Yes                    ↓ No
Fixer (debug) → Retry      Store in Memory
     ↓
Evolution (prompt update) → Complete
⚙️ Configuration
Environment Variables
Variable
Default
Description
LLM_PROVIDERS
["fallback"]
Comma-separated: openai,groq,anthropic,fallback
LLM_ROUTING_STRATEGY
priority
priority, round_robin, load_balance, random
OPENAI_API_KEY
-
OpenAI API key
GROQ_API_KEY
-
Groq API key (fast inference)
ANTHROPIC_API_KEY
-
Claude API key
MAX_PARALLEL_WORKERS
4
Number of parallel execution workers
SANDBOX_TIMEOUT
30
Code execution timeout (seconds)
LOG_LEVEL
INFO
DEBUG, INFO, WARNING, ERROR
Provider Priority
Default priority order: 1. Groq (priority=2) - Fastest inference 2. OpenAI (priority=1) - Best quality 3. Anthropic (priority=3) - Complex reasoning 4. Fallback (priority=999) - Mock responses for testing
🎮 Usage
Create a Task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Write a Python function to calculate Fibonacci numbers",
    "context": "Use memoization for optimization",
    "max_iterations": 3,
    "parallel_candidates": 2
  }'
Response:
{
  "task_id": "task_a1b2c3d4",
  "status": "started"
}
Monitor via WebSocket
import asyncio
import websockets
import json

async def monitor():
    uri = "ws://localhost:8000/ws/tasks"
    async with websockets.connect(uri) as ws:
        await ws.send("list_tasks")
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"[{data['type']}] {data.get('task', {}).get('status')}")

asyncio.run(monitor())
Search Memory
curl "http://localhost:8000/memory/search?query=fibonacci memoization&k=5"
🔌 API Reference
Endpoints
Method
Endpoint
Description
POST
/tasks
Create new engineering task
GET
/tasks/{id}
Get task status and results
GET
/tasks
List all tasks
GET
/memory/search
Search solution memory
GET
/health
Health check
GET
/health/llm
LLM provider status
WS
/ws/tasks
Real-time task updates
Task Statuses
    • pending - Waiting to start
    • planning - Agent decomposition
    • executing - Code generation and execution
    • evaluating - Scoring outputs
    • fixing - Self-healing in progress
    • completed - Task finished successfully
    • failed - Task failed after max retries
🛠️ Development
Project Structure
quantumforge-ai/
├── backend/
│   ├── agents/           # Multi-agent system
│   ├── api/              # FastAPI routes
│   ├── core/             # Config, models, logging
│   ├── distributed/      # Ray execution
│   ├── memory/           # Vector store
│   ├── optimization/     # Evolution engine
│   ├── sandbox/          # Code execution
│   └── services/         # LLM providers
├── frontend/
│   ├── src/components/   # React components
│   ├── src/store/        # Zustand state
│   └── src/hooks/        # WebSocket hooks
├── docker-compose.yml
└── README.md
Running Tests
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Load testing
python scripts/load_test.py --concurrent 10
📊 Performance
Metric
Value
Task Latency (simple)
~5-10s
Task Latency (complex)
~30-60s
Parallel Candidates
Up to 8
Success Rate
~85-95%
WebSocket Latency
<50ms
🤝 Contributing
    1. Fork the repository
    2. Create feature branch (git checkout -b feature/amazing)
    3. Commit changes (git commit -m 'Add amazing feature')
    4. Push to branch (git push origin feature/amazing)
    5. Open Pull Request
📄 License
MIT License - see LICENSE file.
🙏 Acknowledgments
    • OpenAI for GPT models
    • Groq for ultra-fast inference
    • Anthropic for Claude models
    • FastAPI team for the excellent framework
    • Ray team for distributed computing tools

Built with ❤️ by the QuantumForge Team GitHub • Documentation • Discord

