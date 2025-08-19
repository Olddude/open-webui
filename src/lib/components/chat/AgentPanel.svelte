<script lang="ts">
	import { agentState, togglePanel } from '$lib/stores/agentState';
	import { taskQueue } from '$lib/stores/taskQueue';
	import TaskPlanning from './Messages/TaskPlanning.svelte';
	import ReasoningDisplay from './Messages/ReasoningDisplay.svelte';
	import TaskMonitor from './Messages/TaskMonitor.svelte';
	import { ChevronDown, ChevronRight, Brain, ListTodo, Activity, Settings } from 'lucide-svelte';

	$: showTaskPanel = $agentState.showTaskPanel;
	$: showReasoningPanel = $agentState.showReasoningPanel;
	$: activeTasks = $agentState.activeTasks;
	$: reasoningChain = $agentState.reasoningChain;
	$: currentPlan = $agentState.currentPlan;
	$: queuedTasks = $taskQueue.queue;
	$: runningTasks = $taskQueue.running;
</script>

<div class="agent-panel-container h-full flex flex-col">
	<div class="panel-header p-4 border-b border-gray-200 dark:border-gray-700">
		<div class="flex items-center justify-between mb-2">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">
				Agent Activity
			</h2>
			<button
				class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
				title="Settings"
			>
				<Settings size={18} />
			</button>
		</div>
		<div class="flex gap-2 text-xs">
			<span class="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
				{runningTasks.length} Active
			</span>
			<span class="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
				{queuedTasks.length} Queued
			</span>
		</div>
	</div>

	<div class="panel-content flex-1 overflow-y-auto">
		<!-- Task Planning Section -->
		<div class="section border-b border-gray-200 dark:border-gray-700">
			<button
				class="section-header w-full p-3 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
				on:click={() => togglePanel('task')}
			>
				<div class="flex items-center gap-2">
					<ListTodo size={16} class="text-blue-600 dark:text-blue-400" />
					<span class="font-medium text-gray-700 dark:text-gray-300">Task Planning</span>
					{#if activeTasks.length > 0}
						<span class="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full">
							{activeTasks.length}
						</span>
					{/if}
				</div>
				{#if showTaskPanel}
					<ChevronDown size={16} class="text-gray-500" />
				{:else}
					<ChevronRight size={16} class="text-gray-500" />
				{/if}
			</button>
			
			{#if showTaskPanel}
				<div class="section-content p-3">
					{#if currentPlan}
						<TaskPlanning task={currentPlan} />
					{:else if activeTasks.length > 0}
						<TaskMonitor tasks={activeTasks} />
					{:else}
						<div class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
							No active tasks
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Reasoning Display Section -->
		<div class="section border-b border-gray-200 dark:border-gray-700">
			<button
				class="section-header w-full p-3 flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
				on:click={() => togglePanel('reasoning')}
			>
				<div class="flex items-center gap-2">
					<Brain size={16} class="text-purple-600 dark:text-purple-400" />
					<span class="font-medium text-gray-700 dark:text-gray-300">Agent Reasoning</span>
					{#if reasoningChain.length > 0}
						<span class="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-full">
							{reasoningChain.length}
						</span>
					{/if}
				</div>
				{#if showReasoningPanel}
					<ChevronDown size={16} class="text-gray-500" />
				{:else}
					<ChevronRight size={16} class="text-gray-500" />
				{/if}
			</button>
			
			{#if showReasoningPanel}
				<div class="section-content p-3">
					{#if reasoningChain.length > 0}
						<ReasoningDisplay steps={reasoningChain} />
					{:else}
						<div class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
							No reasoning steps yet
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Execution Monitor Section -->
		<div class="section">
			<div class="section-header p-3 flex items-center gap-2">
				<Activity size={16} class="text-green-600 dark:text-green-400" />
				<span class="font-medium text-gray-700 dark:text-gray-300">Execution Monitor</span>
			</div>
			<div class="section-content p-3">
				{#if runningTasks.length > 0}
					<div class="space-y-2">
						{#each runningTasks as task}
							<div class="task-item p-2 bg-gray-50 dark:bg-gray-800 rounded">
								<div class="flex items-center justify-between mb-1">
									<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
										{task.name}
									</span>
									<span class="text-xs text-gray-500 dark:text-gray-400">
										{task.progress}%
									</span>
								</div>
								<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
									<div 
										class="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
										style="width: {task.progress}%"
									></div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
						No running tasks
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.agent-panel-container {
		width: 100%;
		background: var(--panel-bg, white);
	}

	.section {
		position: relative;
	}

	.section-header {
		text-align: left;
		outline: none;
	}

	.section-header:focus-visible {
		box-shadow: inset 0 0 0 2px rgba(99, 102, 241, 0.5);
	}

	.section-content {
		animation: slideDown 0.2s ease-out;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.task-item {
		animation: fadeIn 0.3s ease-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	:global(.dark) .agent-panel-container {
		--panel-bg: rgb(17 24 39);
	}
</style>