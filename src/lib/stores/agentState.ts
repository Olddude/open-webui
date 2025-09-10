import { writable, derived } from 'svelte/store';
import type { Writable } from 'svelte/store';

export interface Task {
	id: string;
	title: string;
	description?: string;
	status: 'pending' | 'planning' | 'executing' | 'completed' | 'failed';
	progress: number;
	parent_id?: string;
	children: Task[];
	dependencies: string[];
	startTime?: Date;
	endTime?: Date;
	error?: string;
	result?: any;
}

export interface ReasoningStep {
	id: string;
	timestamp: Date;
	type: 'thinking' | 'decision' | 'analysis' | 'strategy';
	content: string;
	confidence?: number;
	alternatives?: string[];
	selected?: boolean;
}

export interface ParallelExecution {
	id: string;
	tasks: Task[];
	startTime: Date;
	endTime?: Date;
	status: 'running' | 'completed' | 'failed';
	syncPoints: Date[];
}

export interface Artifact {
	id: string;
	type: 'code' | 'document' | 'diagram' | 'data';
	title: string;
	content: string;
	language?: string;
	version: number;
	createdAt: Date;
	modifiedAt: Date;
	parentMessageId?: string;
}

export interface AgentState {
	isAgenticMode: boolean;
	currentPlan: Task | null;
	activeTasks: Task[];
	taskHistory: Task[];
	reasoningChain: ReasoningStep[];
	parallelExecutions: ParallelExecution[];
	artifacts: Artifact[];
	showReasoningPanel: boolean;
	showTaskPanel: boolean;
	showArtifactsPanel: boolean;
	showPanel: boolean; // Main agent panel visibility
}

const initialState: AgentState = {
	isAgenticMode: true,
	currentPlan: null,
	activeTasks: [],
	taskHistory: [],
	reasoningChain: [],
	parallelExecutions: [],
	artifacts: [],
	showReasoningPanel: true,
	showTaskPanel: true,
	showArtifactsPanel: true,
	showPanel: false // Default to closed
};

export const agentState: Writable<AgentState> = writable(initialState);

// Derived stores for specific views
export const activeTasksCount = derived(
	agentState,
	($state) => $state.activeTasks.filter((t) => t.status === 'executing').length
);

export const completedTasksCount = derived(
	agentState,
	($state) => $state.taskHistory.filter((t) => t.status === 'completed').length
);

export const currentReasoningSteps = derived(
	agentState,
	($state) => $state.reasoningChain.slice(-10) // Last 10 reasoning steps
);

// Actions
export const addTask = (task: Task) => {
	agentState.update((state) => ({
		...state,
		activeTasks: [...state.activeTasks, task]
	}));
};

export const updateTaskStatus = (taskId: string, status: Task['status'], progress?: number) => {
	agentState.update((state) => ({
		...state,
		activeTasks: state.activeTasks.map((task) =>
			task.id === taskId ? { ...task, status, progress: progress ?? task.progress } : task
		)
	}));
};

export const completeTask = (taskId: string, result?: any) => {
	agentState.update((state) => {
		const task = state.activeTasks.find((t) => t.id === taskId);
		if (!task) return state;

		const completedTask = {
			...task,
			status: 'completed' as const,
			progress: 100,
			endTime: new Date(),
			result
		};

		return {
			...state,
			activeTasks: state.activeTasks.filter((t) => t.id !== taskId),
			taskHistory: [...state.taskHistory, completedTask]
		};
	});
};

export const addReasoningStep = (step: ReasoningStep) => {
	agentState.update((state) => ({
		...state,
		reasoningChain: [...state.reasoningChain, step]
	}));
};

export const startParallelExecution = (tasks: Task[]) => {
	const execution: ParallelExecution = {
		id: `parallel-${Date.now()}`,
		tasks,
		startTime: new Date(),
		status: 'running',
		syncPoints: []
	};

	agentState.update((state) => ({
		...state,
		parallelExecutions: [...state.parallelExecutions, execution]
	}));

	return execution.id;
};

export const addArtifact = (artifact: Artifact) => {
	agentState.update((state) => ({
		...state,
		artifacts: [...state.artifacts, artifact]
	}));
};

export const updateArtifact = (artifactId: string, content: string) => {
	agentState.update((state) => ({
		...state,
		artifacts: state.artifacts.map((artifact) =>
			artifact.id === artifactId
				? {
						...artifact,
						content,
						version: artifact.version + 1,
						modifiedAt: new Date()
					}
				: artifact
		)
	}));
};

export const togglePanel = (panel: 'reasoning' | 'task' | 'artifacts') => {
	agentState.update((state) => {
		const key = `show${panel.charAt(0).toUpperCase() + panel.slice(1)}Panel` as keyof AgentState;
		return {
			...state,
			[key]: !state[key]
		};
	});
};

export const toggleAgenticMode = () => {
	agentState.update((state) => ({
		...state,
		isAgenticMode: !state.isAgenticMode
	}));
};

export const resetAgentState = () => {
	agentState.set(initialState);
};

export const loadDemoData = () => {
	const demoTasks: Task[] = [
		{
			id: 'task-1',
			title: 'Analyze User Requirements',
			description: 'Breaking down the user request into actionable components',
			status: 'completed',
			progress: 100,
			children: [],
			dependencies: [],
			startTime: new Date(Date.now() - 30000),
			endTime: new Date(Date.now() - 20000)
		},
		{
			id: 'task-2',
			title: 'Design System Architecture',
			description: 'Creating a scalable architecture plan',
			status: 'executing',
			progress: 75,
			children: [],
			dependencies: ['task-1'],
			startTime: new Date(Date.now() - 20000)
		},
		{
			id: 'task-3',
			title: 'Implement Core Features',
			description: 'Build the main functionality',
			status: 'pending',
			progress: 0,
			children: [],
			dependencies: ['task-2']
		}
	];

	const demoReasoning: ReasoningStep[] = [
		{
			id: 'reason-1',
			type: 'thinking',
			content:
				'The user is asking for a complex system that requires careful planning. I need to break this down into manageable steps.',
			timestamp: new Date(Date.now() - 60000),
			confidence: 0.9
		},
		{
			id: 'reason-2',
			type: 'analysis',
			content:
				'Looking at the requirements, I can identify three main areas: data processing, user interface, and integration layer.',
			timestamp: new Date(Date.now() - 45000),
			confidence: 0.85
		},
		{
			id: 'reason-3',
			type: 'strategy',
			content:
				"I'll use an incremental approach, starting with core functionality and building up complexity.",
			timestamp: new Date(Date.now() - 30000),
			confidence: 0.8,
			alternatives: ['Waterfall approach', 'Parallel development'],
			selected: true
		}
	];

	const demoArtifacts: Artifact[] = [
		{
			id: 'artifact-1',
			type: 'code',
			title: 'main.py',
			content: `#!/usr/bin/env python3
"""
Main application entry point
"""

import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Demo App")

class Task(BaseModel):
    id: str
    title: str
    status: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/tasks")
async def get_tasks():
    return [
        Task(id="1", title="Sample Task", status="completed")
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)`,
			language: 'python',
			version: 1,
			createdAt: new Date(Date.now() - 120000),
			modifiedAt: new Date(Date.now() - 120000)
		},
		{
			id: 'artifact-2',
			type: 'document',
			title: 'Architecture Plan',
			content: `# System Architecture Plan

## Overview
This document outlines the proposed architecture for the new system.

## Components

### 1. API Layer
- FastAPI framework
- RESTful endpoints
- Authentication middleware

### 2. Business Logic
- Service layer pattern
- Domain models
- Use case implementations

### 3. Data Layer
- PostgreSQL database
- SQLAlchemy ORM
- Migration management

## Deployment Strategy
- Docker containers
- Kubernetes orchestration
- CI/CD pipeline with GitHub Actions`,
			version: 1,
			createdAt: new Date(Date.now() - 90000),
			modifiedAt: new Date(Date.now() - 60000)
		}
	];

	agentState.update((state) => ({
		...state,
		activeTasks: demoTasks,
		reasoningChain: demoReasoning,
		artifacts: demoArtifacts,
		currentPlan: {
			id: 'plan-demo',
			title: 'Build Scalable System',
			description: 'Create a comprehensive solution with proper architecture',
			status: 'executing',
			progress: 60,
			children: demoTasks,
			dependencies: [],
			startTime: new Date(Date.now() - 120000)
		}
	}));
};
