import { APP_NAME } from '$lib/constants';
import { type Writable, writable, derived } from 'svelte/store';
import type { ModelConfig } from '$lib/apis';
import type { Banner } from '$lib/types';
import type { Socket } from 'socket.io-client';

import emojiShortCodes from '$lib/emoji-shortcodes.json';

// Backend
export const WEBUI_NAME = writable(APP_NAME);
export const config: Writable<Config | undefined> = writable(undefined);
export const user: Writable<SessionUser | undefined> = writable(undefined);

// Electron App
export const isApp = writable(false);
export const appInfo = writable(null);
export const appData = writable(null);

// Frontend
export const MODEL_DOWNLOAD_POOL = writable({});

export const mobile = writable(false);

export const socket: Writable<null | Socket> = writable(null);
export const activeUserIds: Writable<null | string[]> = writable(null);
export const USAGE_POOL: Writable<null | string[]> = writable(null);

export const theme = writable('system');

export const shortCodesToEmojis = writable(
	Object.entries(emojiShortCodes).reduce((acc, [key, value]) => {
		if (typeof value === 'string') {
			acc[value] = key;
		} else {
			for (const v of value) {
				acc[v] = key;
			}
		}

		return acc;
	}, {})
);

export const TTSWorker = writable(null);

export const chatId = writable('');
export const chatTitle = writable('');

export const channels = writable([]);
export const chats = writable(null);
export const pinnedChats = writable([]);
export const tags = writable([]);

export const selectedFolder = writable(null);

export const models: Writable<Model[]> = writable([]);

export const prompts: Writable<null | Prompt[]> = writable(null);
export const knowledge: Writable<null | Document[]> = writable(null);
export const tools = writable(null);
export const functions = writable(null);

export const toolServers = writable([]);

export const banners: Writable<Banner[]> = writable([]);

export const settings: Writable<Settings> = writable({});

export const showSidebar = writable(false);
export const showSearch = writable(false);
export const showSettings = writable(false);
export const showArchivedChats = writable(false);
export const showChangelog = writable(false);

export const showControls = writable(false);
export const showOverview = writable(false);
export const showArtifacts = writable(false);
export const showCallOverlay = writable(false);

export const artifactCode = writable(null);

export const temporaryChatEnabled = writable(false);
export const scrollPaginationEnabled = writable(false);
export const currentChatPage = writable(1);

export const isLastActiveTab = writable(true);
export const playingNotificationSound = writable(false);

// Agent State Store
const initialAgentState: AgentState = {
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
	showPanel: false, // Default to closed
	activity: {
		status: 'idle',
		currentTask: null
	},
	logs: []
};

export const agentState: Writable<AgentState> = writable(initialAgentState);

// Agent State Derived Stores
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

// Task Queue Store
const initialTaskQueue: TaskQueue = {
	id: `queue-${Date.now()}`,
	name: 'Main Task Queue',
	rootTask: null,
	queue: [],
	running: [],
	completed: [],
	failed: [],
	concurrencyLimit: 3,
	totalTasks: 0,
	completedTasks: 0,
	failedTasks: 0
};

export const taskQueue: Writable<TaskQueue> = writable(initialTaskQueue);

// Task Queue Derived Stores
export const queueProgress = derived(taskQueue, ($queue) => {
	if ($queue.totalTasks === 0) return 0;
	return ($queue.completedTasks / $queue.totalTasks) * 100;
});

export const runningTasks = derived(taskQueue, ($queue) => $queue.running);

export const pendingTasks = derived(taskQueue, ($queue) => $queue.queue);

export const canExecuteMore = derived(
	taskQueue,
	($queue) => $queue.running.length < $queue.concurrencyLimit
);

// Tool Usage Store
const initialToolUsageState: ToolUsageState = {
	activeCalls: [],
	callHistory: [],
	toolChains: [],
	metrics: {
		totalCalls: 0,
		successRate: 100,
		averageDuration: 0,
		callsByType: {},
		callsByTool: {},
		errorRate: 0,
		recentErrors: []
	},
	showToolPanel: true,
	selectedTool: null
};

export const toolUsage: Writable<ToolUsageState> = writable(initialToolUsageState);

// Tool Usage Derived Stores
export const activeToolsCount = derived(toolUsage, ($state) => $state.activeCalls.length);

export const toolSuccessRate = derived(toolUsage, ($state) => $state.metrics.successRate);

export const mostUsedTools = derived(toolUsage, ($state) => {
	const entries = Object.entries($state.metrics.callsByTool);
	return entries
		.sort(([, a], [, b]) => b - a)
		.slice(0, 5)
		.map(([tool, count]) => ({ tool, count }));
});

export const activeToolChains = derived(toolUsage, ($state) =>
	$state.toolChains.filter((chain) => chain.status === 'running')
);

// Agent State Actions
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
	agentState.set(initialAgentState);
};

// Load test data for agent activity
export const loadAgentActivityTestData = () => {
	agentState.update((state) => ({
		...state,
		activity: {
			status: 'active',
			currentTask: 'Analyzing code structure and dependencies'
		},
		logs: [
			{
				id: 'log-1',
				type: 'info',
				message: 'Agent initialized successfully',
				timestamp: new Date(Date.now() - 120000)
			},
			{
				id: 'log-2',
				type: 'success',
				message: 'Connected to language model',
				timestamp: new Date(Date.now() - 110000)
			},
			{
				id: 'log-3',
				type: 'info',
				message: 'Starting code analysis',
				timestamp: new Date(Date.now() - 100000)
			},
			{
				id: 'log-4',
				type: 'warning',
				message: 'Large file detected, processing may take longer',
				timestamp: new Date(Date.now() - 90000)
			},
			{
				id: 'log-5',
				type: 'success',
				message: 'Successfully parsed 42 files',
				timestamp: new Date(Date.now() - 60000)
			},
			{
				id: 'log-6',
				type: 'info',
				message: 'Building dependency graph',
				timestamp: new Date(Date.now() - 30000)
			},
			{
				id: 'log-7',
				type: 'error',
				message: 'Failed to resolve module: @unknown/package',
				timestamp: new Date(Date.now() - 20000)
			},
			{
				id: 'log-8',
				type: 'info',
				message: 'Continuing with partial analysis',
				timestamp: new Date(Date.now() - 10000)
			},
			{
				id: 'log-9',
				type: 'success',
				message: 'Analysis complete - found 3 optimization opportunities',
				timestamp: new Date()
			}
		]
	}));
};

// Update agent activity status
export const updateAgentActivity = (
	status: 'idle' | 'active' | 'processing',
	currentTask: string | null = null
) => {
	agentState.update((state) => ({
		...state,
		activity: {
			status,
			currentTask
		}
	}));
};

// Add a log entry to agent
export const addAgentLog = (type: 'info' | 'warning' | 'error' | 'success', message: string) => {
	agentState.update((state) => ({
		...state,
		logs: [
			...state.logs.slice(-99), // Keep last 100 logs
			{
				id: `log-${Date.now()}`,
				type,
				message,
				timestamp: new Date()
			}
		]
	}));
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

// Task Queue Actions
export const enqueueTask = (task: TaskNode) => {
	taskQueue.update((queue) => ({
		...queue,
		queue: [...queue.queue, task],
		totalTasks: queue.totalTasks + 1
	}));
};

export const enqueueTasks = (tasks: TaskNode[]) => {
	taskQueue.update((queue) => ({
		...queue,
		queue: [...queue.queue, ...tasks],
		totalTasks: queue.totalTasks + tasks.length
	}));
};

export const dequeueTask = (): TaskNode | null => {
	let nextTask: TaskNode | null = null;

	taskQueue.update((queue) => {
		if (queue.queue.length === 0) return queue;

		// Find next task with satisfied dependencies
		const availableTaskIndex = queue.queue.findIndex((task) =>
			task.dependencies.every((depId) =>
				queue.completed.some((completed) => completed.id === depId)
			)
		);

		if (availableTaskIndex === -1) return queue;

		nextTask = queue.queue[availableTaskIndex];
		const updatedQueue = [...queue.queue];
		updatedQueue.splice(availableTaskIndex, 1);

		return {
			...queue,
			queue: updatedQueue,
			running: [...queue.running, { ...nextTask, status: 'running' as const }]
		};
	});

	return nextTask;
};

export const startTask = (taskId: string) => {
	taskQueue.update((queue) => {
		const taskIndex = queue.queue.findIndex((t) => t.id === taskId);
		if (taskIndex === -1) return queue;

		const task = queue.queue[taskIndex];
		const updatedQueue = [...queue.queue];
		updatedQueue.splice(taskIndex, 1);

		return {
			...queue,
			queue: updatedQueue,
			running: [
				...queue.running,
				{
					...task,
					status: 'running',
					startedAt: new Date()
				}
			]
		};
	});
};

export const completeTaskQueue = (taskId: string, output?: any) => {
	taskQueue.update((queue) => {
		const taskIndex = queue.running.findIndex((t) => t.id === taskId);
		if (taskIndex === -1) return queue;

		const task = queue.running[taskIndex];
		const updatedRunning = [...queue.running];
		updatedRunning.splice(taskIndex, 1);

		const completedTask = {
			...task,
			status: 'completed' as const,
			progress: 100,
			output,
			completedAt: new Date(),
			metadata: {
				...task.metadata,
				actualTime: task.startedAt ? new Date().getTime() - task.startedAt.getTime() : 0
			}
		};

		return {
			...queue,
			running: updatedRunning,
			completed: [...queue.completed, completedTask],
			completedTasks: queue.completedTasks + 1
		};
	});
};

export const failTask = (taskId: string, error: Error) => {
	taskQueue.update((queue) => {
		const taskIndex = queue.running.findIndex((t) => t.id === taskId);
		if (taskIndex === -1) return queue;

		const task = queue.running[taskIndex];
		const updatedRunning = [...queue.running];
		updatedRunning.splice(taskIndex, 1);

		const failedTask = {
			...task,
			status: 'failed' as const,
			error,
			completedAt: new Date()
		};

		// Check if we should retry
		if (task.metadata.retryCount < task.metadata.maxRetries) {
			const retriedTask = {
				...task,
				status: 'queued' as const,
				metadata: {
					...task.metadata,
					retryCount: task.metadata.retryCount + 1
				}
			};

			return {
				...queue,
				running: updatedRunning,
				queue: [...queue.queue, retriedTask]
			};
		}

		return {
			...queue,
			running: updatedRunning,
			failed: [...queue.failed, failedTask],
			failedTasks: queue.failedTasks + 1
		};
	});
};

export const updateTaskProgress = (taskId: string, progress: number) => {
	taskQueue.update((queue) => ({
		...queue,
		running: queue.running.map((task) => (task.id === taskId ? { ...task, progress } : task))
	}));
};

export const createTaskTree = (
	name: string,
	tasks: Omit<TaskNode, 'id' | 'status' | 'progress'>[]
): TaskNode => {
	const rootTask: TaskNode = {
		id: `task-${Date.now()}`,
		name,
		type: 'sequential',
		status: 'queued',
		progress: 0,
		dependencies: [],
		children: tasks.map((task, index) => ({
			...task,
			id: `task-${Date.now()}-${index}`,
			status: 'queued' as const,
			progress: 0
		})),
		metadata: {
			retryCount: 0,
			maxRetries: 3,
			priority: 1
		}
	};

	return rootTask;
};

export const setRootTask = (task: TaskNode) => {
	taskQueue.update((queue) => ({
		...queue,
		rootTask: task
	}));
};

export const clearTaskQueue = () => {
	taskQueue.set(initialTaskQueue);
};

export const setConcurrencyLimit = (limit: number) => {
	taskQueue.update((queue) => ({
		...queue,
		concurrencyLimit: Math.max(1, limit)
	}));
};

// Tool Usage Actions
export const recordToolCall = (tool: ToolCall) => {
	toolUsage.update((usage) => ({
		...usage,
		activeCalls: [...usage.activeCalls, tool],
		callHistory: [...usage.callHistory, tool]
	}));
};

export const updateToolCall = (toolId: string, updates: Partial<ToolCall>) => {
	toolUsage.update((usage) => ({
		...usage,
		activeCalls: usage.activeCalls.map((tool) =>
			tool.id === toolId ? { ...tool, ...updates } : tool
		),
		callHistory: usage.callHistory.map((tool) =>
			tool.id === toolId ? { ...tool, ...updates } : tool
		)
	}));
};

export const completeToolCall = (toolId: string, result?: unknown) => {
	toolUsage.update((usage) => {
		const tool = usage.activeCalls.find((t) => t.id === toolId);
		if (!tool) return usage;

		const completedTool: ToolCall = {
			...tool,
			status: 'success' as const,
			output: result
		};

		return {
			...usage,
			activeCalls: usage.activeCalls.filter((t) => t.id !== toolId),
			callHistory: usage.callHistory.map((t) => (t.id === toolId ? completedTool : t)),
			metrics: {
				...usage.metrics,
				totalCalls: usage.metrics.totalCalls + 1
			}
		};
	});
};

export const failToolCall = (toolId: string, error: string) => {
	toolUsage.update((usage) => {
		const tool = usage.activeCalls.find((t) => t.id === toolId);
		if (!tool) return usage;

		const failedTool: ToolCall = {
			...tool,
			status: 'error' as const,
			error
		};

		return {
			...usage,
			activeCalls: usage.activeCalls.filter((t) => t.id !== toolId),
			callHistory: usage.callHistory.map((t) => (t.id === toolId ? failedTool : t)),
			metrics: {
				...usage.metrics,
				recentErrors: [
					...usage.metrics.recentErrors,
					{
						toolName: tool.toolName,
						error,
						timestamp: new Date()
					}
				]
			}
		};
	});
};

export const clearActiveTools = () => {
	toolUsage.update((usage) => ({
		...usage,
		activeCalls: []
	}));
};

export const clearToolHistory = () => {
	toolUsage.update((usage) => ({
		...usage,
		callHistory: []
	}));
};

export const resetToolUsage = () => {
	toolUsage.set(initialToolUsageState);
};

export type Model = OpenAIModel | OllamaModel;

type BaseModel = {
	id: string;
	name: string;
	info?: ModelConfig;
	owned_by: 'ollama' | 'openai' | 'arena';
};

export interface OpenAIModel extends BaseModel {
	owned_by: 'openai';
	external: boolean;
	source?: string;
}

export interface OllamaModel extends BaseModel {
	owned_by: 'ollama';
	details: OllamaModelDetails;
	size: number;
	description: string;
	model: string;
	modified_at: string;
	digest: string;
	ollama?: {
		name?: string;
		model?: string;
		modified_at: string;
		size?: number;
		digest?: string;
		details?: {
			parent_model?: string;
			format?: string;
			family?: string;
			families?: string[];
			parameter_size?: string;
			quantization_level?: string;
		};
		urls?: number[];
	};
}

type OllamaModelDetails = {
	parent_model: string;
	format: string;
	family: string;
	families: string[] | null;
	parameter_size: string;
	quantization_level: string;
};

type Settings = {
	pinnedModels?: never[];
	toolServers?: never[];
	detectArtifacts?: boolean;
	showUpdateToast?: boolean;
	showChangelog?: boolean;
	showEmojiInCall?: boolean;
	voiceInterruption?: boolean;
	collapseCodeBlocks?: boolean;
	expandDetails?: boolean;
	notificationSound?: boolean;
	notificationSoundAlways?: boolean;
	stylizedPdfExport?: boolean;
	notifications?: any;
	imageCompression?: boolean;
	imageCompressionSize?: any;
	widescreenMode?: null;
	largeTextAsFile?: boolean;
	promptAutocomplete?: boolean;
	hapticFeedback?: boolean;
	responseAutoCopy?: any;
	richTextInput?: boolean;
	params?: any;
	userLocation?: any;
	webSearch?: boolean;
	memory?: boolean;
	autoTags?: boolean;
	autoFollowUps?: boolean;
	splitLargeChunks?(body: any, splitLargeChunks: any): unknown;
	backgroundImageUrl?: null;
	landingPageMode?: string;
	iframeSandboxAllowForms?: boolean;
	iframeSandboxAllowSameOrigin?: boolean;
	scrollOnBranchChange?: boolean;
	directConnections?: null;
	chatBubble?: boolean;
	copyFormatted?: boolean;
	models?: string[];
	conversationMode?: boolean;
	speechAutoSend?: boolean;
	responseAutoPlayback?: boolean;
	audio?: AudioSettings;
	showUsername?: boolean;
	notificationEnabled?: boolean;
	highContrastMode?: boolean;
	title?: TitleSettings;
	splitLargeDeltas?: boolean;
	chatDirection?: 'LTR' | 'RTL' | 'auto';
	ctrlEnterToSend?: boolean;

	system?: string;
	seed?: number;
	temperature?: string;
	repeat_penalty?: string;
	top_k?: string;
	top_p?: string;
	num_ctx?: string;
	num_batch?: string;
	num_keep?: string;
	options?: ModelOptions;
};

type ModelOptions = {
	stop?: boolean;
};

type AudioSettings = {
	stt: any;
	tts: any;
	STTEngine?: string;
	TTSEngine?: string;
	speaker?: string;
	model?: string;
	nonLocalVoices?: boolean;
};

type TitleSettings = {
	auto?: boolean;
	model?: string;
	modelExternal?: string;
	prompt?: string;
};

type Prompt = {
	command: string;
	user_id: string;
	title: string;
	content: string;
	timestamp: number;
};

type Document = {
	collection_name: string;
	filename: string;
	name: string;
	title: string;
};

type Config = {
	license_metadata: any;
	status: boolean;
	name: string;
	version: string;
	default_locale: string;
	default_models: string;
	default_prompt_suggestions: PromptSuggestion[];
	features: {
		auth: boolean;
		auth_trusted_header: boolean;
		enable_api_key: boolean;
		enable_signup: boolean;
		enable_login_form: boolean;
		enable_web_search?: boolean;
		enable_google_drive_integration: boolean;
		enable_onedrive_integration: boolean;
		enable_image_generation: boolean;
		enable_admin_export: boolean;
		enable_admin_chat_access: boolean;
		enable_community_sharing: boolean;
		enable_autocomplete_generation: boolean;
		enable_direct_connections: boolean;
		enable_version_update_check: boolean;
	};
	oauth: {
		providers: {
			[key: string]: string;
		};
	};
	ui?: {
		pending_user_overlay_title?: string;
		pending_user_overlay_description?: string;
	};
};

type PromptSuggestion = {
	content: string;
	title: [string, string];
};

type SessionUser = {
	permissions: any;
	id: string;
	email: string;
	name: string;
	role: string;
	profile_image_url: string;
};

// Agent State Types
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
	activity: {
		status: 'idle' | 'active' | 'processing';
		currentTask: string | null;
	};
	logs: Array<{
		id: string;
		type: 'info' | 'warning' | 'error' | 'success';
		message: string;
		timestamp: Date;
	}>;
}

// Task Queue Types
export interface TaskNode {
	id: string;
	name: string;
	description?: string;
	type: 'sequential' | 'parallel' | 'conditional';
	status: 'queued' | 'running' | 'completed' | 'failed' | 'skipped';
	progress: number;
	dependencies: string[];
	children: TaskNode[];
	metadata: {
		estimatedTime?: number;
		actualTime?: number;
		retryCount: number;
		maxRetries: number;
		priority: number;
		assignedModel?: string;
		toolsUsed?: string[];
	};
	input?: any;
	output?: any;
	error?: Error;
	startedAt?: Date;
	completedAt?: Date;
}

export interface TaskQueue {
	id: string;
	name: string;
	rootTask: TaskNode | null;
	queue: TaskNode[];
	running: TaskNode[];
	completed: TaskNode[];
	failed: TaskNode[];
	concurrencyLimit: number;
	totalTasks: number;
	completedTasks: number;
	failedTasks: number;
}

// Tool Usage Types
export interface ToolCall {
	id: string;
	toolName: string;
	toolType: 'function' | 'retrieval' | 'code_interpreter' | 'web_search' | 'custom';
	timestamp: Date;
	duration?: number;
	status: 'pending' | 'running' | 'success' | 'error';
	input: any;
	output?: any;
	error?: string;
	metadata: {
		model?: string;
		messageId?: string;
		tokenUsage?: {
			input: number;
			output: number;
		};
		reasoning?: string;
		confidence?: number;
	};
}

export interface ToolChain {
	id: string;
	name: string;
	tools: ToolCall[];
	startTime: Date;
	endTime?: Date;
	status: 'running' | 'completed' | 'failed';
	description?: string;
}

export interface ToolMetrics {
	totalCalls: number;
	successRate: number;
	averageDuration: number;
	callsByType: Record<string, number>;
	callsByTool: Record<string, number>;
	errorRate: number;
	recentErrors: Array<{
		toolName: string;
		error: string;
		timestamp: Date;
	}>;
}

export interface ToolUsageState {
	activeCalls: ToolCall[];
	callHistory: ToolCall[];
	toolChains: ToolChain[];
	metrics: ToolMetrics;
	showToolPanel: boolean;
	selectedTool: ToolCall | null;
}
