import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from backend.core.config import settings
from backend.core.exceptions import SandboxException
from backend.core.logger import get_logger
from backend.core.models import ExecutionResult

logger = get_logger(__name__)


class SandboxExecutor:
    def __init__(self):
        self.timeout = settings.sandbox_timeout
        self.max_memory_mb = settings.sandbox_max_memory_mb
        self.temp_dir = tempfile.mkdtemp(prefix="quantumforge_")
    
    def execute(
        self,
        code: str,
        input_data: Optional[str] = None,
        dependencies: Optional[list] = None
    ) -> ExecutionResult:
        start_time = time.time()
        execution_id = str(uuid.uuid4())[:8]
        
        # Create isolated temp directory for this execution
        work_dir = Path(self.temp_dir) / execution_id
        work_dir.mkdir(parents=True, exist_ok=True)
        
        script_path = work_dir / "script.py"
        
        try:
            # Write code to file
            with open(script_path, "w") as f:
                f.write(code)
            
            # Prepare environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(work_dir)
            env["OPENBLAS_NUM_THREADS"] = "1"  # Limit threading
            
            # Build command
            cmd = [
                "python", "-u",  # Unbuffered output
                "-m", "resource",
                "-m", "time",
                str(script_path)
            ]
            
            # Execute with resource limits
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(work_dir),
                env=env,
                input=input_data
            )
            
            try:
                stdout, stderr = process.communicate(
                    input=input_data,
                    timeout=self.timeout
                )
                execution_time = time.time() - start_time
                
                # Check for memory limit (soft check via stderr patterns)
                memory_exceeded = "MemoryError" in stderr or "Killed" in stderr
                
                result = ExecutionResult(
                    success=process.returncode == 0 and not memory_exceeded,
                    stdout=stdout[-10000:] if len(stdout) > 10000 else stdout,  # Truncate
                    stderr=stderr[-5000:] if len(stderr) > 5000 else stderr,
                    exit_code=process.returncode,
                    execution_time=execution_time,
                    artifacts={"work_dir": str(work_dir)}
                )
                
                log_structured(
                    logger,
                    "info" if result.success else "warning",
                    "Execution completed",
                    execution_id=execution_id,
                    success=result.success,
                    execution_time=execution_time
                )
                
                return result
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                
                return ExecutionResult(
                    success=False,
                    stdout="",
                    stderr=f"Execution timed out after {self.timeout} seconds",
                    exit_code=-1,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            log_structured(logger, "error", "Execution failed", error=str(e))
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=-1,
                execution_time=time.time() - start_time
            )
        
        finally:
            # Cleanup
            try:
                import shutil
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass
    
    def validate_code(self, code: str) -> tuple[bool, str]:
        """Basic validation before execution"""
        # Check for dangerous imports
        dangerous = ["os.system", "subprocess", "eval(", "exec(", "__import__", "open("]
        for pattern in dangerous:
            if pattern in code:
                return False, f"Potentially dangerous pattern detected: {pattern}"
        
        # Check for infinite loops (basic static analysis)
        if code.count("while True") > 2:
            return False, "Multiple infinite loops detected"
        
        return True, "Code passed validation"
    
    def cleanup(self):
        """Cleanup all temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
