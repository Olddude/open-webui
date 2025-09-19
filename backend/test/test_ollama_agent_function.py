"""
Integration tests for ollama_agent_function.py

Tests the Ollama agent with websocket streaming, task monitoring, and tool usage.
"""

import pytest
import asyncio
import os
import time
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import json
import aiohttp

# Add the functions directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions"))

# Import the function under test
from functions.ollama_agent_function import (
    Pipe,
    TaskMonitor,
    AgentMemory,
    ToolExecutor,
    TaskStatus,
    ToolType,
    main,
)


class TestOllamaAgentFunction:
    """Test class for Ollama agent function"""

    @pytest.fixture
    def pipe_instance(self):
        """Create a Pipe instance for testing"""
        pipe = Pipe()
        pipe.valves.ollama_model = "llama3.2"
        return pipe

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing"""
        return [
            {
                "role": "user",
                "content": "Search for information about Python async programming",
            }
        ]

    @pytest.fixture
    def sample_body(self, sample_messages):
        """Sample request body"""
        return {"messages": sample_messages}

    @pytest.mark.asyncio
    async def test_pipe_instance_creation(self):
        """Test Pipe instance creation and configuration"""
        pipe = Pipe()

        assert pipe.name == "Ollama Agent with WebSocket Streaming"
        assert pipe.valves.ollama_model == "llama3.2"
        assert pipe.valves.temperature == 0.7
        assert pipe.valves.stream is True
        assert pipe.valves.enable_tools is True
        assert pipe.valves.enable_memory is True
        assert pipe.valves.enable_task_monitor is True

    @pytest.mark.asyncio
    async def test_task_monitor_creation(self):
        """Test TaskMonitor functionality"""
        monitor = TaskMonitor()

        # Create a task
        task_id = "test_task_1"
        task = await monitor.create_task(task_id, "Test task description")

        assert task["id"] == task_id
        assert task["status"] == TaskStatus.PENDING.value
        assert task["progress"] == 0
        assert task["description"] == "Test task description"

        # Update task
        updated = await monitor.update_task(
            task_id, {"status": TaskStatus.RUNNING.value, "progress": 50}
        )

        assert updated["status"] == TaskStatus.RUNNING.value
        assert updated["progress"] == 50

        # Add step
        await monitor.add_step(task_id, "Step 1 completed")
        assert len(monitor.tasks[task_id]["steps"]) == 1

        # Complete task
        await monitor.complete_task(task_id, "Task completed successfully")
        assert monitor.tasks[task_id]["status"] == TaskStatus.COMPLETED.value
        assert monitor.tasks[task_id]["progress"] == 100

        # Fail task
        await monitor.fail_task(task_id, "Error occurred")
        assert monitor.tasks[task_id]["status"] == TaskStatus.FAILED.value
        assert monitor.tasks[task_id]["error"] == "Error occurred"

    @pytest.mark.asyncio
    async def test_agent_memory_system(self):
        """Test AgentMemory functionality"""
        memory = AgentMemory()

        # Test short-term memory
        await memory.store_short_term({"type": "test", "data": "short-term data"})
        assert len(memory.short_term) == 1
        assert memory.short_term[0]["data"]["type"] == "test"

        # Test memory limit
        for i in range(12):
            await memory.store_short_term({"id": i})
        assert len(memory.short_term) == 10  # Should keep only max_short_term

        # Test long-term memory
        await memory.store_long_term("key1", {"data": "long-term data"})
        assert "key1" in memory.long_term
        assert memory.long_term["key1"]["data"]["data"] == "long-term data"

        # Test recall
        await memory.store_short_term({"content": "Python async programming"})
        await memory.store_long_term("python_docs", {"info": "Python documentation"})

        results = await memory.recall("python")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_tool_executor_web_search(self):
        """Test ToolExecutor web search functionality"""
        events = []

        async def mock_event_emitter(event):
            events.append(event)

        executor = ToolExecutor(mock_event_emitter)
        result = await executor.execute_web_search("Python async")

        assert result["query"] == "Python async"
        assert "results" in result
        assert len(result["results"]) > 0
        assert "timestamp" in result

        # Check events were emitted
        assert len(events) >= 2
        status_events = [e for e in events if e["type"] == "status"]
        assert len(status_events) > 0

    @pytest.mark.asyncio
    async def test_tool_executor_code_execution(self):
        """Test ToolExecutor code execution functionality"""
        executor = ToolExecutor()

        code = "print('Hello, World!')"
        result = await executor.execute_code(code, "python")

        assert result["language"] == "python"
        assert result["code"] == code
        assert result["status"] == "success"
        assert "output" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_tool_executor_file_operations(self):
        """Test ToolExecutor file operations"""
        executor = ToolExecutor()

        # Test read operation
        result = await executor.file_operation("read", "/test/file.txt")
        assert result["operation"] == "read"
        assert result["path"] == "/test/file.txt"
        assert "content" in result

        # Test write operation
        content = "Test content"
        result = await executor.file_operation("write", "/test/file.txt", content)
        assert result["operation"] == "write"
        assert result["bytes_written"] == len(content)

    @pytest.mark.asyncio
    async def test_on_startup_connection(self):
        """Test startup with Ollama connection"""
        pipe = Pipe()

        # Mock aiohttp session
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = mock_session

            await pipe.on_startup()

            assert pipe.session is not None
            mock_session.get.assert_called_once_with(
                f"{pipe.valves.ollama_base_url}/api/tags"
            )

    @pytest.mark.asyncio
    async def test_on_shutdown(self):
        """Test cleanup on shutdown"""
        pipe = Pipe()
        pipe.session = AsyncMock()

        await pipe.on_shutdown()

        pipe.session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_and_execute_tools(self, pipe_instance):
        """Test tool analysis and execution"""
        mock_executor = AsyncMock()
        mock_executor.execute_web_search = AsyncMock(
            return_value={"tool": "web_search", "results": []}
        )

        # Test search detection
        results = await pipe_instance._analyze_and_execute_tools(
            "Search for Python tutorials", mock_executor, None
        )

        assert len(results) > 0
        assert results[0]["tool"] == "web_search"
        mock_executor.execute_web_search.assert_called_once()

        # Test code execution detection
        mock_executor.execute_code = AsyncMock(return_value={"output": "result"})

        results = await pipe_instance._analyze_and_execute_tools(
            "Execute this code: ```print('test')```", mock_executor, None
        )

        code_results = [r for r in results if r["tool"] == "code_execution"]
        assert len(code_results) > 0

    @pytest.mark.asyncio
    async def test_build_enhanced_context(self, pipe_instance):
        """Test context building with tool results"""
        messages = [{"role": "user", "content": "Test message"}]
        tool_results = [
            {"tool": "web_search", "result": {"query": "test", "results": ["result1"]}}
        ]

        enhanced = await pipe_instance._build_enhanced_context(messages, tool_results)

        # Should have system prompt
        assert enhanced[0]["role"] == "system"
        assert enhanced[0]["content"] == pipe_instance.valves.system_prompt

        # Should have tool results
        tool_messages = [
            m for m in enhanced if "Tool execution results" in m.get("content", "")
        ]
        assert len(tool_messages) > 0

        # Should have original message
        user_messages = [m for m in enhanced if m["role"] == "user"]
        assert len(user_messages) > 0

    @pytest.mark.asyncio
    async def test_streaming_response(self, pipe_instance, sample_body):
        """Test streaming response from Ollama"""
        # Mock aiohttp session
        mock_session = AsyncMock()
        pipe_instance.session = mock_session

        # Mock streaming response
        async def mock_content():
            chunks = [
                '{"message": {"content": "Hello"}}',
                '{"message": {"content": " world"}}',
                '{"done": true, "message": {"content": ""}}',
            ]
            for chunk in chunks:
                yield chunk.encode()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = mock_content()
        mock_session.post.return_value.__aenter__.return_value = mock_response

        # Collect streamed response
        result = []
        async for chunk in pipe_instance._stream_ollama_response([], None):
            result.append(chunk)

        assert "Hello" in result
        assert " world" in result

    @pytest.mark.asyncio
    async def test_streaming_with_task_monitoring(self, pipe_instance, sample_body):
        """Test streaming with task monitoring enabled"""
        pipe_instance.valves.enable_task_monitor = True

        # Mock aiohttp session for successful response
        mock_session = AsyncMock()
        pipe_instance.session = mock_session

        mock_response = AsyncMock()
        mock_response.status = 200

        async def mock_content():
            yield '{"message": {"content": "Response"}, "done": true}'.encode()

        mock_response.content = mock_content()
        mock_session.post.return_value.__aenter__.return_value = mock_response

        # Process with task monitoring
        events = []

        async def mock_event_emitter(event):
            events.append(event)

        result = []
        async for chunk in pipe_instance.pipe(
            sample_body, __event_emitter__=mock_event_emitter
        ):
            result.append(chunk)

        # Check task events
        task_events = [e for e in events if e["type"] == "task"]
        assert len(task_events) >= 1

        # Check task was created
        assert len(pipe_instance.task_monitor.tasks) > 0

    @pytest.mark.asyncio
    async def test_memory_integration(self, pipe_instance, sample_body):
        """Test memory system integration"""
        pipe_instance.valves.enable_memory = True

        # Mock aiohttp session
        mock_session = AsyncMock()
        pipe_instance.session = mock_session

        mock_response = AsyncMock()
        mock_response.status = 200

        async def mock_content():
            yield '{"message": {"content": "Test"}, "done": true}'.encode()

        mock_response.content = mock_content()
        mock_session.post.return_value.__aenter__.return_value = mock_response

        # Process messages
        async for _ in pipe_instance.pipe(sample_body):
            pass

        # Check conversation history was stored
        assert len(pipe_instance.memory.conversation_history) > 0
        assert (
            pipe_instance.memory.conversation_history[0]["content"]
            == sample_body["messages"][0]["content"]
        )

    @pytest.mark.asyncio
    async def test_error_handling_ollama_error(self, pipe_instance, sample_body):
        """Test error handling for Ollama API errors"""
        # Mock aiohttp session to return error
        mock_session = AsyncMock()
        pipe_instance.session = mock_session

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"
        mock_session.post.return_value.__aenter__.return_value = mock_response

        # Collect error response
        result = []
        async for chunk in pipe_instance.pipe(sample_body):
            result.append(chunk)

        assert len(result) == 1
        assert "Agent error" in result[0] or "Ollama error" in result[0]

    @pytest.mark.asyncio
    async def test_non_streaming_response(self, pipe_instance, sample_body):
        """Test non-streaming response"""
        pipe_instance.valves.stream = False

        # Mock aiohttp session
        mock_session = AsyncMock()
        pipe_instance.session = mock_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"message": {"content": "Complete response"}}

        # Use timeout context manager
        mock_session.post.return_value = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session.post.return_value.__aexit__.return_value = None

        # Get response
        response = await pipe_instance._get_ollama_response([])

        assert response == "Complete response"

    @pytest.mark.asyncio
    async def test_tools_disabled(self, pipe_instance, sample_body):
        """Test behavior when tools are disabled"""
        pipe_instance.valves.enable_tools = False

        mock_executor = AsyncMock()

        results = await pipe_instance._analyze_and_execute_tools(
            "Search for information", mock_executor, None
        )

        assert len(results) == 0
        mock_executor.execute_web_search.assert_not_called()

    @pytest.mark.asyncio
    async def test_main_function_execution(self, capsys):
        """Test main function execution"""
        with patch("ollama_agent_function.Pipe") as mock_pipe_class:
            mock_pipe = AsyncMock()
            mock_pipe_class.return_value = mock_pipe

            # Mock successful connection
            mock_pipe.session = MagicMock()
            mock_pipe.valves.ollama_model = "llama3.2"
            mock_pipe.valves.enable_memory = True
            mock_pipe.valves.enable_task_monitor = True
            mock_pipe.task_monitor.tasks = {
                "task_1": {"status": "completed", "progress": 100}
            }
            mock_pipe.memory.short_term = []
            mock_pipe.memory.long_term = {}
            mock_pipe.memory.conversation_history = []

            # Mock streaming response
            async def mock_stream(*args, **kwargs):
                yield "Test response"

            mock_pipe.pipe.return_value = mock_stream()

            # Run main
            await main()

            # Check output
            captured = capsys.readouterr()
            assert "🤖 Ollama Agent Test" in captured.out
            assert "Testing agent with tools and streaming..." in captured.out
            assert "✅ Agent test completed!" in captured.out
            assert "Task Monitor Status:" in captured.out
            assert "Memory System:" in captured.out

    @pytest.mark.asyncio
    async def test_timeout_handling(self, pipe_instance):
        """Test timeout handling"""
        mock_session = AsyncMock()
        pipe_instance.session = mock_session

        # Simulate timeout
        mock_session.post.side_effect = asyncio.TimeoutError()

        response = await pipe_instance._get_ollama_response([])

        assert "Request timed out" in response

    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """Test tool initialization"""
        pipe = Pipe()

        assert len(pipe.tools) == 5

        tool_types = [tool.type for tool in pipe.tools]
        assert ToolType.WEB_SEARCH in tool_types
        assert ToolType.CODE_EXECUTION in tool_types
        assert ToolType.FILE_OPERATION in tool_types
        assert ToolType.MEMORY_RECALL in tool_types
        assert ToolType.TASK_PLANNING in tool_types


if __name__ == "__main__":
    """Run tests directly"""
    pytest.main([__file__, "-v", "-s"])
