<script lang="ts">
	import type { ReasoningStep } from '$lib/stores/agentState';
	import { Brain, Lightbulb, Target, TrendingUp, ChevronDown, ChevronRight } from 'lucide-svelte';
	
	export let steps: ReasoningStep[] = [];
	
	let expandedSteps: Record<string, boolean> = {};
	
	function toggleStep(stepId: string) {
		expandedSteps[stepId] = !expandedSteps[stepId];
	}
	
	function getStepIcon(type: ReasoningStep['type']) {
		switch (type) {
			case 'thinking':
				return Brain;
			case 'decision':
				return Target;
			case 'analysis':
				return TrendingUp;
			case 'strategy':
				return Lightbulb;
			default:
				return Brain;
		}
	}
	
	function getStepColor(type: ReasoningStep['type']) {
		switch (type) {
			case 'thinking':
				return 'text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-900/30';
			case 'decision':
				return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30';
			case 'analysis':
				return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
			case 'strategy':
				return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
			default:
				return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30';
		}
	}
</script>

<div class="reasoning-display">
	{#if steps.length > 0}
		<div class="reasoning-chain">
			{#each steps as step, index}
				<div class="reasoning-step">
					<div class="step-connector">
						{#if index > 0}
							<div class="connector-line"></div>
						{/if}
						<div class="connector-dot {getStepColor(step.type).split(' ')[0]}"></div>
					</div>
					
					<div class="step-content">
						<button class="step-header" on:click={() => toggleStep(step.id)}>
							<div class="step-icon {getStepColor(step.type)}">
								<svelte:component this={getStepIcon(step.type)} size={14} />
							</div>
							
							<div class="step-info">
								<div class="step-type">
									{step.type.charAt(0).toUpperCase() + step.type.slice(1)}
								</div>
								<div class="step-timestamp">
									{step.timestamp.toLocaleTimeString()}
								</div>
							</div>
							
							{#if step.confidence !== undefined}
								<div class="step-confidence">
									<div class="confidence-value">{Math.round(step.confidence * 100)}%</div>
								</div>
							{/if}
							
							<div class="step-expand">
								{#if expandedSteps[step.id]}
									<ChevronDown size={14} />
								{:else}
									<ChevronRight size={14} />
								{/if}
							</div>
						</button>
						
						<div class="step-preview">
							{step.content.slice(0, 100)}{step.content.length > 100 ? '...' : ''}
						</div>
						
						{#if expandedSteps[step.id]}
							<div class="step-details">
								<div class="step-full-content">
									{step.content}
								</div>
								
								{#if step.alternatives && step.alternatives.length > 0}
									<div class="step-alternatives">
										<div class="alternatives-label">Alternatives considered:</div>
										<ul class="alternatives-list">
											{#each step.alternatives as alt}
												<li class="alternative-item">{alt}</li>
											{/each}
										</ul>
									</div>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="empty-state">
			<Brain size={24} class="text-gray-400" />
			<p>No reasoning steps available</p>
		</div>
	{/if}
</div>

<style>
	.reasoning-display {
		width: 100%;
	}
	
	.reasoning-chain {
		position: relative;
		padding-left: 1rem;
	}
	
	.reasoning-step {
		position: relative;
		display: flex;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}
	
	.step-connector {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 20px;
	}
	
	.connector-line {
		position: absolute;
		top: -1rem;
		width: 2px;
		height: 1rem;
		background: #e5e7eb;
	}
	
	.connector-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		margin-top: 0.375rem;
	}
	
	.step-content {
		flex: 1;
	}
	
	.step-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.5rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		cursor: pointer;
		text-align: left;
	}
	
	.step-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border-radius: 0.375rem;
	}
	
	.step-info {
		flex: 1;
	}
	
	.step-type {
		font-size: 0.875rem;
		font-weight: 500;
		color: #1f2937;
	}
	
	.step-timestamp {
		font-size: 0.75rem;
		color: #6b7280;
	}
	
	.step-preview {
		margin-top: 0.25rem;
		padding: 0 0.5rem;
		font-size: 0.8125rem;
		color: #6b7280;
	}
	
	.step-details {
		margin-top: 0.5rem;
		padding: 0.75rem;
		background: #f9fafb;
		border-radius: 0.375rem;
	}
	
	.step-full-content {
		font-size: 0.875rem;
		color: #374151;
		line-height: 1.5;
		white-space: pre-wrap;
	}
	
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 2rem;
		color: #6b7280;
	}
</style>