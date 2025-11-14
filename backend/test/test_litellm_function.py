"""
Integration tests for litellm_function.py

Tests the LiteLLM streaming chat function with file upload capability.
"""

import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock, MagicMock

from functions.litellm_function import Pipe, main


class TestLiteLLMFunction:
    """Test class for LiteLLM streaming function"""

    @pytest.fixture
    def pipe_instance(self):
        """Create a Pipe instance for testing"""
        pipe = Pipe()
        pipe.valves.litellm_api_key = "password"
        pipe.valves.litellm_api_base = "http://localhost:8080"
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

        assert pipe.name == "LiteLLM Streaming Chat with File Upload"
        assert pipe.valves.litellm_model == "gemma"
        assert pipe.valves.litellm_api_base == "http://localhost:8080"
        assert pipe.valves.temperature == 0.7
        assert pipe.valves.stream is True
        assert pipe.valves.vision_enabled is True

    @pytest.mark.asyncio
    async def test_on_startup_with_api_key(self):
        """Test startup with valid API key"""
        pipe = Pipe()
        pipe.valves.litellm_api_key = "password"
        pipe.valves.litellm_api_base = "http://localhost:8080"

        with patch("litellm_function.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            await pipe.on_startup()

            assert pipe.litellm_client is not None
            mock_openai.assert_called_once_with(
                api_key="password", base_url="http://localhost:8080"
            )

    @pytest.mark.asyncio
    async def test_on_startup_without_api_key(self, capsys):
        """Test startup without API key - should use dummy key"""
        pipe = Pipe()
        pipe.valves.litellm_api_key = ""

        with patch.dict(os.environ, {"LITELLM_API_KEY": ""}, clear=True):
            with patch("backend.functions.litellm_function.AsyncOpenAI") as mock_openai:
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client

                await pipe.on_startup()

                # Should still initialize with dummy key
                assert pipe.litellm_client is not None
                mock_openai.assert_called_once()
                call_kwargs = mock_openai.call_args[1]
                assert call_kwargs["api_key"] == "dummy"

    @pytest.mark.asyncio
    async def test_pipe_without_client_initialized(self, sample_body):
        """Test pipe function when LiteLLM client is not initialized"""
        pipe = Pipe()
        pipe.litellm_client = None

        result = []
        async for chunk in pipe.pipe(sample_body):
            result.append(chunk)

        assert len(result) == 1
        assert "LiteLLM client not initialized" in result[0]

    @pytest.mark.asyncio
    async def test_streaming_response(self, pipe_instance, sample_body):
        """Test streaming response functionality"""
        # Mock the LiteLLM client
        mock_client = AsyncMock()
        pipe_instance.litellm_client = mock_client

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

        # Mock the LiteLLM client
        mock_client = AsyncMock()
        pipe_instance.litellm_client = mock_client

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
                        "mime_type": "image/jpeg",
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
        # Mock the LiteLLM client to raise an error
        mock_client = AsyncMock()
        pipe_instance.litellm_client = mock_client
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
        with patch("backend.functions.litellm_function.Pipe") as mock_pipe_class:
            mock_pipe = AsyncMock()
            mock_pipe_class.return_value = mock_pipe

            # Mock successful connection
            mock_pipe.litellm_client = MagicMock()
            mock_pipe.valves.litellm_api_key = "password"
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
            assert "🤖 LiteLLM Streaming Function Test" in captured.out
            assert "Testing streaming response..." in captured.out
            assert "✅ Streaming test completed!" in captured.out
            assert "✅ Non-streaming test completed!" in captured.out

    @pytest.mark.asyncio
    async def test_timeout_handling(self, pipe_instance, sample_body):
        """Test timeout handling"""
        mock_client = AsyncMock()
        pipe_instance.litellm_client = mock_client

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
        pipe_instance.valves.litellm_model = "gpt-4o"
        assert pipe_instance.supports_vision() is True

        # Test with non-vision model
        pipe_instance.valves.litellm_model = "gemma"
        assert pipe_instance.supports_vision() is False

        # Test image processing with vision model
        pipe_instance.valves.litellm_model = "gpt-4o"
        image_data = {"data": "base64_data", "type": "image/jpeg"}

        result = await pipe_instance.process_image(image_data)
        assert result["type"] == "image_url"

        # Test with non-vision model
        pipe_instance.valves.litellm_model = "gemma"
        pipe_instance.valves.vision_enabled = True

        result = await pipe_instance.process_image(image_data)
        assert result["type"] == "text"
        assert "model doesn't support vision" in result["text"]

    @pytest.mark.asyncio
    async def test_model_enum_values(self, pipe_instance):
        """Test that model enum contains expected values"""
        expected_models = [
            "gemma",
            "gpt-oss",
            "ollama-embeddings",
            "ollama-embeddings-large",
            "genkit",
            "llama-cpp",
        ]

        # Check that all expected models are in the enum
        model_field = pipe_instance.valves.__fields__["litellm_model"]
        enum_values = model_field.field_info.extra.get("enum", [])

        for model in expected_models:
            assert model in enum_values

    @pytest.mark.asyncio
    async def test_event_emitter_functionality(self, pipe_instance, sample_body):
        """Test event emitter functionality"""
        events = []

        async def mock_event_emitter(event):
            events.append(event)

        # Setup mock client
        mock_client = AsyncMock()
        pipe_instance.litellm_client = mock_client
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
        pipe_instance.litellm_client = MagicMock()
        pipe_instance.litellm_client.close = AsyncMock()

        await pipe_instance.on_shutdown()

        pipe_instance.litellm_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_base_configuration(self):
        """Test that API base URL is correctly configured"""
        pipe = Pipe()

        assert pipe.valves.litellm_api_base == "http://localhost:8080"

        # Test custom base URL
        pipe.valves.litellm_api_base = "http://custom-host:9000"
        assert pipe.valves.litellm_api_base == "http://custom-host:9000"

    @pytest.mark.asyncio
    async def test_authentication_with_bearer_token(self):
        """Test that API key is used as Bearer token"""
        pipe = Pipe()
        pipe.valves.litellm_api_key = "password"
        pipe.valves.litellm_api_base = "http://localhost:8080"

        with patch("backend.functions.litellm_function.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            await pipe.on_startup()

            # Verify that the API key is passed
            mock_openai.assert_called_once_with(
                api_key="password", base_url="http://localhost:8080"
            )

    @pytest.mark.asyncio
    async def test_multiple_models_support(self, pipe_instance):
        """Test that different models can be configured"""
        test_models = ["gemma", "gpt-oss", "llama-cpp", "genkit"]

        for model in test_models:
            pipe_instance.valves.litellm_model = model
            assert pipe_instance.valves.litellm_model == model

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, pipe_instance):
        """Test timeout configuration"""
        assert pipe_instance.valves.timeout == 60

        # Test custom timeout
        pipe_instance.valves.timeout = 120
        assert pipe_instance.valves.timeout == 120


if __name__ == "__main__":
    """Run tests directly"""
    pytest.main([__file__, "-v", "-s"])
