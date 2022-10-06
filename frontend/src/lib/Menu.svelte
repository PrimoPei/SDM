<script lang="ts">
	import { showFrames } from '$lib/store';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();
</script>

<div class="grid grid-cols-4 gap-3 text-sm w-max mx-auto">
	<div class="flex items-center">
		<input
			id="showframes"
			type="checkbox"
			bind:checked={$showFrames}
			class="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 cursor-pointer"
		/>
		<label for="showframes" class="text-white dark:text-white cursor-pointer ml-2">
			Show Frames
		</label>
	</div>
	<button class="button" title="Move" on:click={() => dispatch('paintMode', { mode: 'move' })}>
		Move
	</button>
	<button
		class="button-paint bg-violet-100 text-violet-900"
		title="New Paint Frame"
		on:click={() => dispatch('paintMode', { mode: 'paint' })}
	>
		<span
			class="rounded-sm h-5 w-5 m-1 flex justify-center items-center border-2 border-dashed border-violet-700 mr-2"
			>+</span
		>
		Paint
	</button>
</div>

<style lang="postcss" scoped>
	.button {
		@apply disabled:opacity-50 dark:bg-white dark:text-black bg-black text-white rounded-2xl text-xs shadow-sm focus:outline-none focus:border-gray-400;
	}
	.button-paint {
		@apply flex justify-center items-center disabled:opacity-50  dark:bg-white dark:text-black rounded-2xl shadow-sm focus:outline-none focus:border-gray-400;
	}
</style>
