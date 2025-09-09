"""
title: Recipe RAG Processing Function
author: Open WebUI
description: A comprehensive function for processing recipe data using RAG with OpenAI integration
requirements: pandas, openpyxl, jsonschema, openai
"""

from typing import List, Dict, Any, Optional, Generator, Union
import asyncio
import json
import time
import pandas as pd
import os
from datetime import datetime
from pydantic import BaseModel
from jsonschema import validate, ValidationError
import tempfile
import uuid
import logging
import traceback
from openai import AsyncOpenAI
import base64
from io import BytesIO

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecipeProcessingStep(BaseModel):
    id: str
    step_name: str
    description: str
    status: str = "pending"  # pending, processing, completed, failed
    progress: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    sub_steps: List[str] = []


class RecipeProcessingSession(BaseModel):
    session_id: str
    files: List[str] = []
    schema: Optional[Dict[str, Any]] = None
    steps: List[RecipeProcessingStep] = []
    total_recipes: int = 0
    processed_recipes: int = 0
    failed_recipes: int = 0
    output_json: Optional[Dict[str, Any]] = None
    status: str = "initializing"  # initializing, processing, completed, failed
    created_at: datetime
    completed_at: Optional[datetime] = None


class Pipe:
    class Valves(BaseModel):
        # Pipeline configuration
        enable_progress_tracking: bool = True
        chunk_size: int = 10  # Process recipes in chunks
        max_retries: int = 3
        enable_schema_validation: bool = True
        output_format: str = "structured_json"  # structured_json, flat_json
        enable_reasoning_display: bool = True
        openai_api_key: str = ""  # Will be set from env
        openai_api_base: str = "https://api.openai.com/v1"
        openai_model: str = "gpt-4o-mini"
        temperature: float = 0.7

    def __init__(self):
        self.name = "Recipe RAG Processing Function"
        self.valves = self.Valves()
        self.sessions: Dict[str, RecipeProcessingSession] = {}
        self.openai_client: Optional[AsyncOpenAI] = None
        self.recipe_data_cache: Dict[str, List[Dict]] = {}

    async def on_startup(self):
        """Initialize the function"""
        logger.info(f"Starting {self.name}")

        # Initialize OpenAI client
        try:
            # Try to get API key from environment or config
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
    ) -> Union[str, Generator, Iterator]:
        """Main processing function for the RAG pipeline"""

        messages = body.get("messages", [])
        if not messages:
            return "No messages provided"

        last_message = messages[-1]
        user_input = last_message.get("content", "")

        # Detect recipe processing requests
        recipe_triggers = [
            "process recipe",
            "recipe excel",
            "convert recipe",
            "parse recipe",
            "recipe data",
            "excel to json",
            "recipe schema",
            "bulk recipe",
            "rag recipe",
            "recipe rag",
        ]

        should_process_recipes = any(
            trigger in user_input.lower() for trigger in recipe_triggers
        )

        if should_process_recipes:
            # Create a processing session
            session = await self.create_processing_session(user_input, __user__)

            # Start processing
            processing_result = await self.process_recipes(session, __event_emitter__)

            # Format the response
            response = self.format_response(session, processing_result)

            # Stream the response
            if body.get("stream", False):
                for chunk in response:
                    yield chunk
            else:
                yield response
        else:
            # Pass through for non-recipe requests
            yield "I can help you process recipe data using RAG. Try asking me to 'process recipes' or 'convert recipe data to JSON'."

    async def create_processing_session(
        self,
        user_input: str,
        user: Optional[dict] = None,
    ) -> RecipeProcessingSession:
        """Create a new recipe processing session"""

        session_id = f"recipe_{uuid.uuid4().hex[:8]}"

        session = RecipeProcessingSession(
            session_id=session_id, created_at=datetime.now()
        )

        # Define processing steps
        processing_steps = [
            RecipeProcessingStep(
                id=f"{session_id}_step_1",
                step_name="Input Analysis",
                description="Analyzing input and extracting requirements",
                sub_steps=[
                    "Parse user request",
                    "Identify data sources",
                    "Extract schema requirements",
                ],
            ),
            RecipeProcessingStep(
                id=f"{session_id}_step_2",
                step_name="Data Preparation",
                description="Preparing recipe data for RAG processing",
                sub_steps=[
                    "Load sample data",
                    "Clean and normalize",
                    "Prepare for enhancement",
                ],
            ),
            RecipeProcessingStep(
                id=f"{session_id}_step_3",
                step_name="RAG Enhancement",
                description="Using RAG to enhance and structure recipe data",
                sub_steps=[
                    "Semantic analysis",
                    "Ingredient standardization",
                    "Instruction processing",
                    "Nutritional enrichment",
                ],
            ),
            RecipeProcessingStep(
                id=f"{session_id}_step_4",
                step_name="Output Generation",
                description="Generating structured output",
                sub_steps=[
                    "Format data",
                    "Apply transformations",
                    "Generate final JSON",
                ],
            ),
        ]

        session.steps = processing_steps
        self.sessions[session_id] = session

        return session

    async def process_recipes(
        self, session: RecipeProcessingSession, event_emitter=None
    ) -> Dict[str, Any]:
        """Process recipes through the RAG pipeline"""

        session.status = "processing"
        results = {}

        try:
            for step in session.steps:
                # Emit progress event
                if event_emitter:
                    await event_emitter(
                        {
                            "type": "status",
                            "data": {
                                "description": f"Processing: {step.step_name}",
                                "done": False,
                            },
                        }
                    )

                # Process the step
                await self.process_step(session, step)

                # Update progress
                completed_steps = sum(
                    1 for s in session.steps if s.status == "completed"
                )
                progress = (completed_steps / len(session.steps)) * 100

                if event_emitter:
                    await event_emitter(
                        {"type": "progress", "data": {"percentage": progress}}
                    )

            session.status = "completed"
            session.completed_at = datetime.now()

            # Generate final output
            results = await self.generate_final_output(session)

        except Exception as e:
            session.status = "failed"
            logger.error(f"Recipe processing failed: {e}")
            results = {"error": str(e)}

        return results

    async def process_step(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Process an individual step"""

        step.status = "processing"
        step.start_time = datetime.now()

        try:
            if "Input Analysis" in step.step_name:
                await self.analyze_input(session, step)
            elif "Data Preparation" in step.step_name:
                await self.prepare_data(session, step)
            elif "RAG Enhancement" in step.step_name:
                await self.rag_enhancement(session, step)
            elif "Output Generation" in step.step_name:
                await self.generate_output(session, step)

            step.status = "completed"
            step.progress = 100
            step.end_time = datetime.now()

        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.end_time = datetime.now()
            raise

    async def analyze_input(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Analyze input requirements"""
        # Simulate analysis
        step.progress = 50
        await asyncio.sleep(0.5)
        step.progress = 100
        logger.info("Input analysis completed")

    async def prepare_data(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Prepare recipe data"""
        try:
            step.progress = 20

            # Sample recipe data for demonstration
            sample_recipes = [
                {
                    "name": "Spaghetti Carbonara",
                    "ingredients": "400g spaghetti, 200g pancetta, 4 eggs, 100g parmesan, black pepper, salt",
                    "instructions": "Cook pasta. Fry pancetta. Mix eggs with cheese. Combine all together.",
                    "prep_time": "10 mins",
                    "cook_time": "20 mins",
                },
                {
                    "name": "Chicken Stir Fry",
                    "ingredients": "500g chicken breast, 2 bell peppers, 1 onion, 3 cloves garlic, soy sauce, ginger, oil",
                    "instructions": "Cut chicken and vegetables. Heat wok. Stir fry chicken then vegetables. Add sauce.",
                    "prep_time": "15 mins",
                    "cook_time": "15 mins",
                },
                {
                    "name": "Chocolate Chip Cookies",
                    "ingredients": "225g butter, 200g sugar, 2 eggs, 280g flour, 1 tsp vanilla, 340g chocolate chips",
                    "instructions": "Mix butter and sugar. Add eggs. Mix in flour. Add chocolate chips. Bake at 180C.",
                    "prep_time": "20 mins",
                    "cook_time": "12 mins",
                },
            ]

            step.progress = 60
            self.recipe_data_cache[session.session_id] = sample_recipes
            session.total_recipes = len(sample_recipes)

            step.progress = 100
            logger.info(f"Prepared {len(sample_recipes)} recipes")

        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            raise

    async def rag_enhancement(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Enhance recipes using RAG"""
        try:
            recipes = self.recipe_data_cache.get(session.session_id, [])
            if not recipes:
                logger.warning("No recipes found in cache")
                return

            enhanced_recipes = []

            for idx, recipe in enumerate(recipes):
                # Update progress
                progress = int((idx / len(recipes)) * 100)
                step.progress = progress

                # Enhance recipe with OpenAI (or use mock enhancement)
                enhanced = await self.enhance_recipe_with_rag(recipe)
                enhanced_recipes.append(enhanced)
                session.processed_recipes += 1

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.2)

            # Store enhanced recipes
            self.recipe_data_cache[f"{session.session_id}_enhanced"] = enhanced_recipes
            step.progress = 100
            logger.info(f"Enhanced {len(enhanced_recipes)} recipes with RAG")

        except Exception as e:
            logger.error(f"Error in RAG enhancement: {e}")
            raise

    async def enhance_recipe_with_rag(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a single recipe using RAG"""
        if not self.openai_client:
            # Mock enhancement if no OpenAI client
            return {
                **recipe,
                "enhanced": True,
                "servings": 4,
                "difficulty": "medium",
                "cuisine": (
                    "Italian"
                    if "pasta" in recipe.get("name", "").lower()
                    else "International"
                ),
                "dietary_info": "Contains gluten and dairy",
            }

        try:
            prompt = f"""
            Enhance this recipe with additional information:
            
            Name: {recipe.get('name', '')}
            Ingredients: {recipe.get('ingredients', '')}
            Instructions: {recipe.get('instructions', '')}
            
            Provide:
            1. Properly formatted ingredients list
            2. Detailed step-by-step instructions
            3. Servings, difficulty level, cuisine type
            4. Brief nutritional highlights
            
            Return as JSON.
            """

            response = await self.openai_client.chat.completions.create(
                model=self.valves.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a recipe enhancement expert.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.valves.temperature,
            )

            enhanced_data = json.loads(response.choices[0].message.content)
            return enhanced_data

        except Exception as e:
            logger.error(f"OpenAI enhancement failed: {e}")
            # Return original recipe on error
            return recipe

    async def generate_output(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Generate final output"""
        step.progress = 50
        await asyncio.sleep(0.3)
        step.progress = 100
        logger.info("Output generation completed")

    async def generate_final_output(
        self, session: RecipeProcessingSession
    ) -> Dict[str, Any]:
        """Generate the final JSON output"""
        try:
            # Get enhanced recipes from cache
            enhanced_recipes = self.recipe_data_cache.get(
                f"{session.session_id}_enhanced",
                self.recipe_data_cache.get(session.session_id, []),
            )

            # Format final output
            output = {
                "metadata": {
                    "total_recipes": len(enhanced_recipes),
                    "processed_recipes": session.processed_recipes,
                    "processing_method": (
                        "RAG Enhanced" if self.openai_client else "Mock Mode"
                    ),
                    "processed_at": datetime.now().isoformat(),
                },
                "recipes": enhanced_recipes,
                "session": {
                    "id": session.session_id,
                    "status": session.status,
                    "created_at": session.created_at.isoformat(),
                    "completed_at": (
                        session.completed_at.isoformat()
                        if session.completed_at
                        else None
                    ),
                },
            }

            session.output_json = output
            return output

        except Exception as e:
            logger.error(f"Error generating final output: {e}")
            return {"error": str(e)}

    def format_response(
        self, session: RecipeProcessingSession, results: Dict[str, Any]
    ) -> str:
        """Format the response for the user"""
        if "error" in results:
            return f"❌ Recipe processing failed: {results['error']}"

        metadata = results.get("metadata", {})
        recipes = results.get("recipes", [])

        response = f"""
✅ **Recipe RAG Processing Completed**

📊 **Processing Summary:**
- Total Recipes Processed: {metadata.get('total_recipes', 0)}
- Processing Method: {metadata.get('processing_method', 'Unknown')}
- Session ID: {session.session_id}

📝 **Sample Recipes Processed:**
"""

        for i, recipe in enumerate(recipes[:3], 1):
            response += f"\n{i}. **{recipe.get('name', 'Unnamed Recipe')}**"
            if recipe.get("enhanced"):
                response += f"\n   - Servings: {recipe.get('servings', 'N/A')}"
                response += f"\n   - Difficulty: {recipe.get('difficulty', 'N/A')}"
                response += f"\n   - Cuisine: {recipe.get('cuisine', 'N/A')}"

        response += f"\n\n📦 **Full JSON Output:**\n```json\n{json.dumps(results, indent=2)[:1000]}...\n```"

        return response
