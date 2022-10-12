<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import PPButton from '$lib/Buttons/PPButton.svelte';
	const dispatch = createEventDispatcher();

	const onKeyup = (e: KeyboardEvent) => {
		if (e.key === 'Enter') {
			dispatch('paintMode', { mode: 'paint' });
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
	<!-- <div class="flex items-center">
		<input
			id="showframes"
			type="checkbox"
			bind:checked={$showFrames}
			class="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 cursor-pointer"
		/>
		<label for="showframes" class="text-white dark:text-white cursor-pointer ml-2">
			Show Frames
		</label>
	</div> -->
	<!-- <button class="button" title="Move" on:click={() => dispatch('paintMode', { mode: 'move' })}>
		Move
	</button> -->
	<PPButton on:click={() => dispatch('paintMode', { mode: 'paint' })} />
</div>
