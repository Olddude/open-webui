"""
Integration tests for openai_function.py

Tests the OpenAI streaming chat function with file upload capability.
"""

import pytest
import json
import asyncio
import base64
import os
from unittest.mock import patch, AsyncMock, MagicMock
import sys
from typing import AsyncGenerator

# Add the functions directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions"))

# Import the function under test
from functions.openai_function import Pipe, main


class TestOpenAIFunction:
    """Test class for OpenAI streaming function"""

    @pytest.fixture
    def pipe_instance(self):
        """Create a Pipe instance for testing"""
        pipe = Pipe()
        pipe.valves.openai_api_key = "test_api_key"
        return pipe

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing"""
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! How are you?"},
        ]

    @pytest.fixture
    def sample_body(self, sample_messages):
        """Sample request body"""
        return {"messages": sample_messages}

    @pytest.mark.asyncio
    async def test_pipe_instance_creation(self):
        """Test Pipe instance creation and configuration"""
        pipe = Pipe()

        assert pipe.name == "OpenAI Streaming Chat with File Upload"
        assert pipe.valves.openai_model == "gpt-4o-mini"
        assert pipe.valves.temperature == 0.7
        assert pipe.valves.stream is True
        assert pipe.valves.vision_enabled is True

    @pytest.mark.asyncio
    async def test_on_startup_with_api_key(self):
        """Test startup with valid API key"""
        pipe = Pipe()
        pipe.valves.openai_api_key = "test_api_key"

        with patch("openai_function.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            await pipe.on_startup()

            assert pipe.openai_client is not None
            mock_openai.assert_called_once_with(
                api_key="test_api_key", base_url="https://api.openai.com/v1"
            )

    @pytest.mark.asyncio
    async def test_on_startup_without_api_key(self, capsys):
        """Test startup without API key"""
        pipe = Pipe()
        pipe.valves.openai_api_key = ""

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            await pipe.on_startup()

            assert pipe.openai_client is None

    @pytest.mark.asyncio
    async def test_pipe_without_client_initialized(self, sample_body):
        """Test pipe function when OpenAI client is not initialized"""
        pipe = Pipe()
        pipe.openai_client = None

        result = []
        async for chunk in pipe.pipe(sample_body):
            result.append(chunk)

        assert len(result) == 1
        assert "OpenAI client not initialized" in result[0]

    @pytest.mark.asyncio
    async def test_streaming_response(self, pipe_instance, sample_body):
        """Test streaming response functionality"""
        # Mock the OpenAI client
        mock_client = AsyncMock()
        pipe_instance.openai_client = mock_client

        # Create a mock streaming response
        async def mock_stream():
            chunks = ["Hello", " there", ", how", " can", " I", " help?"]
            for chunk in chunks:
                mock_chunk = MagicMock()
                mock_chunk.choices = [MagicMock()]
                mock_chunk.choices[0].delta.content = chunk
                yield mock_chunk

        mock_client.chat.completions.create.return_value = mock_stream()

        # Collect streamed response
        result = []
        async for chunk in pipe_instance.pipe(sample_body):
            result.append(chunk)

        assert result == ["Hello", " there", ", how", " can", " I", " help?"]
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_streaming_response(self, pipe_instance, sample_body):
        """Test non-streaming response functionality"""
        pipe_instance.valves.stream = False

        # Mock the OpenAI client
        mock_client = AsyncMock()
        pipe_instance.openai_client = mock_client

        # Mock non-streaming response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a complete response"
        mock_client.chat.completions.create.return_value = mock_response

        # Collect response
        result = []
        async for chunk in pipe_instance.pipe(sample_body):
            result.append(chunk)

        assert len(result) == 1
        assert result[0] == "This is a complete response"

    @pytest.mark.asyncio
    async def test_image_processing(self, pipe_instance):
        """Test image upload and processing"""
        # Create a message with image
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image",
                        "data": "base64_encoded_image_data",
                        "type": "image/jpeg",
                    },
                ],
            }
        ]

        processed = await pipe_instance.process_messages(messages)

        assert len(processed) == 1
        assert processed[0]["role"] == "user"
        assert isinstance(processed[0]["content"], list)

        # Check if image was processed correctly
        content_types = [item["type"] for item in processed[0]["content"]]
        assert "text" in content_types
        assert "image_url" in content_types

    @pytest.mark.asyncio
    async def test_file_processing_text_file(self, pipe_instance):
        """Test text file processing"""
        file_data = {
            "name": "test.txt",
            "type": "text/plain",
            "content": "This is test content",
        }

        result = await pipe_instance.process_file(file_data)

        assert result is not None
        assert result["type"] == "text"
        assert "test.txt" in result["text"]
        assert "This is test content" in result["text"]

    @pytest.mark.asyncio
    async def test_file_processing_unsupported_type(self, pipe_instance):
        """Test unsupported file type handling"""
        file_data = {"name": "test.exe", "type": "application/x-executable"}

        result = await pipe_instance.process_file(file_data)

        assert result is not None
        assert result["type"] == "text"
        assert "Unsupported file type" in result["text"]

    @pytest.mark.asyncio
    async def test_error_handling_api_error(self, pipe_instance, sample_body):
        """Test error handling for API errors"""
        # Mock the OpenAI client to raise an error
        mock_client = AsyncMock()
        pipe_instance.openai_client = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        # Collect error response
        result = []
        async for chunk in pipe_instance.pipe(sample_body):
            result.append(chunk)

        assert len(result) == 1
        assert "Error" in result[0]
        assert "API Error" in result[0]

    @pytest.mark.asyncio
    async def test_main_function_execution(self, capsys):
        """Test main function execution"""
        with patch("openai_function.Pipe") as mock_pipe_class:
            mock_pipe = AsyncMock()
            mock_pipe_class.return_value = mock_pipe

            # Mock successful connection
            mock_pipe.openai_client = MagicMock()
            mock_pipe.valves.openai_api_key = "test_key"
            mock_pipe.valves.stream = True

            # Mock streaming response
            async def mock_stream(*args, **kwargs):
                yield "Test "
                yield "response"

            mock_pipe.pipe.return_value = mock_stream()

            # Run main
            await main()

            # Check output
            captured = capsys.readouterr()
            assert "🤖 OpenAI Streaming Function Test" in captured.out
            assert "Testing streaming response..." in captured.out
            assert "✅ Streaming test completed!" in captured.out
            assert "✅ Non-streaming test completed!" in captured.out

    @pytest.mark.asyncio
    async def test_timeout_handling(self, pipe_instance, sample_body):
        """Test timeout handling"""
        mock_client = AsyncMock()
        pipe_instance.openai_client = mock_client

        # Simulate timeout
        mock_client.chat.completions.create.side_effect = asyncio.TimeoutError()

        result = []
        async for chunk in pipe_instance.pipe(sample_body):
            result.append(chunk)

        assert len(result) == 1
        assert "Request timed out" in result[0]

    @pytest.mark.asyncio
    async def test_vision_model_detection(self, pipe_instance):
        """Test vision model capability detection"""
        # Test with vision model
        pipe_instance.valves.openai_model = "gpt-4o"
        image_data = {"data": "base64_data", "type": "image/jpeg"}

        result = await pipe_instance.process_image(image_data)
        assert result["type"] == "image_url"

        # Test with non-vision model
        pipe_instance.valves.openai_model = "gpt-3.5-turbo"
        pipe_instance.valves.vision_enabled = True

        result = await pipe_instance.process_image(image_data)
        assert result["type"] == "text"
        assert "model doesn't support vision" in result["text"]

    @pytest.mark.asyncio
    async def test_event_emitter_functionality(self, pipe_instance, sample_body):
        """Test event emitter functionality"""
        events = []

        async def mock_event_emitter(event):
            events.append(event)

        # Setup mock client
        mock_client = AsyncMock()
        pipe_instance.openai_client = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response

        pipe_instance.valves.stream = False

        # Process with event emitter
        messages = [
            {
                "role": "user",
                "content": {
                    "text": "Test",
                    "files": [
                        {
                            "name": "test.txt",
                            "type": "text/plain",
                            "content": "Test content",
                        }
                    ],
                },
            }
        ]

        body = {"messages": messages}
        result = []
        async for chunk in pipe_instance.pipe(
            body, __event_emitter__=mock_event_emitter
        ):
            result.append(chunk)

        # Check that events were emitted
        assert len(events) > 0
        status_events = [e for e in events if e["type"] == "status"]
        assert len(status_events) > 0

    @pytest.mark.asyncio
    async def test_on_shutdown(self, pipe_instance):
        """Test cleanup on shutdown"""
        # Mock the aiohttp session
        mock_session = AsyncMock()
        pipe_instance.openai_client = MagicMock()
        pipe_instance.openai_client.close = AsyncMock()

        await pipe_instance.on_shutdown()

        pipe_instance.openai_client.close.assert_called_once()


if __name__ == "__main__":
    """Run tests directly"""
    pytest.main([__file__, "-v", "-s"])
