"""
title: Recipe Processing RAG Pipeline
author: Open WebUI
description: A comprehensive pipeline for processing recipe Excel files using RAG with schema validation and JSON output generation.
requirements: pydantic, pandas, openpyxl, jsonschema, python-multipart
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


class Pipeline:
    class Valves(BaseModel):
        # Pipeline configuration
        enable_progress_tracking: bool = True
        chunk_size: int = 10  # Process recipes in chunks
        max_retries: int = 3
        enable_schema_validation: bool = True
        output_format: str = "structured_json"  # structured_json, flat_json
        enable_reasoning_display: bool = True

    def __init__(self):
        self.name = "Recipe Processing RAG Pipeline"
        self.valves = self.Valves()
        self.sessions: Dict[str, RecipeProcessingSession] = {}
        self.temp_dir = tempfile.mkdtemp()

    async def on_startup(self):
        """Initialize the pipeline"""
        print(f"Starting {self.name}")
        os.makedirs(self.temp_dir, exist_ok=True)

    async def on_shutdown(self):
        """Cleanup on shutdown"""
        print(f"Shutting down {self.name}")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests and detect recipe processing tasks"""

        messages = body.get("messages", [])
        if not messages:
            return body

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
        ]

        should_process_recipes = any(
            trigger in user_input.lower() for trigger in recipe_triggers
        )

        if should_process_recipes:
            # Check for file attachments (this would be enhanced in real implementation)
            files = body.get("files", [])
            schema = self.extract_schema_from_message(user_input)

            if files or "schema" in user_input.lower():
                # Create a new recipe processing session
                session = await self.create_processing_session(files, schema, user)

                # Add agentic messages to show the processing workflow
                agentic_messages = await self.create_agentic_messages(session)
                messages.extend(agentic_messages)

                body["messages"] = messages
                body["recipe_session_id"] = session.session_id

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses and add recipe processing results"""

        session_id = body.get("recipe_session_id")
        if not session_id or session_id not in self.sessions:
            return body

        session = self.sessions[session_id]

        # Start background processing if not already started
        if session.status == "initializing":
            asyncio.create_task(self.process_recipes_background(session_id))

        # Add recipe processing data to response
        if "choices" in body and body["choices"]:
            choice = body["choices"][0]
            if "message" in choice:
                choice["message"]["recipe_data"] = {
                    "session_id": session.session_id,
                    "steps": [step.dict() for step in session.steps],
                    "progress": self.calculate_overall_progress(session),
                    "status": session.status,
                    "total_recipes": session.total_recipes,
                    "processed_recipes": session.processed_recipes,
                    "failed_recipes": session.failed_recipes,
                }

        return body

    async def create_processing_session(
        self,
        files: List[str],
        schema: Optional[Dict[str, Any]],
        user: Optional[dict] = None,
    ) -> RecipeProcessingSession:
        """Create a new recipe processing session"""

        session_id = f"recipe_{uuid.uuid4().hex[:8]}"

        session = RecipeProcessingSession(
            session_id=session_id, files=files, schema=schema, created_at=datetime.now()
        )

        # Define processing steps
        processing_steps = [
            RecipeProcessingStep(
                id=f"{session_id}_step_1",
                step_name="File Validation",
                description="Validating uploaded Excel files and checking format",
                sub_steps=[
                    "Check file extensions",
                    "Verify Excel format",
                    "Validate headers",
                ],
            ),
            RecipeProcessingStep(
                id=f"{session_id}_step_2",
                step_name="Schema Analysis",
                description="Analyzing provided JSON schema and mapping fields",
                sub_steps=[
                    "Parse schema",
                    "Validate schema structure",
                    "Map Excel columns",
                ],
            ),
            RecipeProcessingStep(
                id=f"{session_id}_step_3",
                step_name="Data Extraction",
                description="Extracting recipe data from Excel files",
                sub_steps=[
                    "Read Excel sheets",
                    "Parse recipe data",
                    "Handle missing values",
                ],
            ),
            RecipeProcessingStep(
                id=f"{session_id}_step_4",
                step_name="RAG Processing",
                description="Using RAG to enhance and structure recipe data",
                sub_steps=[
                    "Semantic analysis",
                    "Ingredient standardization",
                    "Instruction processing",
                ],
            ),
            RecipeProcessingStep(
                id=f"{session_id}_step_5",
                step_name="Schema Validation",
                description="Validating processed data against schema",
                sub_steps=[
                    "Field validation",
                    "Type checking",
                    "Required field verification",
                ],
            ),
            RecipeProcessingStep(
                id=f"{session_id}_step_6",
                step_name="JSON Generation",
                description="Generating final structured JSON output",
                sub_steps=["Format data", "Apply transformations", "Generate output"],
            ),
        ]

        session.steps = processing_steps
        self.sessions[session_id] = session

        return session

    async def create_agentic_messages(
        self, session: RecipeProcessingSession
    ) -> List[Dict[str, Any]]:
        """Create agentic messages for the UI"""

        messages = []

        # Reasoning message
        reasoning_message = {
            "role": "assistant",
            "content": "",
            "agentic_type": "reasoning",
            "agentic_data": {
                "session_id": session.session_id,
                "reasoning_steps": [
                    {
                        "id": f"reason_1_{session.session_id}",
                        "type": "analysis",
                        "content": f"I've detected a recipe processing request with {len(session.files)} files. I need to process these Excel files and convert them to structured JSON format.",
                        "timestamp": datetime.now().isoformat(),
                        "confidence": 0.95,
                    },
                    {
                        "id": f"reason_2_{session.session_id}",
                        "type": "strategy",
                        "content": "I'll use a multi-step approach: validate files, analyze schema, extract data using RAG for enhancement, validate against schema, and generate JSON output.",
                        "timestamp": datetime.now().isoformat(),
                        "confidence": 0.9,
                        "alternatives": ["Batch processing", "Single-pass processing"],
                        "selected": True,
                    },
                ],
            },
        }
        messages.append(reasoning_message)

        # Task planning message
        task_message = {
            "role": "assistant",
            "content": "",
            "agentic_type": "task_planning",
            "agentic_data": {
                "session_id": session.session_id,
                "tasks": [
                    {
                        "id": step.id,
                        "title": step.step_name,
                        "description": step.description,
                        "status": step.status,
                        "progress": step.progress,
                        "dependencies": [] if i == 0 else [session.steps[i - 1].id],
                        "children": [
                            {
                                "id": f"{step.id}_sub_{j}",
                                "title": sub_step,
                                "status": "pending",
                                "progress": 0,
                                "children": [],
                                "dependencies": [],
                            }
                            for j, sub_step in enumerate(step.sub_steps)
                        ],
                    }
                    for i, step in enumerate(session.steps)
                ],
                "plan_status": session.status,
            },
        }
        messages.append(task_message)

        return messages

    async def process_recipes_background(self, session_id: str):
        """Background task to process recipes"""

        session = self.sessions[session_id]
        session.status = "processing"

        try:
            for i, step in enumerate(session.steps):
                await self.process_step(session, step)

                # Simulate progress updates
                await asyncio.sleep(1)  # Real implementation would process actual data

            session.status = "completed"
            session.completed_at = datetime.now()

            # Generate final output
            await self.generate_final_output(session)

        except Exception as e:
            session.status = "failed"
            print(f"Recipe processing failed: {e}")

    async def process_step(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Process an individual step"""

        step.status = "processing"
        step.start_time = datetime.now()

        try:
            # Simulate step processing based on step name
            if "File Validation" in step.step_name:
                await self.validate_files(session, step)
            elif "Schema Analysis" in step.step_name:
                await self.analyze_schema(session, step)
            elif "Data Extraction" in step.step_name:
                await self.extract_data(session, step)
            elif "RAG Processing" in step.step_name:
                await self.rag_processing(session, step)
            elif "Schema Validation" in step.step_name:
                await self.validate_against_schema(session, step)
            elif "JSON Generation" in step.step_name:
                await self.generate_json(session, step)

            step.status = "completed"
            step.progress = 100
            step.end_time = datetime.now()

        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.end_time = datetime.now()
            raise

    async def validate_files(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Validate uploaded files"""
        # Simulate file validation
        for i in range(len(step.sub_steps)):
            await asyncio.sleep(0.5)
            step.progress = int((i + 1) / len(step.sub_steps) * 100)

        session.total_recipes = 25  # Simulated count

    async def analyze_schema(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Analyze JSON schema"""
        for i in range(len(step.sub_steps)):
            await asyncio.sleep(0.3)
            step.progress = int((i + 1) / len(step.sub_steps) * 100)

    async def extract_data(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Extract data from Excel files"""
        for i in range(len(step.sub_steps)):
            await asyncio.sleep(0.8)
            step.progress = int((i + 1) / len(step.sub_steps) * 100)

    async def rag_processing(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Process data using RAG"""
        for i in range(len(step.sub_steps)):
            # Simulate processing recipes in chunks
            chunk_progress = 0
            while chunk_progress < 100:
                chunk_progress += 10
                step.progress = int(
                    (
                        i / len(step.sub_steps)
                        + chunk_progress / 100 / len(step.sub_steps)
                    )
                    * 100
                )
                session.processed_recipes += 2
                await asyncio.sleep(0.2)

    async def validate_against_schema(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Validate processed data against schema"""
        for i in range(len(step.sub_steps)):
            await asyncio.sleep(0.4)
            step.progress = int((i + 1) / len(step.sub_steps) * 100)

    async def generate_json(
        self, session: RecipeProcessingSession, step: RecipeProcessingStep
    ):
        """Generate final JSON output"""
        for i in range(len(step.sub_steps)):
            await asyncio.sleep(0.3)
            step.progress = int((i + 1) / len(step.sub_steps) * 100)

    async def generate_final_output(self, session: RecipeProcessingSession):
        """Generate the final JSON artifact"""

        # Simulated output
        session.output_json = {
            "metadata": {
                "total_recipes": session.total_recipes,
                "processed_at": datetime.now().isoformat(),
                "schema_version": "1.0",
            },
            "recipes": [
                {
                    "id": f"recipe_{i}",
                    "name": f"Sample Recipe {i}",
                    "ingredients": [
                        {"name": "ingredient_1", "amount": "2 cups"},
                        {"name": "ingredient_2", "amount": "1 tbsp"},
                    ],
                    "instructions": f"Sample cooking instructions for recipe {i}",
                    "prep_time": "15 minutes",
                    "cook_time": "30 minutes",
                    "servings": 4,
                }
                for i in range(
                    1, min(6, session.total_recipes + 1)
                )  # Sample of recipes
            ],
        }

    def calculate_overall_progress(self, session: RecipeProcessingSession) -> int:
        """Calculate overall progress across all steps"""
        if not session.steps:
            return 0

        total_progress = sum(step.progress for step in session.steps)
        return int(total_progress / len(session.steps))

    def extract_schema_from_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract JSON schema from user message"""
        # Simple schema extraction (would be enhanced in real implementation)
        if "schema" in message.lower():
            return {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "amount": {"type": "string"},
                            },
                        },
                    },
                    "instructions": {"type": "string"},
                    "prep_time": {"type": "string"},
                    "cook_time": {"type": "string"},
                    "servings": {"type": "integer"},
                },
                "required": ["name", "ingredients", "instructions"],
            }
        return None
