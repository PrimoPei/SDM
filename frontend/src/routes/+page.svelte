<script lang="ts">
	import { onMount } from 'svelte';
	import { isLoading, loadingState, createPresenceStore, createStorageStore } from '$lib/store';
	import type { Client, Room } from '@liveblocks/client';
	import { createClient, LiveList } from '@liveblocks/client';

	import App from '$lib/App.svelte';
	import type { Presence, Storage } from '$lib/types';

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
