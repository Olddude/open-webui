<script lang="ts">
	import { slide } from 'svelte/transition';
	import { Pane, PaneResizer } from 'paneforge';

	import { onDestroy, onMount, tick } from 'svelte';
	import { mobile } from '$lib/stores';
	import { agentState } from '$lib/stores';

	import AgentPanel from './AgentPanel.svelte';

	export let pane;

	let mediaQuery;
	let largeScreen = false;
	let dragged = false;

	let minSize = 0;

	export const openPane = () => {
		if (parseInt(localStorage?.agentControlsSize)) {
			pane.resize(parseInt(localStorage?.agentControlsSize));
		} else {
			pane.resize(30); // Default size for agent panel
		}
	};

	const handleMediaQuery = async (e) => {
		if (e.matches) {
			largeScreen = true;
			minSize = 20;
		} else {
			largeScreen = false;
			minSize = 0;
		}

		if (!$agentState.showPanel) {
			pane.collapse();
		}
	};

	onMount(async () => {
		mediaQuery = window.matchMedia('(min-width: 768px)');
		mediaQuery.addEventListener('change', handleMediaQuery);
		handleMediaQuery(mediaQuery);

		if ($agentState.showPanel && largeScreen) {
			await tick();
			openPane();
		} else {
			pane.collapse();
		}
	});

	onDestroy(() => {
		if (mediaQuery) {
			mediaQuery.removeEventListener('change', handleMediaQuery);
		}
	});

	$: if (pane) {
		if ($agentState.showPanel && largeScreen) {
			openPane();
		} else {
			pane.collapse();
		}
	}

	const handlePaneResize = (size) => {
		if (size.size > minSize) {
			localStorage.agentControlsSize = size.size;
			dragged = true;
		}
	};
</script>

<PaneResizer 
	class="w-2 bg-transparent hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
	on:resize={handlePaneResize}
/>

<Pane 
	bind:pane
	{minSize} 
	defaultSize={0}
	class="h-full"
	collapsible={true}
	collapsedSize={0}
>
	{#if $agentState.showPanel || dragged}
		<div class="h-full" transition:slide={{ axis: 'x', duration: 200 }}>
			<AgentPanel />
		</div>
	{/if}
</Pane>
