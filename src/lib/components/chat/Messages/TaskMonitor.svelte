<script lang="ts">
	import type { Task } from '$lib/stores/agentState';
	import { CheckCircle, Circle, Clock, AlertCircle, Loader } from 'lucide-svelte';
	
	export let tasks: Task[] = [];
	
	function getStatusIcon(status: Task['status']) {
		switch (status) {
			case 'completed':
				return CheckCircle;
			case 'executing':
				return Loader;
			case 'planning':
				return Clock;
			case 'failed':
				return AlertCircle;
			default:
				return Circle;
		}
	}
	
	function getStatusColor(status: Task['status']) {
		switch (status) {
			case 'completed':
				return 'text-green-600 dark:text-green-400';
			case 'executing':
				return 'text-blue-600 dark:text-blue-400';
			case 'planning':
				return 'text-yellow-600 dark:text-yellow-400';
			case 'failed':
				return 'text-red-600 dark:text-red-400';
			default:
				return 'text-gray-400 dark:text-gray-600';
		}
	}
	
	function getProgressColor(status: Task['status']) {
		switch (status) {
			case 'completed':
				return 'bg-green-600';
			case 'executing':
				return 'bg-blue-600';
			case 'planning':
				return 'bg-yellow-600';
			case 'failed':
				return 'bg-red-600';
			default:
				return 'bg-gray-400';
		}
	}
</script>

<div class="task-monitor">
	{#if tasks.length > 0}
		<div class="task-list">
			{#each tasks as task}
				<div class="task-item" class:executing={task.status === 'executing'}>
					<div class="task-header">
						<div class="task-status">
							<svelte:component 
								this={getStatusIcon(task.status)} 
								size={16} 
								class="{getStatusColor(task.status)} {task.status === 'executing' ? 'animate-spin' : ''}"
							/>
						</div>
						
						<div class="task-info">
							<div class="task-title">{task.title}</div>
							{#if task.description}
								<div class="task-description">{task.description}</div>
							{/if}
						</div>
					</div>
					
					<div class="task-progress-section">
						<div class="progress-info">
							<span class="progress-text">{task.progress}%</span>
						</div>
						
						<div class="progress-bar">
							<div 
								class="progress-fill {getProgressColor(task.status)}"
								style="width: {task.progress}%"
							></div>
						</div>
					</div>
					
					{#if task.error}
						<div class="task-error">
							<AlertCircle size={14} class="text-red-500" />
							<span class="error-message">{task.error}</span>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{:else}
		<div class="empty-state">
			<Circle size={24} class="text-gray-400" />
			<p>No tasks to monitor</p>
		</div>
	{/if}
</div>

<style>
	.task-monitor {
		width: 100%;
	}
	
	.task-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.task-item {
		padding: 0.75rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		transition: all 0.2s;
	}
	
	:global(.dark) .task-item {
		background: #1f2937;
		border-color: #374151;
	}
	
	.task-item.executing {
		border-color: #3b82f6;
		box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.1);
	}
	
	.task-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
	}
	
	.task-info {
		flex: 1;
		min-width: 0;
	}
	
	.task-title {
		font-size: 0.875rem;
		font-weight: 500;
		color: #1f2937;
	}
	
	:global(.dark) .task-title {
		color: #f3f4f6;
	}
	
	.task-description {
		font-size: 0.75rem;
		color: #6b7280;
		margin-top: 0.125rem;
	}
	
	.task-progress-section {
		margin-bottom: 0.5rem;
	}
	
	.progress-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.25rem;
	}
	
	.progress-text {
		font-size: 0.75rem;
		font-weight: 500;
		color: #4b5563;
	}
	
	:global(.dark) .progress-text {
		color: #d1d5db;
	}
	
	.progress-bar {
		width: 100%;
		height: 6px;
		background: #e5e7eb;
		border-radius: 3px;
		overflow: hidden;
	}
	
	:global(.dark) .progress-bar {
		background: #374151;
	}
	
	.progress-fill {
		height: 100%;
		transition: width 0.3s ease-out;
		border-radius: 3px;
	}
	
	.task-error {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.5rem;
		padding: 0.375rem;
		border-radius: 0.25rem;
		font-size: 0.8125rem;
		background: #fef2f2;
		color: #dc2626;
	}
	
	:global(.dark) .task-error {
		background: #7f1d1d;
		color: #fca5a5;
	}
	
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 2rem;
		color: #6b7280;
		text-align: center;
	}
</style>