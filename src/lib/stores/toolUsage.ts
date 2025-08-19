import { writable, derived } from 'svelte/store';
import type { Writable } from 'svelte/store';

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

const initialState: ToolUsageState = {
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

export const toolUsage: Writable<ToolUsageState> = writable(initialState);

// Derived stores
export const activeToolsCount = derived(
	toolUsage,
	$state => $state.activeCalls.length
);

export const toolSuccessRate = derived(
	toolUsage,
	$state => $state.metrics.successRate
);

export const mostUsedTools = derived(
	toolUsage,
	$state => {
		const entries = Object.entries($state.metrics.callsByTool);
		return entries
			.sort(([, a], [, b]) => b - a)
			.slice(0, 5)
			.map(([tool, count]) => ({ tool, count }));
	}
);

export const activeToolChains = derived(
	toolUsage,
	$state => $state.toolChains.filter(chain => chain.status === 'running')
);

// Actions
export const startToolCall = (
	toolName: string,
	toolType: ToolCall['toolType'],
	input: any,
	metadata?: ToolCall['metadata']
): string => {
	const toolCall: ToolCall = {
		id: `tool-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
		toolName,
		toolType,
		timestamp: new Date(),
		status: 'pending',
		input,
		metadata: metadata || {}
	};
	
	toolUsage.update(state => ({
		...state,
		activeCalls: [...state.activeCalls, toolCall],
		metrics: {
			...state.metrics,
			totalCalls: state.metrics.totalCalls + 1,
			callsByType: {
				...state.metrics.callsByType,
				[toolType]: (state.metrics.callsByType[toolType] || 0) + 1
			},
			callsByTool: {
				...state.metrics.callsByTool,
				[toolName]: (state.metrics.callsByTool[toolName] || 0) + 1
			}
		}
	}));
	
	return toolCall.id;
};

export const updateToolStatus = (
	toolId: string,
	status: ToolCall['status'],
	output?: any,
	error?: string
) => {
	toolUsage.update(state => {
		const toolIndex = state.activeCalls.findIndex(t => t.id === toolId);
		if (toolIndex === -1) return state;
		
		const tool = state.activeCalls[toolIndex];
		const duration = new Date().getTime() - tool.timestamp.getTime();
		
		const updatedTool: ToolCall = {
			...tool,
			status,
			duration,
			output,
			error
		};
		
		// Move to history if completed or failed
		if (status === 'success' || status === 'error') {
			const updatedActiveCalls = [...state.activeCalls];
			updatedActiveCalls.splice(toolIndex, 1);
			
			// Update metrics
			const successCount = state.callHistory.filter(c => c.status === 'success').length + 
				(status === 'success' ? 1 : 0);
			const totalCompleted = state.callHistory.length + 1;
			const successRate = (successCount / totalCompleted) * 100;
			
			const totalDuration = state.callHistory.reduce((sum, c) => sum + (c.duration || 0), 0) + duration;
			const averageDuration = totalDuration / totalCompleted;
			
			let recentErrors = [...state.metrics.recentErrors];
			if (status === 'error') {
				recentErrors.unshift({
					toolName: tool.toolName,
					error: error || 'Unknown error',
					timestamp: new Date()
				});
				recentErrors = recentErrors.slice(0, 10); // Keep last 10 errors
			}
			
			return {
				...state,
				activeCalls: updatedActiveCalls,
				callHistory: [...state.callHistory, updatedTool],
				metrics: {
					...state.metrics,
					successRate,
					averageDuration,
					errorRate: ((totalCompleted - successCount) / totalCompleted) * 100,
					recentErrors
				}
			};
		}
		
		// Just update status if still running
		return {
			...state,
			activeCalls: state.activeCalls.map(t =>
				t.id === toolId ? updatedTool : t
			)
		};
	});
};

export const startToolChain = (name: string, description?: string): string => {
	const chain: ToolChain = {
		id: `chain-${Date.now()}`,
		name,
		tools: [],
		startTime: new Date(),
		status: 'running',
		description
	};
	
	toolUsage.update(state => ({
		...state,
		toolChains: [...state.toolChains, chain]
	}));
	
	return chain.id;
};

export const addToolToChain = (chainId: string, toolCall: ToolCall) => {
	toolUsage.update(state => ({
		...state,
		toolChains: state.toolChains.map(chain =>
			chain.id === chainId
				? { ...chain, tools: [...chain.tools, toolCall] }
				: chain
		)
	}));
};

export const completeToolChain = (chainId: string, status: 'completed' | 'failed') => {
	toolUsage.update(state => ({
		...state,
		toolChains: state.toolChains.map(chain =>
			chain.id === chainId
				? { ...chain, status, endTime: new Date() }
				: chain
		)
	}));
};

export const selectTool = (tool: ToolCall | null) => {
	toolUsage.update(state => ({
		...state,
		selectedTool: tool
	}));
};

export const toggleToolPanel = () => {
	toolUsage.update(state => ({
		...state,
		showToolPanel: !state.showToolPanel
	}));
};

export const clearToolHistory = () => {
	toolUsage.update(state => ({
		...state,
		callHistory: [],
		metrics: {
			...initialState.metrics,
			totalCalls: state.activeCalls.length
		}
	}));
};

export const resetToolUsage = () => {
	toolUsage.set(initialState);
};