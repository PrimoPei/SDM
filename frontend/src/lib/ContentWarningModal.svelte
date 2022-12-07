<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';

	const dispatch = createEventDispatcher();

	let okButton: HTMLButtonElement;

	onMount(() => {
		okButton.focus();
	});
</script>

<form
	class="fixed w-screen top-0 left-0 bottom-0 right-0 h-screen z-50 flex items-center justify-center bg-black bg-opacity-80"
>
	<div
		class="text-center p-3 m-3 bg-white overflow-hidden rounded-2xl w-full max-w-lg 2xl:max-w-xl"
	>
		<h3
			class="font-semibold text-black text-base 2xl:text-2xl spacing tracking-wide hover:saturate-150 mb-3"
		>
			Since the project is an open interactive art canvas, you may encounter some disturbing and
			potentially NSFW content in the rooms.
		</h3>

		<button
			bind:this={okButton}
			on:click={() => dispatch('contentModal')}
			class="font-semibold bg-blue-700 text-white rounded-lg px-5 text-xl 2xl:text-2xl spacing tracking-wide hover:saturate-150"
			title="Input prompt to generate image and  negative prompt inside brackets <NEGATIVE PROMPT>"
			>OK
		</button>
	</div>
</form>
