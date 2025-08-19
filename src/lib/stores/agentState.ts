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
	showArtifactsPanel: true
};

export const agentState: Writable<AgentState> = writable(initialState);

// Derived stores for specific views
export const activeTasksCount = derived(
	agentState,
	$state => $state.activeTasks.filter(t => t.status === 'executing').length
);

export const completedTasksCount = derived(
	agentState,
	$state => $state.taskHistory.filter(t => t.status === 'completed').length
);

export const currentReasoningSteps = derived(
	agentState,
	$state => $state.reasoningChain.slice(-10) // Last 10 reasoning steps
);

// Actions
export const addTask = (task: Task) => {
	agentState.update(state => ({
		...state,
		activeTasks: [...state.activeTasks, task]
	}));
};

export const updateTaskStatus = (taskId: string, status: Task['status'], progress?: number) => {
	agentState.update(state => ({
		...state,
		activeTasks: state.activeTasks.map(task =>
			task.id === taskId 
				? { ...task, status, progress: progress ?? task.progress }
				: task
		)
	}));
};

export const completeTask = (taskId: string, result?: any) => {
	agentState.update(state => {
		const task = state.activeTasks.find(t => t.id === taskId);
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
			activeTasks: state.activeTasks.filter(t => t.id !== taskId),
			taskHistory: [...state.taskHistory, completedTask]
		};
	});
};

export const addReasoningStep = (step: ReasoningStep) => {
	agentState.update(state => ({
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
	
	agentState.update(state => ({
		...state,
		parallelExecutions: [...state.parallelExecutions, execution]
	}));
	
	return execution.id;
};

export const addArtifact = (artifact: Artifact) => {
	agentState.update(state => ({
		...state,
		artifacts: [...state.artifacts, artifact]
	}));
};

export const updateArtifact = (artifactId: string, content: string) => {
	agentState.update(state => ({
		...state,
		artifacts: state.artifacts.map(artifact =>
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
	agentState.update(state => {
		const key = `show${panel.charAt(0).toUpperCase() + panel.slice(1)}Panel` as keyof AgentState;
		return {
			...state,
			[key]: !state[key]
		};
	});
};

export const toggleAgenticMode = () => {
	agentState.update(state => ({
		...state,
		isAgenticMode: !state.isAgenticMode
	}));
};

export const resetAgentState = () => {
	agentState.set(initialState);
};