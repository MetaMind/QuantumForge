# 🔧 QuantumForge AI - Debugging & Troubleshooting Guide

This guide covers common issues, debugging techniques, and solutions for QuantumForge AI.

## 📋 Quick Diagnostics

Run the diagnostic script:
```bash
./scripts/diagnose.sh
🚨 Common Issues
1. Backend Won’t Start
Symptom:
ImportError: cannot import name 'Settings' from 'backend.core.config'
Solution:
# Ensure you're in the backend directory
cd backend
export PYTHONPATH=/full/path/to/backend:$PYTHONPATH

# Or use absolute imports
python -m backend.main
Symptom:
pydantic_settings.exceptions.SettingsError: error parsing value for field "llm_providers"
Solution:
# Use valid JSON format
export LLM_PROVIDERS='["fallback"]'

# Or comma-separated (handled by validator)
export LLM_PROVIDERS="openai,groq,fallback"

# Check for empty strings
unset LLM_PROVIDERS  # Let it use default
2. WebSocket Connection Issues
Symptom:
websockets.exceptions.InvalidStatus: server rejected WebSocket connection: HTTP 403
Solution:
# In backend/api/routes.py, ensure CORS is configured:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Symptom:
Connection lost: no close frame received or sent
Solution:
# Add ping/pong keepalive to WebSocket handler
@app.websocket("/ws/tasks")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=30.0
            )
            if data == "ping":
                await websocket.send_text("pong")
    except asyncio.TimeoutError:
        await websocket.close()
3. LLM Provider Failures
Symptom:
LLMException: Groq generation failed: Connection timeout
Solution:
# Check provider health
curl http://localhost:8000/health/llm

# Test with fallback only
export LLM_PROVIDERS='["fallback"]'
export USE_FALLBACK_LLM=true

# Verify API keys
echo $GROQ_API_KEY | wc -c  # Should be > 20
Symptom:
NameError: name 'log_structured' is not defined
Solution:
# In sandbox/executor.py, import correctly:
from backend.core.logger import get_logger  # NOT log_structured

logger = get_logger(__name__)
logger.error(f"Execution failed: {e}")  # Use logger directly
4. Ray/Distributed Execution Errors
Symptom:
TypeError: object NoneType can't be used in 'await' expression
Solution:
# Make initialize() async
async def initialize(self):
    if self.initialized:
        return
    # ... initialization code
Symptom:
RayTaskError: NameError: name 'log_structured' is not defined
Solution: Ray functions must be self-contained. Define the remote function at module level:
@ray.remote
def execute_remote(code: str) -> dict:
    # All imports inside function
    import subprocess
    # ... execution logic
    return result
5. Frontend Connection Issues
Symptom:
Proxy error: Could not proxy request /api/tasks from localhost:3000
Solution:
// In vite.config.ts, check proxy settings:
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
Symptom:
Module not found: Can't resolve '@/components/ui/button'
Solution:
# Check path aliases in vite.config.ts
npm install
npx vite --clearScreen false  # Clear cache
📝 Logging & Debugging
Enable Debug Logging
# Backend
export LOG_LEVEL=DEBUG
export LOG_FORMAT=json  # or 'text'

# Run with verbose output
uvicorn backend.main:app --reload --log-level debug
Structured Log Filtering
# Watch specific components
tail -f logs/quantumforge.jsonl | jq 'select(.logger | contains("agents"))'

# Filter by level
tail -f logs/quantumforge.jsonl | jq 'select(.level=="ERROR")'

# Pretty print specific fields
tail -f logs/quantumforge.jsonl | jq '{time: .timestamp, msg: .message, step: .extra_data.step}'
WebSocket Debugging
# Test with wscat
npm install -g wscat
wscat -c ws://localhost:8000/ws/tasks

# Or use websocat
websocat ws://localhost:8000/ws/tasks
API Testing with curl
# Health check
curl -s http://localhost:8000/health | jq

# Create task and capture ID
TASK_ID=$(curl -s -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"description":"test","max_iterations":1}' | jq -r '.task_id')

# Poll task
watch -n 1 "curl -s http://localhost:8000/tasks/$TASK_ID | jq '.status, .metrics'"
🧪 Testing
Unit Tests
cd backend
pytest tests/ -v --tb=short

# Run specific test
pytest tests/test_agents.py::test_planner -v
Integration Tests
# Start services
docker-compose up -d

# Run test suite
./scripts/integration_test.sh
Load Testing
# Install locust
pip install locust

# Run load test
locust -f scripts/locustfile.py --host http://localhost:8000
🔍 Deep Debugging
Check Ray Dashboard
# Ray dashboard available at
open http://localhost:8265

# Or check ray status
ray status
Memory Store Inspection
# Debug script
from backend.memory.vector_store import VectorStore
store = VectorStore()
print(f"Vectors: {len(store.metadata)}")
results = store.search("fibonacci", k=3)
print(results)
Task State Inspection
# Get full task state
curl http://localhost:8000/tasks/{task_id} | jq '.' > task_debug.json

# Analyze steps
cat task_debug.json | jq '.steps[] | {id: .step_id, attempts: (.attempts | length), status}'
🐛 Common Error Patterns
Popen.__init__() got an unexpected keyword argument 'input'
Cause: Subprocess input should be in communicate(), not Popen().
Fix:
process = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
stdout, stderr = process.communicate(input=input_data)  # Correct
RuntimeWarning: coroutine 'X' was never awaited
Cause: Missing await on async function.
Fix:
await distributed_executor.initialize()  # Add await
JSONDecodeError: Expecting value
Cause: Empty or malformed environment variable.
Fix:
unset LLM_PROVIDERS  # Remove empty var
# Or set properly:
export LLM_PROVIDERS='["fallback"]'
📊 Performance Debugging
Slow Task Execution
    1. Check provider latency:
    • curl http://localhost:8000/health/llm | jq '.[].avg_latency'
    2. Enable timing logs:
    • import time
start = time.time()
result = await execute()
print(f"Duration: {time.time() - start}s")
    3. Check parallel execution:
    • # Monitor Ray utilization
ray timeline logs/timeline.json
Memory Leaks
# Monitor Python memory
pip install memory_profiler
mprof run backend/main.py
mprof plot

# Check for unclosed connections
lsof -i :8000 | wc -l
🆘 Emergency Procedures
Complete Reset
# 1. Stop all services
pkill -f uvicorn
pkill -f ray
pkill -f node

# 2. Clear temporary files
rm -rf /tmp/ray
rm -rf backend/data/vector_store
rm -f logs/*.jsonl

# 3. Restart fresh
docker-compose down
docker-compose up --build
Database Corruption
# Rebuild vector store
from backend.memory.vector_store import VectorStore
store = VectorStore()
store.clear()  # Removes all stored solutions
Reset Evolution
# Reset prompt evolution
from backend.optimization.evolution import PromptEvolution
evo = PromptEvolution()
evo.population = []  # Clear evolved prompts
evo._initialize_population()
📞 Support
    • GitHub Issues: https://github.com/yourusername/quantumforge-ai/issues
    • Discord: https://discord.gg/quantumforge
    • Email: support@quantumforge.ai
📝 Debug Checklist
When reporting issues, include:
    • ☐ Backend logs (logs/quantumforge.jsonl)
    • ☐ Frontend console errors
    • ☐ Environment variables (redact API keys)
    • ☐ Task ID if applicable
    • ☐ Steps to reproduce
    • ☐ Expected vs actual behavior

