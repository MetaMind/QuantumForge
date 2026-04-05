from typing import Any, Dict, List, Optional, Set
import asyncio
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.core.logger import get_logger, log_structured
from backend.core.models import Task, TaskStatus, MemoryEntry, ExecutionResult
from backend.core.config import settings
from backend.distributed.executor import distributed_executor
from backend.memory.manager import MemoryManager
from backend.optimization.evolution import PromptEvolution
from backend.agents.planner import PlannerAgent
from backend.agents.executor import ExecutorAgent
from backend.agents.evaluator import EvaluatorAgent
from backend.agents.fixer import FixerAgent
from backend.sandbox.executor import SandboxExecutor
from backend.services.llm import LLMClient
from backend.services.llm_providers import ProviderType

logger = get_logger(__name__)

# Request/Response Models
class TaskRequest(BaseModel):
    description: str
    context: Optional[str] = None
    max_iterations: int = 3
    parallel_candidates: int = 2
    preferred_provider: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None

class FeedbackRequest(BaseModel):
    entry_id: str
    score: float

# Global state management
"""
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        log_structured(logger, "info", "WebSocket client connected", 
                      total_clients=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        log_structured(logger, "info", "WebSocket client disconnected",
                      total_clients=len(self.active_connections))
    
    async def broadcast(self, message: Dict[str, Any]):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        # Cleanup failed connections
        for conn in disconnected:
            self.active_connections.discard(conn)
"""
class ConnectionManager:
    def __init__(self):
        self.active_connections: list = []

    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)

# Initialize global components
manager = ConnectionManager()
memory_manager = MemoryManager()
prompt_evolution = PromptEvolution()
sandbox = SandboxExecutor()
active_tasks: Dict[str, Task] = {}

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("QuantumForge AI starting up...")
    await distributed_executor.initialize()
    yield
    logger.info("Shutting down...")
    distributed_executor.shutdown()
    sandbox.cleanup()

app = FastAPI(
    title="QuantumForge AI",
    description="Autonomous AI Engineering Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

#Add CORS middleware - required for WebSocket
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/tasks", response_model=TaskResponse)
@limiter.limit("10/minute")
async def create_task(request: Request, task_request: TaskRequest, background_tasks: BackgroundTasks):
    """Create a new autonomous coding task"""
    task = Task(
        task_id=f"task_{uuid.uuid4().hex[:8]}",
        description=task_request.description,
        status=TaskStatus.PENDING
    )
    active_tasks[task.task_id] = task
    
    # Broadcast task creation
    await manager.broadcast({
        "type": "task_created",
        "task": task.dict()
    })
    
    # Start background execution
    background_tasks.add_task(
        execute_autonomous_task,
        task.task_id,
        task_request
    )
    
    log_structured(logger, "info", "Task created", 
                  task_id=task.task_id, 
                  description=task_request.description[:50])
    
    return TaskResponse(
        task_id=task.task_id,
        status="started"
    )

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status and results"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    return {
        "task_id": task.task_id,
        "status": task.status,
        "description": task.description,
        "steps": [s.dict() if hasattr(s, 'dict') else s for s in task.steps],
        "final_output": task.final_output,
        "metrics": task.metrics,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat()
    }

@app.get("/tasks")
async def list_tasks(limit: int = 50, status: Optional[str] = None):
    """List recent tasks"""
    tasks = list(active_tasks.values())
    
    if status:
        tasks = [t for t in tasks if t.status == status]
    
    # Sort by creation date descending
    tasks.sort(key=lambda x: x.created_at, reverse=True)
    tasks = tasks[:limit]
    
    return {
        "tasks": [t.dict() for t in tasks],
        "total": len(active_tasks)
    }

@app.post("/seed")
async def seed_task(payload: Dict[str, Any]):
    """Inject a fully-formed mock task for UI development/demo purposes."""
    try:
        from backend.core.models import TaskStep
        steps = [
            TaskStep(
                step_id=s.get("step_id", f"step_{i}"),
                description=s.get("description", ""),
                status=TaskStatus(s.get("status", "pending")),
                attempts=s.get("attempts", []),
                best_attempt=s.get("best_attempt"),
                created_at=datetime.fromisoformat(s["created_at"]) if s.get("created_at") else datetime.utcnow(),
                completed_at=datetime.fromisoformat(s["completed_at"]) if s.get("completed_at") else None,
            )
            for i, s in enumerate(payload.get("steps", []))
        ]
        task = Task(
            task_id=payload.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
            description=payload["description"],
            status=TaskStatus(payload.get("status", "pending")),
            steps=steps,
            final_output=payload.get("final_output"),
            metrics={k: float(v) for k, v in payload.get("metrics", {}).items()},
            created_at=datetime.fromisoformat(payload["created_at"]) if payload.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(payload["updated_at"]) if payload.get("updated_at") else datetime.utcnow(),
        )
        active_tasks[task.task_id] = task
        await manager.broadcast({"type": "task_created", "task": task.dict()})
        return {"status": "seeded", "task_id": task.task_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/memory/feedback")
async def provide_feedback(request: FeedbackRequest):
    """Provide feedback to evolve prompts"""
    prompt_evolution.evolve({request.entry_id: request.score})
    return {"status": "feedback recorded", "entry_id": request.entry_id}

@app.get("/memory/search")
async def search_memory(query: str, k: int = 5):
    """Search memory for relevant solutions"""
    results = memory_manager.retrieve_relevant(query, k=k)
    return {
        "query": query,
        "results": [r.dict() for r in results],
        "count": len(results)
    }

@app.get("/health")
async def health():
    """Basic health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "active_tasks": len(active_tasks),
        "ray_status": "available" if distributed_executor.initialized else "unavailable"
    }

@app.get("/health/llm")
async def llm_health():
    """Get LLM provider health status"""
    client = LLMClient()
    return client.get_health()
@app.websocket("/ws/tasks")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time task updates"""
    try:
        await websocket.accept()
        await manager.connect(websocket)
        logger.info(f"WebSocket client connected. Total: {len(manager.active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket accept failed: {e}")
        return

    try:
        # Send welcome message
        await websocket.send_json({"type": "connected", "message": "WebSocket connected"})

        while True:
            try:
                # Simple receive without timeout
                data = await websocket.receive_text()

                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "list_tasks":
                    await websocket.send_json({
                        "type": "task_list",
                        "tasks": [t.dict() for t in active_tasks.values()]
                    })
                elif data == "health":
                    await websocket.send_json({
                        "type": "health",
                        "active_tasks": len(active_tasks),
                        "connected_clients": len(manager.active_connections)
                    })

            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
    finally:
        manager.disconnect(websocket)
        logger.info("WebSocket connection closed")
"""
@app.websocket("/ws/tasks")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await manager.connect(websocket)
    try:
        # Send initial connection success
        await websocket.send_json({"type": "connected", "message": "WebSocket connected"})

        while True:
            try:
                # Wait for messages with timeout to allow periodic checks
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )

                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "list_tasks":
                    await websocket.send_json({
                        "type": "task_list",
                        "tasks": [t.dict() for t in active_tasks.values()]
                    })
                elif data == "health":
                    await websocket.send_json({
                        "type": "health",
                        "active_tasks": len(active_tasks),
                        "connected_clients": len(manager.active_connections)
                    })

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
                except Exception:
                    break  # Connection dead

    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        logger.info("WebSocket connection cleaned up")
"""
"""
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "list_tasks":
                # Send current task list to new client
                await websocket.send_json({
                    "type": "task_list",
                    "tasks": [t.dict() for t in active_tasks.values()]
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
"""

async def broadcast_task_update(task: Task):
    """Broadcast task update to all connected clients"""
    await manager.broadcast({
        "type": "task_update",
        "task": task.dict()
    })

async def execute_autonomous_task(task_id: str, request: TaskRequest):
    """Main autonomous execution loop with full agent orchestration"""
    task = active_tasks.get(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return
    
    task.status = TaskStatus.PLANNING
    await broadcast_task_update(task)
    
    try:
        # Initialize LLM client with preferred provider if specified
        preferred = None
        if request.preferred_provider:
            try:
                preferred = ProviderType(request.preferred_provider)
            except ValueError:
                logger.warning(f"Invalid provider specified: {request.preferred_provider}")
        
        llm = LLMClient(preferred_provider=preferred)
        
        # Initialize agents
        planner = PlannerAgent(llm)
        executor = ExecutorAgent(llm)
        evaluator = EvaluatorAgent(llm)
        fixer = FixerAgent(llm)
        
        # PLANNING PHASE
        log_structured(logger, "info", "Starting planning phase", task_id=task_id)
        memories = memory_manager.retrieve_relevant(request.description, k=3)
        
        plan_steps = planner.run({
            "task": request.description,
            "context": request.context,
            "memories": [{"description": m.task_description, "score": m.score} for m in memories]
        })
        
        # Convert plan to TaskStep objects
        from backend.core.models import TaskStep
        task.steps = [
            TaskStep(
                step_id=s.get("id", f"step_{i}"),
                description=s.get("description", ""),
                status=TaskStatus.PENDING
            )
            for i, s in enumerate(plan_steps)
        ]
        
        await broadcast_task_update(task)
        
        all_code = []
        
        # EXECUTION PHASE for each step
        for step_idx, step_info in enumerate(plan_steps):
            step_desc = step_info.get("description", f"Step {step_idx + 1}")
            current_step = task.steps[step_idx]
            current_step.status = TaskStatus.EXECUTING
            
            log_structured(logger, "info", "Executing step", 
                          task_id=task_id, 
                          step=step_idx + 1,
                          total_steps=len(plan_steps))
            
            await broadcast_task_update(task)
            
            # Generate parallel candidates
            candidates = []
            genome = prompt_evolution.get_best_genome()
            
            for i in range(request.parallel_candidates):
                candidate_task = prompt_evolution.format_task(
                    genome, 
                    step_desc, 
                    context=request.context or ""
                )
                
                # Retrieve relevant patterns
                patterns = memory_manager.get_successful_patterns(step_desc[:20], limit=2)
                
                code = executor.run({
                    "step": candidate_task,
                    "patterns": patterns,
                    "step_number": step_idx + 1,
                    "total_steps": len(plan_steps)
                })
                
                candidates.append({
                    "code": code,
                    "candidate_id": i,
                    "genome_id": genome.genome_id
                })
            
            # Execute candidates in parallel
            #await distributed_executor.initialize()
            
            exec_inputs = [{"code": c["code"]} for c in candidates]
            results = await distributed_executor.execute_parallel(
                #lambda code: sandbox.execute(code),
                None,
                exec_inputs
            )
            
            # Evaluate candidates
            best_candidate = None
            best_score = -1.0
            
            for i, (candidate, result) in enumerate(zip(candidates, results)):
                if not isinstance(result, ExecutionResult):
                    result = ExecutionResult(**result) if isinstance(result, dict) else ExecutionResult(success=False)
                
                eval_result = evaluator.run({
                    "step": step_desc,
                    "code": candidate["code"],
                    "result": result
                })
                
                score = eval_result.get("final_score", 0.0)
                
                current_step.attempts.append({
                    "candidate_id": i,
                    "code": candidate["code"],
                    "score": score,
                    "success": result.success,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_code,
                    "execution_time": result.execution_time
                })
                
                if score > best_score:
                    best_score = score
                    best_candidate = {
                        "code": candidate["code"],
                        "result": result,
                        "score": score,
                        "eval": eval_result
                    }
            
            current_step.best_attempt = 0 if best_candidate else None
            await broadcast_task_update(task)
            
            # SELF-HEALING LOOP
            current_code = best_candidate["code"] if best_candidate else candidates[0]["code"]
            current_result = best_candidate["result"] if best_candidate else results[0]
            
            attempt = 0
            while not current_result.success and attempt < request.max_iterations:
                task.status = TaskStatus.FIXING
                current_step.status = TaskStatus.FIXING
                await broadcast_task_update(task)
                
                log_structured(logger, "info", "Entering fixer loop", 
                              task_id=task_id, 
                              attempt=attempt + 1)
                
                fixed_code = fixer.run({
                    "code": current_code,
                    "error": "Execution failed" if current_result.exit_code != 0 else "Incorrect output",
                    "stderr": current_result.stderr,
                    "stdout": current_result.stdout,
                    "step": step_desc
                })
                
                # Validate fixed code
                valid, msg = sandbox.validate_code(fixed_code)
                if not valid:
                    logger.warning(f"Fixed code failed validation: {msg}")
                
                fix_results = await distributed_executor.execute_parallel(
                    None, [{"code": fixed_code}]
                )
                current_result = fix_results[0]
                
                current_step.attempts.append({
                    "candidate_id": f"fix_{attempt}",
                    "code": fixed_code,
                    "success": current_result.success,
                    "stdout": current_result.stdout,
                    "stderr": current_result.stderr,
                    "exit_code": current_result.exit_code,
                    "execution_time": current_result.execution_time,
                    "is_fix": True
                })
                
                if current_result.success:
                    current_code = fixed_code
                    best_score = min(1.0, best_score + 0.1)  # Bonus for fixing
                    break
                
                attempt += 1
            
            # Store successful solution in memory
            if current_result.success and best_score > 0.5:
                entry = MemoryEntry(
                    task_description=step_desc,
                    code=current_code,
                    result=current_result,
                    score=best_score,
                    tags=["success", request.description.split()[0].lower(), f"step_{step_idx}"]
                )
                memory_manager.store_solution(entry)
                
                # Update prompt evolution
                prompt_evolution.evolve({genome.genome_id: best_score})
            
            all_code.append(current_code)
            current_step.status = TaskStatus.COMPLETED if current_result.success else TaskStatus.FAILED
            current_step.completed_at = datetime.utcnow()
            
            await broadcast_task_update(task)
        
        # Task completion
        task.status = TaskStatus.COMPLETED
        task.final_output = "\n\n".join(all_code)
        task.metrics = {
            "total_steps": len(plan_steps),
            "success_rate": sum(1 for s in task.steps if s.status == TaskStatus.COMPLETED) / len(plan_steps),
            "total_attempts": sum(len(s.attempts) for s in task.steps),
            "parallel_candidates": request.parallel_candidates
        }
        task.updated_at = datetime.utcnow()
        
        log_structured(logger, "info", "Task completed successfully", 
                      task_id=task_id,
                      success_rate=task.metrics["success_rate"])
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}", exc_info=True)
        task.status = TaskStatus.FAILED
        task.final_output = f"Error: {str(e)}"
        task.updated_at = datetime.utcnow()
    
    finally:
        await broadcast_task_update(task)
        # Cleanup old tasks if memory grows too large
        if len(active_tasks) > 1000:
            # Remove oldest completed tasks
            sorted_tasks = sorted(
                active_tasks.items(), 
                key=lambda x: x[1].created_at
            )
            for old_id, old_task in sorted_tasks[:100]:
                if old_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    del active_tasks[old_id]
