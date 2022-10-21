<script lang="ts">
	import { onMount } from 'svelte';
	import { createClient } from '@liveblocks/client';
	import type { Client } from '@liveblocks/client';
	import LiveblocksProvider from '$lib/liveblocks/LiveblocksProvider.svelte';
	import RoomProvider from '$lib/liveblocks/RoomProvider.svelte';
	import App from '$lib/App.svelte';
	import About from '$lib/About.svelte';
	import { PUBLIC_API_BASE } from '$env/static/public';
	import { selectedRoomID, toggleAbout } from '$lib/store';
	import type { RoomResponse } from '$lib/types';
	import { MAX_CAPACITY } from '$lib/constants';

	let loading = true;
	let client: Client;

	$: roomId = $selectedRoomID;

	onMount(() => {
		// document.addEventListener('wheel', (e) => e.preventDefault(), { passive: false });
		client = createClient({
			authEndpoint: PUBLIC_API_BASE + '/auth'
		});

		updateRooms();
	});
	async function updateRooms() {
		loading = true;
		const roomidParam = new URLSearchParams(window.location.search).get('roomid');
		const res = await fetch(PUBLIC_API_BASE + '/rooms');
		const rooms: RoomResponse[] = await res.json();

		if (roomidParam) {
			const room = rooms.find((room) => room.room_id === roomidParam);
			if (room) {
				selectedRoomID.set(roomidParam);
			}
		} else {
			const room = rooms.find((room) => room.users_count < MAX_CAPACITY) || null;
			selectedRoomID.set(room ? room.room_id : null);
		}
		loading = false;
		return { rooms };
	}
</script>

<About classList={$toggleAbout ? 'flex' : 'hidden'} on:click={() => ($toggleAbout = false)} />

{#if !loading}
	<LiveblocksProvider {client}>
		{#if roomId}
			<RoomProvider id={roomId}>
				<App />
			</RoomProvider>
		{:else}
			<div class="flex flex-col items-center justify-center h-full">
				<h1 class="text-2xl font-bold">No room selected</h1>
				<p class="text-gray-500">Please select a room in the URL</p>
			</div>
		{/if}
	</LiveblocksProvider>
{:else}
	<div class="flex flex-col items-center justify-center h-full">
		<h1 class="text-2xl font-bold">Loading...</h1>
	</div>
{/if}
