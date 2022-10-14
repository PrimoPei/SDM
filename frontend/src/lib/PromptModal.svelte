<script lang="ts">
	import { createEventDispatcher, onMount, tick } from 'svelte';
	import { useMyPresence } from '$lib/liveblocks';
	import { Status } from '$lib/types';

	const dispatch = createEventDispatcher();
	export let initPrompt = '';
	let prompt: string;
	let inputEl: HTMLInputElement;
	let buttonEl: HTMLElement;
	const myPresence = useMyPresence();

	const onKeyup = (e: KeyboardEvent) => {
		if (e.key === 'Escape') {
			cancel(e);
		}
	};

	onMount(() => {
		inputEl.focus();
		inputEl.addEventListener('focusout', cancel);
		prompt = initPrompt;
		window.addEventListener('keyup', onKeyup);
		return () => {
			window.removeEventListener('keyup', onKeyup);
			inputEl.removeEventListener('focusout', cancel);
		};
	});

	let timer: NodeJS.Timeout;
	function debouce(newPrompt: string) {
		clearTimeout(timer);
		timer = setTimeout(() => {
			prompt = newPrompt;
			myPresence.update({
				currentPrompt: prompt,
				status: Status.prompting
			});
		}, 100);
	}
	function onPrompt() {
		if (prompt.trim() !== '') {
			console.log('Prompting with: ', prompt);
			dispatch('paint');
			dispatch('close');
		}
	}
	function onInput(event: Event) {
		const target = event.target as HTMLInputElement;
		debouce(target.value);
	}
	function cancel(event?: Event) {
		console.log(event?.relatedTarget)
		if (!(event instanceof KeyboardEvent) && event?.relatedTarget !== null) return;

		myPresence.update({
			status: Status.ready
		});
		dispatch('close');
	}
</script>

<form
	class="fixed w-screen top-0 left-0 bottom-0 right-0 max-h-screen z-50 flex items-center justify-center bg-black bg-opacity-80 px-3"
	on:submit|preventDefault={onPrompt}
>
	<div class="flex bg-white rounded-2xl px-2 w-full max-w-md">
		<input
			value={prompt}
			bind:this={inputEl}
			on:click|stopPropagation
			on:input={onInput}
			class="input"
			placeholder="Type a prompt..."
			title="Input prompt to generate image and obtain palette"
			type="text"
			name="prompt"
		/>
		<button
			bind:this={buttonEl}
			on:click|preventDefault={onPrompt}
			class="font-mono border-l-2 pl-2"
			type="submit">Paint</button
		>
	</div>
</form>

<style lang="postcss" scoped>
	.input {
		@apply flex-grow text-sm m-2 p-0 disabled:opacity-50 italic placeholder:text-black text-black placeholder:text-opacity-50 border-0 focus:outline-none focus:border-gray-400 focus:ring-1;
	}
</style>
