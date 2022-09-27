<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	const dispatch = createEventDispatcher();
	let prompt: string;

	const onKeyup = (e: KeyboardEvent) => {
		if (e.key === 'Escape') {
			dispatch('close');
		}
	};
	onMount(() => {
		window.addEventListener('keyup', onKeyup);
		return () => {
			window.removeEventListener('keyup', onKeyup);
		};
	});
</script>

<form
	class="fixed w-screen top-0 left-0 bottom-0 right-0 max-h-screen z-50 flex items-center justify-center bg-black bg-opacity-80 px-3"
	on:submit|preventDefault={() => dispatch('prompt', { prompt })}
	on:click={() => dispatch('close')}
>
	<input
		on:click|stopPropagation
		class="input"
		placeholder="Type a prompt..."
		title="Input prompt to generate image and obtain palette"
		type="text"
		name="prompt"
		bind:value={prompt}
	/>
</form>

<style lang="postcss" scoped>
	.link {
		@apply text-xs underline font-bold hover:no-underline hover:text-gray-500 visited:text-gray-500;
	}
	.input {
		@apply w-full max-w-sm text-sm disabled:opacity-50 italic placeholder:text-white text-white placeholder:text-opacity-50 bg-slate-900 border-2 border-white rounded-2xl px-2 shadow-sm focus:outline-none focus:border-gray-400 focus:ring-1;
	}
</style>
