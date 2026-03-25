import asyncio
import websockets
import json
import sys

class QuantumForgeMonitor:
    def __init__(self, uri="ws://localhost:8010/ws/tasks"):
        self.uri = uri
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        
    async def connect(self):
        """Connect with automatic reconnection"""
        while True:
            try:
                print(f"🔌 Connecting to {self.uri}...")
                async with websockets.connect(
                    self.uri,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5
                ) as ws:
                    print("✅ Connected to QuantumForge WebSocket")
                    self.reconnect_delay = 1  # Reset delay on success
                    
                    # Request current task list
                    await ws.send("list_tasks")
                    
                    # Listen for messages
                    await self.listen(ws)
                    
            except (websockets.exceptions.ConnectionClosed, 
                    websockets.exceptions.InvalidStatus,
                    OSError) as e:
                print(f"❌ Connection lost: {e}")
                print(f"🔄 Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            except Exception as e:
                print(f"💥 Unexpected error: {e}")
                await asyncio.sleep(5)
    
    async def listen(self, ws):
        """Handle incoming messages"""
        try:
            async for message in ws:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON: {message[:100]}")
                except Exception as e:
                    print(f"⚠️  Error handling message: {e}")
        except websockets.exceptions.ConnectionClosedOK:
            print("👋 Connection closed normally")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"⚠️  Connection closed unexpectedly: {e}")
            raise  # Trigger reconnection
    
    async def handle_message(self, data: dict):
        """Process different message types"""
        msg_type = data.get('type', 'unknown')
        
        if msg_type == 'connected':
            print(f"🟢 {data.get('message')}")
            
        elif msg_type == 'ping':
            # Respond to server ping
            pass  # websockets library handles this automatically
            
        elif msg_type == 'task_list':
            tasks = data.get('tasks', [])
            print(f"\n📋 Active Tasks: {len(tasks)}")
            for task in tasks[-5:]:  # Show last 5
                status_icon = {
                    'completed': '✅',
                    'failed': '❌',
                    'executing': '⚙️',
                    'pending': '⏳'
                }.get(task['status'], '❓')
                print(f"   {status_icon} {task['task_id'][:8]}... | {task['status']}")
                
        elif msg_type == 'task_created':
            task = data.get('task', {})
            print(f"\n🆕 New Task: {task.get('task_id', 'unknown')[:8]}...")
            print(f"   Status: {task.get('status')}")
            
        elif msg_type == 'task_update':
            task = data.get('task', {})
            status = task.get('status', 'unknown')
            
            # Status emoji
            icon = {
                'completed': '✅',
                'failed': '❌',
                'executing': '⚙️',
                'fixing': '🔧',
                'planning': '📝',
                'pending': '⏳'
            }.get(status, '🔄')
            
            print(f"\n{icon} Task Update: {task.get('task_id', 'unknown')[:8]}...")
            print(f"   Status: {status}")
            
            # Show current step info
            steps = task.get('steps', [])
            if steps:
                current_steps = [s for s in steps if s.get('status') in ['executing', 'fixing']]
                if current_steps:
                    step = current_steps[-1]
                    print(f"   Step: {step.get('description', 'N/A')[:50]}...")
                    attempts = len(step.get('attempts', []))
                    if attempts > 0:
                        print(f"   Attempts: {attempts}")
            
            # Show completion
            if status == 'completed' and task.get('final_output'):
                code_len = len(task.get('final_output', ''))
                print(f"   📝 Generated: {code_len} characters")
                metrics = task.get('metrics', {})
                if metrics:
                    print(f"   📊 Success Rate: {metrics.get('success_rate', 0):.0%}")
                    print(f"   🔄 Total Attempts: {metrics.get('total_attempts', 0)}")
                    
        elif msg_type == 'health':
            print(f"💓 Health: {data.get('active_tasks', 0)} tasks, {data.get('connected_clients', 0)} clients")
            
        else:
            print(f"\n📨 {msg_type}: {json.dumps(data, indent=2)[:200]}...")

async def main():
    monitor = QuantumForgeMonitor()
    await monitor.connect()

if __name__ == "__main__":
    print("starting socker monitoring")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
