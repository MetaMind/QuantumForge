# QuantumForge AI

A production-grade autonomous AI engineering platform with multi-agent architecture, evolutionary optimization, and distributed execution.

## Architecture

- **Multi-Agent System**: Planner, Executor, Evaluator, Fixer agents
- **Competitive Parallel Execution**: Multiple candidates per step with Ray
- **Self-Healing Loop**: Automatic error detection and fixing
- **Vector Memory**: FAISS-based RAG for solution retrieval
- **Evolutionary Optimization**: Prompt evolution based on success rates
- **Sandboxed Execution**: Safe subprocess-based code execution

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with fallback LLM (no API key needed for testing)
export USE_FALLBACK_LLM=true
python -m backend.main
