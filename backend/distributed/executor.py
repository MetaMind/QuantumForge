import asyncio
import ray
from typing import Any, Callable, Dict, List

from backend.core.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)

# Ray remote function defined at module level (required for serialization)
@ray.remote
def execute_code_remote(code: str, sandbox_config: Dict) -> Dict:
    """
    Ray remote function - must be self-contained at module level
    """
    import subprocess
    import tempfile
    import time
    import os
    from pathlib import Path
    
    start_time = time.time()
    work_dir = tempfile.mkdtemp()
    script_path = Path(work_dir) / "script.py"
    
    try:
        with open(script_path, "w") as f:
            f.write(code)
        
        env = os.environ.copy()
        env["PYTHONPATH"] = str(work_dir)
        
        process = subprocess.Popen(
            ["python", "-u", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(work_dir),
            env=env
        )
        
        try:
            stdout, stderr = process.communicate(timeout=sandbox_config.get("timeout", 30))
            execution_time = time.time() - start_time
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout[-10000:] if len(stdout) > 10000 else stdout,
                "stderr": stderr[-5000:] if len(stderr) > 5000 else stderr,
                "exit_code": process.returncode,
                "execution_time": execution_time
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "success": False,
                "stdout": "",
                "stderr": "Timeout",
                "exit_code": -1,
                "execution_time": time.time() - start_time
            }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "execution_time": time.time() - start_time
        }
    finally:
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)


class DistributedExecutor:
    def __init__(self):
        self.initialized = False
        self.max_workers = settings.max_parallel_workers
    
    async def initialize(self):
        """Initialize Ray"""
        if self.initialized:
            return
        
        try:
            if settings.ray_address:
                ray.init(address=settings.ray_address)
            else:
                ray.init(ignore_reinit_error=True)
            
            self.initialized = True
            logger.info("Ray initialized successfully")
        except Exception as e:
            logger.warning(f"Ray initialization failed: {e}")
            self.initialized = False
    
    async def execute_parallel(
        self,
        func: Callable,
        items: List[Dict[str, Any]],
        max_workers: int = None
    ) -> List[Any]:
        """Execute in parallel"""
        if not self.initialized:
            await self.initialize()
        
        workers = max_workers or self.max_workers
        
        if self.initialized and ray.is_initialized():
            return await self._execute_with_ray(items, workers)
        else:
            return await self._execute_with_async(func, items, workers)
    
    async def _execute_with_ray(self, items: List[Dict], max_workers: int) -> List[Any]:
        """Execute using Ray - sandbox code runs in parallel processes"""
        from backend.core.models import ExecutionResult
        
        # Submit all tasks to Ray
        futures = []
        for item in items:
            # Extract code and config
            code = item.get("code", "")
            config = {"timeout": settings.sandbox_timeout}
            future = execute_code_remote.remote(code, config)
            futures.append(future)
        
        # Gather all results
        ray_results = ray.get(futures)
        
        # Convert back to ExecutionResult objects
        results = []
        for r in ray_results:
            results.append(ExecutionResult(
                success=r["success"],
                stdout=r["stdout"],
                stderr=r["stderr"],
                exit_code=r["exit_code"],
                execution_time=r["execution_time"]
            ))
        
        return results
    
    async def _execute_with_async(self, func: Callable, items: List[Dict], max_workers: int) -> List[Any]:
        """Fallback to asyncio"""
        semaphore = asyncio.Semaphore(max_workers)
        
        async def run_with_limit(item):
            async with semaphore:
                if asyncio.iscoroutinefunction(func):
                    return await func(**item)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, lambda: func(**item))
        
        tasks = [run_with_limit(item) for item in items]
        return await asyncio.gather(*tasks)
    
    def shutdown(self):
        if self.initialized and ray.is_initialized():
            ray.shutdown()
            self.initialized = False


distributed_executor = DistributedExecutor()
