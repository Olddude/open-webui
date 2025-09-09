"""
title: Agentic Reasoning Pipeline
author: Open WebUI
description: A pipeline that provides multi-step reasoning, task decomposition, and agentic workflow capabilities.
requirements: pydantic
"""

from typing import List, Dict, Any, Optional, Generator, Union
import asyncio
import json
import time
from datetime import datetime
from pydantic import BaseModel


class TaskStep(BaseModel):
    id: str
    title: str
    description: str
    status: str = "pending"  # pending, planning, executing, completed, failed
    progress: int = 0
    dependencies: List[str] = []
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ReasoningStep(BaseModel):
    id: str
    type: str  # thinking, decision, analysis, strategy
    content: str
    timestamp: datetime
    confidence: Optional[float] = None
    alternatives: List[str] = []
    selected: Optional[bool] = None


class AgenticPlan(BaseModel):
    id: str
    title: str
    description: str
    tasks: List[TaskStep] = []
    reasoning: List[ReasoningStep] = []
    status: str = "planning"
    created_at: datetime


class Pipeline:
    class Valves(BaseModel):
        # Pipeline configuration
        enable_reasoning_display: bool = True
        enable_task_decomposition: bool = True
        max_reasoning_steps: int = 10
        enable_parallel_execution: bool = True
        reasoning_model: str = "gpt-4o-mini"
        task_execution_timeout: int = 300  # 5 minutes

    def __init__(self):
        self.name = "Agentic Reasoning Pipeline"
        self.valves = self.Valves()
        self.plans: Dict[str, AgenticPlan] = {}

    async def on_startup(self):
        """Initialize the pipeline"""
        print(f"Starting {self.name}")

    async def on_shutdown(self):
        """Cleanup on shutdown"""
        print(f"Shutting down {self.name}")

    async def on_valves_updated(self):
        """Handle configuration updates"""
        print("Pipeline configuration updated")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests and add agentic capabilities"""

        # Check if this is an agentic request
        messages = body.get("messages", [])
        if not messages:
            return body

        last_message = messages[-1]
        user_input = last_message.get("content", "")

        # Detect if we should use agentic processing
        agentic_triggers = [
            "plan",
            "break down",
            "step by step",
            "analyze",
            "create a strategy",
            "multiple steps",
            "complex task",
        ]

        should_use_agentic = any(
            trigger in user_input.lower() for trigger in agentic_triggers
        )

        if should_use_agentic and self.valves.enable_task_decomposition:
            # Create an agentic plan
            plan = await self.create_plan(user_input, user)

            # Add reasoning steps to the response
            if self.valves.enable_reasoning_display:
                reasoning_message = self.format_reasoning_for_ui(plan)
                messages.append(reasoning_message)

            # Add task breakdown to the response
            task_message = self.format_tasks_for_ui(plan)
            messages.append(task_message)

            body["messages"] = messages
            body["agentic_plan_id"] = plan.id

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses and enhance with agentic data"""

        plan_id = body.get("agentic_plan_id")
        if not plan_id or plan_id not in self.plans:
            return body

        plan = self.plans[plan_id]

        # Update plan status
        plan.status = "executing"

        # Add agentic metadata to response
        if "choices" in body and body["choices"]:
            choice = body["choices"][0]
            if "message" in choice:
                choice["message"]["agentic_data"] = {
                    "plan_id": plan.id,
                    "tasks": [task.dict() for task in plan.tasks],
                    "reasoning": [step.dict() for step in plan.reasoning],
                    "status": plan.status,
                }

        return body

    async def create_plan(
        self, user_input: str, user: Optional[dict] = None
    ) -> AgenticPlan:
        """Create an agentic plan with reasoning and task decomposition"""

        plan_id = f"plan_{int(time.time())}"
        plan = AgenticPlan(
            id=plan_id,
            title=f"Plan for: {user_input[:50]}...",
            description=user_input,
            created_at=datetime.now(),
        )

        # Add reasoning steps
        if self.valves.enable_reasoning_display:
            await self.add_reasoning_steps(plan, user_input)

        # Decompose into tasks
        if self.valves.enable_task_decomposition:
            await self.decompose_into_tasks(plan, user_input)

        self.plans[plan_id] = plan
        return plan

    async def add_reasoning_steps(self, plan: AgenticPlan, user_input: str):
        """Add reasoning steps to the plan"""

        reasoning_steps = [
            ReasoningStep(
                id=f"reason_1_{plan.id}",
                type="thinking",
                content=f"Analyzing the request: '{user_input}'. This appears to be a complex task that would benefit from structured planning.",
                timestamp=datetime.now(),
                confidence=0.9,
            ),
            ReasoningStep(
                id=f"reason_2_{plan.id}",
                type="analysis",
                content="Breaking down the request into component parts to identify key requirements and dependencies.",
                timestamp=datetime.now(),
                confidence=0.85,
            ),
            ReasoningStep(
                id=f"reason_3_{plan.id}",
                type="strategy",
                content="Selecting an incremental approach with clear milestones to ensure progress can be tracked and validated.",
                timestamp=datetime.now(),
                confidence=0.8,
                alternatives=["Parallel execution approach", "Waterfall approach"],
                selected=True,
            ),
        ]

        plan.reasoning.extend(reasoning_steps)

    async def decompose_into_tasks(self, plan: AgenticPlan, user_input: str):
        """Decompose the request into actionable tasks"""

        # Simple task decomposition logic (can be enhanced with LLM)
        if "write" in user_input.lower() or "create" in user_input.lower():
            tasks = [
                TaskStep(
                    id=f"task_1_{plan.id}",
                    title="Research and Planning",
                    description="Gather requirements and create outline",
                    status="pending",
                ),
                TaskStep(
                    id=f"task_2_{plan.id}",
                    title="Implementation",
                    description="Create the requested content/code",
                    status="pending",
                    dependencies=[f"task_1_{plan.id}"],
                ),
                TaskStep(
                    id=f"task_3_{plan.id}",
                    title="Review and Refinement",
                    description="Test and refine the output",
                    status="pending",
                    dependencies=[f"task_2_{plan.id}"],
                ),
            ]
        else:
            # Generic task breakdown
            tasks = [
                TaskStep(
                    id=f"task_1_{plan.id}",
                    title="Understanding",
                    description="Analyze and understand the request",
                    status="pending",
                ),
                TaskStep(
                    id=f"task_2_{plan.id}",
                    title="Execution",
                    description="Execute the requested action",
                    status="pending",
                    dependencies=[f"task_1_{plan.id}"],
                ),
            ]

        plan.tasks.extend(tasks)

    def format_reasoning_for_ui(self, plan: AgenticPlan) -> dict:
        """Format reasoning steps for UI consumption"""
        return {
            "role": "assistant",
            "content": "",
            "agentic_type": "reasoning",
            "agentic_data": {
                "plan_id": plan.id,
                "reasoning_steps": [step.dict() for step in plan.reasoning],
            },
        }

    def format_tasks_for_ui(self, plan: AgenticPlan) -> dict:
        """Format task breakdown for UI consumption"""
        return {
            "role": "assistant",
            "content": "",
            "agentic_type": "task_planning",
            "agentic_data": {
                "plan_id": plan.id,
                "tasks": [task.dict() for task in plan.tasks],
                "plan_status": plan.status,
            },
        }

    async def update_task_progress(
        self, plan_id: str, task_id: str, progress: int, status: str = None
    ):
        """Update task progress"""
        if plan_id in self.plans:
            plan = self.plans[plan_id]
            for task in plan.tasks:
                if task.id == task_id:
                    task.progress = progress
                    if status:
                        task.status = status
                    if status == "executing" and not task.start_time:
                        task.start_time = datetime.now()
                    elif status in ["completed", "failed"]:
                        task.end_time = datetime.now()
                    break
