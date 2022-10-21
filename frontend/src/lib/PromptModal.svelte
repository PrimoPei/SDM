<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { useMyPresence } from '$lib/liveblocks';
	import { Status } from '$lib/types';

	const dispatch = createEventDispatcher();
	export let initPrompt = '';
	let prompt: string;
	let inputEl: HTMLInputElement;
	let boxEl: HTMLDivElement;
	const myPresence = useMyPresence();

	const onKeyup = (e: KeyboardEvent) => {
		if (e.key === 'Escape') {
			myPresence.update({
				status: Status.ready
			});
			dispatch('close');
		}
	};

	onMount(() => {
		inputEl.focus();
		prompt = initPrompt;
		window.addEventListener('keyup', onKeyup);
		window.addEventListener('pointerdown', cancelHandler, true);

		return () => {
			window.removeEventListener('keyup', onKeyup);
			window.removeEventListener('pointerdown', cancelHandler, true);
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
			dispatch('paint');
			dispatch('close');
		}
	}
	function onInput(event: Event) {
		const target = event.target as HTMLInputElement;
		debouce(target.value);
	}
	function cancelHandler(event: Event) {
		if (boxEl.contains(event.target as Node)) {
			return;
		}
		myPresence.update({
			status: Status.ready
		});
		dispatch('close');
	}
</script>

<form
	class="fixed w-screen top-0 left-0 bottom-0 right-0 max-h-screen z-50 flex items-center justify-center bg-black bg-opacity-80"
	on:submit|preventDefault={onPrompt}
>
	<div
		class="flex bg-white itemx-center overflow-hidden rounded-lg w-full max-w-lg 2xl:max-w-xl"
		bind:this={boxEl}
	>
		<input
			value={prompt}
			bind:this={inputEl}
			on:click|stopPropagation
			on:input={onInput}
			class="flex-1 outline-none ring-0 border-none text-xl 2xl:text-2xl"
			placeholder="Describe your prompt"
			title="Input prompt to generate image and obtain palette"
			type="text"
			name="prompt"
		/>
		<button
			on:click|preventDefault={onPrompt}
			class="font-bold bg-blue-700 text-white border-l-2 px-5 text-xl 2xl:text-2xl spacing tracking-wide"
			type="submit"><span class="mr-2">🖌</span> Paint</button
		>
	</div>
</form>
