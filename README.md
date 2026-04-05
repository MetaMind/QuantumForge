# ⚛️ QuantumForge AI

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18%2B-61dafb)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Autonomous AI Engineering Platform** — A production-grade multi-agent system that writes, executes, debugs, and evolves Python code using Large Language Models.

---

## 🚀 Features

- **Multi-Agent Architecture** — Planner, Executor, Evaluator, and Fixer agents working collaboratively
- **Parallel Execution** — Competitive candidate generation with Ray distributed computing
- **Self-Healing Code** — Automatic error detection, debugging, and retry loops
- **Multi-Provider LLM Support** — OpenAI, Groq, Anthropic, and local models with intelligent routing
- **Vector Memory (RAG)** — FAISS-based retrieval of past successful solutions
- **Prompt Evolution** — Genetic algorithm optimization of prompts based on success rates
- **Real-time Monitoring** — WebSocket-based live updates with React dashboard
- **Sandboxed Execution** — Secure subprocess-based code isolation with resource limits

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Development](#-development)
- [Seeding Mock Data](#-seeding-mock-data)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- Git

### One-command start

```bash
# Clone
git clone https://github.com/metamind/quantumforge-ai.git
cd quantumforge-ai

# Set API keys (optional — fallback mock works without them)
export GROQ_API_KEY="gsk-..."
export OPENAI_API_KEY="sk-..."

# Start everything
./scripts/start_all.sh
```

Access:
- UI → http://localhost:3001
- API Docs → http://localhost:8000/docs
- WebSocket → ws://localhost:8000/ws/tasks

### Stop everything

```bash
./scripts/stop_all.sh
```

> Both scripts auto-detect port conflicts and increment to the next free port.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Dashboard│ │   Code   │ │  Task    │ │Provider  │      │
│  │ Metrics  │ │  Editor  │ │ Monitor  │ │ Status   │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼────────────┼────────────┼────────────┼────────────┘
        └────────────┴─────┬──────┴────────────┘
                           │ WebSocket / HTTP
┌──────────────────────────┼──────────────────────────────────┐
│                   FastAPI Backend                           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │   Planner    │  │   Executor   │  │   Evaluator    │    │
│  │   Agent      │  │   Agent      │  │   Agent        │    │
│  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘    │
│         └────────┬─────────┘                  │             │
│                  │          ┌──────────────────┘             │
│         ┌────────▼────────┐ ┌──────▼──────┐                │
│         │  LLM Router     │ │Code Sandbox │                │
│         │ OpenAI/Groq/... │ │(subprocess) │                │
│         └─────────────────┘ └─────────────┘                │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │    FAISS     │  │     Ray      │  │   Evolution    │    │
│  │  Vector DB   │  │  Distributed │  │   Engine       │    │
│  └──────────────┘  └──────────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Agent Flow

```
User Request → Planner (decompose into steps)
                    ↓
         Executor (parallel candidates)
                    ↓
         Sandbox (execute each candidate)
                    ↓
         Evaluator (score outputs)
           ↙ score < 0.8        ↘ score ≥ 0.8
    Fixer (debug & retry)    Store in Memory
           ↓
    Evolution (update prompts)
           ↓
        Complete
```

---

## 📦 Installation

### Manual Setup

**Backend**

```bash
cd /path/to/quantumforge-ai

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Set providers
export LLM_PROVIDERS="groq,fallback"
export GROQ_API_KEY="your-key"

# Start backend
python3 -m uvicorn backend.main:create_app --host 0.0.0.0 --port 8000 --workers 1
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
cp .env.example .env   # add your API keys
docker-compose up --build
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDERS` | `["fallback"]` | Comma-separated: `openai,groq,anthropic,fallback` |
| `LLM_ROUTING_STRATEGY` | `priority` | `priority`, `round_robin`, `load_balance`, `random` |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GROQ_API_KEY` | — | Groq API key (fast inference) |
| `ANTHROPIC_API_KEY` | — | Claude API key |
| `MAX_PARALLEL_WORKERS` | `4` | Number of parallel Ray workers |
| `SANDBOX_TIMEOUT` | `30` | Code execution timeout in seconds |
| `EVOLUTION_POPULATION_SIZE` | `5` | Prompt genome pool size |
| `EVOLUTION_MUTATION_RATE` | `0.3` | Prompt mutation probability |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Provider Priority

Default routing order:

1. **OpenAI** (priority=1) — best quality
2. **Groq** (priority=2) — fastest inference
3. **Anthropic** (priority=3) — complex reasoning
4. **Fallback** (priority=999) — mock responses, no API key needed

---

## 🎮 Usage

### Create a Task via UI

Open http://localhost:3001, type a description in the **New Task** panel, and click **Forge Code**.

### Create a Task via API

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Write a Python function to calculate Fibonacci numbers",
    "context": "Use memoization for optimization",
    "max_iterations": 3,
    "parallel_candidates": 2
  }'
```

Response:

```json
{
  "task_id": "task_a1b2c3d4",
  "status": "started"
}
```

### Monitor via WebSocket

```python
import asyncio, websockets, json

async def monitor():
    async with websockets.connect("ws://localhost:8000/ws/tasks") as ws:
        await ws.send("list_tasks")
        while True:
            data = json.loads(await ws.recv())
            print(f"[{data['type']}] {data.get('task', {}).get('status')}")

asyncio.run(monitor())
```

### Search Memory

```bash
curl "http://localhost:8000/memory/search?query=fibonacci+memoization&k=5"
```

---

## 🔌 API Reference

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/tasks` | Create a new engineering task |
| `GET` | `/tasks/{id}` | Get task status and results |
| `GET` | `/tasks` | List all tasks |
| `POST` | `/seed` | Inject a pre-built mock task (dev/demo) |
| `GET` | `/memory/search` | Search solution memory |
| `POST` | `/memory/feedback` | Submit score feedback |
| `GET` | `/health` | Basic health check |
| `GET` | `/health/llm` | LLM provider status |
| `WS` | `/ws/tasks` | Real-time task updates |

### Task Statuses

| Status | Meaning |
|---|---|
| `pending` | Waiting to start |
| `planning` | Agent decomposing the task |
| `executing` | Code generation and sandbox execution |
| `evaluating` | Scoring candidate outputs |
| `fixing` | Self-healing loop in progress |
| `completed` | Task finished successfully |
| `failed` | Task failed after max retries |

---

## 🛠️ Development

### Project Structure

```
quantumforge-ai/
├── backend/
│   ├── agents/               # Planner, Executor, Evaluator, Fixer
│   ├── api/routes.py         # FastAPI endpoints + WebSocket
│   ├── core/                 # Config, models, logging, exceptions
│   ├── distributed/          # Ray parallel execution
│   ├── memory/               # FAISS vector store + manager
│   ├── optimization/         # Prompt evolution engine
│   ├── sandbox/              # Sandboxed code execution
│   ├── services/             # LLM providers (OpenAI, Groq, Anthropic, local)
│   └── tests/                # Property-based and bug condition tests
├── frontend/
│   ├── src/
│   │   ├── components/       # Header, TaskList, TaskDetail, MetricsDashboard, ...
│   │   ├── hooks/            # useWebSocket
│   │   ├── store/            # Zustand global state
│   │   └── lib/              # Utilities (cn helper)
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── postcss.config.js
├── scripts/
│   ├── start_all.sh          # Start backend + frontend (auto port selection)
│   ├── stop_all.sh           # Stop all services
│   └── seed_data.py          # Inject mock tasks for UI development
└── README.md
```

### Running Tests

```bash
# Backend unit + property-based tests
cd /path/to/quantumforge-ai
source venv/bin/activate
pytest backend/tests/ -v

# Frontend type check + build
cd frontend
npm run build

# Frontend unit tests
cd frontend
npm run test -- --run
```

---

## 🌱 Seeding Mock Data

To populate the UI with realistic mock tasks without running real LLM calls:

```bash
# Make sure backend is running first
source venv/bin/activate
python3 -m uvicorn backend.main:create_app --host 0.0.0.0 --port 8000 --workers 1

# In another terminal
source venv/bin/activate
python3 scripts/seed_data.py --host localhost --port 8000

# Seed more tasks
python3 scripts/seed_data.py --count 15

# Just inspect the JSON payloads without hitting the API
python3 scripts/seed_data.py --json-only
```

The seed script injects 7 tasks by default covering all status types: `completed`, `failed`, `executing`, `fixing`, and `pending` — each with realistic steps, attempts, scores, and code output.

---

## 📊 Performance

| Metric | Value |
|---|---|
| Task latency (simple) | ~5–10s |
| Task latency (complex) | ~30–60s |
| Parallel candidates | Up to 8 |
| Typical success rate | ~85–95% |
| WebSocket latency | <50ms |

---

## 🔧 Troubleshooting

**Backend won't start — `ModuleNotFoundError`**

Make sure you're running from the project root with the venv active:

```bash
source /path/to/venv/bin/activate
python3 -m uvicorn backend.main:create_app --host 0.0.0.0 --port 8000
```

**UI shows no tasks after seeding**

The backend uses an in-memory store — tasks are lost on restart. Re-run the seed script after every backend restart:

```bash
python3 scripts/seed_data.py --host localhost --port 8000
```

**Frontend can't reach the backend**

Check `frontend/vite.config.ts` — the proxy target must match the backend port:

```ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',   // must match backend port
    rewrite: (path) => path.replace(/^\/api/, ''),
  }
}
```

**Port already in use**

`start_all.sh` auto-increments ports. Check `scripts/.quantumforge.pids` for the actual ports in use.

**LLM calls failing**

No API keys? Set `LLM_PROVIDERS=fallback` — the fallback provider returns mock responses so the full pipeline still runs.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) for GPT models
- [Groq](https://groq.com) for ultra-fast inference
- [Anthropic](https://anthropic.com) for Claude models
- [FastAPI](https://fastapi.tiangolo.com) for the excellent framework
- [Ray](https://ray.io) for distributed computing

---
## Author

**Vikas Budde**

- LinkedIn: [linkedin.com/in/vikasbudde](https://in.linkedin.com/in/vikasbudde)
- X (Twitter): [x.com/vickcodes](https://x.com/vickcodes)
- Email: [vikas.budde@hotmail.com](mailto:vikas.budde@hotmail.com)
