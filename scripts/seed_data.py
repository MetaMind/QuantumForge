#!/usr/bin/env python3
"""
seed_data.py — Inject mock tasks directly into the running QuantumForge backend.

Usage:
    python scripts/seed_data.py [--host HOST] [--port PORT]

Defaults: host=localhost, port=8000 (or whatever the backend is running on).
The script POSTs tasks via the real API so they flow through WebSocket
broadcasts and appear live in the UI.
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timedelta
import random

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)


# ── Mock data ──────────────────────────────────────────────────────────────────

TASKS = [
    {
        "description": "Implement a binary search tree with insert, delete, and in-order traversal",
        "context": "Python, must include unit tests",
    },
    {
        "description": "Write a rate limiter using the token bucket algorithm",
        "context": "Thread-safe implementation in Python",
    },
    {
        "description": "Build a LRU cache with O(1) get and put operations",
        "context": "Use doubly linked list + hashmap",
    },
    {
        "description": "Create a async HTTP client with retry logic and exponential backoff",
        "context": "aiohttp, max 3 retries",
    },
    {
        "description": "Implement Dijkstra's shortest path algorithm with a priority queue",
        "context": "Return both distance and path",
    },
    {
        "description": "Write a Fibonacci generator using memoization and dynamic programming",
        "context": "Handle n up to 10000",
    },
    {
        "description": "Build a simple pub/sub event system with wildcard topic support",
        "context": "Pure Python, no external deps",
    },
]

FINAL_OUTPUTS = [
    '''\
class Node:
    def __init__(self, val):
        self.val = val
        self.left = self.right = None

class BST:
    def __init__(self):
        self.root = None

    def insert(self, val):
        def _insert(node, val):
            if not node:
                return Node(val)
            if val < node.val:
                node.left = _insert(node.left, val)
            else:
                node.right = _insert(node.right, val)
            return node
        self.root = _insert(self.root, val)

    def inorder(self):
        result = []
        def _inorder(node):
            if node:
                _inorder(node.left)
                result.append(node.val)
                _inorder(node.right)
        _inorder(self.root)
        return result
''',
    '''\
import time
import threading

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
''',
    '''\
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
''',
]


def make_step(idx: int, desc: str, status: str, success_rate: float) -> dict:
    """Build a realistic TaskStep dict."""
    now = datetime.utcnow()
    attempts = []
    n_attempts = random.randint(1, 3)
    for a in range(n_attempts):
        success = (a == n_attempts - 1) and (random.random() < success_rate)
        attempts.append({
            "candidate_id": a,
            "code": f"# attempt {a + 1}\npass",
            "score": round(random.uniform(0.4, 0.95), 3),
            "success": success,
            "stdout": "All tests passed\n" if success else "",
            "stderr": "" if success else f"AssertionError: expected 42, got {random.randint(0, 41)}\n",
            "exit_code": 0 if success else 1,
            "execution_time": round(random.uniform(0.05, 2.5), 3),
        })

    completed_at = (now + timedelta(seconds=random.randint(5, 30))).isoformat()
    return {
        "step_id": f"step_{uuid.uuid4().hex[:6]}",
        "description": desc,
        "status": status,
        "attempts": attempts,
        "best_attempt": n_attempts - 1,
        "created_at": now.isoformat(),
        "completed_at": completed_at if status == "completed" else None,
    }


def build_mock_task(task_def: dict, status: str) -> dict:
    """Build a full mock task payload matching the Task model."""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()

    step_descs = [
        "Analyse requirements and design data structures",
        "Implement core algorithm logic",
        "Add error handling and edge cases",
        "Write unit tests and validate output",
    ]

    # Decide per-step statuses based on overall task status
    if status == "completed":
        step_statuses = ["completed"] * len(step_descs)
        success_rate = random.uniform(0.75, 1.0)
    elif status == "failed":
        step_statuses = ["completed", "completed", "failed", "pending"]
        success_rate = random.uniform(0.2, 0.5)
    elif status == "executing":
        step_statuses = ["completed", "executing", "pending", "pending"]
        success_rate = random.uniform(0.6, 0.9)
    elif status == "fixing":
        step_statuses = ["completed", "completed", "fixing", "pending"]
        success_rate = random.uniform(0.4, 0.7)
    else:
        step_statuses = ["pending"] * len(step_descs)
        success_rate = 0.0

    steps = [
        make_step(i, desc, step_statuses[i], success_rate)
        for i, desc in enumerate(step_descs)
    ]

    completed_steps = sum(1 for s in steps if s["status"] == "completed")
    total_steps = len(steps)
    sr = completed_steps / total_steps if total_steps else 0.0

    final_output = None
    if status == "completed":
        final_output = random.choice(FINAL_OUTPUTS)

    return {
        "task_id": task_id,
        "description": task_def["description"],
        "status": status,
        "steps": steps,
        "final_output": final_output,
        "metrics": {
            "success_rate": round(sr, 3),
            "total_steps": float(total_steps),
            "total_attempts": float(sum(len(s["attempts"]) for s in steps)),
            "parallel_candidates": 2.0,
        },
        "created_at": (now - timedelta(minutes=random.randint(1, 120))).isoformat(),
        "updated_at": now.isoformat(),
    }


# ── Injection ──────────────────────────────────────────────────────────────────

def inject_via_seed_endpoint(base_url: str, payload: dict) -> bool:
    """POST to /seed to inject a fully-formed mock task."""
    try:
        resp = requests.post(f"{base_url}/seed", json=payload, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def inject_via_api(base_url: str, task_def: dict) -> str | None:
    """POST a task via the real API endpoint (triggers live execution)."""
    try:
        resp = requests.post(
            f"{base_url}/tasks",
            json={
                "description": task_def["description"],
                "context": task_def.get("context", ""),
                "max_iterations": 1,
                "parallel_candidates": 1,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("task_id")
        else:
            print(f"  API error {resp.status_code}: {resp.text[:120]}")
            return None
    except requests.exceptions.ConnectionError:
        return None


def inject_via_seed_endpoint_old(base_url: str, payload: dict) -> bool:
    """Kept for reference."""
    return False


def print_task_json(payload: dict):
    """Fallback: print JSON so user can manually inspect."""
    print(json.dumps(payload, indent=2, default=str))


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed QuantumForge UI with mock data")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--count", default=7, type=int, help="Number of tasks to seed")
    parser.add_argument("--json-only", action="store_true", help="Just print JSON, don't hit the API")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"

    statuses = ["completed", "completed", "completed", "failed", "executing", "fixing", "pending"]
    tasks_to_seed = (TASKS * 3)[: args.count]
    status_cycle = (statuses * 3)[: args.count]

    print(f"\n🌱  Seeding {args.count} mock tasks → {base_url}\n")

    seeded = 0
    for i, (task_def, status) in enumerate(zip(tasks_to_seed, status_cycle)):
        payload = build_mock_task(task_def, status)

        if args.json_only:
            print(f"── Task {i + 1} ({status}) ──")
            print_task_json(payload)
            seeded += 1
            continue

        ok = inject_via_seed_endpoint(base_url, payload)
        if ok:
            print(f"  ✓ [{status:10s}] {task_def['description'][:60]}")
            seeded += 1
        else:
            # Fall back: POST via normal task creation (will run real execution)
            task_id = inject_via_api(base_url, task_def)
            if task_id:
                print(f"  ✓ [{status:10s}] {task_def['description'][:60]}  (live: {task_id})")
                seeded += 1
            else:
                print(f"  ✗ Backend unreachable — printing JSON for task {i + 1}")
                print_task_json(payload)

        time.sleep(0.2)  # small delay between requests

    print(f"\n✅  Done. {seeded}/{args.count} tasks seeded.\n")

    if seeded == 0:
        print("Tip: start the backend first with ./scripts/start_all.sh")
        print("     or use --json-only to inspect the mock payloads.\n")


if __name__ == "__main__":
    main()
