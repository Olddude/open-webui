"""
title: Recipe Processing Function
author: open-webui
description: Process Excel recipe files and convert to structured JSON with agentic UI integration
required_packages:
- pandas
- openpyxl
- jsonschema
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class Tools:
    def __init__(self):
        pass


def main(
    body: dict,
    __user__: dict,
    __event_emitter__: callable = None,
    __tools__: Tools = None,
) -> dict:
    """
    Main function called by Open WebUI
    """

    # Extract messages from the request
    messages = body.get("messages", [])
    if not messages:
        return body

    last_message = messages[-1]
    user_input = last_message.get("content", "")

    # Check if this is a recipe processing request
    recipe_triggers = [
        "process recipe",
        "recipe excel",
        "convert recipe",
        "parse recipe",
        "recipe data",
        "excel to json",
        "recipe schema",
        "bulk recipe",
        "recipe processing",
    ]

    should_process_recipes = any(
        trigger in user_input.lower() for trigger in recipe_triggers
    )

    if should_process_recipes:
        print("🧑‍🍳 RECIPE PROCESSING DETECTED!")
        print(f"User input: {user_input}")
        print(f"User: {__user__.get('name', 'Unknown')}")

        # This is where you can set breakpoints!
        # Add: import pdb; pdb.set_trace() here to debug

        # Emit reasoning steps to the UI
        if __event_emitter__:
            emit_reasoning_steps(__event_emitter__, user_input)
            emit_task_planning(__event_emitter__)

            # Simulate processing with progress updates
            asyncio.create_task(simulate_recipe_processing(__event_emitter__))

        # Add recipe processing response
        assistant_message = {
            "role": "assistant",
            "content": "🧑‍🍳 Starting recipe processing pipeline...\n\n"
            + "I've detected your recipe processing request and will now:\n"
            + "1. Validate Excel files\n"
            + "2. Extract recipe data using RAG\n"
            + "3. Apply schema validation\n"
            + "4. Generate structured JSON output\n\n"
            + "Check the Agent Panel for real-time progress updates!",
        }

        messages.append(assistant_message)
        body["messages"] = messages

        print("✅ Recipe processing initiated!")

    return body


def emit_reasoning_steps(__event_emitter__: callable, user_input: str):
    """Emit AI reasoning steps to the frontend"""

    reasoning_steps = [
        {
            "type": "analysis",
            "content": f"Analyzing request: '{user_input}'. Detected recipe processing task requiring multi-step pipeline execution.",
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
        },
        {
            "type": "strategy",
            "content": "Planning approach: File validation → RAG processing → Schema validation → JSON output. Using chunked processing for optimal performance.",
            "confidence": 0.9,
            "alternatives": ["Batch processing", "Single-pass processing"],
            "selected": True,
            "timestamp": datetime.now().isoformat(),
        },
        {
            "type": "thinking",
            "content": "Preparing pipeline components and initializing processing queues. Ready to handle Excel file uploads.",
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat(),
        },
    ]

    # Emit reasoning data to frontend
    __event_emitter__(
        {
            "type": "agent_reasoning",
            "data": {
                "reasoning_steps": reasoning_steps,
                "session_id": f"recipe_{int(datetime.now().timestamp())}",
            },
        }
    )

    print("🧠 Emitted reasoning steps to frontend")


def emit_task_planning(__event_emitter__: callable):
    """Emit task planning data to the frontend"""

    tasks = [
        {
            "id": "task_1",
            "title": "File Validation",
            "description": "Validate uploaded Excel files and check format",
            "status": "pending",
            "progress": 0,
            "dependencies": [],
            "sub_steps": [
                "Check file extensions",
                "Verify Excel format",
                "Validate headers",
            ],
        },
        {
            "id": "task_2",
            "title": "RAG Processing",
            "description": "Extract and enhance recipe data using RAG",
            "status": "pending",
            "progress": 0,
            "dependencies": ["task_1"],
            "sub_steps": [
                "Semantic analysis",
                "Ingredient standardization",
                "Instruction processing",
            ],
        },
        {
            "id": "task_3",
            "title": "Schema Validation",
            "description": "Validate against provided JSON schema",
            "status": "pending",
            "progress": 0,
            "dependencies": ["task_2"],
            "sub_steps": [
                "Field validation",
                "Type checking",
                "Required fields verification",
            ],
        },
        {
            "id": "task_4",
            "title": "JSON Generation",
            "description": "Generate final structured JSON output",
            "status": "pending",
            "progress": 0,
            "dependencies": ["task_3"],
            "sub_steps": ["Format data", "Apply transformations", "Generate output"],
        },
    ]

    __event_emitter__(
        {
            "type": "agent_tasks",
            "data": {
                "tasks": tasks,
                "plan_status": "initializing",
                "session_id": f"recipe_{int(datetime.now().timestamp())}",
            },
        }
    )

    print("📋 Emitted task planning to frontend")


async def simulate_recipe_processing(__event_emitter__: callable):
    """Simulate the recipe processing pipeline with progress updates"""

    print("🔄 Starting simulated recipe processing...")

    # Simulate step 1: File Validation
    await asyncio.sleep(1)
    __event_emitter__(
        {
            "type": "task_update",
            "data": {"task_id": "task_1", "status": "executing", "progress": 50},
        }
    )

    await asyncio.sleep(1)
    __event_emitter__(
        {
            "type": "task_update",
            "data": {"task_id": "task_1", "status": "completed", "progress": 100},
        }
    )

    # Simulate step 2: RAG Processing
    await asyncio.sleep(0.5)
    __event_emitter__(
        {
            "type": "task_update",
            "data": {"task_id": "task_2", "status": "executing", "progress": 25},
        }
    )

    # Simulate incremental progress
    for progress in range(30, 101, 15):
        await asyncio.sleep(0.8)
        __event_emitter__(
            {
                "type": "task_update",
                "data": {
                    "task_id": "task_2",
                    "status": "executing",
                    "progress": progress,
                },
            }
        )

    # Complete remaining tasks
    for task_id in ["task_3", "task_4"]:
        await asyncio.sleep(0.5)
        __event_emitter__(
            {
                "type": "task_update",
                "data": {"task_id": task_id, "status": "executing", "progress": 50},
            }
        )

        await asyncio.sleep(0.5)
        __event_emitter__(
            {
                "type": "task_update",
                "data": {"task_id": task_id, "status": "completed", "progress": 100},
            }
        )

    # Emit final artifact
    await asyncio.sleep(1)
    __event_emitter__(
        {
            "type": "artifact_generated",
            "data": {
                "id": "recipe_output_json",
                "type": "code",
                "title": "recipes_output.json",
                "content": json.dumps(
                    {
                        "metadata": {
                            "total_recipes": 25,
                            "processed_at": datetime.now().isoformat(),
                            "processing_time": "45 seconds",
                            "success_rate": "100%",
                        },
                        "recipes": [
                            {
                                "id": "recipe_001",
                                "name": "Margherita Pizza",
                                "ingredients": [
                                    {"name": "pizza dough", "amount": "1 lb"},
                                    {"name": "tomato sauce", "amount": "1/2 cup"},
                                    {"name": "mozzarella", "amount": "8 oz"},
                                ],
                                "instructions": "Preheat oven to 475°F...",
                                "prep_time": "15 minutes",
                                "cook_time": "15 minutes",
                            }
                        ],
                    },
                    indent=2,
                ),
                "language": "json",
            },
        }
    )

    print("✅ Recipe processing simulation completed!")


# For debugging - add this to set breakpoints
def debug_breakpoint():
    """
    Add this line in your code where you want to break:
    debug_breakpoint()
    """
    import pdb

    pdb.set_trace()


if __name__ == "__main__":
    # Test the function locally
    test_body = {
        "messages": [
            {
                "role": "user",
                "content": "Please process my recipe excel files and convert them to JSON",
            }
        ]
    }

    test_user = {"name": "Test User", "id": "test123"}

    print("Testing recipe processor function...")
    result = main(test_body, test_user)
    print("Result:", json.dumps(result, indent=2))
