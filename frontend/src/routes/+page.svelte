<script lang="ts">
	import { onMount } from 'svelte';
	import { isLoading, loadingState, createPresenceStore } from '$lib/store';
	import { PUBLIC_WS_ENDPOINT, PUBLIC_DEV_MODE } from '$env/static/public';
	import type { Client, Room } from '@liveblocks/client';
	import { createClient } from '@liveblocks/client';

	import App from '$lib/App.svelte';
	import type { Presence, Storage } from '$lib/types';
	console.log('PUBLIC_DEV_MODE', PUBLIC_DEV_MODE);
	const apiUrl =
		PUBLIC_DEV_MODE === 'DEV'
			? 'http://localhost:7860'
			: '/embed/huggingface-projects/color-palette-generator-sd';

	console.log(apiUrl);

	let client: Client;
	let room: Room;
	let roomId = 'multiplayer-SD';

	onMount(() => {
		client = createClient({
			publicApiKey: 'pk_test_JlUZGH3kQmhmZQiqU2l8eIi5'
		});

		room = client.enter<Presence, Storage /* UserMeta, RoomEvent */>(roomId, {
			initialPresence: {
				cursor: null
			},
			initialStorage: {}
		});
		const unsubscribe = room.subscribe('history', (e) => {
			// Do something
			console.log('history', e);
		});
		const unsubscribePresence = createPresenceStore(room);
		return () => {
			if (client && room) {
				client.leave(roomId);
				unsubscribePresence();
				unsubscribe();
			}
		};
	});
</script>

<div class="max-w-screen-md mx-auto px-3 py-8 relative">
	<div class="relative z-10">
		<h1 class="text-3xl font-bold leading-normal">Stable Diffussion Outpainting Multiplayer</h1>
		<p class="text-sm" />
		<div class="relative bg-white dark:bg-black py-3">
			<form class="grid grid-cols-6">
				<input
					class="input"
					placeholder="A photo of a beautiful sunset in San Francisco"
					title="Input prompt to generate image and obtain palette"
					type="text"
					name="prompt"
					disabled={$isLoading}
				/>
				<button class="button" disabled={$isLoading} title="Generate Palette">
					Create Palette
				</button>
			</form>
		</div>
	</div>
	<div class="relative z-0">
		{#if room}
			<App {room} />
		{/if}
	</div>
</div>

<style lang="postcss" scoped>
	.link {
		@apply text-xs underline font-bold hover:no-underline hover:text-gray-500 visited:text-gray-500;
	}
	.input {
		@apply text-sm disabled:opacity-50 col-span-4 md:col-span-5 italic dark:placeholder:text-black placeholder:text-white text-white dark:text-black placeholder:text-opacity-30 dark:placeholder:text-opacity-10 dark:bg-white bg-slate-900 border-2 border-black rounded-2xl px-2 shadow-sm focus:outline-none focus:border-gray-400 focus:ring-1;
	}
	.button {
		@apply disabled:opacity-50 col-span-2 md:col-span-1 dark:bg-white dark:text-black border-2 border-black rounded-2xl ml-2 px-2 py-2  text-xs shadow-sm font-bold focus:outline-none focus:border-gray-400;
	}
</style>
