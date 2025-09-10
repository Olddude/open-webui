<script lang="ts">
	import { slide } from 'svelte/transition';
	import { Pane, PaneResizer } from 'paneforge';

	import { onDestroy, onMount, tick } from 'svelte';
	import { mobile } from '$lib/stores';
	import { agentState } from '$lib/stores';

	import AgentPanel from './AgentPanel.svelte';
	import EllipsisVertical from '../icons/EllipsisVertical.svelte';
	import Drawer from '../common/Drawer.svelte';

	export let pane;

	let mediaQuery;
	let largeScreen = false;
	let dragged = false;

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
		dragged = true;
	};

	const onMouseUp = (event) => {
		dragged = false;
	};

	onMount(() => {
		// listen to resize 1024px for consistency with ChatControls
		mediaQuery = window.matchMedia('(min-width: 1024px)');

		mediaQuery.addEventListener('change', handleMediaQuery);
		handleMediaQuery(mediaQuery);

		// Select the container element you want to observe
		const container = document.getElementById('chat-container');

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

		document.addEventListener('mousedown', onMouseDown);
		document.addEventListener('mouseup', onMouseUp);
	});

	onDestroy(() => {
		agentState.update(state => ({
			...state,
			showPanel: false
		}));

		mediaQuery.removeEventListener('change', handleMediaQuery);
		document.removeEventListener('mousedown', onMouseDown);
		document.removeEventListener('mouseup', onMouseUp);
	});
</script>

{#if !largeScreen}
	{#if $agentState.showPanel}
		<Drawer
			show={$agentState.showPanel}
			onClose={() => {
				agentState.update(state => ({
					...state,
					showPanel: false
				}));
			}}
		>
			<div class="px-6 py-4 h-full">
				<AgentPanel />
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
		{minSize}
		onResize={(size) => {
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
					<AgentPanel />
				</div>
			</div>
		{/if}
	</Pane>
{/if}
