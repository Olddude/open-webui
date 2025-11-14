"""
title: Ollama Agent with WebSocket Streaming
author: Open WebUI
description: Agentic Ollama function with websocket streaming, task monitoring, and tool usage
requirements: aiohttp, asyncio, json
"""

from typing import Dict, Any, Optional, AsyncGenerator, List, Callable
import asyncio
import json
import logging
import time
from datetime import datetime
from pydantic import BaseModel, Field
import aiohttp
from enum import Enum

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolType(Enum):
    """Available tool types for the agent"""

    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    FILE_OPERATION = "file_operation"
    MEMORY_RECALL = "memory_recall"
    TASK_PLANNING = "task_planning"


class AgentTool(BaseModel):
    """Base class for agent tools"""

    type: ToolType
    name: str
    description: str
    parameters: Dict[str, Any] = {}


class TaskMonitor:
    """Task monitoring and tracking system"""

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: List[str] = []

    async def create_task(self, task_id: str, description: str) -> Dict[str, Any]:
        """Create a new task"""
        task = {
            "id": task_id,
            "description": description,
            "status": TaskStatus.PENDING.value,
            "created_at": time.time(),
            "updated_at": time.time(),
            "progress": 0,
            "steps": [],
            "result": None,
            "error": None,
        }
        self.tasks[task_id] = task
        return task

    async def update_task(
        self, task_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update task status and progress"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
            self.tasks[task_id]["updated_at"] = time.time()
            return self.tasks[task_id]
        return None

    async def add_step(self, task_id: str, step: str, status: str = "running"):
        """Add a step to task execution"""
        if task_id in self.tasks:
            step_data = {
                "description": step,
                "status": status,
                "timestamp": time.time(),
            }
            self.tasks[task_id]["steps"].append(step_data)

    async def complete_task(self, task_id: str, result: Any):
        """Mark task as completed"""
        await self.update_task(
            task_id,
            {"status": TaskStatus.COMPLETED.value, "progress": 100, "result": result},
        )

    async def fail_task(self, task_id: str, error: str):
        """Mark task as failed"""
        await self.update_task(
            task_id, {"status": TaskStatus.FAILED.value, "error": error}
        )


class AgentMemory:
    """Agent memory system for context persistence"""

    def __init__(self):
        self.short_term: List[Dict[str, Any]] = []
        self.long_term: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_short_term = 10

    async def store_short_term(self, data: Dict[str, Any]):
        """Store in short-term memory"""
        self.short_term.append({"data": data, "timestamp": time.time()})
        # Keep only recent items
        if len(self.short_term) > self.max_short_term:
            self.short_term.pop(0)

    async def store_long_term(self, key: str, data: Any):
        """Store in long-term memory"""
        self.long_term[key] = {"data": data, "timestamp": time.time()}

    async def recall(self, query: str) -> List[Dict[str, Any]]:
        """Recall relevant information from memory"""
        # Simple keyword matching for now
        results = []
        query_lower = query.lower()

        # Search short-term memory
        for item in self.short_term:
            if query_lower in str(item["data"]).lower():
                results.append(item)

        # Search long-term memory
        for key, value in self.long_term.items():
            if query_lower in key.lower() or query_lower in str(value["data"]).lower():
                results.append({"key": key, **value})

        return results


class ToolExecutor:
    """Execute various tools for the agent"""

    def __init__(self, event_emitter: Optional[Callable] = None):
        self.event_emitter = event_emitter

    async def execute_web_search(self, query: str) -> Dict[str, Any]:
        """Execute web search"""
        await self._emit_status(f"Searching web for: {query}")

        # Simulated web search - replace with actual API
        results = {
            "query": query,
            "results": [
                {
                    "title": f"Result 1 for {query}",
                    "snippet": "This is a sample search result snippet...",
                    "url": "https://example.com/1",
                },
                {
                    "title": f"Result 2 for {query}",
                    "snippet": "Another sample search result...",
                    "url": "https://example.com/2",
                },
            ],
            "timestamp": datetime.now().isoformat(),
        }

        await self._emit_status(f"Found {len(results['results'])} results")
        return results

    async def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code (simulated for safety)"""
        await self._emit_status(f"Executing {language} code")

        # For safety, this is simulated - implement actual sandboxed execution
        result = {
            "language": language,
            "code": code,
            "output": "# Code execution simulated for safety",
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }

        await self._emit_status("Code execution completed")
        return result

    async def file_operation(
        self, operation: str, path: str, content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform file operations"""
        await self._emit_status(f"Performing {operation} on {path}")

        # Simulated file operations
        result = {
            "operation": operation,
            "path": path,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }

        if operation == "read":
            result["content"] = "# File content would be here"
        elif operation == "write" and content:
            result["bytes_written"] = len(content)

        await self._emit_status(f"File operation {operation} completed")
        return result

    async def _emit_status(self, message: str):
        """Emit status update via event emitter"""
        if self.event_emitter:
            await self.event_emitter(
                {"type": "status", "data": {"description": message, "done": False}}
            )


class Pipe:
    class Valves(BaseModel):
        ollama_base_url: str = Field(
            default="http://localhost:11434", description="Ollama API Base URL"
        )
        ollama_model: str = Field(default="llama3.2", description="Ollama model to use")
        temperature: float = Field(
            default=0.7, description="Temperature for text generation"
        )
        max_tokens: int = Field(default=4096, description="Maximum tokens for response")
        stream: bool = Field(default=True, description="Enable streaming responses")
        enable_tools: bool = Field(
            default=True, description="Enable tool usage for agent"
        )
        enable_memory: bool = Field(default=True, description="Enable memory system")
        enable_task_monitor: bool = Field(
            default=True, description="Enable task monitoring"
        )
        system_prompt: str = Field(
            default="""You are an advanced AI agent with access to various tools and capabilities.
You can search the web, execute code, manage files, and remember context across conversations.
Always think step-by-step and use tools when appropriate to provide accurate and helpful responses.
When executing tasks, provide clear status updates about your progress.""",
            description="System prompt for the agent",
        )

    def __init__(self):
        self.name = "Ollama Agent with WebSocket Streaming"
        self.valves = self.Valves()
        self.session: Optional[aiohttp.ClientSession] = None
        self.task_monitor = TaskMonitor()
        self.memory = AgentMemory()
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> List[AgentTool]:
        """Initialize available tools"""
        return [
            AgentTool(
                type=ToolType.WEB_SEARCH,
                name="web_search",
                description="Search the web for information",
                parameters={"query": "string"},
            ),
            AgentTool(
                type=ToolType.CODE_EXECUTION,
                name="execute_code",
                description="Execute code in a sandboxed environment",
                parameters={"code": "string", "language": "string"},
            ),
            AgentTool(
                type=ToolType.FILE_OPERATION,
                name="file_operation",
                description="Read, write, or modify files",
                parameters={
                    "operation": "string",
                    "path": "string",
                    "content": "string",
                },
            ),
            AgentTool(
                type=ToolType.MEMORY_RECALL,
                name="recall_memory",
                description="Recall information from memory",
                parameters={"query": "string"},
            ),
            AgentTool(
                type=ToolType.TASK_PLANNING,
                name="plan_task",
                description="Create a task execution plan",
                parameters={"task": "string", "steps": "array"},
            ),
        ]

    async def on_startup(self):
        """Initialize the agent"""
        logger.info(f"Starting {self.name}")

        # Initialize aiohttp session
        self.session = aiohttp.ClientSession()

        # Test Ollama connection
        try:
            async with self.session.get(
                f"{self.valves.ollama_base_url}/api/tags"
            ) as response:
                if response.status == 200:
                    logger.info("Successfully connected to Ollama")
                else:
                    logger.error(f"Failed to connect to Ollama: {response.status}")
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")

    async def on_shutdown(self):
        """Cleanup on shutdown"""
        logger.info(f"Shutting down {self.name}")
        if self.session:
            await self.session.close()

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> AsyncGenerator[str, None]:
        """Main pipe function for handling agent requests with streaming"""

        messages = body.get("messages", [])
        if not messages:
            yield "No messages provided"
            return

        # Create task if monitoring is enabled
        task_id = None
        if self.valves.enable_task_monitor:
            task_id = f"task_{int(time.time() * 1000)}"
            await self.task_monitor.create_task(task_id, "Processing agent request")

            # Emit task creation event
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "task",
                        "data": {
                            "task_id": task_id,
                            "status": "created",
                            "description": "Agent task initiated",
                        },
                    }
                )

        # Store conversation in memory if enabled
        if self.valves.enable_memory:
            for msg in messages:
                self.memory.conversation_history.append(msg)

        # Process with agent logic
        tool_executor = ToolExecutor(__event_emitter__)

        try:
            # Update task status
            if task_id:
                await self.task_monitor.update_task(
                    task_id, {"status": TaskStatus.RUNNING.value, "progress": 10}
                )

            # Analyze message for tool requirements
            last_message = messages[-1]
            user_input = last_message.get("content", "")

            # Check if tools are needed
            tool_results = await self._analyze_and_execute_tools(
                user_input, tool_executor, __event_emitter__
            )

            # Build enhanced context with tool results
            enhanced_messages = await self._build_enhanced_context(
                messages, tool_results
            )

            # Stream response from Ollama
            if self.valves.stream:
                async for chunk in self._stream_ollama_response(
                    enhanced_messages, __event_emitter__, task_id
                ):
                    yield chunk
            else:
                response = await self._get_ollama_response(enhanced_messages)
                yield response

            # Complete task
            if task_id:
                await self.task_monitor.complete_task(
                    task_id, "Request processed successfully"
                )

                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "task",
                            "data": {
                                "task_id": task_id,
                                "status": "completed",
                                "description": "Agent task completed",
                            },
                        }
                    )

        except Exception as e:
            logger.error(f"Error in agent processing: {e}")

            if task_id:
                await self.task_monitor.fail_task(task_id, str(e))

            yield f"❌ Agent error: {str(e)}"

    async def _analyze_and_execute_tools(
        self, user_input: str, tool_executor: ToolExecutor, event_emitter
    ) -> List[Dict[str, Any]]:
        """Analyze user input and execute necessary tools"""
        results = []

        if not self.valves.enable_tools:
            return results

        # Simple keyword-based tool detection
        input_lower = user_input.lower()

        # Web search detection
        if any(
            keyword in input_lower
            for keyword in ["search", "find", "look up", "google"]
        ):
            # Extract search query (simplified)
            query = user_input
            for keyword in ["search for", "find", "look up", "google"]:
                if keyword in input_lower:
                    query = user_input.split(keyword)[-1].strip()
                    break

            result = await tool_executor.execute_web_search(query)
            results.append({"tool": "web_search", "result": result})

        # Code execution detection
        if any(
            keyword in input_lower
            for keyword in ["execute", "run code", "python", "javascript"]
        ):
            # Extract code block if present
            if "```" in user_input:
                code = user_input.split("```")[1].split("```")[0]
                result = await tool_executor.execute_code(code)
                results.append({"tool": "code_execution", "result": result})

        # Memory recall
        if self.valves.enable_memory and "remember" in input_lower:
            query = user_input.replace("remember", "").strip()
            memories = await self.memory.recall(query)
            if memories:
                results.append({"tool": "memory_recall", "result": memories})

        return results

    async def _build_enhanced_context(
        self, messages: List[Dict], tool_results: List[Dict]
    ) -> List[Dict]:
        """Build enhanced context with tool results"""
        enhanced = messages.copy()

        # Add system prompt
        enhanced.insert(0, {"role": "system", "content": self.valves.system_prompt})

        # Add tool results as context
        if tool_results:
            tool_context = "Tool execution results:\n"
            for result in tool_results:
                tool_context += (
                    f"\n{result['tool']}:\n{json.dumps(result['result'], indent=2)}\n"
                )

            enhanced.append({"role": "system", "content": tool_context})

        # Add memory context if available
        if self.valves.enable_memory and self.memory.short_term:
            memory_context = "Recent context from memory:\n"
            for item in self.memory.short_term[-3:]:  # Last 3 items
                memory_context += f"- {item['data']}\n"

            enhanced.append({"role": "system", "content": memory_context})

        return enhanced

    async def _stream_ollama_response(
        self, messages: List[Dict], event_emitter, task_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response from Ollama with WebSocket events"""

        url = f"{self.valves.ollama_base_url}/api/chat"
        payload = {
            "model": self.valves.ollama_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.valves.temperature,
                "num_predict": self.valves.max_tokens,
            },
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    yield f"❌ Ollama error: {error_text}"
                    return

                total_tokens = 0
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)

                            if "message" in data and "content" in data["message"]:
                                content = data["message"]["content"]
                                yield content

                                # Update token count
                                total_tokens += 1

                                # Emit streaming event
                                if event_emitter and total_tokens % 10 == 0:
                                    await event_emitter(
                                        {
                                            "type": "stream",
                                            "data": {
                                                "tokens": total_tokens,
                                                "content": content,
                                            },
                                        }
                                    )

                                # Update task progress
                                if task_id and total_tokens % 50 == 0:
                                    progress = min(90, 10 + (total_tokens // 10))
                                    await self.task_monitor.update_task(
                                        task_id, {"progress": progress}
                                    )

                            # Check if done
                            if data.get("done", False):
                                # Store response in memory
                                if self.valves.enable_memory and "message" in data:
                                    await self.memory.store_short_term(
                                        {
                                            "type": "response",
                                            "content": data["message"].get(
                                                "content", ""
                                            ),
                                            "model": self.valves.ollama_model,
                                        }
                                    )

                                # Emit completion event
                                if event_emitter:
                                    await event_emitter(
                                        {
                                            "type": "completion",
                                            "data": {
                                                "total_tokens": total_tokens,
                                                "model": self.valves.ollama_model,
                                            },
                                        }
                                    )
                                break

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"❌ Streaming error: {str(e)}"

    async def _get_ollama_response(self, messages: List[Dict]) -> str:
        """Get non-streaming response from Ollama"""

        url = f"{self.valves.ollama_base_url}/api/chat"
        payload = {
            "model": self.valves.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.valves.temperature,
                "num_predict": self.valves.max_tokens,
            },
        }

        try:
            async with self.session.post(url, json=payload, timeout=60) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return f"❌ Ollama error: {error_text}"

                data = await response.json()
                content = data.get("message", {}).get("content", "")

                # Store in memory if enabled
                if self.valves.enable_memory:
                    await self.memory.store_short_term(
                        {
                            "type": "response",
                            "content": content,
                            "model": self.valves.ollama_model,
                        }
                    )

                return content

        except asyncio.TimeoutError:
            return "❌ Request timed out. Please try again."
        except Exception as e:
            logger.error(f"API error: {e}")
            return f"❌ API error: {str(e)}"


async def main():
    """Test the Ollama agent function"""

    print("🤖 Ollama Agent Test")
    print("=" * 50)

    # Initialize the Pipe
    pipe_instance = Pipe()

    # Configure for local Ollama
    pipe_instance.valves.ollama_model = "gemma3:1b"  # or your preferred model

    # Call startup
    await pipe_instance.on_startup()

    # Test messages
    test_messages = [
        {
            "role": "user",
            "content": "Search for information about Python async programming",
        }
    ]

    example_body = {"messages": test_messages}

    # Simulated event emitter for testing
    async def test_event_emitter(event):
        print(
            f"📡 Event: {event['type']} - {event.get('data', {}).get('description', '')}"
        )

    print("Testing agent with tools and streaming...")
    print("-" * 50)

    response = ""
    async for chunk in pipe_instance.pipe(
        body=example_body, __event_emitter__=test_event_emitter
    ):
        print(chunk, end="", flush=True)
        response += chunk

    print("\n" + "=" * 50)
    print("✅ Agent test completed!")

    # Test task monitoring
    print("\nTask Monitor Status:")
    for task_id, task in pipe_instance.task_monitor.tasks.items():
        print(f"  Task {task_id}: {task['status']} ({task['progress']}%)")

    # Test memory system
    if pipe_instance.valves.enable_memory:
        print("\nMemory System:")
        print(f"  Short-term memory items: {len(pipe_instance.memory.short_term)}")
        print(f"  Long-term memory keys: {len(pipe_instance.memory.long_term)}")
        print(
            f"  Conversation history: {len(pipe_instance.memory.conversation_history)} messages"
        )

    # Shutdown
    await pipe_instance.on_shutdown()


if __name__ == "__main__":
    """Entry point for testing"""
    print("Starting Ollama Agent Test...")
    asyncio.run(main())
