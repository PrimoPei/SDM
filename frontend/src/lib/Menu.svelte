<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import PPButton from '$lib/Buttons/PPButton.svelte';
	import RoomsSelector from './Buttons/RoomsSelector.svelte';
	const dispatch = createEventDispatcher();
	export let isLoading = false;
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

<div class="grid grid-cols-1 gap-1 w-max mx-auto">
	<PPButton {isLoading} on:click={() => dispatch('prompt')} />
	<RoomsSelector {isLoading} />
</div>
