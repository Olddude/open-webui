<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import Chat from '$lib/components/chat/Chat.svelte';

	onMount(() => {
		// Any initialization logic can go here
	});
</script>

<div class="h-full w-full">
	<Chat chatIdProp={$page.params.id} />
</div>