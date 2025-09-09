"""
title: Simple Recipe JSON Converter
author: Open WebUI
description: Converts recipe data to JSON using OpenAI
requirements: openai
"""

from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import json
import os
import logging
from pydantic import BaseModel
from openai import AsyncOpenAI
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipe:
    class Valves(BaseModel):
        openai_api_key: str = ""
        openai_api_base: str = "https://api.openai.com/v1"
        openai_model: str = "gpt-4o-mini"
        temperature: float = 0.7

    def __init__(self):
        self.name = "Simple Recipe JSON Converter"
        self.valves = self.Valves()
        self.openai_client: Optional[AsyncOpenAI] = None

    async def on_startup(self):
        """Initialize the function"""
        logger.info(f"Starting {self.name}")

        # Initialize OpenAI client
        try:
            api_key = os.getenv("OPENAI_API_KEY", self.valves.openai_api_key)
            if api_key:
                self.openai_client = AsyncOpenAI(
                    api_key=api_key, base_url=self.valves.openai_api_base
                )
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("No OpenAI API key found - using mock mode")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None

    async def on_shutdown(self):
        """Cleanup on shutdown"""
        logger.info(f"Shutting down {self.name}")

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> AsyncGenerator[str, None]:
        """Convert recipe data to JSON"""

        messages = body.get("messages", [])
        if not messages:
            yield "No messages provided"
            return

        last_message = messages[-1]
        user_input = last_message.get("content", "")

        # Process the input to create JSON
        try:
            json_result = await self.convert_to_json(user_input)

            # Create downloadable JSON response
            response = f"""## Recipe Data Converted to JSON

Here's your recipe data in JSON format:

```json
{json.dumps(json_result, indent=2)}
```

**Download Instructions:**
1. Copy the JSON content above
2. Save it as a .json file
3. Or use the browser's download feature if available

Total items processed: {len(json_result.get('recipes', []))}
"""
            yield response

        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            yield f"❌ Error processing your request: {str(e)}"

    async def convert_to_json(self, user_input: str) -> Dict[str, Any]:
        """Convert user input to structured JSON using OpenAI or mock data"""

        if self.openai_client:
            return await self.convert_with_openai(user_input)
        else:
            return await self.create_mock_json(user_input)

    async def convert_with_openai(self, user_input: str) -> Dict[str, Any]:
        """Use OpenAI to convert input to structured JSON"""

        prompt = f"""
        Convert the following recipe data into a well-structured JSON format.
        
        Instructions:
        1. Extract any recipes, ingredients, or cooking instructions
        2. Structure the data with proper fields like name, ingredients, instructions, servings, etc.
        3. If the input contains multiple recipes, create an array
        4. Add any missing standard fields with reasonable defaults
        5. Return only valid JSON
        
        Input data:
        {user_input}
        
        Return the data as a JSON object with this structure:
        {{
            "recipes": [
                {{
                    "name": "Recipe Name",
                    "ingredients": ["ingredient1", "ingredient2"],
                    "instructions": ["step1", "step2"],
                    "servings": number,
                    "prep_time": "time",
                    "cook_time": "time",
                    "difficulty": "easy/medium/hard",
                    "cuisine": "cuisine type"
                }}
            ],
            "metadata": {{
                "total_recipes": number,
                "processed_at": "timestamp",
                "source": "user_input"
            }}
        }}
        """

        try:
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model=self.valves.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a recipe data conversion expert. Return only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.valves.temperature,
                ),
                timeout=30.0,
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON if wrapped in markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()

            return json.loads(content)

        except Exception as e:
            logger.error(f"OpenAI conversion failed: {e}")
            return await self.create_mock_json(user_input)

    async def create_mock_json(self, user_input: str) -> Dict[str, Any]:
        """Create mock JSON structure when OpenAI is not available"""

        # Simple parsing - look for recipe-like content
        lines = user_input.split("\n")

        mock_recipe = {
            "name": "User Recipe",
            "ingredients": [],
            "instructions": [],
            "servings": 4,
            "prep_time": "15 mins",
            "cook_time": "30 mins",
            "difficulty": "medium",
            "cuisine": "international",
        }

        # Basic parsing
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:
                if any(
                    word in line.lower()
                    for word in ["cup", "tsp", "tbsp", "oz", "lb", "kg", "gram"]
                ):
                    mock_recipe["ingredients"].append(line)
                elif any(
                    word in line.lower()
                    for word in ["cook", "bake", "mix", "heat", "add", "stir"]
                ):
                    mock_recipe["instructions"].append(line)

        # If no ingredients/instructions found, use the input as-is
        if not mock_recipe["ingredients"] and not mock_recipe["instructions"]:
            mock_recipe["ingredients"] = ["Ingredients extracted from user input"]
            mock_recipe["instructions"] = [
                user_input[:200] + "..." if len(user_input) > 200 else user_input
            ]

        return {
            "recipes": [mock_recipe],
            "metadata": {
                "total_recipes": 1,
                "processed_at": datetime.now().isoformat(),
                "source": "user_input",
                "processing_mode": "mock",
            },
        }
