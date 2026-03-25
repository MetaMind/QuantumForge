#!/bin/bash
echo "Testing WebSocket connection..."

# Test 1: Direct wscat (if available)
if command -v wscat 2> /dev/null; then
    echo "✓ Testing with wscat (Ctrl+C to exit):"
    timeout 5 wscat -c ws://localhost:8010/ws/tasks || echo "wscat test complete"
fi

# Test 2: Python monitor
echo ""
echo "✓ Testing with Python monitor:"
python3 socket_monitor.py
