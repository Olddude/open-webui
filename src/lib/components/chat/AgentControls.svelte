<script lang="ts">
	import { SvelteFlowProvider } from '@xyflow/svelte';
	import { Pane, PaneResizer } from 'paneforge';

	import { onDestroy, onMount, tick } from 'svelte';
	import { mobile, agentState, loadAgentActivityTestData } from '$lib/stores';

	import Drawer from '../common/Drawer.svelte';
	import EllipsisVertical from '../icons/EllipsisVertical.svelte';
	import { Activity, X, FlaskConical } from 'lucide-svelte';

	export let pane;

	let mediaQuery;
	let largeScreen = false;
	let minSize = 0;

	export const openPane = () => {
		if (parseInt(localStorage?.agentControlsSize)) {
			pane.resize(parseInt(localStorage?.agentControlsSize));
		} else {
			pane.resize(minSize);
		}
	};

	const handleMediaQuery = async (e) => {
		if (e.matches) {
			largeScreen = true;
		} else {
			largeScreen = false;
			pane = null;
		}
	};

	const onMouseDown = (event) => {
		// Handle mouse down if needed
	};

	const onMouseUp = (event) => {
		// Handle mouse up if needed
	};

	onMount(() => {
		// listen to resize 1024px
		mediaQuery = window.matchMedia('(min-width: 1024px)');

		mediaQuery.addEventListener('change', handleMediaQuery);
		handleMediaQuery(mediaQuery);

		// Select the container element you want to observe
		const container = document.getElementById('chat-container');

		if (container) {
			// initialize the minSize based on the container width
			minSize = Math.floor((350 / container.clientWidth) * 100);

			// Create a new ResizeObserver instance
			const resizeObserver = new ResizeObserver((entries) => {
				for (let entry of entries) {
					const width = entry.contentRect.width;
					// calculate the percentage of 350px
					const percentage = (350 / width) * 100;
					// set the minSize to the percentage, must be an integer
					minSize = Math.floor(percentage);

					if ($agentState.showPanel) {
						if (pane && pane.isExpanded() && pane.getSize() < minSize) {
							pane.resize(minSize);
						}
					}
				}
			});

			// Start observing the container's size changes
			resizeObserver.observe(container);
		}

		document.addEventListener('mousedown', onMouseDown);
		document.addEventListener('mouseup', onMouseUp);
	});

	onDestroy(() => {
		agentState.update(state => ({
			...state,
			showPanel: false
		}));

		if (mediaQuery) {
			mediaQuery.removeEventListener('change', handleMediaQuery);
		}
		document.removeEventListener('mousedown', onMouseDown);
		document.removeEventListener('mouseup', onMouseUp);
	});

	const closeHandler = () => {
		agentState.update(state => ({
			...state,
			showPanel: false
		}));
	};
</script>

<SvelteFlowProvider>
	{#if !largeScreen}
		{#if $agentState.showPanel}
			<Drawer
				show={$agentState.showPanel}
				onClose={closeHandler}
			>
				<div class="px-6 py-4 h-full">
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center gap-2">
							<Activity class="size-5" />
							<h2 class="text-lg font-semibold">Agent Activity</h2>
						</div>
						<div class="flex items-center gap-2">
							{#if import.meta.env.DEV}
								<button
									on:click={loadAgentActivityTestData}
									class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition"
									title="Load test data"
								>
									<FlaskConical class="size-4" />
								</button>
							{/if}
							<button
								on:click={closeHandler}
								class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition"
							>
								<X class="size-4" />
							</button>
						</div>
					</div>
					
				<div class="space-y-4">
					<div class="text-sm text-gray-600 dark:text-gray-400">
						{#if $agentState.activity && $agentState.activity.status !== 'idle'}
							<div class="space-y-2">
								<div class="flex items-center gap-2">
									{#if $agentState.activity.status === 'active'}
										<div class="size-2 bg-green-500 rounded-full animate-pulse"></div>
										<span>Agent is active</span>
									{:else if $agentState.activity.status === 'processing'}
										<div class="size-2 bg-blue-500 rounded-full animate-pulse"></div>
										<span>Agent is processing</span>
									{/if}
								</div>
								<div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
									<p class="text-xs uppercase tracking-wide text-gray-500 mb-1">Current Status</p>
									<p class="font-medium capitalize">{$agentState.activity.status}</p>
									{#if $agentState.activity.currentTask}
										<p class="text-xs uppercase tracking-wide text-gray-500 mt-2 mb-1">Current Task</p>
										<p class="text-sm">{$agentState.activity.currentTask}</p>
									{/if}
								</div>
							</div>
						{:else}
							<div class="flex items-center gap-2">
								<div class="size-2 bg-gray-400 rounded-full"></div>
								<span>Agent is idle</span>
							</div>
						{/if}
					</div>

						{#if $agentState.logs && $agentState.logs.length > 0}
							<div class="mt-4">
								<h3 class="text-sm font-medium mb-2">Activity Log</h3>
								<div class="space-y-2 max-h-96 overflow-y-auto">
									{#each $agentState.logs as log}
										<div class="text-xs p-2 bg-gray-50 dark:bg-gray-800 rounded">
											<span class="text-gray-500">{log.timestamp}:</span>
											<span class="ml-2">{log.message}</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				</div>
			</Drawer>
		{/if}
	{:else}
		{#if $agentState.showPanel}
			<PaneResizer class="relative flex w-2 items-center justify-center bg-background group">
				<div class="z-10 flex h-7 w-5 items-center justify-center rounded-xs">
					<EllipsisVertical className="size-4 invisible group-hover:visible" />
				</div>
			</PaneResizer>
		{/if}

		<Pane
			bind:pane
			defaultSize={0}
			onResize={(size) => {
				console.log('agent panel size', size, minSize);

				if ($agentState.showPanel && pane.isExpanded()) {
					if (size < minSize) {
						pane.resize(minSize);
					}

					if (size < minSize) {
						localStorage.agentControlsSize = 0;
					} else {
						localStorage.agentControlsSize = size;
					}
				}
			}}
			onCollapse={() => {
				agentState.update(state => ({
					...state,
					showPanel: false
				}));
			}}
			collapsible={true}
			class="z-10"
		>
			{#if $agentState.showPanel}
				<div class="flex max-h-full min-h-full">
					<div
						class="w-full px-4 py-4 bg-white dark:shadow-lg dark:bg-gray-850 border border-gray-100 dark:border-gray-850 z-40 pointer-events-auto overflow-y-auto scrollbar-hidden"
					>
						<div class="flex items-center justify-between mb-4">
							<div class="flex items-center gap-2">
								<Activity class="size-5" />
								<h2 class="text-lg font-semibold">Agent Activity</h2>
							</div>
							<div class="flex items-center gap-2">
								{#if import.meta.env.DEV}
									<button
										on:click={loadAgentActivityTestData}
										class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition"
										title="Load test data"
									>
										<FlaskConical class="size-4" />
									</button>
								{/if}
								<button
									on:click={closeHandler}
									class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition"
								>
									<X class="size-4" />
								</button>
							</div>
						</div>
						
						<div class="space-y-4">
							<div class="text-sm text-gray-600 dark:text-gray-400">
								{#if $agentState.activity && $agentState.activity.status !== 'idle'}
									<div class="space-y-2">
										<div class="flex items-center gap-2">
											{#if $agentState.activity.status === 'active'}
												<div class="size-2 bg-green-500 rounded-full animate-pulse"></div>
												<span>Agent is active</span>
											{:else if $agentState.activity.status === 'processing'}
												<div class="size-2 bg-blue-500 rounded-full animate-pulse"></div>
												<span>Agent is processing</span>
											{/if}
										</div>
										<div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
											<p class="text-xs uppercase tracking-wide text-gray-500 mb-1">Current Status</p>
											<p class="font-medium capitalize">{$agentState.activity.status}</p>
											{#if $agentState.activity.currentTask}
												<p class="text-xs uppercase tracking-wide text-gray-500 mt-2 mb-1">Current Task</p>
												<p class="text-sm">{$agentState.activity.currentTask}</p>
											{/if}
										</div>
									</div>
								{:else}
									<div class="flex items-center gap-2">
										<div class="size-2 bg-gray-400 rounded-full"></div>
										<span>Agent is idle</span>
									</div>
								{/if}
							</div>

							{#if $agentState.logs && $agentState.logs.length > 0}
								<div class="mt-4">
									<h3 class="text-sm font-medium mb-2">Activity Log</h3>
									<div class="space-y-2 max-h-96 overflow-y-auto">
										{#each $agentState.logs as log}
											<div class="text-xs p-2 bg-gray-50 dark:bg-gray-800 rounded flex items-start gap-2">
												<span class={`inline-block px-1.5 py-0.5 rounded text-xs font-medium ${
													log.type === 'error' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
													log.type === 'warning' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
													log.type === 'success' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
													'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
												}`}>
													{log.type}
												</span>
												<div class="flex-1">
													<span class="text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}:</span>
													<span class="ml-2">{log.message}</span>
												</div>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					</div>
				</div>
			{/if}
		</Pane>
	{/if}
</SvelteFlowProvider>
