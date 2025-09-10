<script lang="ts">
	import type { Task } from '$lib/stores';
	import { CheckCircle, Circle, Clock, AlertCircle, ChevronRight, ChevronDown, Loader } from 'lucide-svelte';
	
	export let task: Task;
	
	let expanded: Record<string, boolean> = {};
	
	function toggleExpand(taskId: string) {
		expanded[taskId] = !expanded[taskId];
	}
	
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
				return 'text-blue-600 dark:text-blue-400 animate-spin';
			case 'planning':
				return 'text-yellow-600 dark:text-yellow-400';
			case 'failed':
				return 'text-red-600 dark:text-red-400';
			default:
				return 'text-gray-400 dark:text-gray-600';
		}
	}
	
	// Component props for recursive rendering
	export let level: number = 0;
</script>

<div class="task-planning">
	{#if task}
		<div class="task-tree">
			<div class="task-node" style="padding-left: {level * 20}px">
				<div class="task-header">
					<button
						class="task-expand-btn"
						on:click={() => toggleExpand(task.id)}
						disabled={!task.children || task.children.length === 0}
					>
						{#if task.children && task.children.length > 0}
							{#if expanded[task.id]}
								<ChevronDown size={14} />
							{:else}
								<ChevronRight size={14} />
							{/if}
						{:else}
							<span class="w-3.5"></span>
						{/if}
					</button>
					
					<svelte:component 
						this={getStatusIcon(task.status)} 
						size={16} 
						class={getStatusColor(task.status)}
					/>
					
					<div class="task-info flex-1">
						<div class="task-title">
							{task.title}
						</div>
						{#if task.description}
							<div class="task-description">
								{task.description}
							</div>
						{/if}
					</div>
					
					{#if task.progress > 0 && task.progress < 100}
						<div class="task-progress">
							<div class="progress-text">{task.progress}%</div>
							<div class="progress-bar">
								<div 
									class="progress-fill"
									style="width: {task.progress}%"
								></div>
							</div>
						</div>
					{/if}
				</div>
				
				{#if task.dependencies && task.dependencies.length > 0}
					<div class="task-dependencies">
						<span class="dep-label">Depends on:</span>
						{#each task.dependencies as dep}
							<span class="dep-item">{dep}</span>
						{/each}
					</div>
				{/if}
				
				{#if expanded[task.id] && task.children && task.children.length > 0}
					<div class="task-children">
						{#each task.children as child}
							<svelte:self task={child} level={level + 1} />
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{:else}
		<div class="empty-state">
			<p>No task plan available</p>
		</div>
	{/if}
</div>

<style>
	.task-planning {
		width: 100%;
	}
	
	.task-tree {
		font-size: 0.875rem;
	}
	
	.task-node {
		margin-bottom: 0.5rem;
		animation: fadeIn 0.3s ease-out;
	}
	
	.task-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
		border-radius: 0.375rem;
		transition: background-color 0.2s;
	}
	
	.task-header:hover {
		background-color: rgba(0, 0, 0, 0.05);
	}
	
	:global(.dark) .task-header:hover {
		background-color: rgba(255, 255, 255, 0.05);
	}
	
	.task-expand-btn {
		padding: 0;
		background: none;
		border: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		color: #6b7280;
	}
	
	.task-expand-btn:disabled {
		cursor: default;
	}
	
	.task-info {
		min-width: 0;
	}
	
	.task-title {
		font-weight: 500;
		color: #1f2937;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	:global(.dark) .task-title {
		color: #f3f4f6;
	}
	
	.task-description {
		font-size: 0.75rem;
		color: #6b7280;
		margin-top: 0.125rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	:global(.dark) .task-description {
		color: #9ca3af;
	}
	
	.task-progress {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		min-width: 80px;
	}
	
	.progress-text {
		font-size: 0.75rem;
		color: #6b7280;
		min-width: 32px;
		text-align: right;
	}
	
	.progress-bar {
		flex: 1;
		height: 4px;
		background-color: #e5e7eb;
		border-radius: 2px;
		overflow: hidden;
	}
	
	:global(.dark) .progress-bar {
		background-color: #374151;
	}
	
	.progress-fill {
		height: 100%;
		background-color: #3b82f6;
		transition: width 0.3s ease-out;
	}
	
	.task-dependencies {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		margin-top: 0.25rem;
		margin-left: 3rem;
		font-size: 0.75rem;
	}
	
	.dep-label {
		color: #6b7280;
	}
	
	.dep-item {
		padding: 0.125rem 0.375rem;
		background-color: #f3f4f6;
		color: #4b5563;
		border-radius: 0.25rem;
	}
	
	:global(.dark) .dep-item {
		background-color: #374151;
		color: #d1d5db;
	}
	
	.task-children {
		margin-top: 0.25rem;
	}
	
	.empty-state {
		text-align: center;
		padding: 2rem;
		color: #6b7280;
	}
	
	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateX(-10px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}
</style>