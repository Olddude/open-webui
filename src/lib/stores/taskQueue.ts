import { writable, derived } from 'svelte/store';
import type { Writable } from 'svelte/store';

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

const initialQueue: TaskQueue = {
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

export const taskQueue: Writable<TaskQueue> = writable(initialQueue);

// Derived stores
export const queueProgress = derived(
	taskQueue,
	$queue => {
		if ($queue.totalTasks === 0) return 0;
		return ($queue.completedTasks / $queue.totalTasks) * 100;
	}
);

export const runningTasks = derived(
	taskQueue,
	$queue => $queue.running
);

export const pendingTasks = derived(
	taskQueue,
	$queue => $queue.queue
);

export const canExecuteMore = derived(
	taskQueue,
	$queue => $queue.running.length < $queue.concurrencyLimit
);

// Task Queue Actions
export const enqueueTask = (task: TaskNode) => {
	taskQueue.update(queue => ({
		...queue,
		queue: [...queue.queue, task],
		totalTasks: queue.totalTasks + 1
	}));
};

export const enqueueTasks = (tasks: TaskNode[]) => {
	taskQueue.update(queue => ({
		...queue,
		queue: [...queue.queue, ...tasks],
		totalTasks: queue.totalTasks + tasks.length
	}));
};

export const dequeueTask = (): TaskNode | null => {
	let nextTask: TaskNode | null = null;
	
	taskQueue.update(queue => {
		if (queue.queue.length === 0) return queue;
		
		// Find next task with satisfied dependencies
		const availableTaskIndex = queue.queue.findIndex(task =>
			task.dependencies.every(depId =>
				queue.completed.some(completed => completed.id === depId)
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
	taskQueue.update(queue => {
		const taskIndex = queue.queue.findIndex(t => t.id === taskId);
		if (taskIndex === -1) return queue;
		
		const task = queue.queue[taskIndex];
		const updatedQueue = [...queue.queue];
		updatedQueue.splice(taskIndex, 1);
		
		return {
			...queue,
			queue: updatedQueue,
			running: [...queue.running, { 
				...task, 
				status: 'running',
				startedAt: new Date()
			}]
		};
	});
};

export const completeTask = (taskId: string, output?: any) => {
	taskQueue.update(queue => {
		const taskIndex = queue.running.findIndex(t => t.id === taskId);
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
				actualTime: task.startedAt 
					? new Date().getTime() - task.startedAt.getTime()
					: 0
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
	taskQueue.update(queue => {
		const taskIndex = queue.running.findIndex(t => t.id === taskId);
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
	taskQueue.update(queue => ({
		...queue,
		running: queue.running.map(task =>
			task.id === taskId ? { ...task, progress } : task
		)
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
	taskQueue.update(queue => ({
		...queue,
		rootTask: task
	}));
};

export const clearQueue = () => {
	taskQueue.set(initialQueue);
};

export const setConcurrencyLimit = (limit: number) => {
	taskQueue.update(queue => ({
		...queue,
		concurrencyLimit: Math.max(1, limit)
	}));
};