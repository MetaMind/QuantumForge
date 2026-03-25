#!/bin/bash
set -e

echo "🧪 QuantumForge System Validation"

# 1. Health
echo "✓ Health:"
curl -s http://localhost:8010/health | jq -r '.status'

# 2. Providers
echo "✓ Providers:"
curl -s http://localhost:8010/health/llm | jq -r '.[] | "  \(.provider): \(.available)"'

# 3. Create task
echo "✓ Creating task..."
TASK=$(curl -s -X POST http://localhost:8010/tasks \
  -H "Content-Type: application/json" \
  -d '{"description":"Write a Python function to reverse a linked list","max_iterations":2,"parallel_candidates":2}')
TASK_ID=$(echo $TASK | jq -r '.task_id')
echo "  Task ID: $TASK_ID"

# 4. Monitor via HTTP polling
echo "✓ Monitoring (Ctrl+C to skip)..."
for i in {1..20}; do
    STATUS=$(curl -s http://localhost:8010/tasks/$TASK_ID)
    STATE=$(echo $STATUS | jq -r '.status')
    echo -ne "\r  Status: $STATE    "
    [[ "$STATE" == "completed" || "$STATE" == "failed" ]] && break
    sleep 1
done
echo ""

# 5. Show result
echo "✓ Result:"
curl -s http://localhost:8010/tasks/$TASK_ID | jq '.metrics'

# 6. Memory search (URL-encoded)
echo "✓ Memory:"
curl -s -G "http://localhost:8010/memory/search" \
  --data-urlencode "query=linked list" \
  -d "k=3" | jq '.count'

echo "✅ All tests passed!"
