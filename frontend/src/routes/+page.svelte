<script lang="ts">
	import { onMount } from 'svelte';
	import { isLoading, loadingState, createPresenceStore, createStorageStore } from '$lib/store';
	import { PUBLIC_WS_ENDPOINT, PUBLIC_DEV_MODE } from '$env/static/public';
	import type { Client, Room } from '@liveblocks/client';
	import { createClient, LiveList } from '@liveblocks/client';

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
			initialStorage: { imagesList: new LiveList() }
		});
		const unsubscribe = room.subscribe('error', (error) => {
			console.error('error', error);
		});

		const unsubscribePresence = createPresenceStore(room);
		createStorageStore(room);
		return () => {
			if (client && room) {
				client.leave(roomId);
				unsubscribePresence();
			}
		};
	});
</script>

<div class="max-w-screen-md mx-auto p-5 relative pointer-events-none touch-none z-10">
	<h1 class="text-lg md:text-3xl font-bold leading-normal">
		Stable Diffussion Outpainting Multiplayer
	</h1>
</div>
{#if room}
	<App {room} />
{/if}
