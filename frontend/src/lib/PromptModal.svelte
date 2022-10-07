<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { useMyPresence } from '$lib/liveblocks';

	const dispatch = createEventDispatcher();
	let prompt: string;
	let inputEl: HTMLInputElement;
	const myPresence = useMyPresence();

	$: {
		myPresence.update({
			currentPrompt: prompt,
			isPrompting: true
		});
	}

	const onKeyup = (e: KeyboardEvent) => {
		if (e.key === 'Escape') {
			dispatch('close');
			myPresence.update({
				currentPrompt: '',
				isPrompting: false
			});
		}
	};
	onMount(() => {
		inputEl.focus();
		window.addEventListener('keyup', onKeyup);
		return () => {
			window.removeEventListener('keyup', onKeyup);
		};
	});

	function onPrompt() {
		if (prompt.trim() !== '') {
			dispatch('prompt', prompt);
		}
	}
</script>

<form
	class="fixed w-screen top-0 left-0 bottom-0 right-0 max-h-screen z-50 flex items-center justify-center bg-black bg-opacity-80 px-3"
	on:submit|preventDefault={onPrompt}
	on:click={() => dispatch('close')}
>
	<input
		bind:this={inputEl}
		bind:value={prompt}
		on:click|stopPropagation
		class="input"
		placeholder="Type a prompt..."
		title="Input prompt to generate image and obtain palette"
		type="text"
		name="prompt"
	/>
</form>

<style lang="postcss" scoped>
	.input {
		@apply w-full max-w-sm text-sm disabled:opacity-50 italic placeholder:text-white text-white placeholder:text-opacity-50 bg-slate-900 border-2 border-white rounded-2xl px-2 shadow-sm focus:outline-none focus:border-gray-400 focus:ring-1;
	}
</style>
