<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import PPButton from '$lib/Buttons/PPButton.svelte';
	import RoomsSelector from '$lib/Buttons/RoomsSelector.svelte';
	import AboutButton from '$lib/Buttons/AboutButton.svelte';

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

<div class="flex justify-center">
	<button
		on:click={() => dispatch('prompt')}
		class="text-3xl bg-blue-600 text-white px-6 py-2 rounded-xl ring ring-blue-500 font-semibold shadow-2xl"
		>🖍 Paint</button
	>
	<!-- <PPButton {isLoading} on:click={() => dispatch('prompt')} /> -->
	<RoomsSelector {isLoading} />
	<AboutButton on:click={() => dispatch('toggleAbout')} />
</div>
