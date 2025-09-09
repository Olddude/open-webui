<script lang="ts">
	import { agentState } from '$lib/stores/agentState';
	import { X } from 'lucide-svelte';
	import Modal from '../common/Modal.svelte';
	import AgentPanel from '../chat/AgentPanel.svelte';
	
	export let show = false;
	
	$: showModal = $agentState.showTaskPanel || $agentState.showReasoningPanel;
	
	// Sync the modal visibility with the agent state
	$: if (showModal && !show) {
		show = true;
	}
	
	function closeModal() {
		show = false;
		agentState.update(state => ({
			...state,
			showTaskPanel: false,
			showReasoningPanel: false
		}));
	}
</script>

<Modal bind:show size="lg">
	<div class="flex items-center justify-between text-lg font-medium dark:text-gray-300 px-5 pt-4 pb-3">
		<div class="flex items-center gap-2">
			Agent Activity
		</div>
		<button
			class="self-center p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
			on:click={closeModal}
		>
			<X size={16} />
		</button>
	</div>
	
	<div class="px-5 pb-5 h-[70vh] overflow-hidden">
		<AgentPanel />
	</div>
</Modal>
