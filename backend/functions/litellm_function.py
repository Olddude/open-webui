"""
title: LiteLLM Streaming Chat with File Upload
author: Open WebUI
description: LiteLLM chat function with streaming support and file upload capability using OpenAI client
requirements: openai, tiktoken, base64
"""

from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
import os
import logging
import base64
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import mimetypes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipe:
    class Valves(BaseModel):
        litellm_api_base: str = Field(
            default="http://localhost:8080",
            description="LiteLLM proxy base URL",
        )
        litellm_api_key: str = Field(
            default="password", description="API Key for LiteLLM proxy (if required)"
        )
        litellm_model: str = Field(
            default="gemma",
            description="Model to use from LiteLLM proxy",
            enum=[
                "gemma",
                "gpt-oss",
                "ollama-embeddings",
                "ollama-embeddings-large",
                "genkit",
                "llama-cpp",
            ],
        )
        temperature: float = Field(
            default=0.7, description="Temperature for text generation"
        )
        max_tokens: int = Field(default=4096, description="Maximum tokens for response")
        stream: bool = Field(default=True, description="Enable streaming responses")
        vision_enabled: bool = Field(
            default=True, description="Enable vision capabilities for image uploads"
        )
        supported_file_types: List[str] = Field(
            default=[
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
                "text/plain",
                "text/markdown",
                "text/html",
                "application/pdf",
            ],
            description="Supported file types for upload",
        )
        timeout: int = Field(default=60, description="Request timeout in seconds")

    def __init__(self):
        self.name = "LiteLLM Streaming Chat with File Upload"
        self.valves = self.Valves()
        self.litellm_client: Optional[AsyncOpenAI] = None

    async def on_startup(self):
        """Initialize the LiteLLM client using OpenAI client"""
        logger.info(f"Starting {self.name}")

        try:
            # Set API key from environment or valves
            api_key = os.getenv("LITELLM_API_KEY") or self.valves.litellm_api_key
            if not api_key:
                api_key = "dummy"  # LiteLLM proxy may not require an API key
                logger.warning(
                    "No LiteLLM API key provided. Using dummy key. If LiteLLM proxy requires authentication, set LITELLM_API_KEY."
                )

            # Initialize OpenAI client pointing to LiteLLM proxy
            self.litellm_client = AsyncOpenAI(
                api_key=api_key, base_url=self.valves.litellm_api_base
            )

            logger.info("LiteLLM client initialized successfully")
            logger.info(f"Using LiteLLM proxy at: {self.valves.litellm_api_base}")
            logger.info(f"Using model: {self.valves.litellm_model}")
            logger.info(f"Streaming: {self.valves.stream}")

        except Exception as e:
            logger.error(f"Failed to initialize LiteLLM client: {e}")
            self.litellm_client = None

    async def on_shutdown(self):
        """Cleanup on shutdown"""
        logger.info(f"Shutting down {self.name}")
        if self.litellm_client:
            await self.litellm_client.close()

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> AsyncGenerator[str, None]:
        """Main pipe function for handling chat with streaming and file uploads"""

        # Initialize client if not already initialized
        if not self.litellm_client:
            try:
                # Set API key from environment or valves
                api_key = os.getenv("LITELLM_API_KEY") or self.valves.litellm_api_key
                if not api_key:
                    api_key = "dummy"  # LiteLLM proxy may not require an API key

                # Initialize OpenAI client pointing to LiteLLM proxy
                self.litellm_client = AsyncOpenAI(
                    api_key=api_key, base_url=self.valves.litellm_api_base
                )

                logger.info("LiteLLM client initialized in pipe method")
                logger.info(f"Using LiteLLM proxy at: {self.valves.litellm_api_base}")
                logger.info(f"Using model: {self.valves.litellm_model}")

            except Exception as e:
                logger.error(f"Failed to initialize LiteLLM client: {e}")
                yield f"❌ Failed to initialize LiteLLM client: {str(e)}"
                return

        messages = body.get("messages", [])
        if not messages:
            yield "No messages provided"
            return

        # Process messages and handle file uploads
        processed_messages = await self.process_messages(messages, __event_emitter__)

        try:
            if self.valves.stream:
                # Streaming response
                async for chunk in self.stream_litellm_response(processed_messages):
                    yield chunk
            else:
                # Non-streaming response
                response = await self.get_litellm_response(processed_messages)
                yield response

        except Exception as e:
            logger.error(f"Error in LiteLLM API call: {e}")
            yield f"❌ Error: {str(e)}"

    async def process_messages(
        self, messages: List[Dict], event_emitter=None
    ) -> List[Dict]:
        """Process messages and handle file uploads"""
        processed = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Check for file attachments
            if isinstance(content, dict):
                # Handle structured content with potential file uploads
                processed_content = await self.process_structured_content(
                    content, event_emitter
                )
                processed.append({"role": role, "content": processed_content})
            elif isinstance(content, list):
                # Handle array of content items (text + images)
                processed_content = []
                for item in content:
                    if isinstance(item, dict):
                        processed_item = await self.process_content_item(
                            item, event_emitter
                        )
                        if processed_item:
                            processed_content.append(processed_item)
                    else:
                        processed_content.append({"type": "text", "text": str(item)})
                processed.append({"role": role, "content": processed_content})
            else:
                # Simple text content
                processed.append({"role": role, "content": str(content)})

        return processed

    async def process_structured_content(
        self, content: Dict, event_emitter=None
    ) -> Any:
        """Process structured content that may include files"""
        if "files" in content or "images" in content:
            # Handle file/image uploads
            processed_items = []

            # Add text if present
            if "text" in content:
                processed_items.append({"type": "text", "text": content["text"]})

            # Process files
            if "files" in content:
                for file_data in content["files"]:
                    file_content = await self.process_file(file_data, event_emitter)
                    if file_content:
                        processed_items.append(file_content)

            # Process images
            if "images" in content:
                for image_data in content["images"]:
                    image_content = await self.process_image(image_data, event_emitter)
                    if image_content:
                        processed_items.append(image_content)

            return processed_items
        else:
            # Return content as-is if no files
            return content.get("text", "") if isinstance(content, dict) else content

    async def process_content_item(
        self, item: Dict, event_emitter=None
    ) -> Optional[Dict]:
        """Process individual content items"""
        item_type = item.get("type", "text")

        if item_type == "text":
            return {"type": "text", "text": item.get("text", "")}
        elif item_type == "image_url":
            return item  # Already in correct format
        elif item_type == "image":
            return await self.process_image(item, event_emitter)
        elif item_type == "file":
            return await self.process_file(item, event_emitter)

        return None

    async def process_file(self, file_data: Dict, event_emitter=None) -> Optional[Dict]:
        """Process uploaded files"""
        try:
            file_path = file_data.get("path")
            file_name = file_data.get("name", "uploaded_file")
            file_type = file_data.get("type") or mimetypes.guess_type(file_name)[0]

            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Processing file: {file_name}",
                            "done": False,
                        },
                    }
                )

            # Check if file type is supported
            if file_type not in self.valves.supported_file_types:
                logger.warning(f"Unsupported file type: {file_type}")
                return {"type": "text", "text": f"[Unsupported file type: {file_name}]"}

            # Handle different file types
            if file_type and file_type.startswith("image/"):
                # Image file - convert to base64 for vision models
                if self.valves.vision_enabled and self.supports_vision():
                    base64_data = file_data.get("data")
                    if not base64_data and file_path:
                        # Read file if path is provided
                        with open(file_path, "rb") as f:
                            base64_data = base64.b64encode(f.read()).decode("utf-8")

                    if base64_data:
                        return {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{file_type};base64,{base64_data}"
                            },
                        }
                else:
                    return {"type": "text", "text": f"[Image file: {file_name}]"}

            elif file_type and file_type.startswith("text/"):
                # Text file - extract content
                content = file_data.get("content")
                if not content and file_path:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                if content:
                    return {
                        "type": "text",
                        "text": f"### File: {file_name}\n```\n{content}\n```",
                    }

            # Default fallback
            return {"type": "text", "text": f"[File uploaded: {file_name}]"}

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {"type": "text", "text": f"[Error processing file: {str(e)}]"}

    async def process_image(
        self, image_data: Dict, event_emitter=None
    ) -> Optional[Dict]:
        """Process uploaded images"""
        try:
            if not self.valves.vision_enabled:
                return {"type": "text", "text": "[Image upload - vision disabled]"}

            # Check if model supports vision
            if not self.supports_vision():
                return {
                    "type": "text",
                    "text": "[Image upload - model doesn't support vision]",
                }

            image_url = image_data.get("url")
            image_data_b64 = image_data.get("data")

            if image_url:
                return {"type": "image_url", "image_url": {"url": image_url}}
            elif image_data_b64:
                mime_type = image_data.get("type", "image/jpeg")
                return {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data_b64}"},
                }

            return None

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {"type": "text", "text": f"[Error processing image: {str(e)}]"}

    def supports_vision(self) -> bool:
        """Check if the current model supports vision"""
        model = self.valves.litellm_model.lower()
        vision_models = [
            "gpt-4o",
            "gpt-4-vision",
            "gpt-4-turbo",
            "claude-3",
            "gemini-pro-vision",
            "gemini-1.5",
        ]
        return any(vm in model for vm in vision_models)

    async def stream_litellm_response(
        self, messages: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """Stream response from LiteLLM proxy using OpenAI client"""
        try:
            stream = await self.litellm_client.chat.completions.create(
                model=self.valves.litellm_model,
                messages=messages,
                temperature=self.valves.temperature,
                max_tokens=self.valves.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except asyncio.TimeoutError:
            yield "❌ Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"❌ Streaming error: {str(e)}"

    async def get_litellm_response(self, messages: List[Dict]) -> str:
        """Get non-streaming response from LiteLLM proxy using OpenAI client"""
        try:
            response = await asyncio.wait_for(
                self.litellm_client.chat.completions.create(
                    model=self.valves.litellm_model,
                    messages=messages,
                    temperature=self.valves.temperature,
                    max_tokens=self.valves.max_tokens,
                    stream=False,
                ),
                timeout=float(self.valves.timeout),
            )

            return response.choices[0].message.content

        except asyncio.TimeoutError:
            return "❌ Request timed out. Please try again."
        except Exception as e:
            logger.error(f"API error: {e}")
            return f"❌ API error: {str(e)}"


async def main():
    """Test the LiteLLM function with example inputs"""

    # Example messages
    example_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Hello! Can you help me understand how streaming works?",
        },
    ]

    # Example body
    example_body = {"messages": example_messages}

    print("🤖 LiteLLM Streaming Function Test")
    print("=" * 50)

    # Initialize the Pipe
    pipe_instance = Pipe()

    # Set up API key and base URL for testing
    pipe_instance.valves.litellm_api_key = os.getenv("LITELLM_API_KEY", "password")
    pipe_instance.valves.litellm_api_base = os.getenv(
        "LITELLM_API_BASE", "http://localhost:8080"
    )
    pipe_instance.valves.litellm_model = "gemma"

    # Call startup
    await pipe_instance.on_startup()

    print("Testing streaming response...")
    print("-" * 50)

    # Test streaming
    response = ""
    async for chunk in pipe_instance.pipe(body=example_body):
        print(chunk, end="", flush=True)
        response += chunk

    print("\n" + "=" * 50)
    print("✅ Streaming test completed!")

    # Test non-streaming
    print("\nTesting non-streaming response...")
    print("-" * 50)

    pipe_instance.valves.stream = False
    async for chunk in pipe_instance.pipe(body=example_body):
        print(chunk)

    print("=" * 50)
    print("✅ Non-streaming test completed!")

    # Shutdown
    await pipe_instance.on_shutdown()


if __name__ == "__main__":
    """Entry point for testing"""
    print("Starting LiteLLM Function Test...")
    asyncio.run(main())
