<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import PPButton from '$lib/Buttons/PPButton.svelte';
	const dispatch = createEventDispatcher();

	const onKeyup = (e: KeyboardEvent) => {
		if (e.key === 'Enter') {
			dispatch('prompt');
		}
	};
	onMount(() => {
		window.addEventListener('keyup', onKeyup);
		return () => {
			window.removeEventListener('keyup', onKeyup);
		};
	});
</script>

<div class="grid grid-cols-1 gap-3 w-max mx-auto">
	<PPButton on:click={() => dispatch('prompt')} />
</div>
