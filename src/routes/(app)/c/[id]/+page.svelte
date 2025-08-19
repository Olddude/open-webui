<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import Chat from '$lib/components/chat/Chat.svelte';
	import AgentPanel from '$lib/components/chat/AgentPanel.svelte';
	import ArtifactsPanel from '$lib/components/chat/ArtifactsPanel.svelte';
	import { agentState } from '$lib/stores/agentState';
	import { toolUsage } from '$lib/stores/toolUsage';

	let containerEl: HTMLDivElement;
	let leftPanelWidth = 25;
	let rightPanelWidth = 25;
	let isDraggingLeft = false;
	let isDraggingRight = false;
	
	$: isAgenticMode = $agentState.isAgenticMode;
	$: showAgentPanel = $agentState.showTaskPanel || $agentState.showReasoningPanel;
	$: showArtifactsPanel = $agentState.showArtifactsPanel;

	function handleLeftResize(e: MouseEvent) {
		if (!isDraggingLeft) return;
		const containerRect = containerEl.getBoundingClientRect();
		const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
		leftPanelWidth = Math.min(Math.max(newWidth, 15), 40);
	}

	function handleRightResize(e: MouseEvent) {
		if (!isDraggingRight) return;
		const containerRect = containerEl.getBoundingClientRect();
		const newWidth = ((containerRect.right - e.clientX) / containerRect.width) * 100;
		rightPanelWidth = Math.min(Math.max(newWidth, 15), 40);
	}

	function stopDragging() {
		isDraggingLeft = false;
		isDraggingRight = false;
	}

	onMount(() => {
		window.addEventListener('mousemove', handleLeftResize);
		window.addEventListener('mousemove', handleRightResize);
		window.addEventListener('mouseup', stopDragging);
		
		return () => {
			window.removeEventListener('mousemove', handleLeftResize);
			window.removeEventListener('mousemove', handleRightResize);
			window.removeEventListener('mouseup', stopDragging);
		};
	});
</script>

<div 
	bind:this={containerEl}
	class="flex h-full w-full relative {isAgenticMode ? 'agentic-mode' : ''}"
>
	{#if isAgenticMode && showAgentPanel}
		<div 
			class="agent-panel border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50"
			style="width: {leftPanelWidth}%"
		>
			<AgentPanel />
		</div>
		<div 
			class="resize-handle left"
			on:mousedown={() => isDraggingLeft = true}
			role="separator"
			aria-orientation="vertical"
			tabindex="0"
		/>
	{/if}
	
	<div class="chat-container flex-1 min-w-0">
		<Chat chatIdProp={$page.params.id} />
	</div>
	
	{#if isAgenticMode && showArtifactsPanel}
		<div 
			class="resize-handle right"
			on:mousedown={() => isDraggingRight = true}
			role="separator"
			aria-orientation="vertical"
			tabindex="0"
		/>
		<div 
			class="artifacts-panel border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50"
			style="width: {rightPanelWidth}%"
		>
			<ArtifactsPanel />
		</div>
	{/if}
</div>

<style>
	.agentic-mode {
		background: linear-gradient(135deg, rgba(99, 102, 241, 0.02) 0%, rgba(168, 85, 247, 0.02) 100%);
	}

	.resize-handle {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 4px;
		cursor: col-resize;
		background: transparent;
		transition: background 0.2s;
		z-index: 10;
	}

	.resize-handle:hover,
	.resize-handle:active {
		background: rgba(99, 102, 241, 0.3);
	}

	.resize-handle.left {
		left: calc(var(--left-panel-width, 25%) - 2px);
	}

	.resize-handle.right {
		right: calc(var(--right-panel-width, 25%) - 2px);
	}

	.agent-panel {
		overflow-y: auto;
		overflow-x: hidden;
	}

	.artifacts-panel {
		overflow-y: auto;
		overflow-x: hidden;
	}

	.chat-container {
		position: relative;
		overflow: hidden;
	}

	:global(.dark) .agentic-mode {
		background: linear-gradient(135deg, rgba(99, 102, 241, 0.03) 0%, rgba(168, 85, 247, 0.03) 100%);
	}
</style>